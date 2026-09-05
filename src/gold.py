"""Fase 4 - Selecao do gold (`_docs/decisions.md#28(c)` e `#29(f)/(g)`):
escolhe os 5 videos gold e o video da reanotacao de 48h a partir do
corpus real de `@MackExplains7`, com um unico sorteio deterministico,
duration-blind, e persiste o resultado em
`gold/mackexplains7/selection.json`.

`scan_cta_candidates` e so um filtro de candidatos (varredura de texto
completo das janelas em busca de frases fixas de call-to-action); nao e
um classificador de `cta` e nao decide a taxa real do fenomeno no canal
(issue #12(a), fora de escopo aqui).

`GOLD_SEED = 42` segue o mesmo precedente de `SAMPLE_SEED`
(`src/amostragem.py`, `_docs/decisions.md#10c`): reproduzivel, uma unica
instancia de `random.Random` criada pelo chamador e passada adiante -
nenhuma funcao reseeda ou reinstancia.
"""

from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path

CORPUS_DIR = Path("corpus/mackexplains7")
MANIFEST_PATH = CORPUS_DIR / "manifesto.csv"
WINDOWS_DIR = CORPUS_DIR / "windows"
SELECTION_PATH = Path("gold/mackexplains7/selection.json")

GOLD_SEED = 42
N_GOLD = 5

CTA_PHRASES = [
    "link in the description",
    "let me know in the comments",
    "let us know in the comments",
]


# --------------------------------------------------------------------------
# 1. Manifesto
# --------------------------------------------------------------------------


def _load_manifest(manifest_path: Path = MANIFEST_PATH) -> list[dict]:
    with manifest_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def profile_video_ids(manifest_path: Path = MANIFEST_PATH) -> list[str]:
    """`video_id` de toda linha `role=profile` do manifesto, na ordem do
    arquivo (o chamador decide se precisa ordenar)."""
    return [row["id"] for row in _load_manifest(manifest_path) if row["role"] == "profile"]


# --------------------------------------------------------------------------
# 2. Scan de candidatos a cta
# --------------------------------------------------------------------------


def scan_cta_candidates(profile_video_ids: list[str], windows_dir: Path = WINDOWS_DIR) -> list[str]:
    """Varre o texto completo (todas as janelas, do inicio ao fim do
    video) de cada `video_id` em `profile_video_ids`, case-insensitive,
    contra exatamente `CTA_PHRASES`. E so um filtro de candidatos, nunca
    um classificador de `cta`. Retorna `sorted(matches)` puro."""
    matches: list[str] = []
    for video_id in profile_video_ids:
        data = json.loads((windows_dir / f"{video_id}.json").read_text(encoding="utf-8"))
        for window in data["windows"]:
            text = window["text"].lower()
            if any(phrase in text for phrase in CTA_PHRASES):
                matches.append(video_id)
                break
    return sorted(matches)


# --------------------------------------------------------------------------
# 3. Sorteio (contrato: uma unica instancia de rng, passada adiante)
# --------------------------------------------------------------------------


def select_gold_videos(
    candidates: list[str], all_profile_video_ids: list[str], rng: random.Random
) -> list[str]:
    """Se `candidates` nao vazio: ancora um deles e completa com mais 4
    sorteados sem reposicao entre os demais videos `profile`. Se vazio:
    sorteia 5 direto do pool inteiro. Nunca usa duracao."""
    if candidates:
        anchor = rng.choice(sorted(candidates))
        rest = rng.sample(sorted(v for v in all_profile_video_ids if v != anchor), N_GOLD - 1)
        return [anchor] + rest
    return rng.sample(sorted(all_profile_video_ids), N_GOLD)


def select_reannotation_video(gold_videos: list[str], rng: random.Random) -> str:
    """Sorteia, com a mesma instancia de rng recebida, qual dos 5 videos
    gold sera reanotado 48h depois pra medir estabilidade de anotador."""
    return rng.choice(sorted(gold_videos))


# --------------------------------------------------------------------------
# 4. Artefato
# --------------------------------------------------------------------------


def write_selection_artifact(
    cta_candidates_found: list[str],
    gold_video_ids: list[str],
    reannotation_video_id: str,
    manifest_path: Path = MANIFEST_PATH,
    path: Path = SELECTION_PATH,
) -> Path:
    """Persiste `gold/mackexplains7/selection.json` com semente, os
    candidatos a cta encontrados no scan, os 5 videos gold (cada um com
    sua `duracao_s` real do manifesto) e o video da reanotacao."""
    durations = {row["id"]: int(row["duracao_s"]) for row in _load_manifest(manifest_path)}
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": GOLD_SEED,
        "cta_candidates_found": cta_candidates_found,
        "gold_video_ids": [
            {"video_id": video_id, "duracao_s": durations[video_id]} for video_id in gold_video_ids
        ],
        "reannotation_video_id": reannotation_video_id,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    all_profile_video_ids = sorted(profile_video_ids())
    candidates = scan_cta_candidates(all_profile_video_ids)
    rng = random.Random(GOLD_SEED)
    gold = select_gold_videos(candidates, all_profile_video_ids, rng)
    reannotation = select_reannotation_video(gold, rng)
    path = write_selection_artifact(candidates, gold, reannotation)
    print(f"gold={gold} reannotation={reannotation} escrito em {path}")


if __name__ == "__main__":
    main()
