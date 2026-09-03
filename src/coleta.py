"""Fase 1 - Coleta: transcricoes limpas do canal de referencia por canal.

Pipeline: lista os videos do canal com `yt-dlp --flat-playlist --dump-json`,
seleciona os `target` videos `profile` pelo desempenho relativo (nao os mais
recentes) e reserva ate `HOLDOUT_TARGET` videos `holdout` elegiveis (sorteio
com semente fixa, nunca a cauda de menor `view_count` - `select_holdout()`,
`_docs/decisions.md#6`) do mesmo pool. So os videos `profile` sao
transcritos: baixa legenda (`youtube-transcript-api`, com `yt-dlp` como
fallback de enumeracao e `whisperX` como ultimo recurso quando nao ha
legenda nenhuma), aplica limpeza minima e escreve `corpus/<canal>/raw/*.json`
+ `corpus/<canal>/manifesto.csv` (coluna `role`: `profile`/`holdout` -
`_docs/decisions.md#7`). Videos `holdout` entram so com
`id`/`titulo`/`duracao_s` - nunca sao transcritos, ate a Fase 8.
Ver `_docs/plano_implementacao.md`, Fase 1, para o desenho e o portao;
`_docs/decisions.md#3` documenta um piso temporario de >= 21 durante um
bloqueio de IP, superado pelo item #4 quando o corpus de `@Zenn0009` foi
completado ate 30 via fallback whisperX.

O cru (o que a fonte devolveu) nunca e sobrescrito: a limpeza sempre gera um
arquivo `.limpo.json` novo ao lado do `.json` cru.
"""

from __future__ import annotations

import csv
import json
import random
import re
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
)

CHANNEL_URL = "https://www.youtube.com/@Zenn0009/videos"
CORPUS_DIR = Path("corpus/zenn0009")
RAW_DIR = CORPUS_DIR / "raw"
MANIFEST_PATH = CORPUS_DIR / "manifesto.csv"

TARGET_COUNT = 30
# Shorts sao ate 3 min (180s) na classificacao atual do YouTube.
MIN_DURATION_S = 180
# "mais de 6 meses", aproximado em dias corridos.
MIN_AGE_DAYS = 182
SLEEP_SECONDS = 3
# Heuristica de fala para o portao de contagem de palavras (Fase 1,
# _docs/plano_implementacao.md): legenda automatica em ingles fala
# tipicamente ~150 palavras/min. Corrigido de 140 (_docs/decisions.md#8) -
# nao reabre o resultado ja commitado de @Zenn0009 (o pior ratio la, 119.1%
# a 140 wpm, continua acima do piso de 60% a 150 wpm).
WORDS_PER_MINUTE = 150
MIN_WORD_RATIO = 0.6
# batch_size=16 (o default historico do whisperX) estoura VRAM em GPUs de
# 6GB (RTX 4050 laptop, testado em video real) mesmo com `large-v2` +
# `int8_float16` - o modelo cabe com folga, o lote grande nao. 4 mede
# ~4GB de pico contra 6GB disponiveis, testado nos extremos de duracao do
# corpus (238s e 777s).
WHISPERX_BATCH_SIZE = 4
# _docs/decisions.md#3 relaxou este piso para >=21 durante um bloqueio de
# IP real da YouTube; _docs/decisions.md#4 completou o corpus de
# @Zenn0009 ate 30 via whisperX e supera o item #3 - o piso volta a ser o
# alvo cheio.
MIN_ROWS = TARGET_COUNT

# Reserva de holdout (`_docs/plano_implementacao.md` v3.0; semente e alvo
# fixados em `_docs/decisions.md#6`): sorteio, nao a cauda de menor
# `view_count` - o plano proibe isso explicitamente. HOLDOUT_TARGET e o
# topo da faixa "4-5" que o plano deixa em aberto; MIN_HOLDOUT e o minimo
# antes de o pool elegivel reprovar o criterio pratico de canal
# (`DECISOES.md#4`) em vez de encolher mais.
HOLDOUT_SEED = 42
HOLDOUT_TARGET = 5
MIN_HOLDOUT = 4

ROLE_PROFILE = "profile"
ROLE_HOLDOUT = "holdout"

MANIFEST_FIELDS = ["id", "titulo", "duracao_s", "contagem_palavras", "fonte", "role"]

MARKER_RE = re.compile(r"\[(m[uú]sica|music|aplausos|applause)\]", re.IGNORECASE)


# --------------------------------------------------------------------------
# 1. Listagem e selecao
# --------------------------------------------------------------------------


def list_channel_videos(channel_url: str = CHANNEL_URL) -> list[dict]:
    """Lista os videos do canal via `yt-dlp --flat-playlist --dump-json`.

    Guarda id, titulo, duracao, data de publicacao (aproximada) e views -
    exatamente os campos que o primeiro criterio de aceite da issue #1 pede.
    `youtubetab:approximate_date` evita uma segunda chamada por video so
    para obter a data de publicacao.
    """
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--extractor-args",
        "youtubetab:approximate_date",
        channel_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    videos = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        timestamp = data.get("timestamp")
        videos.append(
            {
                "id": data["id"],
                "title": data["title"],
                "duration": data.get("duration") or 0,
                "view_count": data.get("view_count") or 0,
                "published_at": (datetime.fromtimestamp(timestamp, tz=UTC) if timestamp else None),
            }
        )
    return videos


def _eligible_pool(
    videos: list[dict],
    target: int,
    min_duration_s: int = MIN_DURATION_S,
    min_age_days: int = MIN_AGE_DAYS,
    now: datetime | None = None,
) -> list[dict]:
    """Pool elegivel (videos longos, com o recuo de canal jovem) que tanto
    `select_videos()` quanto `select_holdout()` usam - fatorado pra elas
    nunca divergirem sobre o que "o mesmo pool" significa.
    """
    now = now or datetime.now(UTC)
    long_form = [v for v in videos if v["duration"] >= min_duration_s]

    def age_days(video: dict) -> int:
        published_at = video.get("published_at")
        if published_at is None:
            return 0  # data desconhecida: trata como recem-publicado
        return (now - published_at).days

    mature = [v for v in long_form if age_days(v) >= min_age_days]
    return mature if len(mature) >= target else long_form


def select_videos(
    videos: list[dict],
    target: int = TARGET_COUNT,
    min_duration_s: int = MIN_DURATION_S,
    min_age_days: int = MIN_AGE_DAYS,
    now: datetime | None = None,
) -> list[dict]:
    """Seleciona `target` videos longos pelo desempenho relativo.

    Nao pega os `target` mais recentes: entre os videos longos (exclui
    shorts por duracao) com mais de `min_age_days`, pega os mais vistos - a
    alternativa mais simples que a Fase 1 do plano permite ("views ÷
    inscritos na epoca, ou simplesmente os 30 mais vistos entre videos com
    mais de 6 meses"), ja que o historico de inscritos por video nao esta
    disponivel via `yt-dlp`.

    Se o canal ainda nao tiver `target` videos com mais de `min_age_days`
    (canal jovem), o filtro de idade recua para o conjunto inteiro de
    videos longos, sempre ranqueado por views - a regra "nao pegue so os
    mais recentes" continua valendo mesmo nesse caso, so muda o tamanho do
    grupo elegivel.
    """
    pool = _eligible_pool(videos, target, min_duration_s, min_age_days, now)
    ranked = sorted(pool, key=lambda v: v["view_count"], reverse=True)
    return ranked[:target]


class ChannelPoolTooSmall(RuntimeError):
    """Pool elegivel nao tem videos suficientes pra `profile_target` +
    `min_holdout` (`_docs/decisions.md#6`) - achado real sobre o canal
    (criterio pratico de `DECISOES.md#4`), nao um bug de codigo. `collect()`
    deixa isso subir sem tentar coleta nenhuma.
    """


def select_holdout(
    videos: list[dict],
    profile: list[dict],
    target: int = HOLDOUT_TARGET,
    min_holdout: int = MIN_HOLDOUT,
    profile_target: int = TARGET_COUNT,
    min_duration_s: int = MIN_DURATION_S,
    min_age_days: int = MIN_AGE_DAYS,
    now: datetime | None = None,
    seed: int = HOLDOUT_SEED,
) -> list[dict]:
    """Reserva ate `target` videos `holdout` do mesmo pool elegivel que
    `select_videos()` usou pros `profile_target` videos `profile`, menos os
    ja selecionados - sorteio com semente fixa (`_docs/decisions.md#6`),
    nunca a cauda de menor `view_count` (o plano proibe isso
    explicitamente).

    Se o pool nao tiver `target` videos sobrando depois do `profile`, o
    holdout encolhe pra caber, ate `min_holdout` (dentro da faixa "4-5" que
    o plano permite). Se o pool inteiro tiver menos que
    `profile_target + min_holdout` videos, levanta `ChannelPoolTooSmall` -
    a coleta nao roda, isso e reportado como achado sobre o canal, nao
    contornado silenciosamente encolhendo mais.

    `target=0` e `min_holdout=0` desativam a reserva inteira (usado por
    chamadas que nao querem holdout nenhum) sem exigir pool nenhum.
    """
    if target <= 0 and min_holdout <= 0:
        return []

    pool = _eligible_pool(videos, profile_target, min_duration_s, min_age_days, now)
    if len(pool) < profile_target + min_holdout:
        raise ChannelPoolTooSmall(
            f"pool elegivel tem {len(pool)} videos, precisa de pelo menos "
            f"{profile_target + min_holdout} ({profile_target} profile + "
            f"{min_holdout} holdout minimo)"
        )

    profile_ids = {v["id"] for v in profile}
    remaining = [v for v in pool if v["id"] not in profile_ids]

    holdout_size = min(target, len(remaining))
    rng = random.Random(seed)
    return rng.sample(remaining, holdout_size)


# --------------------------------------------------------------------------
# 2. Transcricao: legenda -> yt-dlp -> whisperX
# --------------------------------------------------------------------------


def fetch_via_transcript_api(video_id: str) -> list[dict] | None:
    """Fonte primaria: `youtube-transcript-api`. `None` so quando o video
    genuinamente nao tem legenda (`TranscriptsDisabled`/`NoTranscriptFound`).
    Qualquer outro erro (IP bloqueado, rede, video indisponivel) sobe -
    nao e "sem legenda", e nao deve empurrar o video para o whisperX.
    """
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    return [{"start": s.start, "duration": s.duration, "text": s.text} for s in transcript]


def _parse_json3(data: dict) -> list[dict] | None:
    fragments = []
    for event in data.get("events", []):
        segs = event.get("segs")
        if not segs:
            continue
        text = "".join(seg.get("utf8", "") for seg in segs).replace("\n", " ").strip()
        if not text:
            continue
        fragments.append(
            {
                "start": event.get("tStartMs", 0) / 1000,
                "duration": event.get("dDurationMs", 0) / 1000,
                "text": text,
            }
        )
    return fragments or None


def fetch_via_ytdlp_subs(video_id: str, lang: str = "en.*") -> list[dict] | None:
    """Fallback de enumeracao: legenda (manual ou automatica) via `yt-dlp`."""
    with tempfile.TemporaryDirectory() as tmp:
        out_tmpl = str(Path(tmp) / "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-sub",
            "--write-auto-sub",
            "--sub-langs",
            lang,
            "--sub-format",
            "json3",
            "-o",
            out_tmpl,
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        matches = list(Path(tmp).glob(f"{video_id}*.json3"))
        if not matches:
            return None
        data = json.loads(matches[0].read_text())
    return _parse_json3(data)


class WhisperXUnavailable(RuntimeError):
    """whisperX ausente ou audio nao baixado - falha externa esperada
    (dependencia opcional nao instalada, download de audio falhou), nao um
    bug de codigo. Subclasse de `RuntimeError` de proposito estreito: so
    esses dois casos especificos usam essa classe, entao `collect()` pode
    capturar exatamente isso sem tambem engolir um `RuntimeError` generico
    vindo de um bug real em outro lugar do pipeline.
    """


def fetch_via_whisperx(
    video_id: str,
    device: str = "cpu",
    compute_type: str = "int8",
    batch_size: int = WHISPERX_BATCH_SIZE,
) -> list[dict]:
    """Ultimo recurso: transcreve o audio com whisperX. So roda quando nem
    `youtube-transcript-api` nem `yt-dlp` acharam legenda nenhuma - a etapa
    cara que a issue #1 pede para evitar por padrao.
    """
    try:
        import whisperx
    except ImportError as exc:
        raise WhisperXUnavailable(
            "whisperX nao esta instalado. So deve ser adicionado quando um "
            "video realmente nao tem legenda (`uv add whisperx==<versao>`, "
            "ver _docs/blueprint.md para a licenca) - nao roda por padrao."
        ) from exc

    with tempfile.TemporaryDirectory() as tmp:
        out_tmpl = str(Path(tmp) / "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "wav",
            "-o",
            out_tmpl,
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        matches = list(Path(tmp).glob(f"{video_id}*.wav"))
        if not matches:
            raise WhisperXUnavailable(f"whisperX: audio nao baixado para {video_id}")

        model = whisperx.load_model("large-v2", device, compute_type=compute_type)
        audio = whisperx.load_audio(str(matches[0]))
        result = model.transcribe(audio, batch_size=batch_size)
        align_model, metadata = whisperx.load_align_model(
            language_code=result["language"], device=device
        )
        aligned = whisperx.align(
            result["segments"], align_model, metadata, audio, device, return_char_alignments=False
        )

    return [
        {
            "start": segment["start"],
            "duration": segment["end"] - segment["start"],
            "text": segment["text"].strip(),
        }
        for segment in aligned["segments"]
    ]


def collect_transcript(video_id: str) -> tuple[list[dict], str]:
    """Roda o fallback legenda -> yt-dlp -> whisperX. Devolve (fragmentos, fonte)."""
    fragments = fetch_via_transcript_api(video_id)
    if fragments is not None:
        return fragments, "youtube_transcript_api"

    fragments = fetch_via_ytdlp_subs(video_id)
    if fragments is not None:
        return fragments, "yt-dlp"

    fragments = fetch_via_whisperx(video_id)
    return fragments, "whisperx"


# --------------------------------------------------------------------------
# 3. Limpeza minima
# --------------------------------------------------------------------------


def strip_markers(text: str) -> str:
    """Remove marcacoes `[Music]`/`[Aplausos]` (PT/EN) e normaliza espaco.
    Compartilhada com `src/sentencia.py`, que precisa da mesma limpeza
    antes de sentenciar - uma fonte so pra regra de marcador."""
    text = MARKER_RE.sub("", text)
    return " ".join(text.split())


def clean_transcript(fragments: list[dict], gap_threshold: float = 1.0) -> list[dict]:
    """Remove `[Musica]`/`[Aplausos]` e junta fragmentos adjacentes em
    trechos de texto corrido, preservando o timestamp de inicio de cada
    trecho. Sem correcao de pontuacao - isso e Fase 2.

    Um fragmento so-marcacao (ex.: `"[Music]"`) e removido e forca o
    proximo fragmento a comecar um trecho novo, mesmo sem gap de tempo -
    ele normalmente marca uma pausa real. Fragmentos adjacentes sem
    marcacao e sem gap maior que `gap_threshold` segundos sao unidos ao
    trecho corrente.
    """
    trechos: list[dict] = []
    last_end: float | None = None
    force_break = False

    for frag in fragments:
        text = strip_markers(frag["text"])
        start = float(frag["start"])
        end = start + float(frag.get("duration", 0.0))

        if not text:
            last_end = end
            force_break = True
            continue

        gap_too_big = last_end is not None and (start - last_end) > gap_threshold
        if not trechos or force_break or gap_too_big:
            trechos.append({"inicio_s": start, "texto": text})
        else:
            trechos[-1]["texto"] = f"{trechos[-1]['texto']} {text}"

        last_end = end
        force_break = False

    return trechos


def word_count(trechos: list[dict]) -> int:
    return sum(len(t["texto"].split()) for t in trechos)


def expected_word_count(duration_s: float, words_per_minute: int = WORDS_PER_MINUTE) -> float:
    return duration_s / 60 * words_per_minute


# --------------------------------------------------------------------------
# 4. Persistencia: cru, limpo, manifesto
# --------------------------------------------------------------------------


def write_raw(raw_dir: Path, video: dict, fragments: list[dict], source: str) -> Path:
    path = raw_dir / f"{video['id']}.json"
    payload = {
        "video_id": video["id"],
        "source": source,
        "metadata": {
            "title": video["title"],
            "duration": video["duration"],
            "view_count": video["view_count"],
            "published_at": (
                video["published_at"].isoformat() if video.get("published_at") else None
            ),
        },
        "fragments": fragments,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_clean(raw_dir: Path, video_id: str, trechos: list[dict]) -> Path:
    path = raw_dir / f"{video_id}.limpo.json"
    payload = {"video_id": video_id, "trechos": trechos}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_manifesto(rows: list[dict], path: Path = MANIFEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in MANIFEST_FIELDS})


def read_manifesto(path: Path = MANIFEST_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------
# 5. Portao da Fase 1
# --------------------------------------------------------------------------


def check_gate(
    rows: list[dict],
    min_rows: int = MIN_ROWS,
    expect_holdout: bool = False,
    min_holdout: int = MIN_HOLDOUT,
    max_holdout: int = HOLDOUT_TARGET,
) -> tuple[bool, list[str]]:
    """Portao da Fase 1 (`_docs/decisions.md#3`): o manifesto tem pelo menos
    `min_rows` linhas `profile` - um piso duro, nao "quantas o collect()
    produziu" -, e nenhuma transcricao `profile` tem menos de
    `MIN_WORD_RATIO` da contagem esperada de palavras para a duracao.
    Linhas sem coluna `role` (manifesto pre-holdout) contam como `profile`,
    entao manifestos antigos continuam validados exatamente como antes.

    Com `expect_holdout=True` (`_docs/decisions.md#6`/`#7`), tambem exige
    entre `min_holdout` e `max_holdout` linhas `holdout` - essas nao tem
    `contagem_palavras` pra medir e nao entram no piso de 60%.
    """
    problems = []
    profile_rows = [row for row in rows if row.get("role", ROLE_PROFILE) == ROLE_PROFILE]
    holdout_rows = [row for row in rows if row.get("role", ROLE_PROFILE) == ROLE_HOLDOUT]

    if len(profile_rows) < min_rows:
        problems.append(f"manifesto tem {len(profile_rows)} linhas, esperado pelo menos {min_rows}")

    if expect_holdout and not (min_holdout <= len(holdout_rows) <= max_holdout):
        problems.append(
            f"manifesto tem {len(holdout_rows)} linhas holdout, esperado entre "
            f"{min_holdout} e {max_holdout}"
        )

    for row in profile_rows:
        duration_s = float(row["duracao_s"])
        actual = int(row["contagem_palavras"])
        expected = expected_word_count(duration_s)
        ratio = actual / expected if expected else 1.0
        if ratio < MIN_WORD_RATIO:
            problems.append(
                f"{row['id']}: {actual} palavras, esperado ~{expected:.0f} "
                f"({ratio:.0%} - abaixo do minimo de {MIN_WORD_RATIO:.0%})"
            )

    return not problems, problems


# --------------------------------------------------------------------------
# 6. Pipeline
# --------------------------------------------------------------------------


def collect(
    channel_url: str = CHANNEL_URL,
    target: int = TARGET_COUNT,
    holdout_target: int = HOLDOUT_TARGET,
    min_holdout: int = MIN_HOLDOUT,
    holdout_seed: int = HOLDOUT_SEED,
    raw_dir: Path = RAW_DIR,
    manifest_path: Path = MANIFEST_PATH,
    sleep_seconds: float = SLEEP_SECONDS,
    now: datetime | None = None,
) -> list[dict]:
    """Roda o pipeline completo e escreve o manifesto parcial se um video
    estourar um erro esperado no meio do caminho.

    Reserva holdout (`select_holdout()`) antes de transcrever qualquer
    coisa: se o pool elegivel nao tiver `target + min_holdout` videos,
    `ChannelPoolTooSmall` sobe daqui sem criar `raw_dir` nem tentar coleta
    nenhuma - achado real sobre o canal (`DECISOES.md#4`), nao um stop
    parcial. Videos `holdout` nunca passam por `collect_transcript()` -
    entram no manifesto so com `id`/`titulo`/`duracao_s`.

    So `CouldNotRetrieveTranscript` (a base de `youtube_transcript_api`,
    cobre `IpBlocked`, `VideoUnavailable`, etc. - `TranscriptsDisabled`/
    `NoTranscriptFound` ja viram fallback dentro de
    `fetch_via_transcript_api` e nunca chegam aqui), `WhisperXUnavailable`
    (as duas falhas conhecidas do whisperX - dependencia ausente, audio
    nao baixado) e `subprocess.CalledProcessError` (o download de audio do
    whisperX roda com `check=True`) contam como "parar aqui e esperado" e
    interrompem o loop `profile` preservando o que ja foi coletado (as
    linhas `holdout` ja reservadas ainda entram no manifesto). Um
    `RuntimeError` generico (nao a subclasse `WhisperXUnavailable`) e
    qualquer outra excecao sao bugs reais e tem que subir - nao viram
    "coleta parcial" silenciosa.
    """
    videos = list_channel_videos(channel_url)
    selected = select_videos(videos, target=target, now=now)
    holdout = select_holdout(
        videos,
        selected,
        target=holdout_target,
        min_holdout=min_holdout,
        profile_target=target,
        now=now,
        seed=holdout_seed,
    )

    raw_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, video in enumerate(selected):
        if i > 0:
            time.sleep(sleep_seconds)

        try:
            fragments, source = collect_transcript(video["id"])
        except (
            CouldNotRetrieveTranscript,
            WhisperXUnavailable,
            subprocess.CalledProcessError,
        ) as exc:
            print(
                f"coleta interrompida em {video['id']} "
                f"({i + 1}/{len(selected)} tentados, {len(rows)} coletados): {exc}"
            )
            break

        write_raw(raw_dir, video, fragments, source)

        trechos = clean_transcript(fragments)
        write_clean(raw_dir, video["id"], trechos)

        rows.append(
            {
                "id": video["id"],
                "titulo": video["title"],
                "duracao_s": video["duration"],
                "contagem_palavras": word_count(trechos),
                "fonte": "whisperX" if source == "whisperx" else "legenda",
                "role": ROLE_PROFILE,
            }
        )

    rows.extend(
        {
            "id": video["id"],
            "titulo": video["title"],
            "duracao_s": video["duration"],
            "contagem_palavras": "",
            "fonte": "",
            "role": ROLE_HOLDOUT,
        }
        for video in holdout
    )

    write_manifesto(rows, manifest_path)
    return rows


def main() -> None:
    rows = collect()
    ok, problems = check_gate(rows, expect_holdout=True)
    print(f"manifesto: {len(rows)} linhas em {MANIFEST_PATH}")
    if ok:
        print("portao Fase 1: PASSOU")
    else:
        print("portao Fase 1: FALHOU")
        for problem in problems:
            print(f"  - {problem}")


if __name__ == "__main__":
    main()
