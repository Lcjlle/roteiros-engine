"""Testes de `src/janelas.py` (Fase 2 - Janelas e portao criterio 3)."""

from __future__ import annotations

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
# check_gate
# --------------------------------------------------------------------------


def _window(video_id, idx, n_words=10, n_sentences=2):
    return {
        "window_id": f"{video_id}:j{idx:04d}",
        "video_id": video_id,
        "idx": idx,
        "n_words": n_words,
        "n_sentences": n_sentences,
    }


class TestCheckGate:
    def test_isolated_window_over_max_words_reports_one_problem_with_window_id(self):
        windows = [_window("v1", i, n_words=10) for i in range(25)]
        windows[5]["n_words"] = 61

        passed, problems = janelas.check_gate({"v1": windows})

        assert not passed
        matching = [p for p in problems if "v1:j0005" in p]
        assert len(matching) == 1

    def test_video_below_min_windows_reports_problem_with_video_id(self):
        windows = [_window("v1", i) for i in range(10)]

        passed, problems = janelas.check_gate({"v1": windows})

        assert not passed
        assert any("v1" in p and "10 janelas" in p for p in problems)

    def test_intermediate_window_below_min_sentences_reports_problem(self):
        windows = [_window("v1", i, n_sentences=2) for i in range(30)]
        windows[10]["n_sentences"] = 1  # nao e a ultima (idx max = 29)

        passed, problems = janelas.check_gate({"v1": windows})

        assert not passed
        assert any("v1:j0010" in p for p in problems)

    def test_last_window_with_one_sentence_reports_no_problem(self):
        windows = [_window("v1", i, n_sentences=2) for i in range(29)]
        windows.append(_window("v1", 29, n_sentences=1))  # ultima, excecao

        _passed, problems = janelas.check_gate({"v1": windows})

        assert not any("v1:j0029" in p for p in problems)

    def test_video_with_zero_windows_does_not_crash(self):
        passed, problems = janelas.check_gate({"v1": []})

        assert not passed
        assert any("v1" in p and "0 janelas" in p for p in problems)
