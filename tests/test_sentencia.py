"""Testes de `src/sentencia.py` (Fase 2 - Sentenciacao).

`split_sentences` e sempre mockado via `monkeypatch.setattr` - nenhum teste
aqui instancia `wtpsplit.SaT` nem toca rede. Fixtures de
`raw/<video_id>.json` sao escritas em `tmp_path`, no formato real que
`src/coleta.py` grava (`fragments` com `start`/`duration`/`text`,
`metadata.duration`).
"""

from __future__ import annotations

import json
from pathlib import Path

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
                {"start": 0.0, "duration": 2.0, "text": "Hello"},
                {"start": 2.0, "duration": 2.0, "text": "there. World today."},
            ],
            duration=4.0,
        )

        # texto corrido: "Hello there. World today." - a sentenca mockada
        # abaixo cruza a fronteira dos dois chunks originais (chunk0="Hello",
        # chunk1="there. World today."). Ambas as sentencas terminam em
        # pontuacao terminal, entao `merge_incomplete_boundaries` nao mexe -
        # o teste cobre so a reatribuicao de timestamp por offset.
        monkeypatch.setattr(
            sentencia, "split_sentences", lambda text: ["Hello there. ", "World today."]
        )

        records = sentencia.sentence_records("v1", raw_dir=raw_dir)

        assert len(records) == 2
        assert records[0]["text"] == "Hello there."
        assert records[0]["start_s"] == 0.0  # do chunk0 ("Hello")
        assert records[0]["end_s"] == 4.0  # do chunk1 ("there. World today.")
        assert records[1]["text"] == "World today."
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
            [{"start": 0.0, "duration": 5.0, "text": "hello world. foo bar."}],
            duration=5.0,
        )

        monkeypatch.setattr(
            sentencia, "split_sentences", lambda text: ["hello world. ", "foo bar."]
        )

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


# --------------------------------------------------------------------------
# merge_incomplete_boundaries: fixture de regressao da Issue #9 (28 casos
# da Issue #8) - 22 `open` tem que fundir, 6 `false_positive` tem que ficar
# intocados
# --------------------------------------------------------------------------

# `predict_boundary_proba` real (`sat-3l-sm`) medido ao vivo contra
# `raw/*.json` pra cada um dos 28 candidatos, na fronteira exata (Fase A da
# Issue #9) - usado aqui so pros casos em que nenhum sinal estrutural
# decide sozinho (o desempate por confianca), exatamente como
# `sentence_records` vai usar em producao.
_FIXTURE_BOUNDARY_CONFIDENCE = {
    "0neQIzWDXaM:s0091": 0.9910492897033691,
    "5agqeNtjstU:s0158": 0.6639958620071411,
    "88xZotShpxY:s0132": 0.3670434057712555,
    "88xZotShpxY:s0187": 0.5006775856018066,
    "88xZotShpxY:s0208": 0.6467949151992798,
    "AvF3bPcqZeM:s0031": 0.3453260362148285,
    "McXn53SKXYg:s0011": 0.40250954031944275,
    "McXn53SKXYg:s0058": 0.7764534950256348,
    "NcITexwM0Fg:s0102": 0.37250518798828125,
    "NcITexwM0Fg:s0236": 0.00032503585680387914,
    "Qgz_k2JQ3UY:s0097": 0.4093978703022003,
    "Qgz_k2JQ3UY:s0165": 0.5476152896881104,
    "Qgz_k2JQ3UY:s0230": 0.983020007610321,
    "f59QqKgwuq0:s0016": 0.8852352499961853,
    "f59QqKgwuq0:s0098": 0.39881613850593567,
    "f59QqKgwuq0:s0105": 0.2375759482383728,
    "kLYsABip8tI:s0243": 0.14487324655056,
    "lkLwp9o7Djk:s0105": 0.8478417992591858,
    "lkLwp9o7Djk:s0211": 0.002415483118966222,
    "lkLwp9o7Djk:s0222": 0.602587878704071,
    "lkLwp9o7Djk:s0233": 0.24816960096359253,
    "pJYm-8WQbEE:s0046": 0.8312800526618958,
    "pJYm-8WQbEE:s0290": 0.4797017574310303,
    "qsBitnO8djE:s0004": 0.9069831967353821,
    "qsBitnO8djE:s0102": 0.6976089477539062,
    "wihLSMVD6iM:s0085": 0.5223240256309509,
    "yKqe_ey3QOs:s0250": 0.9770664572715759,
    "z1StpnRL4k4:s0116": 0.3845653831958771,
}

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fase2_sentence_boundary_regression.json"


def _load_fixture_cases():
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return payload["cases"]


def _records_for(text, next_text):
    return [
        {
            "sent_id": "x:s0000",
            "video_id": "x",
            "idx": 0,
            "start_s": 0.0,
            "end_s": 1.0,
            "text": text,
            "n_words": len(text.split()),
        },
        {
            "sent_id": "x:s0001",
            "video_id": "x",
            "idx": 1,
            "start_s": 1.0,
            "end_s": 2.0,
            "text": next_text,
            "n_words": len(next_text.split()),
        },
    ]


class TestMergeIncompleteBoundariesFixture:
    @pytest.mark.parametrize("case", _load_fixture_cases(), ids=lambda c: c["sent_id"])
    def test_28_case_regression_fixture(self, case):
        """Todos os 28 casos da Issue #8: os 22 `open` fundem numa unica
        sentenca, os 6 `false_positive` ficam intocados (2 sentencas)."""
        records = _records_for(case["text"], case["next_text"])
        confidence = _FIXTURE_BOUNDARY_CONFIDENCE[case["sent_id"]]

        merged = sentencia.merge_incomplete_boundaries(records, confidences=[confidence])

        if case["label"] == "open":
            assert len(merged) == 1, f"{case['sent_id']} devia fundir ({case['reason']})"
            assert merged[0]["text"] == f"{case['text']} {case['next_text']}"
        else:
            assert len(merged) == 2, f"{case['sent_id']} nao pode fundir ({case['reason']})"
            assert merged[0]["text"] == case["text"]
            assert merged[1]["text"] == case["next_text"]

    def test_fixture_has_22_open_and_6_false_positive(self):
        cases = _load_fixture_cases()
        assert len(cases) == 28
        assert sum(1 for c in cases if c["label"] == "open") == 22
        assert sum(1 for c in cases if c["label"] == "false_positive") == 6


# --------------------------------------------------------------------------
# merge_incomplete_boundaries: edge cases
# --------------------------------------------------------------------------


class TestMergeIncompleteBoundariesEdgeCases:
    def test_single_record_is_returned_unchanged(self):
        records = [
            {
                "sent_id": "x:s0000",
                "video_id": "x",
                "idx": 0,
                "start_s": 0.0,
                "end_s": 1.0,
                "text": "A life of maximized comfort and routine",
                "n_words": 6,
            }
        ]

        merged = sentencia.merge_incomplete_boundaries(records)

        assert merged == records

    def test_terminal_punctuation_never_merges_even_with_low_confidence(self):
        """Fronteira so e candidata se a sentenca nao termina em ./!/? -
        confianca baixa sozinha nao funde uma sentenca ja fechada."""
        records = _records_for("This is a complete sentence.", "So is this one.")

        merged = sentencia.merge_incomplete_boundaries(records, confidences=[0.01])

        assert len(merged) == 2

    def test_undetermined_signal_without_confidences_defaults_to_no_merge(self):
        """Sem `confidences`, um caso `undetermined` (nenhum sinal
        estrutural decide) fica sem fundir - padrao seguro, nunca "virgula
        => funde" (explicitamente proibido pela Issue #9)."""
        # falso-positivo real da fixture: oracao ja completa (sujeito+verbo)
        # terminada em virgula por estilo - nenhum sinal estrutural dispara.
        records = _records_for(
            "This represents a genuinely fascinating, still actively debated mystery "
            "within archaeology,",
            "Exactly what kind of watercraft these early travelers used remains unclear.",
        )

        merged = sentencia.merge_incomplete_boundaries(records, confidences=None)

        assert len(merged) == 2

    def test_cascading_merge_across_three_consecutive_open_boundaries(self):
        """Depois de fundir `i` com `i+1`, o resultado combinado e
        reavaliado contra `i+2` - fusao em cascata."""
        records = [
            {
                "sent_id": "x:s0000",
                "video_id": "x",
                "idx": 0,
                "start_s": 0.0,
                "end_s": 1.0,
                "text": "Early",
                "n_words": 1,
            },
            {
                "sent_id": "x:s0001",
                "video_id": "x",
                "idx": 1,
                "start_s": 1.0,
                "end_s": 2.0,
                "text": "Modern humans with fully developed language and",
                "n_words": 6,
            },
            {
                "sent_id": "x:s0002",
                "video_id": "x",
                "idx": 2,
                "start_s": 2.0,
                "end_s": 3.0,
                "text": "symbolic culture emerged.",
                "n_words": 3,
            },
        ]

        merged = sentencia.merge_incomplete_boundaries(records)

        assert len(merged) == 1
        assert merged[0]["text"] == (
            "Early Modern humans with fully developed language and symbolic culture emerged."
        )
        assert merged[0]["start_s"] == 0.0
        assert merged[0]["end_s"] == 3.0
        assert merged[0]["idx"] == 0
        assert merged[0]["sent_id"] == "x:s0000"

    def test_merge_renumbers_idx_and_sent_id_sequentially(self):
        records = [
            {
                "sent_id": "x:s0000",
                "video_id": "x",
                "idx": 0,
                "start_s": 0.0,
                "end_s": 1.0,
                "text": "Historian",
                "n_words": 1,
            },
            {
                "sent_id": "x:s0001",
                "video_id": "x",
                "idx": 1,
                "start_s": 1.0,
                "end_s": 2.0,
                "text": "Roger spent decades on this.",
                "n_words": 5,
            },
            {
                "sent_id": "x:s0002",
                "video_id": "x",
                "idx": 2,
                "start_s": 2.0,
                "end_s": 3.0,
                "text": "It changed everything.",
                "n_words": 3,
            },
        ]

        merged = sentencia.merge_incomplete_boundaries(records)

        assert [r["idx"] for r in merged] == [0, 1]
        assert [r["sent_id"] for r in merged] == ["x:s0000", "x:s0001"]


# --------------------------------------------------------------------------
# sentence_records: integracao com merge_incomplete_boundaries
# --------------------------------------------------------------------------


class TestSentenceRecordsMergeIntegration:
    def test_structural_signal_merges_without_touching_the_model(self, tmp_path, monkeypatch):
        """Fronteira decidida por sinal estrutural (fragmento maiusculo
        isolado) funde dentro de `sentence_records` sem chamar
        `predict_boundary_proba` - mantem a suite rapida quando a fusao nao
        precisa do desempate por confianca."""
        raw_dir = tmp_path / "raw"
        _write_raw(
            raw_dir,
            "v1",
            [{"start": 0.0, "duration": 4.0, "text": "Historian Roger spent decades on this."}],
            duration=4.0,
        )
        monkeypatch.setattr(
            sentencia,
            "split_sentences",
            lambda text: ["Historian", " Roger spent decades on this."],
        )

        def _boom(text):
            raise AssertionError("predict_boundary_proba nao devia ser chamado")

        monkeypatch.setattr(sentencia, "predict_boundary_proba", _boom)

        records = sentencia.sentence_records("v1", raw_dir=raw_dir)

        assert len(records) == 1
        assert records[0]["text"] == "Historian Roger spent decades on this."

    def test_confidence_tiebreak_merges_when_no_structural_signal_fires(
        self, tmp_path, monkeypatch
    ):
        """Fronteira `undetermined` (nenhum sinal estrutural decide) funde
        quando `predict_boundary_proba` devolve confianca abaixo do
        limiar - o desempate por confianca so entra em jogo aqui."""
        raw_dir = tmp_path / "raw"
        text = (
            "It is found in whether or not you are willing to look at a person "
            "who is suffering in a way that makes you uncomfortable and still say, "
            "This is a person."
        )
        _write_raw(raw_dir, "v1", [{"start": 0.0, "duration": 2.0, "text": text}], duration=2.0)
        monkeypatch.setattr(
            sentencia,
            "split_sentences",
            lambda t: [
                "It is found in whether or not you are willing to look at a person "
                "who is suffering in a way that makes you uncomfortable and still say, ",
                "This is a person.",
            ],
        )
        monkeypatch.setattr(sentencia, "predict_boundary_proba", lambda t: [0.2481696] * len(t))

        records = sentencia.sentence_records("v1", raw_dir=raw_dir)

        assert len(records) == 1

    def test_confidence_at_or_above_threshold_does_not_merge(self, tmp_path, monkeypatch):
        raw_dir = tmp_path / "raw"
        text = (
            "This represents a genuinely fascinating, still actively debated mystery "
            "within archaeology, Exactly what happened remains unclear."
        )
        _write_raw(raw_dir, "v1", [{"start": 0.0, "duration": 2.0, "text": text}], duration=2.0)
        monkeypatch.setattr(
            sentencia,
            "split_sentences",
            lambda t: [
                "This represents a genuinely fascinating, still actively debated mystery "
                "within archaeology, ",
                "Exactly what happened remains unclear.",
            ],
        )
        monkeypatch.setattr(sentencia, "predict_boundary_proba", lambda t: [0.7764535] * len(t))

        records = sentencia.sentence_records("v1", raw_dir=raw_dir)

        assert len(records) == 2
