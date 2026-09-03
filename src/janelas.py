"""Fase 2 - Janelas: agrupa sentencas (`src/sentencia.py`) em janelas de
anotacao e roda o portao automatico da Fase 2 (criterio 3 - os criterios 1
e 2 exigem julgamento humano, cobertos por `src/amostragem.py`).

Regra de construcao (`_docs/plano_implementacao.md`, Fase 2, passo 3):
acumule sentencas consecutivas ate `WINDOW_MAX_WORDS` palavras ou
`WINDOW_MAX_SENTENCES` sentencas, o que vier primeiro, sem sobreposicao.
Minimo de `WINDOW_MIN_SENTENCES`, exceto a ultima janela de cada video.

Roda so contra `corpus/mackexplains7` (`_docs/decisions.md#10d`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

CORPUS_DIR = Path("corpus/mackexplains7")
SENTENCES_DIR = CORPUS_DIR / "sentences"
WINDOWS_DIR = CORPUS_DIR / "windows"

WINDOW_MAX_WORDS = 35
WINDOW_MAX_SENTENCES = 4
WINDOW_MIN_SENTENCES = 2

# GATE_* sao o limite do portao (_docs/plano_implementacao.md linha 312),
# mais frouxo que a regra de construcao WINDOW_* de proposito - da folga
# pra sentencas isoladas longas sem reprovar o portao a toa.
GATE_MAX_WINDOW_WORDS = 60
GATE_MIN_WINDOWS_PER_VIDEO = 25
GATE_MAX_WINDOWS_PER_VIDEO = 60


# --------------------------------------------------------------------------
# 1. Agrupamento
# --------------------------------------------------------------------------


def group_windows(
    sentences: list[dict],
    max_words: int = WINDOW_MAX_WORDS,
    max_sentences: int = WINDOW_MAX_SENTENCES,
) -> list[list[dict]]:
    """Acumula sentencas consecutivas (ja ordenadas por `idx`) ate
    `max_words` ou `max_sentences`, o que vier primeiro, sem sobreposicao.
    A ultima janela do video fica com o que sobrar, mesmo abaixo de
    `WINDOW_MIN_SENTENCES` - excecao explicita do plano, nao um bug. Uma
    sentenca isolada que sozinha ja excede `max_words` vira uma janela de
    1; isso e reportado pelo portao (`check_gate`), nao corrigido aqui em
    silencio."""
    windows: list[list[dict]] = []
    current: list[dict] = []
    current_words = 0

    for sentence in sentences:
        if current and (
            current_words + sentence["n_words"] > max_words or len(current) >= max_sentences
        ):
            windows.append(current)
            current = []
            current_words = 0
        current.append(sentence)
        current_words += sentence["n_words"]

    if current:
        windows.append(current)

    return windows


# --------------------------------------------------------------------------
# 2. Registro de janela
# --------------------------------------------------------------------------


def window_records(
    video_id: str,
    sentences: list[dict],
    duration_s: float,
    max_words: int = WINDOW_MAX_WORDS,
    max_sentences: int = WINDOW_MAX_SENTENCES,
) -> list[dict]:
    records = []
    for idx, group in enumerate(group_windows(sentences, max_words, max_sentences)):
        text = " ".join(s["text"] for s in group)
        start_s = group[0]["start_s"]
        records.append(
            {
                "window_id": f"{video_id}:j{idx:04d}",
                "video_id": video_id,
                "idx": idx,
                "sent_ids": [s["sent_id"] for s in group],
                "start_s": start_s,
                "end_s": group[-1]["end_s"],
                "text": text,
                "n_words": len(text.split()),
                "n_sentences": len(group),
                "pos_pct": start_s / duration_s if duration_s else None,
            }
        )
    return records


# --------------------------------------------------------------------------
# 3. Portao da Fase 2 (criterio 3, automatico)
# --------------------------------------------------------------------------


def check_gate(windows_by_video: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Portao da Fase 2, criterio 3 (`_docs/plano_implementacao.md` linha
    312): por video, entre `GATE_MIN_WINDOWS_PER_VIDEO` e
    `GATE_MAX_WINDOWS_PER_VIDEO` janelas; nenhuma janela com mais de
    `GATE_MAX_WINDOW_WORDS` palavras; nenhuma janela com menos de
    `WINDOW_MIN_SENTENCES` sentencas, exceto a ultima janela de cada video
    (maior `idx`)."""
    problems: list[str] = []

    for video_id, windows in windows_by_video.items():
        n = len(windows)
        if not (GATE_MIN_WINDOWS_PER_VIDEO <= n <= GATE_MAX_WINDOWS_PER_VIDEO):
            problems.append(
                f"{video_id}: {n} janelas, esperado entre "
                f"{GATE_MIN_WINDOWS_PER_VIDEO} e {GATE_MAX_WINDOWS_PER_VIDEO}"
            )

        last_idx = max((w["idx"] for w in windows), default=None)
        for window in windows:
            if window["n_words"] > GATE_MAX_WINDOW_WORDS:
                problems.append(
                    f"{window['window_id']}: {window['n_words']} palavras, "
                    f"maximo {GATE_MAX_WINDOW_WORDS}"
                )
            is_last = window["idx"] == last_idx
            if not is_last and window["n_sentences"] < WINDOW_MIN_SENTENCES:
                problems.append(
                    f"{window['window_id']}: {window['n_sentences']} sentencas, "
                    f"minimo {WINDOW_MIN_SENTENCES} (nao e a ultima janela do video)"
                )

    return not problems, problems


# --------------------------------------------------------------------------
# 4. Pipeline
# --------------------------------------------------------------------------


def run(
    sentences_dir: Path = SENTENCES_DIR, windows_dir: Path = WINDOWS_DIR
) -> dict[str, list[dict]]:
    """Le todo `corpus/<canal>/sentences/*.json`, gera janelas, escreve
    `corpus/<canal>/windows/<video_id>.json` (mesmo envelope de
    `write_sentences`, sem `duration_s` - ja esta embutido em `pos_pct`).
    Devolve `{video_id: windows}` pro `check_gate`."""
    windows_dir.mkdir(parents=True, exist_ok=True)
    windows_by_video: dict[str, list[dict]] = {}

    for path in sorted(sentences_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        video_id = data["video_id"]
        records = window_records(video_id, data["sentences"], data["duration_s"])
        windows_by_video[video_id] = records

        out_path = windows_dir / f"{video_id}.json"
        payload = {
            "video_id": video_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "windows": records,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return windows_by_video


def main() -> None:
    windows_by_video = run()
    passed, problems = check_gate(windows_by_video)
    total = sum(len(w) for w in windows_by_video.values())
    print(f"{len(windows_by_video)} videos, {total} janelas em {WINDOWS_DIR}")
    print("Portao Fase 2 (criterio 3): " + ("PASSOU" if passed else "FALHOU"))
    for p in problems:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
