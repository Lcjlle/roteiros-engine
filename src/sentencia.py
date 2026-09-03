"""Fase 2 - Sentenciacao: texto corrido de `corpus/<canal>/raw/*.json` vira
sentencas com timestamp proprio, prontas pra agrupar em janelas
(`src/janelas.py`).

Pipeline: le cada fragmento bruto (nao o `.limpo.json` ja fundido - a
reatribuicao de timestamp precisa do `end_s` individual de cada fragmento),
descarta fragmento so-marcacao via `strip_markers()` (`src/coleta.py`),
junta o resto em texto corrido com offset de caractere por fragmento, roda
`wtpsplit.SaT("sat-3l-sm")` sobre esse texto (`_docs/decisions.md#10`), e
reatribui `start_s`/`end_s` de cada sentenca pelo offset acumulado - nunca
por busca de texto, que falha em silencio quando uma frase se repete no
video (`_docs/plano_implementacao.md`, Fase 2, passo 2).

Roda so contra `corpus/mackexplains7` (`_docs/decisions.md#10d`): e o canal
que destrava a Fase 3. So linhas `role == "profile"` do manifesto sao
processadas - `holdout` fica intocado, mesma regra da Fase 1.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.coleta import ROLE_PROFILE, read_manifesto, strip_markers

CORPUS_DIR = Path("corpus/mackexplains7")
RAW_DIR = CORPUS_DIR / "raw"
SENTENCES_DIR = CORPUS_DIR / "sentences"

SAT_MODEL_NAME = "sat-3l-sm"


# --------------------------------------------------------------------------
# 1. Chunks: fragmentos brutos, sem fusao
# --------------------------------------------------------------------------


def load_chunks(video_id: str, raw_dir: Path = RAW_DIR) -> tuple[list[dict], float]:
    """Le `corpus/<canal>/raw/<video_id>.json` (fragments brutos, nao os
    trechos ja fundidos de `.limpo.json`). Descarta fragmentos so-marcacao
    apos `strip_markers()`; devolve `(chunks, duration_s)` - cada chunk e
    `{"start_s", "end_s", "text"}`, sem fusao, porque o proximo passo
    precisa do `end_s` individual de cada um pra reatribuir timestamp de
    sentenca.
    """
    data = json.loads((raw_dir / f"{video_id}.json").read_text(encoding="utf-8"))

    chunks: list[dict] = []
    for frag in data.get("fragments", []):
        text = strip_markers(frag["text"])
        if not text:
            continue
        start = float(frag["start"])
        end = start + float(frag.get("duration", 0.0))
        chunks.append({"start_s": start, "end_s": end, "text": text})

    duration_s = float(data.get("metadata", {}).get("duration") or 0.0)
    return chunks, duration_s


def _join_chunks(chunks: list[dict]) -> tuple[str, list[tuple[int, int]]]:
    """Junta chunks com um espaco simples; devolve o texto corrido e, por
    chunk, seu span `[inicio, fim)` de caractere nesse texto."""
    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    offset = 0
    for i, chunk in enumerate(chunks):
        if i > 0:
            parts.append(" ")
            offset += 1
        text = chunk["text"]
        spans.append((offset, offset + len(text)))
        parts.append(text)
        offset += len(text)
    return "".join(parts), spans


# --------------------------------------------------------------------------
# 2. Sentenciacao: wtpsplit SaT
# --------------------------------------------------------------------------

_model = None


def _get_model():
    global _model
    if _model is None:
        from wtpsplit import SaT

        _model = SaT(SAT_MODEL_NAME)
    return _model


def split_sentences(text: str) -> list[str]:
    """Sentencas via wtpsplit SaT, ingles. `strip_whitespace=False` (default
    da lib) e exigido: e o que garante `"".join(sentencas) == texto`, usado
    pra mapear offset de sentenca de volta pro chunk de origem sem busca
    por texto."""
    return _get_model().split(text, strip_whitespace=False)


# --------------------------------------------------------------------------
# 3. Reatribuicao de timestamp por offset
# --------------------------------------------------------------------------


def _sentence_char_span(sentence: str, base_offset: int) -> tuple[int, int] | None:
    """Offset absoluto do primeiro e ultimo caractere nao-whitespace da
    sentenca dentro do texto corrido. `None` se a sentenca for so espaco."""
    stripped = sentence.strip()
    if not stripped:
        return None
    start = base_offset + (len(sentence) - len(sentence.lstrip()))
    end = start + len(stripped)
    return start, end


def _chunk_at(offset: int, chunk_spans: list[tuple[int, int]]) -> int:
    """Indice do chunk cujo span contem `offset`; usa o ultimo chunk se
    `offset` cair exatamente no limite final."""
    for i, (start, end) in enumerate(chunk_spans):
        if start <= offset < end:
            return i
    return len(chunk_spans) - 1


# --------------------------------------------------------------------------
# 4. Registro de sentenca
# --------------------------------------------------------------------------


def sentence_records(video_id: str, raw_dir: Path = RAW_DIR) -> list[dict]:
    """chunks -> texto corrido -> `split_sentences` -> reatribuicao de
    timestamp por offset acumulado (nunca busca por texto). Levanta
    `AssertionError` se a saida do wtpsplit nao reconstituir o texto de
    entrada (invariante do offset) - cobre tambem o caso de `split_sentences`
    devolver `[]` pra um texto nao vazio."""
    chunks, _duration_s = load_chunks(video_id, raw_dir=raw_dir)
    if not chunks:
        return []

    text, spans = _join_chunks(chunks)
    sentences = split_sentences(text)

    reconstructed = "".join(sentences)
    if reconstructed != text:
        raise AssertionError(
            f"{video_id}: concatenacao de {len(sentences)} sentencas do wtpsplit "
            f"({len(reconstructed)} caracteres) nao reconstitui o texto de entrada "
            f"({len(text)} caracteres)"
        )

    records: list[dict] = []
    idx = 0
    offset = 0
    for sentence in sentences:
        span = _sentence_char_span(sentence, offset)
        offset += len(sentence)
        if span is None:
            continue
        start_char, end_char = span
        start_s = chunks[_chunk_at(start_char, spans)]["start_s"]
        end_s = chunks[_chunk_at(end_char - 1, spans)]["end_s"]
        text_out = sentence.strip()
        records.append(
            {
                "sent_id": f"{video_id}:s{idx:04d}",
                "video_id": video_id,
                "idx": idx,
                "start_s": start_s,
                "end_s": end_s,
                "text": text_out,
                "n_words": len(text_out.split()),
            }
        )
        idx += 1

    return records


# --------------------------------------------------------------------------
# 5. Persistencia
# --------------------------------------------------------------------------


def write_sentences(
    video_id: str,
    records: list[dict],
    duration_s: float,
    sentences_dir: Path = SENTENCES_DIR,
) -> Path:
    """Escreve `corpus/<canal>/sentences/<video_id>.json`:
    `{"video_id", "duration_s", "generated_at", "sentences"}`. `duration_s`
    persiste aqui porque `src/janelas.py` precisa dele pra `pos_pct` e nao
    deve reabrir `raw/<video_id>.json`."""
    sentences_dir.mkdir(parents=True, exist_ok=True)
    path = sentences_dir / f"{video_id}.json"
    payload = {
        "video_id": video_id,
        "duration_s": duration_s,
        "generated_at": datetime.now(UTC).isoformat(),
        "sentences": records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# 6. Pipeline
# --------------------------------------------------------------------------


def run(
    manifest_path: Path = CORPUS_DIR / "manifesto.csv",
    raw_dir: Path = RAW_DIR,
    sentences_dir: Path = SENTENCES_DIR,
) -> list[str]:
    """Roda `sentence_records` + `write_sentences` pra cada linha
    `role == "profile"` do manifesto (holdout fica intocado - regra da
    Fase 1). Devolve os `video_id` processados."""
    rows = read_manifesto(manifest_path)
    video_ids = [row["id"] for row in rows if row.get("role", ROLE_PROFILE) == ROLE_PROFILE]

    processed = []
    for video_id in video_ids:
        _chunks, duration_s = load_chunks(video_id, raw_dir=raw_dir)
        records = sentence_records(video_id, raw_dir=raw_dir)
        write_sentences(video_id, records, duration_s, sentences_dir=sentences_dir)
        processed.append(video_id)

    return processed


def main() -> None:
    ids = run()
    print(f"{len(ids)} videos sentenciados em {SENTENCES_DIR}")


if __name__ == "__main__":
    main()
