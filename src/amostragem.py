"""Fase 2 - Amostragem: sorteio com semente fixa de janelas
(`src/janelas.py`) pro QA humano medir os criterios 1/2 do portao da
Fase 2 (`_docs/plano_implementacao.md` linha 306-316) - janelas com duas
funcoes narrativas distintas e sentencas cortadas. O criterio 3
(automatico) e medido por `src/janelas.check_gate`, nao aqui.

`SAMPLE_SEED = 42` (`_docs/decisions.md#10c`), mesmo precedente de
`HOLDOUT_SEED` (`_docs/decisions.md#6`): o sorteio precisa ser
reproduzivel, pra QA medir exatamente a mesma amostra que o engineer
mediu, nao um sorteio novo.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

CORPUS_DIR = Path("corpus/mackexplains7")
WINDOWS_DIR = CORPUS_DIR / "windows"
SAMPLE_PATH = CORPUS_DIR / "fase2_sample.md"

SAMPLE_SEED = 42
SAMPLE_VIDEOS = 2
SAMPLE_WINDOWS = 50


# --------------------------------------------------------------------------
# 1. Sorteio de videos
# --------------------------------------------------------------------------


def sample_videos(
    windows_dir: Path = WINDOWS_DIR, seed: int = SAMPLE_SEED, n_videos: int = SAMPLE_VIDEOS
) -> list[str]:
    """Sorteia `n_videos` `video_id`, sem reposicao, com
    `random.Random(seed)`, entre os que tem arquivo em `windows_dir`.
    Candidatos em `sorted()` antes do sorteio - ordem de listagem de
    diretorio nao e garantida entre sistemas de arquivo, e mudaria o
    resultado pra mesma semente se nao fosse fixada. Devolve na ordem
    sorteada por `rng.sample` - essa ordem entra no relatorio."""
    candidates = sorted(p.stem for p in windows_dir.glob("*.json"))
    rng = random.Random(seed)
    return rng.sample(candidates, n_videos)


# --------------------------------------------------------------------------
# 2. Sorteio de janelas
# --------------------------------------------------------------------------


class InsufficientSample(RuntimeError):
    """A soma de janelas disponiveis nos videos sorteados e menor que
    `n_windows` mesmo depois do backfill - com o portao 3 (25-60
    janelas/video) ja passando, 2 videos somam pelo menos 50, entao isso
    so acontece se o portao 3 ainda nao rodou pros videos sorteados. Uma
    amostra abaixo de `n_windows` nao avalia o criterio "<=5 em 50" do
    portao e nao deve ser reportada como se avaliasse."""


def _load_windows(video_id: str, windows_dir: Path) -> list[dict]:
    data = json.loads((windows_dir / f"{video_id}.json").read_text(encoding="utf-8"))
    return data["windows"]


def sample_windows(
    video_ids: list[str],
    windows_dir: Path = WINDOWS_DIR,
    n_windows: int = SAMPLE_WINDOWS,
    seed: int = SAMPLE_SEED,
) -> list[dict]:
    """Amostra aleatoria sem reposicao (`_docs/plano_implementacao.md`
    linha 310 exige "amostra aleatoria com semente fixa") - nunca as
    primeiras janelas em ordem de `idx`, que seria uma fatia previsivel,
    nao uma amostra. Cota base de `n_windows // len(video_ids)` janelas
    sorteadas de cada video com `random.Random(seed).sample()`; um video
    com menos que a cota entra inteiro, e o deficit e completado sorteando
    janelas adicionais (mesmo rng, continuando a sequencia) dentre as
    janelas dos outros videos sorteados que ainda nao entraram - nunca
    excluindo nenhum video. Levanta `InsufficientSample` se, mesmo apos o
    backfill, a soma total ficar abaixo de `n_windows`. A ordem de retorno
    agrupa por video (ordem de `video_ids`) e ordena por `idx` dentro de
    cada grupo, so para leitura do relatorio - a escolha de quais janelas
    entram ja foi decidida pelo sorteio, ordenar a apresentacao depois nao
    reintroduz vies."""
    rng = random.Random(seed)
    per_video = {
        vid: sorted(_load_windows(vid, windows_dir), key=lambda w: w["idx"]) for vid in video_ids
    }
    quota = n_windows // len(video_ids)
    selected: dict[str, list[dict]] = {}
    leftover: dict[str, list[dict]] = {}
    for vid in video_ids:
        windows = per_video[vid]
        if len(windows) <= quota:
            selected[vid], leftover[vid] = list(windows), []
        else:
            chosen = rng.sample(windows, quota)
            chosen_ids = {w["window_id"] for w in chosen}
            selected[vid] = chosen
            leftover[vid] = [w for w in windows if w["window_id"] not in chosen_ids]

    deficit = n_windows - sum(len(v) for v in selected.values())
    if deficit > 0:
        pool = [w for vid in video_ids for w in leftover[vid]]
        for w in rng.sample(pool, min(deficit, len(pool))):
            selected[w["video_id"]].append(w)
        deficit -= min(deficit, len(pool))
    if deficit > 0:
        raise InsufficientSample(
            f"videos sorteados {video_ids} tem {n_windows - deficit} janelas juntos, "
            f"precisa de {n_windows}"
        )

    return [w for vid in video_ids for w in sorted(selected[vid], key=lambda w: w["idx"])]


# --------------------------------------------------------------------------
# 3. Relatorio
# --------------------------------------------------------------------------


def write_sample_report(
    windows: list[dict],
    video_ids: list[str],
    path: Path = SAMPLE_PATH,
    seed: int = SAMPLE_SEED,
) -> Path:
    """Markdown: cabecalho com a semente, `video_id` sorteados, N de
    janelas, e o criterio de aceite (`<=5/50` "duas funcoes", 0 "sentenca
    cortada"); depois uma tabela com `window_id | video_id | start_s |
    end_s | n_sentences | n_words | text | two_functions | sentence_cut`,
    as duas ultimas colunas em branco. QA preenche as duas colunas
    manualmente e soma - o script nao reprocessa o preenchimento."""
    lines = [
        "# Amostra Fase 2 - portao criterio 1/2 (julgamento humano)",
        "",
        f"- Semente: `{seed}`",
        f"- Videos sorteados: {', '.join(video_ids)}",
        f"- Janelas na amostra: {len(windows)}",
        "- Criterio de aceite (`_docs/plano_implementacao.md` linha 306-316):",
        "  - `two_functions` (janelas com duas funcoes narrativas distintas): <= 5 em 50",
        "  - `sentence_cut` (sentencas cortadas no meio de oracao): 0 na mesma amostra",
        "",
        "| window_id | video_id | start_s | end_s | n_sentences | n_words | text "
        "| two_functions | sentence_cut |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for w in windows:
        text = w["text"].replace("|", "\\|")
        lines.append(
            f"| {w['window_id']} | {w['video_id']} | {w['start_s']} | {w['end_s']} | "
            f"{w['n_sentences']} | {w['n_words']} | {text} |  |  |"
        )
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    ids = sample_videos()
    windows = sample_windows(ids)
    path = write_sample_report(windows, ids)
    print(f"amostra de {len(windows)} janelas de {ids} em {path}")


if __name__ == "__main__":
    main()
