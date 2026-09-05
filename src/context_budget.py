"""Fase 4 <-> Fase 5 - funcao compartilhada de bundle de contexto.

`_docs/decisions.md#28(a)` exige exatamente uma funcao de geracao de
bundle Fase4<->Fase5, para que nem o exportador de gold da Fase 4
(`src/gold.py`) nem, futuramente, o prompt builder da Fase 5
reimplementem esta logica. Este modulo e essa unica implementacao.

Um bundle contem:

- `window_id`: o id sequencial real da janela-alvo (ex.: "lkLwp9o7Djk:j0230"),
  persistido apenas no artefato de gold, nunca renderizado ao anotador
  ou ao modelo.
- `display_id`: um token opaco por janela, deterministico a partir de
  `(video_id, window_id)`, sem relacao ordinal com a posicao da janela.
- `context`: os textos das ate 3 janelas imediatamente anteriores a
  janela-alvo, na ordem original do video.
- `target`: o texto da janela-alvo.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

CONTEXT_BUDGET = 3


@dataclass(frozen=True)
class Bundle:
    window_id: str
    display_id: str
    context: list[str]
    target: str


def build_bundle(
    video_id: str,
    window_index: int,
    windows_by_video: dict[str, list[dict]],
) -> Bundle:
    """Monta o bundle Fase4<->Fase5 da janela `window_index` do video `video_id`.

    `windows_by_video[video_id]` deve ser a lista de janelas do video
    ordenada por `idx` (mesmo shape que `src/janelas.py`/`src/amostragem.py`
    ja produzem). `context` e composto pelos campos `text` das janelas de
    indice `window_index - CONTEXT_BUDGET` ate `window_index - 1`
    (inclusive), na ordem original do video - nunca menos que zero
    elementos, nunca mais que `CONTEXT_BUDGET`, nunca de outro video, e
    nunca inclui `window_index + 1` em diante.
    """
    windows = windows_by_video[video_id]
    target_window = windows[window_index]

    context_start = max(0, window_index - CONTEXT_BUDGET)
    context = [w["text"] for w in windows[context_start:window_index]]

    window_id = target_window["window_id"]
    display_id = hashlib.sha1(f"{video_id}:{window_id}".encode()).hexdigest()[:8]

    return Bundle(
        window_id=window_id,
        display_id=display_id,
        context=context,
        target=target_window["text"],
    )
