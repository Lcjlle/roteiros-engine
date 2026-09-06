"""Testes de `src/gold.py` (Fase 4 - selecao do gold, issue #18, e
exportacao dos worksheets de anotacao, issue #20)."""

from __future__ import annotations

import json
import random
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from src import gold
from src.schema_loader import load_ontology


def _make_windows(video_id, texts):
    return [
        {
            "window_id": f"{video_id}:j{i:04d}",
            "video_id": video_id,
            "idx": i,
            "sent_ids": [f"{video_id}:s{i:04d}"],
            "start_s": i * 10.0,
            "end_s": i * 10.0 + 5.0,
            "text": text,
            "n_words": len(text.split()),
            "n_sentences": 1,
            "pos_pct": i * 0.01,
        }
        for i, text in enumerate(texts)
    ]


def _write_windows(windows_dir, video_id, texts):
    windows_dir.mkdir(parents=True, exist_ok=True)
    windows = _make_windows(video_id, texts)
    payload = {"video_id": video_id, "generated_at": "2026-01-01T00:00:00Z", "windows": windows}
    (windows_dir / f"{video_id}.json").write_text(json.dumps(payload), encoding="utf-8")


# --------------------------------------------------------------------------
# scan_cta_candidates contra o corpus real
# --------------------------------------------------------------------------


class TestScanCtaCandidatesRealCorpus:
    def test_reproduces_the_eight_candidates_from_the_real_corpus(self):
        video_ids = sorted(gold.profile_video_ids())
        assert len(video_ids) == 30

        candidates = gold.scan_cta_candidates(video_ids)

        assert candidates == [
            "0neQIzWDXaM",
            "7xgt_LQxedc",
            "MMycNJ05f8M",
            "Qgz_k2JQ3UY",
            "Y_-aMBlHWgE",
            "kLYsABip8tI",
            "pPm3vHUQCpo",
            "yKqe_ey3QOs",
        ]

    def test_result_is_sorted_plain_not_case_folded_key(self):
        video_ids = sorted(gold.profile_video_ids())
        candidates = gold.scan_cta_candidates(video_ids)
        assert candidates == sorted(candidates)


class TestScanCtaCandidatesSynthetic:
    def test_matches_case_insensitive_only_the_three_fixed_phrases(self, tmp_path):
        windows_dir = tmp_path / "windows"
        _write_windows(windows_dir, "hit-desc", ["nothing here", "Link In The Description, thanks"])
        _write_windows(windows_dir, "hit-comment", ["Let me know in the comments what you think"])
        _write_windows(windows_dir, "miss", ["subscribe and hit the bell", "see you next time"])
        _write_windows(windows_dir, "near-miss", ["let us know down in the comments below"])

        candidates = gold.scan_cta_candidates(
            ["hit-desc", "hit-comment", "miss", "near-miss"], windows_dir=windows_dir
        )

        assert candidates == ["hit-comment", "hit-desc"]

    def test_scans_the_whole_video_not_only_the_ending(self, tmp_path):
        windows_dir = tmp_path / "windows"
        # a frase esta na primeira janela (pos_pct baixo), nao no fim do video
        _write_windows(
            windows_dir,
            "early-cta",
            ["link in the description"] + [f"filler sentence {i}" for i in range(20)],
        )

        candidates = gold.scan_cta_candidates(["early-cta"], windows_dir=windows_dir)

        assert candidates == ["early-cta"]


# --------------------------------------------------------------------------
# select_gold_videos - as duas ramificacoes, pool sintetico, semente fixa
# --------------------------------------------------------------------------


class TestSelectGoldVideosBranches:
    def test_candidates_found_anchors_and_samples_the_rest(self):
        # Pool sintetico de 5 videos, 2 sao candidatos a cta.
        # Calculado a mao rodando os mesmos dois primitivos do stdlib,
        # fora de `src/gold.py`, na mesma ordem que o contrato exige:
        #   rng = random.Random(5)
        #   anchor = rng.choice(sorted(["C", "A"]))       -> "C"
        #   rest = rng.sample(sorted(["B","D","E"]), 4... # ver abaixo
        # sorted(candidates) = ["A", "C"]; com seed=5 o primeiro
        # rng.choice(["A", "C"]) cai no indice 1 -> anchor = "C".
        # sorted(pool sem o anchor) = ["A", "B", "D", "E"]; o
        # rng.sample(..., 4) seguinte, no mesmo estado do rng, produz
        # ["D", "E", "A", "B"]. Ambos os valores foram obtidos chamando
        # `random.Random(5)` isoladamente (sem importar `src/gold.py`)
        # e reproduzidos aqui como oraculo da regressao.
        pool = ["A", "B", "C", "D", "E"]
        candidates = ["C", "A"]

        rng = random.Random(5)
        result = gold.select_gold_videos(candidates, pool, rng)

        assert result == ["C", "D", "E", "A", "B"]

    def test_no_candidates_samples_the_whole_pool_duration_blind(self):
        # Pool sintetico de 5 videos, nenhum candidato a cta encontrado.
        # Calculado a mao: sorted(pool) = ["v1","v2","v3","v4","v5"];
        # com `random.Random(1)`, `rng.sample(sorted(pool), 5)` (chamado
        # isoladamente do stdlib, fora de `src/gold.py`) produz
        # ["v2", "v1", "v5", "v4", "v3"].
        pool = ["v3", "v1", "v5", "v2", "v4"]
        candidates: list[str] = []

        rng = random.Random(1)
        result = gold.select_gold_videos(candidates, pool, rng)

        assert result == ["v2", "v1", "v5", "v4", "v3"]

    def test_never_touches_duration_only_video_ids(self):
        pool = ["A", "B", "C", "D", "E"]
        rng = random.Random(9)
        result = gold.select_gold_videos(["A"], pool, rng)
        assert set(result) == set(pool)
        assert all(isinstance(v, str) for v in result)


# --------------------------------------------------------------------------
# select_reannotation_video
# --------------------------------------------------------------------------


class TestSelectReannotationVideo:
    def test_picks_from_sorted_gold_with_the_same_rng_instance(self):
        # sorted(["B", "A", "C"]) = ["A", "B", "C"]; com `random.Random(6)`
        # (calculado isoladamente do stdlib), `rng.choice([...])` produz "C".
        rng = random.Random(6)
        result = gold.select_reannotation_video(["B", "A", "C"], rng)
        assert result == "C"


# --------------------------------------------------------------------------
# Fluxo completo - mesma instancia de rng, ordem do contrato
# --------------------------------------------------------------------------


class TestFullFlowRealCorpus:
    def test_reproduces_the_official_gold_and_reannotation(self):
        all_ids = sorted(gold.profile_video_ids())
        candidates = gold.scan_cta_candidates(all_ids)

        rng = random.Random(gold.GOLD_SEED)
        result_gold = gold.select_gold_videos(candidates, all_ids, rng)
        reannotation = gold.select_reannotation_video(result_gold, rng)

        assert result_gold == [
            "7xgt_LQxedc",
            "0neQIzWDXaM",
            "rk7qIWcLJ40",
            "Leol0DxxGe4",
            "C27Dd23jZzA",
        ]
        assert reannotation == "7xgt_LQxedc"


# --------------------------------------------------------------------------
# write_selection_artifact
# --------------------------------------------------------------------------


class TestWriteSelectionArtifact:
    def test_writes_seed_candidates_gold_durations_and_reannotation(self, tmp_path):
        manifest_path = tmp_path / "manifesto.csv"
        manifest_path.write_text(
            "id,titulo,duracao_s,contagem_palavras,fonte,role\n"
            "A,Titulo A,100,10,whisperX,profile\n"
            "B,Titulo B,200,20,whisperX,profile\n",
            encoding="utf-8",
        )
        out_path = tmp_path / "gold" / "mackexplains7" / "selection.json"

        result_path = gold.write_selection_artifact(
            cta_candidates_found=["A"],
            gold_video_ids=["A", "B"],
            reannotation_video_id="A",
            manifest_path=manifest_path,
            path=out_path,
        )

        assert result_path == out_path
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["seed"] == 42
        assert payload["cta_candidates_found"] == ["A"]
        assert payload["gold_video_ids"] == [
            {"video_id": "A", "duracao_s": 100},
            {"video_id": "B", "duracao_s": 200},
        ]
        assert payload["reannotation_video_id"] == "A"
        assert "generated_at" in payload

    def test_allows_empty_candidates_list(self, tmp_path):
        manifest_path = tmp_path / "manifesto.csv"
        manifest_path.write_text(
            "id,titulo,duracao_s,contagem_palavras,fonte,role\n"
            "A,Titulo A,100,10,whisperX,profile\n",
            encoding="utf-8",
        )
        out_path = tmp_path / "selection.json"

        gold.write_selection_artifact(
            cta_candidates_found=[],
            gold_video_ids=["A"],
            reannotation_video_id="A",
            manifest_path=manifest_path,
            path=out_path,
        )

        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["cta_candidates_found"] == []


# --------------------------------------------------------------------------
# Real selection artifact committed for the channel
# --------------------------------------------------------------------------


class TestRealSelectionArtifact:
    def test_committed_artifact_matches_the_official_selection(self):
        payload = json.loads(gold.SELECTION_PATH.read_text(encoding="utf-8"))

        assert payload["seed"] == 42
        assert payload["cta_candidates_found"] == [
            "0neQIzWDXaM",
            "7xgt_LQxedc",
            "MMycNJ05f8M",
            "Qgz_k2JQ3UY",
            "Y_-aMBlHWgE",
            "kLYsABip8tI",
            "pPm3vHUQCpo",
            "yKqe_ey3QOs",
        ]
        assert [g["video_id"] for g in payload["gold_video_ids"]] == [
            "7xgt_LQxedc",
            "0neQIzWDXaM",
            "rk7qIWcLJ40",
            "Leol0DxxGe4",
            "C27Dd23jZzA",
        ]
        assert payload["reannotation_video_id"] == "7xgt_LQxedc"
        assert all(isinstance(g["duracao_s"], int) for g in payload["gold_video_ids"])


# --------------------------------------------------------------------------
# export_round - schema exato das chaves do worksheet (sem window_id), issue #20
# --------------------------------------------------------------------------


def _expected_worksheet_keys():
    ontology = load_ontology()
    return {"display_id", "context", "target"} | {f["name"] for f in ontology["fields"]}


class TestExportRoundWorksheetSchema:
    def test_every_worksheet_line_has_exactly_the_public_schema_keys(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["a b c", "d e", "f", "g h i j"])}

        worksheet_path, _ = gold.export_round("V", "round1", windows_by_video, tmp_path)

        expected_keys = _expected_worksheet_keys()
        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 4
        for line in lines:
            record = json.loads(line)
            assert set(record.keys()) == expected_keys
            assert "window_id" not in record.keys()

    def test_every_ontology_field_starts_as_null(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["a", "b"])}

        worksheet_path, _ = gold.export_round("V", "round1", windows_by_video, tmp_path)

        ontology_field_names = [f["name"] for f in load_ontology()["fields"]]
        for line in worksheet_path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            for name in ontology_field_names:
                assert record[name] is None


# --------------------------------------------------------------------------
# export_round - .index.json mapeia display_id -> window_id, nunca no worksheet
# --------------------------------------------------------------------------


class TestExportRoundIndex:
    def test_index_has_one_entry_per_window_mapping_display_id_to_window_id(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["a", "b", "c"])}

        _, index_path = gold.export_round("V", "round1", windows_by_video, tmp_path)

        index = json.loads(index_path.read_text(encoding="utf-8"))
        assert len(index) == 3
        assert set(index.values()) == {"V:j0000", "V:j0001", "V:j0002"}

    def test_display_ids_in_worksheet_match_index_keys(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["a", "b"])}

        worksheet_path, index_path = gold.export_round("V", "round1", windows_by_video, tmp_path)

        index = json.loads(index_path.read_text(encoding="utf-8"))
        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        worksheet_display_ids = {json.loads(line)["display_id"] for line in lines}
        assert worksheet_display_ids == set(index.keys())


# --------------------------------------------------------------------------
# export_round - ordem, contagem e localizacao dos artefatos
# --------------------------------------------------------------------------


class TestExportRoundOrderingAndCount:
    def test_line_count_matches_window_count(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", [f"texto {i}" for i in range(7)])}

        worksheet_path, _ = gold.export_round("V", "round1", windows_by_video, tmp_path)

        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 7

    def test_lines_are_in_video_order(self, tmp_path):
        texts = [f"texto {i}" for i in range(5)]
        windows_by_video = {"V": _make_windows("V", texts)}

        worksheet_path, _ = gold.export_round("V", "round1", windows_by_video, tmp_path)

        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        targets = [json.loads(line)["target"] for line in lines]
        assert targets == texts

    def test_writes_files_under_out_dir_round_subdirectory(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["a"])}

        worksheet_path, index_path = gold.export_round("V", "round2", windows_by_video, tmp_path)

        assert worksheet_path == tmp_path / "round2" / "V.worksheet.jsonl"
        assert index_path == tmp_path / "round2" / "V.index.json"


# --------------------------------------------------------------------------
# export_round - contexto nunca inclui janela futura nem cruza video
# --------------------------------------------------------------------------


class TestExportRoundContextBoundaries:
    def test_context_never_includes_a_future_window_of_the_same_video(self, tmp_path):
        texts = [f"texto {i}" for i in range(6)]
        windows_by_video = {"V": _make_windows("V", texts)}

        worksheet_path, _ = gold.export_round("V", "round1", windows_by_video, tmp_path)

        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            record = json.loads(line)
            future_texts = set(texts[idx:])
            assert not (set(record["context"]) & future_texts)

    def test_context_never_crosses_video_boundaries(self, tmp_path):
        windows_by_video = {
            "A": _make_windows("A", ["a0", "a1", "a2"]),
            "B": _make_windows("B", ["b0", "b1", "b2"]),
        }

        worksheet_a, _ = gold.export_round("A", "round1", windows_by_video, tmp_path)
        worksheet_b, _ = gold.export_round("B", "round1", windows_by_video, tmp_path)

        for line in worksheet_a.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            assert all(text.startswith("a") for text in record["context"])
            assert record["target"].startswith("a")

        for line in worksheet_b.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            assert all(text.startswith("b") for text in record["context"])
            assert record["target"].startswith("b")


# --------------------------------------------------------------------------
# export_round - independencia comportamental entre round1 e round2
# --------------------------------------------------------------------------


class TestExportRoundIndependence:
    def test_round2_reproduces_round1_bytes_after_round1_is_physically_deleted(self, tmp_path):
        windows_by_video = {
            "7xgt_LQxedc": _make_windows("7xgt_LQxedc", [f"texto {i}" for i in range(9)])
        }
        out_dir = tmp_path / "gold" / "mackexplains7"

        worksheet1, index1 = gold.export_round("7xgt_LQxedc", "round1", windows_by_video, out_dir)
        worksheet1_bytes = worksheet1.read_bytes()
        index1_bytes = index1.read_bytes()

        round1_dir = out_dir / "round1"
        shutil.rmtree(round1_dir)
        assert not round1_dir.exists()

        worksheet2, index2 = gold.export_round("7xgt_LQxedc", "round2", windows_by_video, out_dir)

        assert worksheet2.read_bytes() == worksheet1_bytes
        assert index2.read_bytes() == index1_bytes


# --------------------------------------------------------------------------
# Real round1/round2 artifacts committed for the channel
# --------------------------------------------------------------------------


def _load_real_windows(video_id):
    payload = (gold.WINDOWS_DIR / f"{video_id}.json").read_text(encoding="utf-8")
    return json.loads(payload)["windows"]


class TestRealRoundArtifacts:
    def test_round1_worksheets_match_the_real_windows_for_every_gold_video(self):
        selection = json.loads(gold.SELECTION_PATH.read_text(encoding="utf-8"))
        expected_keys = _expected_worksheet_keys()
        round1_dir = Path("gold/mackexplains7/round1")

        for entry in selection["gold_video_ids"]:
            video_id = entry["video_id"]
            windows = _load_real_windows(video_id)

            worksheet_path = round1_dir / f"{video_id}.worksheet.jsonl"
            lines = worksheet_path.read_text(encoding="utf-8").splitlines()
            assert len(lines) == len(windows)
            for line in lines:
                record = json.loads(line)
                assert set(record.keys()) == expected_keys

            index = json.loads((round1_dir / f"{video_id}.index.json").read_text(encoding="utf-8"))
            assert len(index) == len(windows)
            assert set(index.values()) == {w["window_id"] for w in windows}

    def test_freshly_exported_round1_worksheet_has_null_annotation_fields(self, tmp_path):
        # A garantia original da #20 ("export_round sempre produz campos
        # ontologicos null, prontos pra anotacao") nao pode mais ser
        # verificada lendo os 5 worksheets reais de round1 - o commit
        # humano `gold: add round1 human annotations` ja preencheu esses
        # arquivos com valores reais. Reproduz aqui a mesma garantia
        # exportando de novo, isoladamente, para `tmp_path`, a partir das
        # janelas reais de um video gold.
        selection = json.loads(gold.SELECTION_PATH.read_text(encoding="utf-8"))
        video_id = selection["gold_video_ids"][0]["video_id"]
        windows = _load_real_windows(video_id)
        ontology_field_names = [f["name"] for f in load_ontology()["fields"]]

        worksheet_path, _ = gold.export_round(video_id, "round1", {video_id: windows}, tmp_path)

        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == len(windows)
        for line in lines:
            record = json.loads(line)
            assert all(record[name] is None for name in ontology_field_names)

    def test_round2_worksheet_matches_the_real_windows_for_the_reannotation_video(self):
        selection = json.loads(gold.SELECTION_PATH.read_text(encoding="utf-8"))
        video_id = selection["reannotation_video_id"]
        windows = _load_real_windows(video_id)
        round2_dir = Path("gold/mackexplains7/round2")

        worksheet_path = round2_dir / f"{video_id}.worksheet.jsonl"
        lines = worksheet_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == len(windows)

        index = json.loads((round2_dir / f"{video_id}.index.json").read_text(encoding="utf-8"))
        assert len(index) == len(windows)
        assert set(index.values()) == {w["window_id"] for w in windows}


# --------------------------------------------------------------------------
# merge_round / write_gold_artifact - fusao e validacao do gold canonico
# (Issue #21)
# --------------------------------------------------------------------------


def _fill_worksheet(worksheet_path, updates):
    """Sobrescreve, na ordem original das linhas, os campos de anotacao de
    um worksheet exportado por `export_round` (que comeca com todo campo
    ontologico `null`) - `updates` e uma lista de dicts, um por linha, com
    apenas os campos a preencher."""
    lines = worksheet_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert len(records) == len(updates)
    for record, update in zip(records, updates, strict=True):
        record.update(update)
    worksheet_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )


def _valid_annotation(**overrides):
    fields = {
        "function": "hook",
        "loop": "opens",
        "evidence_type": None,
        "scale": "individual",
        "density": 0,
    }
    fields.update(overrides)
    return fields


class TestMergeRoundValidRound:
    def test_merges_multiple_videos_into_flat_ordered_canonical_records(self, tmp_path):
        windows_by_video = {
            "V1": _make_windows("V1", ["janela um", "janela dois"]),
            "V2": _make_windows("V2", ["outra janela"]),
        }
        worksheet_dir = tmp_path / "worksheets"
        ws1, _ = gold.export_round("V1", "round1", windows_by_video, worksheet_dir)
        ws2, _ = gold.export_round("V2", "round1", windows_by_video, worksheet_dir)

        _fill_worksheet(
            ws1,
            [
                _valid_annotation(function="hook", loop="opens", scale="individual", density=0),
                _valid_annotation(
                    function="evidence",
                    loop="holds",
                    evidence_type="statistic",
                    scale="human",
                    density=2,
                ),
            ],
        )
        _fill_worksheet(
            ws2,
            [_valid_annotation(function="cta", loop="closes", scale="planetary", density=1)],
        )

        round_dir = worksheet_dir / "round1"
        records = gold.merge_round("round1", ["V1", "V2"], round_dir)

        assert records == [
            {
                "window_id": "V1:j0000",
                "video_id": "V1",
                "function": "hook",
                "loop": "opens",
                "evidence_type": None,
                "scale": "individual",
                "density": 0,
            },
            {
                "window_id": "V1:j0001",
                "video_id": "V1",
                "function": "evidence",
                "loop": "holds",
                "evidence_type": "statistic",
                "scale": "human",
                "density": 2,
            },
            {
                "window_id": "V2:j0000",
                "video_id": "V2",
                "function": "cta",
                "loop": "closes",
                "evidence_type": None,
                "scale": "planetary",
                "density": 1,
            },
        ]
        expected_keys = {
            "window_id",
            "video_id",
            "function",
            "loop",
            "evidence_type",
            "scale",
            "density",
        }
        assert all(set(record.keys()) == expected_keys for record in records)


# --------------------------------------------------------------------------
# merge_round - regra de negocio "condition" de evidence_type, ausente do
# schema_loader por design (ver seu docstring) - checada aqui explicitamente
# --------------------------------------------------------------------------


class TestMergeRoundEvidenceTypeCondition:
    def test_evidence_type_set_with_non_evidence_function_raises(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["texto"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(function="hook", evidence_type="study")])

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "V:j0000" in message
        assert "evidence_type" in message

    def test_evidence_function_without_evidence_type_raises(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["texto"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(function="evidence", evidence_type=None)])

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "V:j0000" in message
        assert "evidence_type" in message


# --------------------------------------------------------------------------
# merge_round - campo obrigatorio ausente, isolado por campo
# --------------------------------------------------------------------------


class TestMergeRoundMissingRequiredFields:
    def test_missing_function_raises_naming_window_id_and_field(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["texto"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(function=None)])

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "V:j0000" in message
        assert "function" in message

    def test_missing_loop_raises_naming_window_id_and_field(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["texto"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(loop=None)])

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "V:j0000" in message
        assert "loop" in message

    def test_missing_scale_raises_naming_window_id_and_field(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["texto"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(scale=None)])

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "V:j0000" in message
        assert "scale" in message

    def test_missing_density_raises_naming_window_id_and_field(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["texto"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(density=None)])

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "V:j0000" in message
        assert "density" in message


# --------------------------------------------------------------------------
# merge_round - descasamento display_id entre worksheet e indice
# --------------------------------------------------------------------------


class TestMergeRoundIndexWorksheetMismatch:
    def test_display_id_in_worksheet_missing_from_index_raises_named_error(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["um", "dois"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, idx = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation(), _valid_annotation()])

        index = json.loads(idx.read_text(encoding="utf-8"))
        removed_display_id = next(iter(sorted(index)))
        del index[removed_display_id]
        idx.write_text(json.dumps(index), encoding="utf-8")

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert removed_display_id in message
        assert "V" in message

    def test_display_id_in_index_missing_from_worksheet_raises_named_error(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["um"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, idx = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(ws, [_valid_annotation()])

        index = json.loads(idx.read_text(encoding="utf-8"))
        index["extra-display-id-not-in-worksheet"] = "V:jFFFF"
        idx.write_text(json.dumps(index), encoding="utf-8")

        with pytest.raises(gold.GoldValidationError) as exc_info:
            gold.merge_round("round1", ["V"], worksheet_dir / "round1")

        message = str(exc_info.value)
        assert "extra-display-id-not-in-worksheet" in message
        assert "V" in message


# --------------------------------------------------------------------------
# write_gold_artifact
# --------------------------------------------------------------------------


class TestWriteGoldArtifact:
    def test_writes_generated_at_ontology_version_and_records_with_exact_keys(self, tmp_path):
        windows_by_video = {"V": _make_windows("V", ["um", "dois"])}
        worksheet_dir = tmp_path / "worksheets"
        ws, _ = gold.export_round("V", "round1", windows_by_video, worksheet_dir)
        _fill_worksheet(
            ws,
            [
                _valid_annotation(function="hook", loop="opens", scale="individual", density=0),
                _valid_annotation(
                    function="evidence",
                    loop="holds",
                    evidence_type="case",
                    scale="human",
                    density=1,
                ),
            ],
        )
        records = gold.merge_round("round1", ["V"], worksheet_dir / "round1")
        out_path = tmp_path / "gold_artifact" / "round1.gold.json"

        result_path = gold.write_gold_artifact("round1", records, out_path)

        assert result_path == out_path
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        datetime.fromisoformat(payload["generated_at"])
        assert payload["ontology_version"] == load_ontology()["version"]
        assert payload["records"] == records
        expected_keys = {
            "window_id",
            "video_id",
            "function",
            "loop",
            "evidence_type",
            "scale",
            "density",
        }
        for record in payload["records"]:
            assert set(record.keys()) == expected_keys
            assert record["window_id"]
            assert "display_id" not in record
            assert "context" not in record
            assert "target" not in record

    def test_creates_parent_directories(self, tmp_path):
        out_path = tmp_path / "nested" / "dir" / "round2.gold.json"

        result_path = gold.write_gold_artifact("round2", [], out_path)

        assert result_path == out_path
        assert out_path.exists()
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["records"] == []
