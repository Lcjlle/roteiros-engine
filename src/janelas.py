"""Fase 2 - Janelas: agrupa sentencas (`src/sentencia.py`) em janelas de
anotacao e roda o portao automatico da Fase 2 (criterio 3 - os criterios 1
e 2 exigem julgamento humano, cobertos por `src/amostragem.py`).

Regra de construcao (`_docs/plano_implementacao.md`, Fase 2, passo 3,
corrigida por `_docs/decisions.md#13`): acumule sentencas consecutivas ate
`WINDOW_MAX_WORDS` palavras ou `WINDOW_MAX_SENTENCES` sentencas, o que vier
primeiro, perseguindo ativamente `WINDOW_MIN_SENTENCES` antes de fechar uma
janela nao-final (aceita estourar `WINDOW_MAX_WORDS`, ate `GATE_MAX_WINDOW_WORDS`,
pra alcancar o minimo). Minimo de `WINDOW_MIN_SENTENCES`, exceto a ultima
janela de cada video.

Portao (criterio 3), reestruturado em 3a/3b/3c/3d por `_docs/decisions.md#14`:
3a/3b sao invariantes (0 de tolerancia, o algoritmo controla o resultado por
completo); 3c/3d sao tolerancias (o comprimento real das sentencas do canal
empurra o resultado, nao o algoritmo) - `check_gate()` PASSA so se 3a/3b/3d
passarem em todos os videos; 3c e sempre medido e reportado, mas nunca
bloqueia PASSOU/FALHOU (termometro de canal, nao portao de algoritmo).

Roda so contra `corpus/mackexplains7` (`_docs/decisions.md#10d`).
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

CORPUS_DIR = Path("corpus/mackexplains7")
SENTENCES_DIR = CORPUS_DIR / "sentences"
WINDOWS_DIR = CORPUS_DIR / "windows"

WINDOW_MAX_WORDS = 35
WINDOW_MAX_SENTENCES = 4
WINDOW_MIN_SENTENCES = 2

# GATE_* sao os limites do portao, criterio 3 (`_docs/decisions.md#14`).
GATE_MAX_WINDOW_WORDS = 60
GATE_WINDOWS_PER_MINUTE = 4.86
GATE_WINDOWS_PER_MINUTE_BAND = 0.4
GATE_NONLAST_SINGLE_WINDOW_MAX_RATIO = 0.15


# --------------------------------------------------------------------------
# 1. Agrupamento
# --------------------------------------------------------------------------


def group_windows(
    sentences: list[dict],
    max_words: int = WINDOW_MAX_WORDS,
    max_sentences: int = WINDOW_MAX_SENTENCES,
    min_sentences: int = WINDOW_MIN_SENTENCES,
    gate_max_words: int = GATE_MAX_WINDOW_WORDS,
) -> list[list[dict]]:
    """Acumula sentencas consecutivas (ja ordenadas por `idx`) ate
    `max_words` ou `max_sentences`, o que vier primeiro, sem sobreposicao,
    perseguindo ativamente `min_sentences` antes de fechar uma janela
    nao-final (`_docs/decisions.md#13`): uma janela nao-final so pode
    fechar se ja tiver `max_sentences` sentencas, ou for uma unica sentenca
    que sozinha ja excede `max_words` (excecao inalterada - fecha imediato,
    nunca tenta puxar mais nada), ou se aceitar a proxima sentenca
    estourasse `max_words` e a janela ja tiver alcancado `min_sentences`,
    ou se aceitar a proxima sentenca estourasse `gate_max_words`. Fora
    desses casos, a janela aceita estourar `max_words` - ate, nunca alem,
    `gate_max_words` - ate alcancar `min_sentences`, retomando a logica
    normal depois disso. A ultima janela do video fica com o que sobrar,
    mesmo abaixo de `min_sentences` - excecao explicita do plano, nao um
    bug."""
    windows: list[list[dict]] = []
    current: list[dict] = []
    current_words = 0

    for sentence in sentences:
        if current:
            reached_max_sentences = len(current) >= max_sentences
            oversized_single = len(current) == 1 and current_words > max_words
            would_overflow = current_words + sentence["n_words"] > max_words
            would_exceed_gate = current_words + sentence["n_words"] > gate_max_words
            reached_min = len(current) >= min_sentences

            should_close = (
                reached_max_sentences
                or oversized_single
                or (would_overflow and (reached_min or would_exceed_gate))
            )
            if should_close:
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
    min_sentences: int = WINDOW_MIN_SENTENCES,
    gate_max_words: int = GATE_MAX_WINDOW_WORDS,
) -> list[dict]:
    records = []
    groups = group_windows(sentences, max_words, max_sentences, min_sentences, gate_max_words)
    for idx, group in enumerate(groups):
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
# 3. Portao da Fase 2 (criterio 3: 3a/3b/3c/3d, `_docs/decisions.md#14`)
# --------------------------------------------------------------------------


def _count_big(
    sentences_by_video: dict[str, dict], windows_by_video: dict[str, list[dict]]
) -> tuple[int, int]:
    """Contagem agregada de sentencas/janelas com `n_words >
    GATE_MAX_WINDOW_WORDS` no corpus inteiro. Sinal util (`check_3a`
    depende dele) mas NAO suficiente sozinho: duas contagens podem empatar
    por coincidencia sem provar que cada janela grande de fato veio de
    relay de uma sentenca ja grande - so a checagem por janela em
    `check_3a` prova proveniencia. Devolve `(n_sentencas_grandes,
    n_janelas_grandes)`."""
    n_sentences = sum(
        1
        for data in sentences_by_video.values()
        for s in data["sentences"]
        if s["n_words"] > GATE_MAX_WINDOW_WORDS
    )
    n_windows = sum(
        1
        for windows in windows_by_video.values()
        for w in windows
        if w["n_words"] > GATE_MAX_WINDOW_WORDS
    )
    return n_sentences, n_windows


def check_3a(
    sentences_by_video: dict[str, dict], windows_by_video: dict[str, list[dict]]
) -> tuple[bool, list[str]]:
    """3a - INVARIANTE + PROVENIENCIA. Dois niveis de checagem, o segundo
    fecha o buraco do primeiro:

    (1) Contagem agregada (`_count_big`): nº de janelas > `GATE_MAX_WINDOW_WORDS`
    no corpus inteiro tem que ser igual ao nº de sentencas > `GATE_MAX_WINDOW_WORDS`.
    Necessario, mas NAO suficiente sozinho - duas contagens podem empatar
    por coincidencia (ex.: uma janela grande formada por fusao de varias
    sentencas medias, enquanto uma sentenca grande de verdade "some" em
    outro lugar do corpus), sem que nenhuma das duas janelas problematicas
    seja de fato explicada.

    (2) Proveniencia por janela (o que fecha o buraco de (1)): toda janela
    com `n_words > GATE_MAX_WINDOW_WORDS` tem que ter `n_sentences == 1` E
    a sentenca referenciada por `sent_ids[0]` (buscada em
    `sentences_by_video[video_id]["sentences"]`) tem que, ela mesma, ter
    `n_words > GATE_MAX_WINDOW_WORDS`. Essa e a unica forma legitima de uma
    janela estourar - `group_windows()` nunca deixa a soma de VARIAS
    sentencas ultrapassar `gate_max_words`, entao uma janela grande so pode
    existir por estar relaying uma sentenca ja grande sozinha, nunca por
    fusao.

    Devolve `(passou, problemas)`: um problema para a contagem agregada se
    ela nao bater, e um problema por janela cuja proveniencia nao foi
    comprovada, cada um citando o `window_id`."""
    problems: list[str] = []

    n_sent_big, n_win_big = _count_big(sentences_by_video, windows_by_video)
    if n_sent_big != n_win_big:
        problems.append(
            f"3a: {n_win_big} janela(s) > {GATE_MAX_WINDOW_WORDS} palavras no corpus, "
            f"esperado igual as {n_sent_big} sentenca(s) > {GATE_MAX_WINDOW_WORDS} palavras "
            "(contagem agregada, invariante, 0 de diferenca)"
        )

    for video_id, windows in windows_by_video.items():
        sent_by_id = {s["sent_id"]: s for s in sentences_by_video[video_id]["sentences"]}
        for w in windows:
            if w["n_words"] <= GATE_MAX_WINDOW_WORDS:
                continue
            if w["n_sentences"] != 1:
                problems.append(
                    f"3a: {w['window_id']} tem {w['n_words']} palavras (> "
                    f"{GATE_MAX_WINDOW_WORDS}) mas {w['n_sentences']} sentencas - janela "
                    "grande so pode vir de relay de uma sentenca ja grande, nunca de "
                    "fusao de varias (proveniencia nao comprovada)"
                )
                continue
            sentence = sent_by_id.get(w["sent_ids"][0])
            if sentence is None or sentence["n_words"] <= GATE_MAX_WINDOW_WORDS:
                found = (
                    f"{sentence['n_words']} palavras"
                    if sentence is not None
                    else "sentenca nao encontrada em sentences_by_video"
                )
                problems.append(
                    f"3a: {w['window_id']} tem {w['n_words']} palavras (> "
                    f"{GATE_MAX_WINDOW_WORDS}) mas a sentenca referenciada "
                    f"({w['sent_ids'][0]}) tem {found}, nao > {GATE_MAX_WINDOW_WORDS} "
                    "(proveniencia nao comprovada)"
                )

    return not problems, problems


def check_3b(
    sentences_by_video: dict[str, dict], windows_by_video: dict[str, list[dict]]
) -> tuple[bool, int]:
    """3b - INVARIANTE: toda janela de 1 sentenca nao-final tem que ser
    explicada por (i) sua sentenca isolada ja excedendo `WINDOW_MAX_WORDS`
    sozinha, ou (ii) um fechamento forcado porque a proxima sentenca (por
    `idx`, em `sentences/*.json`) estouraria `GATE_MAX_WINDOW_WORDS`.
    Residuo nao explicado (total de janelas-de-1-nao-final menos (i) menos
    (ii)) tem que ser 0. Devolve `(passou, residuo)`."""
    residual = 0
    for video_id, windows in windows_by_video.items():
        if not windows:
            continue
        sent_by_id = {s["sent_id"]: s for s in sentences_by_video[video_id]["sentences"]}
        for window in windows[:-1]:  # exclui a ultima janela do video
            if window["n_sentences"] != 1:
                continue
            explained = window["n_words"] > WINDOW_MAX_WORDS  # caso (i)
            if not explained:
                sentence = sent_by_id[window["sent_ids"][0]]
                next_sentence = sent_by_id.get(f"{video_id}:s{sentence['idx'] + 1:04d}")
                explained = next_sentence is not None and (
                    window["n_words"] + next_sentence["n_words"] > GATE_MAX_WINDOW_WORDS
                )  # caso (ii)
            if not explained:
                residual += 1
    return residual == 0, residual


def check_3c(
    windows_by_video: dict[str, list[dict]],
    threshold: float = GATE_NONLAST_SINGLE_WINDOW_MAX_RATIO,
) -> tuple[bool, float]:
    """3c - TOLERANCIA, termometro de canal, nao portao de algoritmo:
    janelas de 1 sentenca nao-final / total de janelas do corpus inteiro
    <= `threshold`. Nao mede se `group_windows()` tem bug (3a/3b ja cobrem
    isso com zero tolerancia) - mede se as sentencas deste canal sao longas
    demais pra unidade de janela (2-4 sentencas) funcionar. Devolve
    `(dentro_da_tolerancia, ratio_medido)`."""
    total = sum(len(windows) for windows in windows_by_video.values())
    if total == 0:
        return True, 0.0
    nonlast_one = sum(
        1 for windows in windows_by_video.values() for w in windows[:-1] if w["n_sentences"] == 1
    )
    ratio = nonlast_one / total
    return ratio <= threshold, ratio


def _window_band(duration_s: float) -> tuple[int, int]:
    """`[baixo, alto]` esperado de janelas pra um video de `duration_s`
    segundos, banda proporcional de `_docs/decisions.md#14`."""
    duration_min = duration_s / 60
    low = math.ceil(duration_min * GATE_WINDOWS_PER_MINUTE * (1 - GATE_WINDOWS_PER_MINUTE_BAND))
    high = math.floor(duration_min * GATE_WINDOWS_PER_MINUTE * (1 + GATE_WINDOWS_PER_MINUTE_BAND))
    return low, high


def check_3d(
    sentences_by_video: dict[str, dict], windows_by_video: dict[str, list[dict]]
) -> tuple[bool, list[str]]:
    """3d - TOLERANCIA, banda proporcional de duracao, por video:
    `ceil(duracao_min * GATE_WINDOWS_PER_MINUTE * (1 - BAND)) <= n_janelas
    <= floor(duracao_min * GATE_WINDOWS_PER_MINUTE * (1 + BAND))`. Devolve
    `(passou_em_todos_os_videos, problemas_por_video)`."""
    problems: list[str] = []
    for video_id, windows in windows_by_video.items():
        duration_s = sentences_by_video[video_id]["duration_s"]
        low, high = _window_band(duration_s)
        n = len(windows)
        if not (low <= n <= high):
            problems.append(
                f"3d: {video_id}: {n} janelas, esperado entre {low} e {high} "
                f"(banda de duracao, {duration_s / 60:.2f} min a "
                f"{GATE_WINDOWS_PER_MINUTE} janelas/min +-{GATE_WINDOWS_PER_MINUTE_BAND:.0%})"
            )
    return not problems, problems


def check_gate(
    windows_by_video: dict[str, list[dict]], sentences_by_video: dict[str, dict]
) -> tuple[bool, list[str]]:
    """Portao da Fase 2, criterio 3 reestruturado em 3a/3b/3c/3d
    (`_docs/decisions.md#14`). `sentences_by_video` e o envelope completo
    de cada `sentences/<video_id>.json` (`video_id`/`duration_s`/`sentences`)
    - 3a/3b precisam do denominador/proxima-sentenca la, `windows/*.json`
    sozinho nao basta; 3d precisa de `duration_s`. PASSA so se 3a, 3b e 3d
    passarem para todos os videos - 3c e medido sempre (ver `check_3c`),
    mas nunca bloqueia PASSOU/FALHOU."""
    problems: list[str] = []

    a_ok, a_problems = check_3a(sentences_by_video, windows_by_video)
    problems.extend(a_problems)

    b_ok, residual = check_3b(sentences_by_video, windows_by_video)
    if not b_ok:
        problems.append(
            f"3b: {residual} janela(s) de 1 sentenca nao-final sem explicacao "
            "(invariante, residuo esperado 0)"
        )

    d_ok, d_problems = check_3d(sentences_by_video, windows_by_video)
    problems.extend(d_problems)

    return a_ok and b_ok and d_ok, problems


# --------------------------------------------------------------------------
# 4. Pipeline
# --------------------------------------------------------------------------


def run(
    sentences_dir: Path = SENTENCES_DIR, windows_dir: Path = WINDOWS_DIR
) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    """Le todo `corpus/<canal>/sentences/*.json`, gera janelas, escreve
    `corpus/<canal>/windows/<video_id>.json` (mesmo envelope de
    `write_sentences`, sem `duration_s` - ja esta embutido em `pos_pct`).
    Devolve `(windows_by_video, sentences_by_video)` pro `check_gate` - o
    segundo e o envelope completo de cada `sentences/<video_id>.json`
    (3a/3b/3d precisam de `duration_s`/`sentences` de la, nao so das
    janelas ja montadas)."""
    windows_dir.mkdir(parents=True, exist_ok=True)
    windows_by_video: dict[str, list[dict]] = {}
    sentences_by_video: dict[str, dict] = {}

    for path in sorted(sentences_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        video_id = data["video_id"]
        sentences_by_video[video_id] = data
        records = window_records(video_id, data["sentences"], data["duration_s"])
        windows_by_video[video_id] = records

        out_path = windows_dir / f"{video_id}.json"
        payload = {
            "video_id": video_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "windows": records,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return windows_by_video, sentences_by_video


def main() -> None:
    windows_by_video, sentences_by_video = run()
    passed, problems = check_gate(windows_by_video, sentences_by_video)
    total = sum(len(w) for w in windows_by_video.values())
    print(f"{len(windows_by_video)} videos, {total} janelas em {WINDOWS_DIR}")

    a_ok, _a_problems = check_3a(sentences_by_video, windows_by_video)
    n_sent_big, n_win_big = _count_big(sentences_by_video, windows_by_video)
    print(
        f"3a (invariante + proveniencia por janela): {n_win_big} janelas > "
        f"{GATE_MAX_WINDOW_WORDS} palavras == {n_sent_big} sentencas > "
        f"{GATE_MAX_WINDOW_WORDS} palavras -> {'OK' if a_ok else 'FALHOU'}"
    )
    b_ok, residual = check_3b(sentences_by_video, windows_by_video)
    print(f"3b (invariante): residuo nao explicado = {residual} -> {'OK' if b_ok else 'FALHOU'}")
    c_ok, ratio = check_3c(windows_by_video)
    print(
        f"3c (tolerancia, <= {GATE_NONLAST_SINGLE_WINDOW_MAX_RATIO:.0%}, nao bloqueia): "
        f"{ratio:.1%} de janelas de 1 sentenca nao-final -> "
        f"{'dentro' if c_ok else 'acima'} da tolerancia"
    )
    d_ok, d_problems = check_3d(sentences_by_video, windows_by_video)
    print(
        f"3d (tolerancia, banda por video): {'OK' if d_ok else 'FALHOU'} "
        f"({len(d_problems)} video(s) fora da banda)"
    )

    print("Portao Fase 2 (criterio 3): " + ("PASSOU" if passed else "FALHOU"))
    for p in problems:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
