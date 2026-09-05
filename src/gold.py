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
from datetime import UTC, datetime
from pathlib import Path

from src.context_budget import build_bundle
from src.schema_loader import load_ontology

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
        return [anchor, *rest]
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
        "generated_at": datetime.now(UTC).isoformat(),
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


# --------------------------------------------------------------------------
# 5. Exportacao dos worksheets de anotacao (round 1 e round 2)
# --------------------------------------------------------------------------


def export_round(
    video_id: str,
    round: str,
    windows_by_video: dict[str, list[dict]],
    out_dir: Path,
) -> tuple[Path, Path]:
    """Exporta o worksheet e o indice de uma rodada de anotacao para um
    unico video.

    Escreve `out_dir/<round>/<video_id>.worksheet.jsonl` - uma linha JSON
    por janela do video, na ordem original do video - e
    `out_dir/<round>/<video_id>.index.json` - o mapeamento
    `{display_id: window_id}` de todas as janelas.

    Todo bundle (contexto, target, display_id, window_id) vem de
    `context_budget.build_bundle`; este modulo nunca reimplementa
    fatiamento de janelas ou a formula de `display_id`. A lista de campos
    ontologicos do worksheet vem de `schema_loader.load_ontology()`,
    nunca hardcoded - cada campo comeca com valor `null`, pronto para o
    dono do projeto anotar a mao.

    Nem o worksheet nem o indice contem qualquer dado variavel entre
    execucoes (timestamp, nome da rodada, caminho absoluto): o conteudo e
    puramente deterministico a partir de `(video_id, windows_by_video)`,
    para que round 1 e round 2 do mesmo video produzam bytes identicos.
    """
    ontology_field_names = [field["name"] for field in load_ontology()["fields"]]
    windows = windows_by_video[video_id]

    worksheet_lines = []
    index: dict[str, str] = {}
    for window_index in range(len(windows)):
        bundle = build_bundle(video_id, window_index, windows_by_video)
        record = {
            "display_id": bundle.display_id,
            "context": bundle.context,
            "target": bundle.target,
            **dict.fromkeys(ontology_field_names),
        }
        worksheet_lines.append(json.dumps(record, ensure_ascii=False))
        index[bundle.display_id] = bundle.window_id

    round_dir = out_dir / round
    round_dir.mkdir(parents=True, exist_ok=True)

    worksheet_path = round_dir / f"{video_id}.worksheet.jsonl"
    worksheet_path.write_text("\n".join(worksheet_lines) + "\n", encoding="utf-8")

    index_path = round_dir / f"{video_id}.index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return worksheet_path, index_path


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
