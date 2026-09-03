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
import re
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


def predict_boundary_proba(text: str):
    """Confianca do SaT (por caractere) de que ali e uma fronteira de
    sentenca - usada so como sinal secundario de desempate em
    `merge_incomplete_boundaries` (Issue #9/#8, `_docs/decisions.md#15`:
    sozinha essa confianca nao separa os 22 casos abertos dos 6 falsos
    positivos, faixas se sobrepoem). Mesmos argumentos padrao de
    `split_sentences` (`strip_whitespace`/`remove_whitespace_before_inference`
    default `False`), pra indexar pelo mesmo offset de caractere."""
    return _get_model().predict_proba(text)


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
# 4. Fusao de fronteiras sintaticamente abertas (Issue #9, root cause de
#    Issue #8/#4: a fronteira nasce dentro de `SaT.split()`, `_docs/decisions.md#15`)
# --------------------------------------------------------------------------
#
# Fase A desta issue (`tests/fixtures/fase2_sentence_boundary_regression.json`,
# 28 casos da Issue #8) mediu que nenhum sinal isolado discrimina os 22 casos
# `open` dos 6 `false_positive` - nem a pontuacao final sozinha (proibido:
# "termina em virgula => funde", regride os 6 falsos positivos), nem
# `predict_boundary_proba` sozinho (`_docs/decisions.md#15`). A combinacao
# abaixo (classe de pontuacao final, palavras fechadas que nao podem
# terminar uma oracao em ingles, presenca/ausencia de marcador de verbo
# finito, e a confianca do SaT so como sinal secundario de desempate)
# corrigiu 22/22 e preservou 6/6 na fixture - ver comentario de
# implementacao da Issue #9 pra tabela completa.

# Fronteira so e candidata a fusao se a sentenca nao termina em pontuacao
# terminal - mesma classe de pontuacao final que a varredura da Issue #8
# usou pra gerar os 28 candidatos originais.
_TERMINAL_PUNCT = (".", "!", "?")
_TRAILING_QUOTES = ("'", '"', ")", "\u201d", "\u2019")

_COORD_CONJUNCTIONS = {"and", "or", "but", "nor", "yet", "so"}
_SUBORD_CONJUNCTIONS = {
    "because",
    "although",
    "though",
    "while",
    "if",
    "when",
    "unless",
    "since",
    "whereas",
    "until",
    "before",
    "after",
    "once",
    "whether",
    "where",
    "as",
}
_PREPOSITIONS = {
    "of",
    "in",
    "on",
    "at",
    "to",
    "from",
    "with",
    "by",
    "about",
    "into",
    "onto",
    "upon",
    "under",
    "over",
    "between",
    "among",
    "through",
    "during",
    "without",
    "within",
    "along",
    "across",
    "behind",
    "beyond",
    "despite",
    "except",
    "near",
    "outside",
    "toward",
    "towards",
    "via",
    "per",
    "against",
    "around",
    "off",
    "for",
}
_ARTICLES = {"a", "an", "the"}
_RELATIVE_PRONOUNS = {"who", "whom", "whose", "which"}
_COPULAS = {"is", "are", "was", "were", "am", "be", "been", "being"}
_AUX_MODALS = {
    "has",
    "have",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "shall",
    "should",
    "can",
    "could",
    "may",
    "might",
    "must",
}
# palavras que nao podem terminar uma oracao em ingles (fechada: conjuncao
# coordenativa/subordinativa, preposicao, artigo, pronome relativo) mais os
# verbos copulativos/auxiliares que exigem complemento
_FORBIDDEN_FINAL_WORDS = (
    _COORD_CONJUNCTIONS
    | _SUBORD_CONJUNCTIONS
    | _PREPOSITIONS
    | _ARTICLES
    | _RELATIVE_PRONOUNS
    | _COPULAS
    | _AUX_MODALS
)
_FINITE_VERB_MARKERS = _COPULAS | _AUX_MODALS
_SUBJECT_PRONOUNS = {"it", "he", "she", "they", "we", "you", "i", "this", "that"}
_PERSONAL_PRONOUNS_SENTENCE_INITIAL = {
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "this",
    "that",
    "these",
    "those",
    "there",
}

# limiar de `predict_boundary_proba` usado so como desempate (nunca sinal
# unico): na fixture da Fase A, o unico caso `open` sem sinal estrutural
# (`lkLwp9o7Djk:s0233`, o proprio j0095 da Issue #4) mediu 0.2482; o menor
# `false_positive` sem sinal estrutural mediu 0.4025 - o limiar fica no meio
# dessa lacuna medida.
SAT_MERGE_CONFIDENCE_THRESHOLD = 0.35


def _words(text: str) -> list[str]:
    return text.strip().split()


def _last_content_word(text: str) -> str:
    tokens = re.findall(r"[A-Za-z\']+", text.strip().rstrip(","))
    return tokens[-1].lower() if tokens else ""


def _first_word(text: str) -> str:
    match = re.match(r"[A-Za-z\']+", text.strip())
    return match.group(0) if match else ""


def _has_contraction_verb(word: str) -> bool:
    return bool(re.search(r"(n't|'s|'re|'ve|'d|'ll)$", word.lower()))


def _contains_finite_verb_marker(text: str, start_word: int = 0) -> bool:
    for word in _words(text)[start_word:]:
        token = re.sub(r"[^A-Za-z\']", "", word).lower()
        if token in _FINITE_VERB_MARKERS or _has_contraction_verb(word):
            return True
    return False


def _has_pronoun_subject_verb(text: str) -> bool:
    """Primeira palavra e um pronome-sujeito e a segunda parece um verbo no
    presente (termina em -s) - indica que ja ha um predicado real (ex.:
    "This represents...", "It requires..."), nao uma lista sem verbo."""
    words = _words(text)
    if len(words) < 2:
        return False
    w1 = re.sub(r"[^A-Za-z\']", "", words[0]).lower()
    w2 = re.sub(r"[^A-Za-z\']", "", words[1]).lower()
    return w1 in _SUBJECT_PRONOUNS and len(w2) > 2 and w2.endswith("s") and not w2.endswith("ss")


def _ends_with_terminal_punctuation(text: str) -> bool:
    stripped = text.strip()
    while stripped and stripped[-1] in _TRAILING_QUOTES:
        stripped = stripped[:-1]
    return stripped.endswith(_TERMINAL_PUNCT)


def _is_bare_fragment(text: str) -> bool:
    words = _words(text)
    return len(words) <= 3 and "," not in text


def _ends_bare_copula_comma(text: str) -> bool:
    return bool(re.search(r"\b(is|are|was|were|am)\s*,", text.strip()))


def _starts_with_subordinator(text: str) -> bool:
    fw = _first_word(text).lower()
    if fw in ("but", "and", "so"):
        rest = text.strip().split(None, 1)
        if len(rest) < 2:
            return False
        nxt = re.match(r"[A-Za-z\']+", rest[1])
        return bool(nxt) and nxt.group(0).lower() in _SUBORD_CONJUNCTIONS
    return fw in _SUBORD_CONJUNCTIONS


def _starts_with_subject_then_relative(text: str) -> bool:
    """Sujeito (ate 4 palavras) seguido de pronome relativo sem que um
    verbo finito apareca antes - a oracao relativa nunca resolve o sujeito
    externo (ex.: "The person who hears..., who smells..., whose...")."""
    words = _words(text)
    for i in range(1, min(5, len(words))):
        token = re.sub(r"[^A-Za-z\']", "", words[i]).lower()
        if token in _RELATIVE_PRONOUNS:
            return True
        if token in _FINITE_VERB_MARKERS:
            return False
    return False


def _ends_noninitial_capitalized_word(text: str, next_text: str) -> bool:
    """Sem virgula, termina numa palavra maiuscula que nao e a primeira da
    sentenca (nome proprio/titulo cortado no meio - ex.: "the Sand" |
    "People of..."), e a proxima sentenca nao comeca com pronome pessoal."""
    if "," in text:
        return False
    words = _words(text)
    if len(words) < 2:
        return False
    last = re.sub(r"[^A-Za-z]", "", words[-1])
    if not last or not last[0].isupper():
        return False
    next_fw = _first_word(next_text).lower() if next_text else ""
    return next_fw not in _PERSONAL_PRONOUNS_SENTENCE_INITIAL


def _is_headless_list(text: str) -> bool:
    """Lista topicalizada separada por virgula (>=2 virgulas), sem nenhum
    marcador de verbo finito e sem sujeito-pronome+verbo - nunca ganha um
    verbo principal (ex.: "Wrestling competitions, foot races, tests of
    throwing accuracy,")."""
    if text.count(",") < 2:
        return False
    if _contains_finite_verb_marker(text):
        return False
    return not _has_pronoun_subject_verb(text)


def _is_headless_np_no_comma(text: str) -> bool:
    if "," in text:
        return False
    words = _words(text)
    if len(words) <= 3:
        return False  # fragmento curto, ja coberto por _is_bare_fragment
    if _contains_finite_verb_marker(text):
        return False
    return not _has_pronoun_subject_verb(text)


def _has_dangling_relative_clause(text: str) -> bool:
    """Ultimo pronome relativo do texto nunca ganha um marcador de verbo
    finito depois dele (ex.: "..., whose work compiling data across the
    Hadza, the Ash..., the Hiwi..." - "compiling" e gerundio, nao verbo
    finito)."""
    words = _words(text)
    last_rel = None
    for i, word in enumerate(words):
        token = re.sub(r"[^A-Za-z\']", "", word).lower()
        if token in _RELATIVE_PRONOUNS:
            last_rel = i
    if last_rel is None or last_rel == len(words) - 1:
        return False
    return not _contains_finite_verb_marker(text, start_word=last_rel + 1)


def _starts_with_dangling_participle(text: str) -> bool:
    """Abre com gerundio/particípio (-ing) sem nenhum verbo finito no
    resto do texto - oracao participial adjunta, sem oracao principal
    (ex.: "Looking back across this entire arc, ... nearly 8 centuries
    later,")."""
    if not _first_word(text).lower().endswith("ing"):
        return False
    return not _contains_finite_verb_marker(text)


def _next_starts_subjectless_predicate(next_text: str) -> bool:
    """Proxima sentenca abre com material so-adverbial seguido de copula
    sem sujeito proprio antes dela - o sujeito e a sentenca candidata (ex.:
    "150,000 years ... to them" + "Directly, without interruption, is the
    simple fact...")."""
    if not next_text:
        return False
    for part in (p.strip() for p in next_text.split(",")):
        part_words = part.split()
        if not part_words:
            continue
        fw = re.sub(r"[^A-Za-z\']", "", part_words[0]).lower()
        if fw in _COPULAS:
            return True
        if fw not in ("directly", "without", "interruption"):
            break
    return False


def _boundary_signal(text: str, next_text: str) -> str:
    """`"complete"` (ja termina em pontuacao terminal - nao e candidato),
    `"open"` (algum sinal estrutural fechado confirma fronteira aberta) ou
    `"undetermined"` (nenhum sinal decide - so a confianca do SaT, se
    disponivel, desempata; sem ela, o padrao seguro e nao fundir - nunca
    "termina em virgula => funde", proibido pela Issue #9)."""
    if _ends_with_terminal_punctuation(text):
        return "complete"

    if _is_bare_fragment(text):
        next_fw = _first_word(next_text).lower() if next_text else ""
        return "complete" if next_fw in _PERSONAL_PRONOUNS_SENTENCE_INITIAL else "open"

    if _last_content_word(text) in _FORBIDDEN_FINAL_WORDS:
        return "open"
    if _ends_bare_copula_comma(text):
        return "open"
    if _starts_with_subordinator(text):
        return "open"
    if _starts_with_subject_then_relative(text):
        return "open"
    if _ends_noninitial_capitalized_word(text, next_text):
        return "open"
    if _is_headless_list(text):
        return "open"
    if _has_dangling_relative_clause(text):
        return "open"
    if _starts_with_dangling_participle(text):
        return "open"
    if _is_headless_np_no_comma(text):
        return "open"
    if _next_starts_subjectless_predicate(next_text):
        return "open"

    return "undetermined"


def _merge_pair(first: dict, second: dict) -> dict:
    text_out = f"{first['text']} {second['text']}"
    return {
        "sent_id": first["sent_id"],
        "video_id": first["video_id"],
        "idx": first["idx"],
        "start_s": first["start_s"],
        "end_s": second["end_s"],
        "text": text_out,
        "n_words": len(text_out.split()),
    }


def merge_incomplete_boundaries(
    records: list[dict], confidences: list[float | None] | None = None
) -> list[dict]:
    """Passo deterministico apos `split_sentences()`/montagem dos
    `records`: funde uma sentenca com a proxima quando a fronteira entre
    elas e sintaticamente aberta (Issue #9, root cause de Issue #8/#4).
    Renumera `idx`/`sent_id` sequencialmente no resultado. Cascateia -
    depois de fundir `i` com `i+1`, o resultado combinado e reavaliado
    contra `i+2`.

    `confidences[i]` e `predict_boundary_proba` no fim de `records[i]`
    dentro do documento - usada so como desempate quando nenhum sinal
    estrutural decide (`_boundary_signal` -> `"undetermined"`); `None`
    (posicao ou lista inteira) significa "sem esse sinal", e o padrao
    permanece nao fundir."""
    if len(records) < 2:
        return list(records)

    merged: list[dict] = []
    current = records[0]
    i = 0
    while i < len(records) - 1:
        nxt = records[i + 1]
        signal = _boundary_signal(current["text"], nxt["text"])
        should_merge = signal == "open"
        if not should_merge and signal == "undetermined" and confidences is not None:
            conf = confidences[i]
            should_merge = conf is not None and conf < SAT_MERGE_CONFIDENCE_THRESHOLD
        if should_merge:
            current = _merge_pair(current, nxt)
        else:
            merged.append(current)
            current = nxt
        i += 1
    merged.append(current)

    for new_idx, record in enumerate(merged):
        record["idx"] = new_idx
        record["sent_id"] = f"{record['video_id']}:s{new_idx:04d}"

    return merged


# --------------------------------------------------------------------------
# 5. Registro de sentenca
# --------------------------------------------------------------------------


def sentence_records(video_id: str, raw_dir: Path = RAW_DIR) -> list[dict]:
    """chunks -> texto corrido -> `split_sentences` -> reatribuicao de
    timestamp por offset acumulado (nunca busca por texto) ->
    `merge_incomplete_boundaries` (fronteiras sintaticamente abertas,
    Issue #9). Levanta `AssertionError` se a saida do wtpsplit nao
    reconstituir o texto de entrada (invariante do offset) - cobre tambem
    o caso de `split_sentences` devolver `[]` pra um texto nao vazio."""
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
    end_chars: list[int] = []
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
        end_chars.append(end_char)
        idx += 1

    if len(records) > 1:
        confidences = _resolve_boundary_confidences(records, text, end_chars)
        records = merge_incomplete_boundaries(records, confidences)

    return records


def _resolve_boundary_confidences(
    records: list[dict], text: str, end_chars: list[int]
) -> list[float | None]:
    """Confianca do SaT em cada fronteira interna candidata a fusao - so
    chama `predict_boundary_proba` (o modelo real) se pelo menos uma
    fronteira for candidata (nao termina em pontuacao terminal) e nenhum
    sinal estrutural decidir sozinho; senao devolve tudo `None` sem tocar o
    modelo (mantem `sentence_records` rapido/mockavel quando a fusao nao
    entra em jogo, ex.: suite de testes)."""
    pending = [
        i
        for i in range(len(records) - 1)
        if _boundary_signal(records[i]["text"], records[i + 1]["text"]) == "undetermined"
    ]
    if not pending:
        return [None] * (len(records) - 1)

    probs = predict_boundary_proba(text)
    pending_set = set(pending)
    return [
        float(probs[end_chars[i] - 1]) if i in pending_set else None
        for i in range(len(records) - 1)
    ]


# --------------------------------------------------------------------------
# 6. Persistencia
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
# 7. Pipeline
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
