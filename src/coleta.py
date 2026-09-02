"""Fase 1 - Coleta: 30 transcricoes limpas do canal de referencia (@Zenn0009).

Pipeline: lista os videos do canal com `yt-dlp --flat-playlist --dump-json`,
seleciona 30 pelo desempenho relativo (nao os mais recentes), baixa legenda
(`youtube-transcript-api`, com `yt-dlp` como fallback de enumeracao e
`whisperX` como ultimo recurso quando nao ha legenda nenhuma), aplica limpeza
minima e escreve `corpus/<canal>/raw/*.json` + `corpus/<canal>/manifesto.csv`.
Ver `_docs/plano_implementacao.md`, Fase 1, para o desenho e o portao.

O cru (o que a fonte devolveu) nunca e sobrescrito: a limpeza sempre gera um
arquivo `.limpo.json` novo ao lado do `.json` cru.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

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
# Heuristica de fala para o portao de contagem de palavras (Armadilhas,
# Fase 1): legenda automatica em ingles fala tipicamente ~140 palavras/min.
WORDS_PER_MINUTE = 140
MIN_WORD_RATIO = 0.6

MANIFEST_FIELDS = ["id", "titulo", "duracao_s", "contagem_palavras", "fonte"]

_MARKER_RE = re.compile(r"\[(m[uú]sica|music|aplausos|applause)\]", re.IGNORECASE)


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
    now = now or datetime.now(UTC)
    long_form = [v for v in videos if v["duration"] >= min_duration_s]

    def age_days(video: dict) -> int:
        published_at = video.get("published_at")
        if published_at is None:
            return 0  # data desconhecida: trata como recem-publicado
        return (now - published_at).days

    mature = [v for v in long_form if age_days(v) >= min_age_days]
    pool = mature if len(mature) >= target else long_form

    ranked = sorted(pool, key=lambda v: v["view_count"], reverse=True)
    return ranked[:target]


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


def fetch_via_whisperx(
    video_id: str, device: str = "cpu", compute_type: str = "int8"
) -> list[dict]:
    """Ultimo recurso: transcreve o audio com whisperX. So roda quando nem
    `youtube-transcript-api` nem `yt-dlp` acharam legenda nenhuma - a etapa
    cara que a issue #1 pede para evitar por padrao.
    """
    try:
        import whisperx
    except ImportError as exc:
        raise RuntimeError(
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
            raise RuntimeError(f"whisperX: audio nao baixado para {video_id}")

        model = whisperx.load_model("large-v2", device, compute_type=compute_type)
        audio = whisperx.load_audio(str(matches[0]))
        result = model.transcribe(audio, batch_size=16)
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
        text = _MARKER_RE.sub("", frag["text"])
        text = " ".join(text.split())
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
            writer.writerow({field: row[field] for field in MANIFEST_FIELDS})


def read_manifesto(path: Path = MANIFEST_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------
# 5. Portao da Fase 1
# --------------------------------------------------------------------------


def check_gate(rows: list[dict], target: int = TARGET_COUNT) -> tuple[bool, list[str]]:
    """Portao da Fase 1 (`_docs/plano_implementacao.md`): o manifesto tem
    exatamente `target` linhas, e nenhuma transcricao tem menos de
    `MIN_WORD_RATIO` da contagem esperada de palavras para a duracao.
    """
    problems = []
    if len(rows) != target:
        problems.append(f"manifesto tem {len(rows)} linhas, esperado {target}")

    for row in rows:
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
    raw_dir: Path = RAW_DIR,
    manifest_path: Path = MANIFEST_PATH,
    sleep_seconds: float = SLEEP_SECONDS,
    now: datetime | None = None,
) -> list[dict]:
    raw_dir.mkdir(parents=True, exist_ok=True)

    videos = list_channel_videos(channel_url)
    selected = select_videos(videos, target=target, now=now)

    rows = []
    for i, video in enumerate(selected):
        if i > 0:
            time.sleep(sleep_seconds)

        fragments, source = collect_transcript(video["id"])
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
            }
        )

    write_manifesto(rows, manifest_path)
    return rows


def main() -> None:
    rows = collect()
    ok, problems = check_gate(rows)
    print(f"manifesto: {len(rows)} linhas em {MANIFEST_PATH}")
    if ok:
        print("portao Fase 1: PASSOU")
    else:
        print("portao Fase 1: FALHOU")
        for problem in problems:
            print(f"  - {problem}")


if __name__ == "__main__":
    main()
