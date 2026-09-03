"""Testes de `src/amostragem.py` (Fase 2 - amostra pro QA humano, F2-c)."""

from __future__ import annotations

import json

import pytest

from src import amostragem


def _write_windows(windows_dir, video_id, n, n_words=10, n_sentences=2):
    windows_dir.mkdir(parents=True, exist_ok=True)
    windows = [
        {
            "window_id": f"{video_id}:j{i:04d}",
            "video_id": video_id,
            "idx": i,
            "sent_ids": [f"{video_id}:s{i:04d}"],
            "start_s": i * 10.0,
            "end_s": i * 10.0 + 5.0,
            "text": f"janela {i}",
            "n_words": n_words,
            "n_sentences": n_sentences,
            "pos_pct": i * 0.01,
        }
        for i in range(n)
    ]
    payload = {"video_id": video_id, "generated_at": "2026-01-01T00:00:00Z", "windows": windows}
    (windows_dir / f"{video_id}.json").write_text(json.dumps(payload), encoding="utf-8")


# --------------------------------------------------------------------------
# sample_videos
# --------------------------------------------------------------------------


class TestSampleVideos:
    def test_same_seed_draws_the_same_videos(self, tmp_path):
        windows_dir = tmp_path / "windows"
        for vid in ["a", "b", "c", "d", "e"]:
            _write_windows(windows_dir, vid, n=30)

        first = amostragem.sample_videos(windows_dir=windows_dir, seed=42, n_videos=2)
        second = amostragem.sample_videos(windows_dir=windows_dir, seed=42, n_videos=2)

        assert first == second


# --------------------------------------------------------------------------
# sample_windows
# --------------------------------------------------------------------------


class TestSampleWindows:
    def test_same_seed_reproduces_the_same_set_and_is_not_a_predictable_slice(self, tmp_path):
        windows_dir = tmp_path / "windows"
        _write_windows(windows_dir, "A", n=60)

        first = amostragem.sample_windows(["A"], windows_dir=windows_dir, n_windows=25, seed=42)
        second = amostragem.sample_windows(["A"], windows_dir=windows_dir, n_windows=25, seed=42)

        first_ids = {w["window_id"] for w in first}
        second_ids = {w["window_id"] for w in second}
        assert first_ids == second_ids

        predictable_slice = {f"A:j{i:04d}" for i in range(25)}
        assert first_ids != predictable_slice

    def test_two_videos_at_full_quota_no_backfill_needed(self, tmp_path):
        windows_dir = tmp_path / "windows"
        _write_windows(windows_dir, "A", n=60)
        _write_windows(windows_dir, "B", n=60)

        result = amostragem.sample_windows(["A", "B"], windows_dir=windows_dir, n_windows=50)

        assert len(result) == 50
        by_video = {"A": 0, "B": 0}
        for w in result:
            by_video[w["video_id"]] += 1
        assert by_video == {"A": 25, "B": 25}

    def test_video_below_quota_is_backfilled_from_the_other_video(self, tmp_path):
        windows_dir = tmp_path / "windows"
        _write_windows(windows_dir, "A", n=60)
        _write_windows(windows_dir, "B", n=10)

        result = amostragem.sample_windows(["A", "B"], windows_dir=windows_dir, n_windows=50)

        assert len(result) == 50
        by_video = {"A": 0, "B": 0}
        for w in result:
            by_video[w["video_id"]] += 1
        assert by_video["B"] == 10  # entra inteiro
        assert by_video["A"] == 40  # 25 da cota + 15 de backfill
        assert by_video["A"] > 0 and by_video["B"] > 0

    def test_insufficient_total_raises_instead_of_returning_partial_sample(self, tmp_path):
        windows_dir = tmp_path / "windows"
        _write_windows(windows_dir, "A", n=5)
        _write_windows(windows_dir, "B", n=5)

        with pytest.raises(amostragem.InsufficientSample):
            amostragem.sample_windows(["A", "B"], windows_dir=windows_dir, n_windows=50)


# --------------------------------------------------------------------------
# write_sample_report
# --------------------------------------------------------------------------


class TestWriteSampleReport:
    def test_writes_blank_columns_and_seed_header(self, tmp_path):
        windows = [
            {
                "window_id": "A:j0000",
                "video_id": "A",
                "start_s": 0.0,
                "end_s": 5.0,
                "n_sentences": 2,
                "n_words": 10,
                "text": "texto de exemplo",
            }
        ]

        path = amostragem.write_sample_report(
            windows, ["A", "B"], path=tmp_path / "fase2_sample.md", seed=42
        )

        content = path.read_text(encoding="utf-8")
        assert "42" in content
        assert "A:j0000" in content
        assert "| A:j0000 | A | 0.0 | 5.0 | 2 | 10 | texto de exemplo |  |  |" in content
