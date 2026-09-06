"""Fase 4/5 - alpha de Krippendorff por campo, human x human (Fase 4,
Issue #22) e, sem reimplementacao, model x human (Fase 5, futura),
`_docs/decisions.md#28(d)/(e)` e `#29(d)/(h)`.

`nltk.metrics.agreement.AnnotationTask` (Apache-2.0) e o unico ponto de
entrada de calculo de concordancia deste projeto - o pacote `krippendorff`
(GPL-3.0, `pln-fing-udelar/fast-krippendorff`) foi explicitamente
rejeitado (`#28(d)`). `AnnotationTask` ja usa `binary_distance` (nominal)
por padrao para `function`, `loop`, `scale` e `evidence_type`; `density`
usa uma distancia ordinal propria (`density_ordinal_distance`), porque a
escala 0/1/2+ do codebook e um balde censurado, nao um intervalo igual
(`schema/codebook.md` linhas 642-686) - nem `abs(c-k)` nem `(c-k)**2`
capturam isso.

`evidence_type` (`required: false`, `condition: function == 'evidence'`,
`schema/ontologia.v1.json`) trata "nao aplicavel" como dado ausente,
nunca como categoria sentinela `n/a`: a tripla `(coder, window_id, valor)`
e simplesmente omitida sempre que `function != 'evidence'` naquela
rodada/janela (`#28(e)`), e seu alpha nunca entra no `passed` booleano do
portao `fase4-self-agreement-alpha` (`#29(h)`) - so `function`, `loop`,
`scale` e `density` (os quatro campos `required: true`) decidem isso.

`write_fase4_gate` consome o par de artefatos canonicos que
`src/gold.py::write_gold_artifact` produz (`{generated_at,
ontology_version, records: [...]}`) e o limiar configurado em
`schema/portoes.json` (gate `fase4-self-agreement-alpha`) - nunca
duplica o numero aqui. Compara no nivel de janela via `window_id`;
fundir janelas em blocos e Fase 5C, fora de escopo.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nltk.metrics.agreement import AnnotationTask, binary_distance
from nltk.probability import FreqDist

from src.schema_loader import load_ontology

REPO_ROOT = Path(__file__).resolve().parent.parent
PORTOES_PATH = REPO_ROOT / "schema/portoes.json"
FASE4_GATE_ID = "fase4-self-agreement-alpha"

# Os quatro campos `required: true` de `schema/ontologia.v1.json`: sozinhos
# decidem o `passed` do portao (`_docs/decisions.md#29(h)`).
REQUIRED_ALPHA_FIELDS: tuple[str, ...] = ("function", "loop", "scale", "density")
ALL_ALPHA_FIELDS: tuple[str, ...] = (*REQUIRED_ALPHA_FIELDS, "evidence_type")

# Escada de escalonamento de `_docs/plano_implementacao.md:504`, escrita
# para o portao da Fase 5B mas reaproveitada aqui, na mesma ordem, para
# `fase4-self-agreement-alpha` (`_docs/decisions.md#28(b)`, paragrafo
# "Escalation when fase4-self-agreement-alpha fails").
ESCALATION_LADDER: list[str] = [
    "reescreva a definicao e o tie-breaker do campo no codebook e reanote (ate duas tentativas)",
    "funda os dois valores que se confundem em um so",
    "remova o campo da ontologia",
]


class ValidaError(ValueError):
    """Erro nomeado de leitura/configuracao do portao de auto-concordancia -
    nunca um `except Exception` generico escondendo a causa real."""


# --------------------------------------------------------------------------
# 1. Distancia ordinal de Krippendorff para `density` (`_docs/decisions.md#28(d)`)
# --------------------------------------------------------------------------


def density_ordinal_distance(freq_dist: FreqDist | dict[int, int]) -> Callable[[int, int], float]:
    """Fecha sobre `freq_dist` (os marginais `n_g` das avaliacoes que
    pertencem exatamente as unidades elegiveis - unidades com >= 2
    avaliacoes validas - nunca os marginais brutos do dataset inteiro
    antes dessa filtragem) e devolve a distancia ordinal de Krippendorff:

        delta^2(c, k) = ( Sum_{g=c}^{k} n_g - (n_c + n_k) / 2 )^2      para c <= k

    `AnnotationTask` so passa dois rotulos por chamada (`distance(l, k)`),
    nunca a tabela de frequencias - por isso o fechamento precisa
    pre-computar `freq_dist` numa passada separada, antes de
    `AnnotationTask` ser construido (`#28(d)`). Nunca
    `abs(c - k)`/`(c - k) ** 2`: ambas sao distancias intervalares
    disfarcadas, que tratariam o balde-teto `density == 2` ("dois ou mais
    conceitos novos", `schema/codebook.md` linhas 642-686) como se
    estivesse a uma distancia numerica fixa de `1`, o que a definicao do
    codebook contradiz.
    """

    def distance(c: int, k: int) -> float:
        lo, hi = (c, k) if c <= k else (k, c)
        cumulative = sum(freq_dist.get(g, 0) for g in range(lo, hi + 1))
        boundary = (freq_dist.get(lo, 0) + freq_dist.get(hi, 0)) / 2
        return (cumulative - boundary) ** 2

    return distance


# --------------------------------------------------------------------------
# 2. Alpha por campo (`compute_field_alpha`, `_docs/decisions.md#29(d)`: uma
#    unica implementacao, reusada pela Fase 5 sem reimplementacao)
# --------------------------------------------------------------------------


def _field_applicable(record: dict[str, Any], field: str) -> bool:
    """`evidence_type` so participa quando `function == 'evidence'` naquele
    registro (`schema/ontologia.v1.json`'s `condition`, `#28(e)`). Os
    outros quatro campos sao `required: true` e sempre aplicaveis."""
    if field == "evidence_type":
        return record.get("function") == "evidence"
    return True


def compute_field_alpha(round1: dict[str, Any], round2: dict[str, Any], field: str) -> float | None:
    """Alpha de Krippendorff de `field` entre as duas rodadas (`round1`,
    `round2`), cada uma no contrato canonico
    `{generated_at, ontology_version, records: [...]}` que
    `src/gold.py::write_gold_artifact` produz.

    1. Forma triplas `(coder, window_id, valor)` validas para `field`, uma
       por rodada/janela, tratando `round1`/`round2` como os dois
       "coders".
    2. Aplica a aplicabilidade do campo (`_field_applicable`): para
       `evidence_type`, a tripla e omitida sempre que `function !=
       'evidence'` naquela rodada/janela - nunca uma categoria sentinela.
    3. Agrupa por unidade (`window_id`).
    4. Mantem somente as unidades com >= 2 avaliacoes validas
       (elegiveis).
    5. Constroi os marginais usados pela distancia ordinal (`density`)
       SOMENTE a partir dessas unidades elegiveis - critico, e a
       correcao que `#28(d)` registra explicitamente.
    6. Degenerescencia: zero unidades elegiveis -> `None`; >= 1 unidade
       elegivel mas os marginais elegiveis colapsam a menos de 2
       categorias distintas -> `None` (nunca deixa `AnnotationTask.alpha()`
       devolver `1` por um atalho de dado degenerado que na verdade
       significa "nao medivel", `#29(h)`). Agreement perfeito legitimo
       com >= 2 categorias presentes permanece `1.0`.
    7. Caso contrario, chama `AnnotationTask(data,
       distance=...).alpha()` normalmente: `binary_distance` (nominal,
       o default da biblioteca) para `function`/`loop`/`scale`/
       `evidence_type`; `density_ordinal_distance(marginais elegiveis)`
       para `density`.

    Sem minimo de duas unidades elegiveis: uma unica unidade elegivel com
    2 categorias distintas ja calcula normalmente.
    """
    ratings_by_window: dict[str, dict[str, Any]] = {}
    for coder, payload in (("round1", round1), ("round2", round2)):
        for record in payload["records"]:
            if not _field_applicable(record, field):
                continue
            ratings_by_window.setdefault(record["window_id"], {})[coder] = record[field]

    eligible_units = {
        window_id: ratings for window_id, ratings in ratings_by_window.items() if len(ratings) >= 2
    }
    if not eligible_units:
        return None

    eligible_freq = FreqDist(
        value for ratings in eligible_units.values() for value in ratings.values()
    )
    if len(eligible_freq.keys()) < 2:
        return None

    distance = density_ordinal_distance(eligible_freq) if field == "density" else binary_distance
    data = [
        (coder, window_id, value)
        for window_id, ratings in eligible_units.items()
        for coder, value in ratings.items()
    ]
    return AnnotationTask(data, distance=distance).alpha()


# --------------------------------------------------------------------------
# 3. Contagens de ocorrencia por campo/valor (`_docs/decisions.md#28(c)`:
#    alpha alto de `function` nao implica que `cta` foi exercitado)
# --------------------------------------------------------------------------


def _possible_field_values(ontology: dict[str, Any], field: str) -> list[Any]:
    spec = next(f for f in ontology["fields"] if f["name"] == field)
    if spec["type"] == "categorical":
        return list(spec["values"])
    return list(range(spec["min"], spec["max"] + 1))


def field_occurrence_counts(
    records: list[dict[str, Any]], field: str, ontology: dict[str, Any]
) -> dict[str, int]:
    """Conta quantas vezes cada valor possivel de `field` (lido de
    `ontology`, nunca duplicado aqui) ocorre em `records`, restrito as
    janelas onde `field` e aplicavel (para `evidence_type`, apenas onde
    `function == 'evidence'`). Todo valor possivel entra no dict, mesmo
    com contagem zero (ex.: `cta: 0`) - essa e a garantia que a Issue
    #12(a) precisa para nao inferir de um alpha alto que uma categoria
    rara foi de fato exercitada; esta funcao nao resolve aquela issue,
    so torna a lacuna visivel."""
    counts = {str(value): 0 for value in _possible_field_values(ontology, field)}
    for record in records:
        if not _field_applicable(record, field):
            continue
        counts[str(record[field])] += 1
    return counts


# --------------------------------------------------------------------------
# 4. Portao `fase4-self-agreement-alpha` (`_docs/decisions.md#28(b)`/`#29(h)`)
# --------------------------------------------------------------------------


def _load_round(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_threshold(gate_id: str = FASE4_GATE_ID, portoes_path: Path = PORTOES_PATH) -> float:
    """Le `threshold.value` do gate `gate_id` em `schema/portoes.json` -
    o numero nunca e duplicado hardcoded aqui nem nos testes."""
    portoes = json.loads(portoes_path.read_text(encoding="utf-8"))
    gate = next((g for g in portoes["gates"] if g["id"] == gate_id), None)
    if gate is None:
        raise ValidaError(f"gate {gate_id!r} nao encontrado em {portoes_path}")
    return gate["threshold"]["value"]


def write_fase4_gate(
    round1_path: Path, round2_path: Path, video_id: str, out_path: Path
) -> dict[str, Any]:
    """Le os dois artefatos canonicos (`round1_path`, `round2_path`,
    contrato da Issue #21) do video gold reanotado 48h depois, compara no
    nivel de janela (via `window_id`, nunca depois de fusao em blocos -
    Fase 5C, fora de escopo), calcula o alpha por campo
    (`compute_field_alpha`) e as contagens de ocorrencia por campo/valor
    (`field_occurrence_counts`, sobre os registros de `round1`), e
    persiste tudo em `out_path`.

    `passed` e `True` somente quando `function`, `loop`, `scale` e
    `density` tem alpha aplicavel (`!= None`) e `>= threshold` lido de
    `schema/portoes.json` (gate `fase4-self-agreement-alpha`);
    `evidence_type` e calculado e reportado, mas nunca entra nesse
    booleano (`_docs/decisions.md#29(h)`). Quando algum campo obrigatorio
    falha, o payload ganha `escalation.failing_fields` e
    `escalation.next_step` com a escada de tres passos de
    `_docs/plano_implementacao.md:504` (reaproveitada, nao reinventada,
    `_docs/decisions.md#28(b)`).
    """
    round1 = _load_round(round1_path)
    round2 = _load_round(round2_path)
    ontology = load_ontology()
    threshold = _gate_threshold()

    alphas = {field: compute_field_alpha(round1, round2, field) for field in ALL_ALPHA_FIELDS}

    failing_fields = [
        field
        for field in REQUIRED_ALPHA_FIELDS
        if alphas[field] is None or alphas[field] < threshold
    ]
    passed = not failing_fields

    payload: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "video_id": video_id,
        "ontology_version": ontology["version"],
        "threshold": threshold,
        "alpha": alphas,
        "occurrence_counts": {
            field: field_occurrence_counts(round1["records"], field, ontology)
            for field in ALL_ALPHA_FIELDS
        },
        "passed": passed,
    }
    if failing_fields:
        payload["escalation"] = {
            "failing_fields": failing_fields,
            "next_step": list(ESCALATION_LADDER),
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
