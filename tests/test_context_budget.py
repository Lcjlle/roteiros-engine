"""Testes de `src/context_budget.py` (Issue #19).

Le apenas os arquivos reais em `corpus/mackexplains7/windows/*.json`
(somente leitura, conforme constraint da issue).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.context_budget import CONTEXT_BUDGET, Bundle, build_bundle

CORPUS_WINDOWS_DIR = Path(__file__).resolve().parent.parent / "corpus/mackexplains7/windows"


def _load_windows(video_id: str) -> list[dict]:
    data = json.loads((CORPUS_WINDOWS_DIR / f"{video_id}.json").read_text(encoding="utf-8"))
    return data["windows"]


@pytest.fixture(scope="module")
def real_windows() -> dict[str, list[dict]]:
    return {
        "lkLwp9o7Djk": _load_windows("lkLwp9o7Djk"),
        "5unhHRFkC7I": _load_windows("5unhHRFkC7I"),
    }


# --------------------------------------------------------------------------
# 1. Bundle e' uma dataclass congelada com o shape exigido
# --------------------------------------------------------------------------


def test_bundle_is_frozen_dataclass() -> None:
    bundle = Bundle(window_id="v:j0001", display_id="deadbeef", context=["a"], target="b")
    with pytest.raises(FrozenInstanceError):
        bundle.window_id = "v:j0002"  # type: ignore[misc]


def test_bundle_fields() -> None:
    bundle = Bundle(window_id="v:j0001", display_id="deadbeef", context=["a", "b"], target="c")
    assert bundle.window_id == "v:j0001"
    assert bundle.display_id == "deadbeef"
    assert bundle.context == ["a", "b"]
    assert bundle.target == "c"


# --------------------------------------------------------------------------
# 2. Regras de orcamento de contexto (0-3 janelas, nunca futuro, nunca outro
#    video) contra fixtures sinteticas simples e explicitas
# --------------------------------------------------------------------------


def _synthetic_windows(video_id: str, n: int) -> list[dict]:
    return [
        {
            "window_id": f"{video_id}:j{i:04d}",
            "video_id": video_id,
            "idx": i,
            "sent_ids": [f"s{i}"],
            "start_s": float(i),
            "end_s": float(i) + 1.0,
            "text": f"texto da janela {i}",
            "n_words": 4,
            "n_sentences": 1,
            "pos_pct": i / n,
        }
        for i in range(n)
    ]


def test_context_empty_for_first_window() -> None:
    windows = _synthetic_windows("vidA", 10)
    bundle = build_bundle("vidA", 0, {"vidA": windows})
    assert bundle.context == []
    assert bundle.target == "texto da janela 0"


def test_context_partial_for_second_window() -> None:
    windows = _synthetic_windows("vidA", 10)
    bundle = build_bundle("vidA", 1, {"vidA": windows})
    assert bundle.context == ["texto da janela 0"]


def test_context_partial_for_third_window() -> None:
    windows = _synthetic_windows("vidA", 10)
    bundle = build_bundle("vidA", 2, {"vidA": windows})
    assert bundle.context == ["texto da janela 0", "texto da janela 1"]


def test_context_full_three_windows_in_video_order() -> None:
    windows = _synthetic_windows("vidA", 10)
    bundle = build_bundle("vidA", 5, {"vidA": windows})
    assert bundle.context == [
        "texto da janela 2",
        "texto da janela 3",
        "texto da janela 4",
    ]
    assert bundle.target == "texto da janela 5"


def test_context_never_exceeds_three_even_deep_in_video() -> None:
    windows = _synthetic_windows("vidA", 200)
    bundle = build_bundle("vidA", 199, {"vidA": windows})
    assert len(bundle.context) == CONTEXT_BUDGET == 3
    assert bundle.context == [
        "texto da janela 196",
        "texto da janela 197",
        "texto da janela 198",
    ]


def test_context_never_includes_future_windows() -> None:
    windows = _synthetic_windows("vidA", 10)
    bundle = build_bundle("vidA", 3, {"vidA": windows})
    future_texts = {w["text"] for w in windows[4:]}
    assert future_texts.isdisjoint(bundle.context)
    assert bundle.target not in future_texts.union({""})  # target is window 3 itself


def test_context_never_mixes_other_video() -> None:
    windows_other = _synthetic_windows("vidOther", 5)
    for w in windows_other:
        w["text"] = f"OUTRO VIDEO {w['idx']}"
    windows_target = _synthetic_windows("vidB", 5)
    windows_by_video = {"vidOther": windows_other, "vidB": windows_target}

    bundle = build_bundle("vidB", 2, windows_by_video)

    assert bundle.context == [w["text"] for w in windows_target[:2]]
    assert all(not text.startswith("OUTRO VIDEO") for text in bundle.context)


# --------------------------------------------------------------------------
# 3. `display_id` - formula exata e nao-monotonicidade real
# --------------------------------------------------------------------------


def test_display_id_exact_formula() -> None:
    windows = _synthetic_windows("vidA", 10)
    bundle = build_bundle("vidA", 4, {"vidA": windows})
    expected = hashlib.sha1(f"vidA:{bundle.window_id}".encode()).hexdigest()[:8]
    assert bundle.display_id == expected


def test_display_id_deterministic_across_calls() -> None:
    windows = _synthetic_windows("vidA", 10)
    first = build_bundle("vidA", 4, {"vidA": windows})
    second = build_bundle("vidA", 4, {"vidA": windows})
    assert first.display_id == second.display_id


def test_display_id_non_monotonic_real_video(real_windows: dict[str, list[dict]]) -> None:
    """Para janelas consecutivas reais de `lkLwp9o7Djk`, a ordem dos
    inteiros de `display_id` nao acompanha a ordem de `idx` - nem
    estritamente crescente, nem estritamente decrescente."""
    video_id = "lkLwp9o7Djk"
    windows = real_windows[video_id]
    windows_by_video = {video_id: windows}

    consecutive_indices = list(range(0, len(windows)))
    display_ints = [
        int(build_bundle(video_id, idx, windows_by_video).display_id, 16)
        for idx in consecutive_indices
    ]

    is_strictly_increasing = all(
        display_ints[i] < display_ints[i + 1] for i in range(len(display_ints) - 1)
    )
    is_strictly_decreasing = all(
        display_ints[i] > display_ints[i + 1] for i in range(len(display_ints) - 1)
    )

    assert not is_strictly_increasing, (
        "display_id nao deveria crescer monotonicamente com idx, mas cresceu: "
        f"{display_ints[:10]}..."
    )
    assert not is_strictly_decreasing, (
        "display_id nao deveria decrescer monotonicamente com idx, mas decresceu: "
        f"{display_ints[:10]}..."
    )


# --------------------------------------------------------------------------
# 4. Worked proof - os 4 casos de `_docs/decisions.md#28(a)` contra os
#    arquivos reais do corpus
# --------------------------------------------------------------------------

WORKED_PROOF_CASES = [
    ("lkLwp9o7Djk", "j0027"),
    ("lkLwp9o7Djk", "j0064"),
    ("lkLwp9o7Djk", "j0076"),
    ("5unhHRFkC7I", "j0075"),
]


@pytest.mark.parametrize("video_id,window_suffix", WORKED_PROOF_CASES)
def test_worked_proof_matches_real_corpus_windows(
    real_windows: dict[str, list[dict]], video_id: str, window_suffix: str
) -> None:
    windows = real_windows[video_id]
    window_id = f"{video_id}:{window_suffix}"

    target_window = next(w for w in windows if w["window_id"] == window_id)
    window_index = target_window["idx"]
    assert windows[window_index] is target_window  # idx == posicao na lista, por construcao

    context_start = max(0, window_index - CONTEXT_BUDGET)
    expected_context = [w["text"] for w in windows[context_start:window_index]]
    expected_target = target_window["text"]

    bundle = build_bundle(video_id, window_index, {video_id: windows})

    assert bundle.window_id == window_id
    assert bundle.context == expected_context
    assert bundle.target == expected_target
    assert len(bundle.context) == min(CONTEXT_BUDGET, window_index)


# --------------------------------------------------------------------------
# 5. Prova de ausencia de metadado - igualdade estrutural, sem regex/substring
# --------------------------------------------------------------------------


@pytest.mark.parametrize("video_id,window_suffix", WORKED_PROOF_CASES)
def test_no_metadata_leak_by_structural_equality(
    real_windows: dict[str, list[dict]], video_id: str, window_suffix: str
) -> None:
    """`context`/`target` so podem conter exatamente os valores `text` de
    origem - comparado por igualdade estrutural (`==`), nunca por regex ou
    busca de substring. Por construcao, isso ja exclui qualquer vazamento
    de `idx`, `video_id`, `sent_ids`, `start_s`/`end_s`, ou `window_id`
    para dentro de `context`/`target`, porque esses campos so podem
    assumir o valor exato de `text`."""
    windows = real_windows[video_id]
    window_id = f"{video_id}:{window_suffix}"

    target_window = next(w for w in windows if w["window_id"] == window_id)
    window_index = target_window["idx"]

    preceding_windows = windows[max(0, window_index - CONTEXT_BUDGET) : window_index]

    bundle = build_bundle(video_id, window_index, {video_id: windows})

    assert bundle.window_id == target_window["window_id"]
    assert bundle.target == target_window["text"]
    assert bundle.context == [w["text"] for w in preceding_windows]
