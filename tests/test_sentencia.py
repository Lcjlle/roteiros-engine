"""Testes de `src/sentencia.py` (Fase 2 - Sentenciacao).

`split_sentences` e sempre mockado via `monkeypatch.setattr` - nenhum teste
aqui instancia `wtpsplit.SaT` nem toca rede. Fixtures de
`raw/<video_id>.json` sao escritas em `tmp_path`, no formato real que
`src/coleta.py` grava (`fragments` com `start`/`duration`/`text`,
`metadata.duration`).
"""

from __future__ import annotations

import json

import pytest

from src import sentencia


def _write_raw(raw_dir, video_id, fragments, duration=100.0):
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "video_id": video_id,
        "source": "whisperx",
        "metadata": {
            "title": "titulo",
            "duration": duration,
            "view_count": 0,
            "published_at": "2026-01-01T00:00:00+00:00",
        },
        "fragments": fragments,
    }
    (raw_dir / f"{video_id}.json").write_text(json.dumps(payload), encoding="utf-8")


# --------------------------------------------------------------------------
# load_chunks
# --------------------------------------------------------------------------


class TestLoadChunks:
    def test_discards_marker_only_fragment(self, tmp_path):
        raw_dir = tmp_path / "raw"
        _write_raw(
            raw_dir,
            "v1",
            [
                {"start": 0.0, "duration": 1.0, "text": "[Music]"},
                {"start": 1.0, "duration": 2.0, "text": "hello there"},
            ],
            duration=10.0,
        )

        chunks, duration_s = sentencia.load_chunks("v1", raw_dir=raw_dir)

        assert chunks == [{"start_s": 1.0, "end_s": 3.0, "text": "hello there"}]
        assert duration_s == 10.0

    def test_all_fragments_discarded_yields_no_chunks(self, tmp_path):
        raw_dir = tmp_path / "raw"
        _write_raw(
            raw_dir,
            "v1",
            [
                {"start": 0.0, "duration": 1.0, "text": "[Music]"},
                {"start": 1.0, "duration": 1.0, "text": "[Applause]"},
            ],
            duration=5.0,
        )

        chunks, duration_s = sentencia.load_chunks("v1", raw_dir=raw_dir)

        assert chunks == []
        assert duration_s == 5.0


# --------------------------------------------------------------------------
# Reatribuicao de timestamp por offset (sentenca cruzando dois chunks)
# --------------------------------------------------------------------------


class TestSentenceRecordsOffsetReattachment:
    def test_sentence_spanning_two_chunks_gets_start_from_first_end_from_second(
        self, tmp_path, monkeypatch
    ):
        raw_dir = tmp_path / "raw"
        _write_raw(
            raw_dir,
            "v1",
            [
                {"start": 0.0, "duration": 2.0, "text": "hello"},
                {"start": 2.0, "duration": 2.0, "text": "there world"},
            ],
            duration=4.0,
        )

        # texto corrido: "hello there world" - a sentenca mockada abaixo
        # cruza a fronteira dos dois chunks originais (chunk0="hello",
        # chunk1="there world").
        monkeypatch.setattr(sentencia, "split_sentences", lambda text: ["hello there ", "world"])

        records = sentencia.sentence_records("v1", raw_dir=raw_dir)

        assert len(records) == 2
        assert records[0]["text"] == "hello there"
        assert records[0]["start_s"] == 0.0  # do chunk0 ("hello")
        assert records[0]["end_s"] == 4.0  # do chunk1 ("there world")
        assert records[1]["text"] == "world"
        assert records[1]["start_s"] == 2.0
        assert records[1]["end_s"] == 4.0


# --------------------------------------------------------------------------
# sentence_records: caso normal
# --------------------------------------------------------------------------


class TestSentenceRecordsNormal:
    def test_sequential_sent_id_and_idx_with_correct_n_words(self, tmp_path, monkeypatch):
        raw_dir = tmp_path / "raw"
        _write_raw(
            raw_dir,
            "abc123",
            [{"start": 0.0, "duration": 5.0, "text": "hello world foo bar"}],
            duration=5.0,
        )

        monkeypatch.setattr(sentencia, "split_sentences", lambda text: ["hello world ", "foo bar"])

        records = sentencia.sentence_records("abc123", raw_dir=raw_dir)

        assert [r["sent_id"] for r in records] == ["abc123:s0000", "abc123:s0001"]
        assert [r["idx"] for r in records] == [0, 1]
        assert [r["video_id"] for r in records] == ["abc123", "abc123"]
        assert records[0]["n_words"] == 2
        assert records[1]["n_words"] == 2

    def test_no_chunks_returns_empty_list_without_error(self, tmp_path):
        raw_dir = tmp_path / "raw"
        _write_raw(raw_dir, "v1", [{"start": 0.0, "duration": 1.0, "text": "[Music]"}])

        records = sentencia.sentence_records("v1", raw_dir=raw_dir)

        assert records == []

    def test_last_sentence_empty_after_strip_is_discarded_without_incrementing_idx(
        self, monkeypatch
    ):
        chunks = [{"start_s": 0.0, "end_s": 1.0, "text": "hello "}]
        monkeypatch.setattr(sentencia, "load_chunks", lambda video_id, raw_dir=None: (chunks, 1.0))
        # ultimo segmento devolvido pelo wtpsplit e so espaco - possivel
        # porque strip_whitespace=False preserva esses segmentos.
        monkeypatch.setattr(sentencia, "split_sentences", lambda text: ["hello", " "])

        records = sentencia.sentence_records("v1")

        assert len(records) == 1
        assert records[0]["idx"] == 0
        assert records[0]["sent_id"] == "v1:s0000"
        assert records[0]["text"] == "hello"


# --------------------------------------------------------------------------
# Invariante do offset: AssertionError
# --------------------------------------------------------------------------


class TestSentenceRecordsInvariant:
    def test_raises_when_mock_does_not_reconstitute_text(self, tmp_path, monkeypatch):
        raw_dir = tmp_path / "raw"
        _write_raw(raw_dir, "v1", [{"start": 0.0, "duration": 1.0, "text": "hello world"}])

        monkeypatch.setattr(sentencia, "split_sentences", lambda text: ["not the same text"])

        with pytest.raises(AssertionError):
            sentencia.sentence_records("v1", raw_dir=raw_dir)

    def test_raises_when_mock_returns_empty_list_for_nonempty_text(self, tmp_path, monkeypatch):
        raw_dir = tmp_path / "raw"
        _write_raw(raw_dir, "v1", [{"start": 0.0, "duration": 1.0, "text": "hello world"}])

        monkeypatch.setattr(sentencia, "split_sentences", lambda text: [])

        with pytest.raises(AssertionError):
            sentencia.sentence_records("v1", raw_dir=raw_dir)


# --------------------------------------------------------------------------
# write_sentences
# --------------------------------------------------------------------------


class TestWriteSentences:
    def test_writes_empty_sentences_list_for_video_with_no_sentences(self, tmp_path):
        sentences_dir = tmp_path / "sentences"

        path = sentencia.write_sentences("v1", [], 5.0, sentences_dir=sentences_dir)

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["video_id"] == "v1"
        assert payload["duration_s"] == 5.0
        assert payload["sentences"] == []
        assert "generated_at" in payload


# --------------------------------------------------------------------------
# run(): so profile, holdout intocado
# --------------------------------------------------------------------------


class TestRun:
    def test_only_profile_rows_are_sentenced_holdout_untouched(self, tmp_path, monkeypatch):
        raw_dir = tmp_path / "raw"
        sentences_dir = tmp_path / "sentences"
        manifest_path = tmp_path / "manifesto.csv"

        _write_raw(raw_dir, "p1", [{"start": 0.0, "duration": 2.0, "text": "hello world"}])

        manifest_path.write_text(
            "id,titulo,duracao_s,contagem_palavras,fonte,role\n"
            "p1,titulo,2,2,whisperX,profile\n"
            "h1,titulo,2,,,holdout\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(sentencia, "split_sentences", lambda text: [text])

        processed = sentencia.run(
            manifest_path=manifest_path, raw_dir=raw_dir, sentences_dir=sentences_dir
        )

        assert processed == ["p1"]
        assert (sentences_dir / "p1.json").exists()
        assert not (sentences_dir / "h1.json").exists()
