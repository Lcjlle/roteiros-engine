"""Testes de `src/janelas.py` (Fase 2 - Janelas e portao criterio 3)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from src import janelas


def _sentence(video_id, idx, n_words, start_s=None, end_s=None):
    return {
        "sent_id": f"{video_id}:s{idx:04d}",
        "video_id": video_id,
        "idx": idx,
        "start_s": idx * 1.0 if start_s is None else start_s,
        "end_s": (idx + 1) * 1.0 if end_s is None else end_s,
        "text": f"sentenca {idx}",
        "n_words": n_words,
    }


def _sentences_payload(video_id, sentences, duration_s=600.0):
    """Envelope de `sentences/<video_id>.json`, o formato que `check_gate`
    (via `sentences_by_video`) espera."""
    return {
        "video_id": video_id,
        "duration_s": duration_s,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "sentences": sentences,
    }


def _write_sentences_input(sentences_dir, payload):
    for sentence in payload["sentences"]:
        sentence["text"] = " ".join(["palavra"] * sentence["n_words"])
    sentences_dir.mkdir()
    (sentences_dir / f"{payload['video_id']}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


# --------------------------------------------------------------------------
# group_windows
# --------------------------------------------------------------------------


class TestGroupWindows:
    def test_closes_window_when_word_sum_exceeds_max_on_third_sentence(self):
        sentences = [
            _sentence("v1", 0, n_words=20),
            _sentence("v1", 1, n_words=10),
            _sentence("v1", 2, n_words=10),  # 20+10+10=40 > 35 -> fecha antes desta
        ]

        windows = janelas.group_windows(sentences, max_words=35, max_sentences=4)

        assert len(windows) == 2
        assert [s["idx"] for s in windows[0]] == [0, 1]
        assert [s["idx"] for s in windows[1]] == [2]

    def test_five_short_sentences_close_into_windows_of_four_and_one(self):
        sentences = [_sentence("v1", i, n_words=5) for i in range(5)]

        windows = janelas.group_windows(sentences, max_words=35, max_sentences=4)

        assert len(windows) == 2
        assert [s["idx"] for s in windows[0]] == [0, 1, 2, 3]
        assert [s["idx"] for s in windows[1]] == [4]  # excecao: ultima abaixo do minimo

    def test_isolated_sentence_longer_than_max_words_becomes_its_own_window(self):
        sentences = [_sentence("v1", 0, n_words=100)]

        windows = janelas.group_windows(sentences, max_words=35, max_sentences=4)

        assert len(windows) == 1
        assert len(windows[0]) == 1
        assert windows[0][0]["n_words"] == 100

    def test_empty_input_returns_empty_list(self):
        assert janelas.group_windows([]) == []

    def test_nonlast_window_overflows_max_words_to_reach_min_sentences(self):
        # 20+20=40 > max_words(35), mas so tem 1 sentenca ainda -> continua
        # acumulando ate alcancar min_sentences(2), sem estourar gate_max_words(60)
        sentences = [
            _sentence("v1", 0, n_words=20),
            _sentence("v1", 1, n_words=20),
            _sentence("v1", 2, n_words=5),
        ]

        windows = janelas.group_windows(
            sentences, max_words=35, max_sentences=4, min_sentences=2, gate_max_words=60
        )

        assert len(windows) == 2
        assert [s["idx"] for s in windows[0]] == [0, 1]
        assert sum(s["n_words"] for s in windows[0]) == 40  # estourou max_words de proposito

    def test_nonlast_window_closes_below_min_sentences_when_next_would_exceed_gate_max_words(self):
        # janela com 1 sentenca (20) nao alcanca min_sentences(2), mas a
        # proxima sentenca (45) faria a soma estourar gate_max_words(60) ->
        # fecha assim mesmo, abaixo do minimo, sem violar o teto do portao
        sentences = [
            _sentence("v1", 0, n_words=20),
            _sentence("v1", 1, n_words=45),
        ]

        windows = janelas.group_windows(
            sentences, max_words=35, max_sentences=4, min_sentences=2, gate_max_words=60
        )

        assert len(windows) == 2
        assert [s["idx"] for s in windows[0]] == [0]  # nao-final, abaixo do minimo
        assert [s["idx"] for s in windows[1]] == [1]


# --------------------------------------------------------------------------
# window_records
# --------------------------------------------------------------------------


class TestWindowRecords:
    def test_pos_pct_sent_ids_order_and_sequential_window_id(self):
        sentences = [
            _sentence("v1", i, n_words=5, start_s=i * 10.0, end_s=i * 10.0 + 5.0) for i in range(6)
        ]

        records = janelas.window_records("v1", sentences, duration_s=100.0)

        assert [r["window_id"] for r in records] == ["v1:j0000", "v1:j0001"]
        assert records[0]["sent_ids"] == ["v1:s0000", "v1:s0001", "v1:s0002", "v1:s0003"]
        assert records[0]["pos_pct"] == records[0]["start_s"] / 100.0
        assert records[1]["pos_pct"] == records[1]["start_s"] / 100.0

    def test_pos_pct_is_none_when_duration_is_zero(self):
        sentences = [_sentence("v1", 0, n_words=5)]

        records = janelas.window_records("v1", sentences, duration_s=0.0)

        assert records[0]["pos_pct"] is None


# --------------------------------------------------------------------------
# check_3a / check_3b / check_3c / check_3d / check_gate
# --------------------------------------------------------------------------


def _window(video_id, idx, n_words=10, n_sentences=2, sent_ids=None):
    return {
        "window_id": f"{video_id}:j{idx:04d}",
        "video_id": video_id,
        "idx": idx,
        "sent_ids": sent_ids or [f"{video_id}:s{idx:04d}"],
        "n_words": n_words,
        "n_sentences": n_sentences,
    }


class TestCheck3a:
    def test_passes_when_big_window_count_matches_big_sentence_count(self):
        # positivo minimo: janela > 60 com n_sentences=1 e a sentenca
        # referenciada por sent_ids[0] de fato > 60 - proveniencia comprovada
        sentences_by_video = {"v1": _sentences_payload("v1", [_sentence("v1", 0, n_words=70)])}
        windows_by_video = {"v1": [_window("v1", 0, n_words=70, n_sentences=1)]}

        ok, problems = janelas.check_3a(sentences_by_video, windows_by_video)

        assert ok
        assert problems == []

    def test_fails_when_oversized_window_has_no_matching_oversized_sentence(self):
        # nenhuma sentenca > 60 palavras, mas uma janela reporta 70 -
        # violacao da invariante (bug de agrupamento, nao explicado por
        # sentenca isolada estourada) e da proveniencia por janela
        sentences_by_video = {"v1": _sentences_payload("v1", [_sentence("v1", 0, n_words=10)])}
        windows_by_video = {"v1": [_window("v1", 0, n_words=70, n_sentences=1)]}

        ok, problems = janelas.check_3a(sentences_by_video, windows_by_video)

        assert not ok
        assert any("v1:j0000" in p for p in problems)

    def test_fails_when_oversized_window_is_a_merge_of_multiple_sentences(self):
        # GAP que a contagem agregada sozinha deixa passar: 1 sentenca
        # grande no corpus (70 palavras, idx 0) e 1 janela grande no corpus
        # (65 palavras) - contagens EMPATAM (1==1), a checagem antiga (so
        # contagem agregada) passaria aqui. Mas a janela grande e uma FUSAO
        # de 2 sentencas (n_sentences=2, sent_ids de s0001/s0002 - nao a
        # s0000 que e a unica realmente grande) - proveniencia falsa, a
        # sentenca de 70 palavras "sumiu" sem estar representada por
        # nenhuma janela grande. A checagem por janela tem que pegar isso.
        sentences_by_video = {
            "v1": _sentences_payload(
                "v1",
                [
                    _sentence("v1", 0, n_words=70),
                    _sentence("v1", 1, n_words=35),
                    _sentence("v1", 2, n_words=30),
                ],
            )
        }
        windows_by_video = {
            "v1": [_window("v1", 0, n_words=65, n_sentences=2, sent_ids=["v1:s0001", "v1:s0002"])]
        }

        ok, problems = janelas.check_3a(sentences_by_video, windows_by_video)

        assert not ok
        assert any("v1:j0000" in p and "2 sentencas" in p for p in problems)
        # a contagem agregada sozinha empataria (1 sentenca grande == 1
        # janela grande) - nao deve ser esse o problema reportado aqui
        assert not any("contagem agregada" in p for p in problems)

    def test_fails_when_oversized_window_references_a_small_sentence(self):
        # mesmo GAP, outra forma: contagens empatam (1==1), janela tem
        # n_sentences=1 (nao fusao visivel), mas sent_ids[0] aponta pra uma
        # sentenca PEQUENA (10 palavras) - proveniencia errada, nao a
        # sentenca de 70 palavras que de fato existe no corpus
        sentences_by_video = {
            "v1": _sentences_payload(
                "v1", [_sentence("v1", 0, n_words=70), _sentence("v1", 1, n_words=10)]
            )
        }
        windows_by_video = {
            "v1": [_window("v1", 0, n_words=65, n_sentences=1, sent_ids=["v1:s0001"])]
        }

        ok, problems = janelas.check_3a(sentences_by_video, windows_by_video)

        assert not ok
        assert any("v1:j0000" in p and "v1:s0001" in p for p in problems)
        assert not any("contagem agregada" in p for p in problems)


class TestCheck3b:
    def test_passes_when_single_nonlast_windows_are_explained(self):
        sentences = [
            _sentence("v1", 0, n_words=40),  # caso (i): isolada > 35 sozinha
            _sentence("v1", 1, n_words=10),
            _sentence("v1", 2, n_words=10),
        ]
        sentences_by_video = {"v1": _sentences_payload("v1", sentences)}
        windows_by_video = {
            "v1": [
                _window("v1", 0, n_words=40, n_sentences=1, sent_ids=["v1:s0000"]),
                _window("v1", 1, n_words=20, n_sentences=2, sent_ids=["v1:s0001", "v1:s0002"]),
            ]
        }

        ok, residual = janelas.check_3b(sentences_by_video, windows_by_video)

        assert ok
        assert residual == 0

    def test_fails_with_unexplained_residual(self):
        # janela nao-final de 1 sentenca (20 palavras, nao estourada), a
        # soma com a proxima sentenca (5) nao chega perto de 60 - nao
        # explicada nem por (i) nem por (ii)
        sentences = [
            _sentence("v1", 0, n_words=20),
            _sentence("v1", 1, n_words=5),
            _sentence("v1", 2, n_words=5),
        ]
        sentences_by_video = {"v1": _sentences_payload("v1", sentences)}
        windows_by_video = {
            "v1": [
                _window("v1", 0, n_words=20, n_sentences=1, sent_ids=["v1:s0000"]),
                _window("v1", 1, n_words=10, n_sentences=2, sent_ids=["v1:s0001", "v1:s0002"]),
            ]
        }

        ok, residual = janelas.check_3b(sentences_by_video, windows_by_video)

        assert not ok
        assert residual == 1

    def test_last_window_with_one_sentence_is_never_counted(self):
        sentences = [
            _sentence("v1", 0, n_words=10),
            _sentence("v1", 1, n_words=10),
            _sentence("v1", 2, n_words=10),
        ]
        sentences_by_video = {"v1": _sentences_payload("v1", sentences)}
        windows_by_video = {
            "v1": [
                _window("v1", 0, n_words=20, n_sentences=2, sent_ids=["v1:s0000", "v1:s0001"]),
                _window("v1", 1, n_words=10, n_sentences=1, sent_ids=["v1:s0002"]),  # ultima
            ]
        }

        ok, residual = janelas.check_3b(sentences_by_video, windows_by_video)

        assert ok
        assert residual == 0


class TestCheck3c:
    def test_measures_ratio_of_nonlast_single_sentence_windows(self):
        windows = [
            _window("v1", 0, n_sentences=1),
            _window("v1", 1, n_sentences=1),
            _window("v1", 2, n_sentences=1),
            _window("v1", 3, n_sentences=2),  # ultima, nunca conta
        ]

        ok, ratio = janelas.check_3c({"v1": windows})

        assert ratio == 0.75
        assert not ok  # 0.75 > 0.15

    def test_does_not_block_check_gate_overall_pass(self):
        # 3 janelas de 1 sentenca isolada > WINDOW_MAX_WORDS (explicadas por
        # 3b caso (i), sem violar 3a pois <= 60) + 1 janela final -> 3c
        # estoura a tolerancia (3/4 = 75% > 15%) mas nao bloqueia o PASSOU
        sentences = [
            _sentence("v1", 0, n_words=40),
            _sentence("v1", 1, n_words=40),
            _sentence("v1", 2, n_words=40),
            _sentence("v1", 3, n_words=10),
            _sentence("v1", 4, n_words=10),
        ]
        sentences_by_video = {"v1": _sentences_payload("v1", sentences, duration_s=60.0)}
        windows_by_video = {
            "v1": [
                _window("v1", 0, n_words=40, n_sentences=1, sent_ids=["v1:s0000"]),
                _window("v1", 1, n_words=40, n_sentences=1, sent_ids=["v1:s0001"]),
                _window("v1", 2, n_words=40, n_sentences=1, sent_ids=["v1:s0002"]),
                _window("v1", 3, n_words=20, n_sentences=2, sent_ids=["v1:s0003", "v1:s0004"]),
            ]
        }

        c_ok, ratio = janelas.check_3c(windows_by_video)
        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert ratio == 0.75
        assert not c_ok
        assert passed  # 3c nao aparece nos problemas nem bloqueia o PASSOU
        assert problems == []


class TestCheck3d:
    def test_video_within_proportional_band_reports_no_problem(self):
        # duration_min=1 -> banda [ceil(1*4.86*0.6), floor(1*4.86*1.4)] = [3, 6]
        windows = [_window("v1", i) for i in range(5)]
        sentences_by_video = {"v1": _sentences_payload("v1", [], duration_s=60.0)}

        ok, problems = janelas.check_3d(sentences_by_video, {"v1": windows})

        assert ok
        assert problems == []

    def test_video_outside_proportional_band_reports_problem_with_video_id(self):
        windows = [_window("v1", 0)]  # 1 janela, abaixo da banda [3, 6]
        sentences_by_video = {"v1": _sentences_payload("v1", [], duration_s=60.0)}

        ok, problems = janelas.check_3d(sentences_by_video, {"v1": windows})

        assert not ok
        assert any("v1" in p and "3d" in p for p in problems)


class TestCheckGate:
    def test_passes_when_3a_3b_3d_all_pass(self):
        # video de 20 minutos, 97 janelas cai dentro da banda
        # [ceil(20*4.86*0.6), floor(20*4.86*1.4)] = [59, 136]
        sentences = [_sentence("v1", i, n_words=10) for i in range(200)]
        sentences_by_video = {"v1": _sentences_payload("v1", sentences, duration_s=1200.0)}
        windows_by_video = {"v1": janelas.window_records("v1", sentences, duration_s=1200.0)}

        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert passed
        assert problems == []

    def test_fails_and_reports_3a_problem(self):
        sentences_by_video = {
            "v1": _sentences_payload("v1", [_sentence("v1", 0, n_words=10)], duration_s=60.0)
        }
        windows_by_video = {"v1": [_window("v1", 0, n_words=70, n_sentences=1)]}

        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert not passed
        assert any(p.startswith("3a:") for p in problems)

    def test_fails_and_reports_3b_problem(self):
        sentences = [
            _sentence("v1", 0, n_words=20),
            _sentence("v1", 1, n_words=5),
            _sentence("v1", 2, n_words=5),
        ]
        sentences_by_video = {"v1": _sentences_payload("v1", sentences, duration_s=60.0)}
        windows_by_video = {
            "v1": [
                _window("v1", 0, n_words=20, n_sentences=1, sent_ids=["v1:s0000"]),
                _window("v1", 1, n_words=10, n_sentences=2, sent_ids=["v1:s0001", "v1:s0002"]),
            ]
        }

        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert not passed
        assert any(p.startswith("3b:") for p in problems)

    def test_fails_and_reports_3d_problem(self):
        sentences_by_video = {"v1": _sentences_payload("v1", [], duration_s=60.0)}
        windows_by_video = {"v1": [_window("v1", 0)]}  # 1 janela, fora da banda [3, 6]

        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert not passed
        assert any(p.startswith("3d:") for p in problems)

    def test_video_with_zero_sentences_and_zero_windows_does_not_crash(self):
        sentences_by_video = {"v1": _sentences_payload("v1", [], duration_s=600.0)}
        windows_by_video = {"v1": []}

        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert not passed  # duration > 0 mas 0 janelas, fora da banda
        assert any("v1" in p for p in problems)

    def test_video_with_zero_duration_and_zero_windows_passes(self):
        sentences_by_video = {"v1": _sentences_payload("v1", [], duration_s=0.0)}
        windows_by_video = {"v1": []}

        passed, problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert passed
        assert problems == []


# --------------------------------------------------------------------------
# gate artifact
# --------------------------------------------------------------------------


class TestGateArtifact:
    def test_persists_each_gate_result_from_the_generated_windows(self, tmp_path):
        sentences_dir = tmp_path / "sentences"
        payload = _sentences_payload(
            "v1", [_sentence("v1", idx, n_words=10) for idx in range(12)], duration_s=60.0
        )
        _write_sentences_input(sentences_dir, payload)

        windows_by_video, sentences_by_video, _result = janelas.run_gate(
            sentences_dir, tmp_path / "windows"
        )
        artifact = json.loads((tmp_path / "fase2_gate.json").read_text(encoding="utf-8"))
        a_ok, a_problems = janelas.check_3a(sentences_by_video, windows_by_video)
        b_ok, residual = janelas.check_3b(sentences_by_video, windows_by_video)
        c_ok, ratio = janelas.check_3c(windows_by_video)
        d_ok, d_problems = janelas.check_3d(sentences_by_video, windows_by_video)
        passed, _problems = janelas.check_gate(windows_by_video, sentences_by_video)

        assert set(artifact) == {
            "generated_at",
            "n_videos",
            "n_windows",
            "passed",
            "3a",
            "3b",
            "3c",
            "3d",
            "constants",
        }
        assert datetime.fromisoformat(artifact["generated_at"]).utcoffset() == timedelta(0)
        assert type(artifact["n_videos"]) is int
        assert type(artifact["n_windows"]) is int
        assert artifact["n_videos"] == len(windows_by_video)
        assert artifact["n_windows"] == sum(len(windows) for windows in windows_by_video.values())
        assert artifact["passed"] is passed
        assert artifact["3a"] == {
            "n_sentencas_grandes": janelas._count_big(sentences_by_video, windows_by_video)[0],
            "n_janelas_grandes": janelas._count_big(sentences_by_video, windows_by_video)[1],
            "passed": a_ok,
            "problems": a_problems,
        }
        assert artifact["3b"] == {"residuo": residual, "passed": b_ok}
        assert artifact["3c"] == {
            "nonlast_single_ratio": ratio,
            "threshold": janelas.GATE_NONLAST_SINGLE_WINDOW_MAX_RATIO,
            "passed": c_ok,
        }
        assert artifact["3d"] == {"passed": d_ok, "problems": d_problems}
        assert all(isinstance(problem, str) for problem in artifact["3a"]["problems"])
        assert all(isinstance(problem, str) for problem in artifact["3d"]["problems"])
        assert artifact["constants"] == {
            "WINDOW_MAX_WORDS": janelas.WINDOW_MAX_WORDS,
            "WINDOW_MAX_SENTENCES": janelas.WINDOW_MAX_SENTENCES,
            "WINDOW_MIN_SENTENCES": janelas.WINDOW_MIN_SENTENCES,
            "GATE_MAX_WINDOW_WORDS": janelas.GATE_MAX_WINDOW_WORDS,
            "GATE_WINDOWS_PER_MINUTE": janelas.GATE_WINDOWS_PER_MINUTE,
            "GATE_WINDOWS_PER_MINUTE_BAND": janelas.GATE_WINDOWS_PER_MINUTE_BAND,
        }

    def test_persists_nonblocking_3c_failure_without_failing_the_gate(self, tmp_path):
        sentences_dir = tmp_path / "sentences"
        payload = _sentences_payload(
            "v1",
            [
                _sentence("v1", 0, n_words=40),
                _sentence("v1", 1, n_words=40),
                _sentence("v1", 2, n_words=40),
                _sentence("v1", 3, n_words=10),
                _sentence("v1", 4, n_words=10),
            ],
            duration_s=60.0,
        )
        _write_sentences_input(sentences_dir, payload)

        windows_by_video, sentences_by_video, _result = janelas.run_gate(
            sentences_dir, tmp_path / "windows"
        )
        artifact = json.loads((tmp_path / "fase2_gate.json").read_text(encoding="utf-8"))
        passed, _problems = janelas.check_gate(windows_by_video, sentences_by_video)
        c_ok, ratio = janelas.check_3c(windows_by_video)

        assert not c_ok
        assert ratio == 0.75
        assert passed
        assert artifact["3c"]["passed"] is False
        assert artifact["3c"]["nonlast_single_ratio"] == ratio
        assert artifact["passed"] is True
