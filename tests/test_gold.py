"""Testes de `src/gold.py` (Fase 4 - selecao do gold, issue #18)."""

from __future__ import annotations

import json
import random

from src import gold


def _write_windows(windows_dir, video_id, texts):
    windows_dir.mkdir(parents=True, exist_ok=True)
    windows = [
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
