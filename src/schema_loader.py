"""Gera Enums e o modelo Pydantic de anotacao de janela a partir de
`schema/ontologia.v1.json` (Issue #16, `_docs/plano_implementacao.md:436`,
F3-b - a camada mecanica que a Issue #11 deixou para depois do portao de
cobertura humana da Fase 3, `_docs/decisions.md#16c`).

`schema/ontologia.v1.json` e o unico dado de entrada: nenhuma lista de
valores categoricos e duplicada aqui. `build_enums` itera
`ontology["fields"]` e cria um `enum.Enum` por campo `"type": "categorical"`
- os 4 Enums do arquivo atual (`function`, `loop`, `evidence_type`, `scale`)
e o modelo `WindowAnnotation` sao apenas o resultado de aplicar essa funcao
ao arquivo real, no momento do import. Uma mudanca futura no JSON (novo
valor, campo renomeado) se reflete aqui sem editar este modulo - e o teste
de consistencia em `tests/test_schema_loader.py` prova isso lendo o mesmo
JSON de forma independente.

Fora de escopo (Issue #16): montar o prompt de anotacao da Fase 5 a partir
de `schema/codebook.md`, e validar a regra de negocio da chave `"condition"`
(`evidence_type` so faz sentido quando `function == "evidence"`) - ambos
adiados para quem precisar deles.
"""

from __future__ import annotations

import enum
import json
from pathlib import Path

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = REPO_ROOT / "schema/ontologia.v1.json"


def load_ontology(path: Path = ONTOLOGY_PATH) -> dict:
    """Le e faz parse do JSON em `path`, sem qualquer transformacao."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _enum_class_name(field_name: str) -> str:
    return "".join(part.capitalize() for part in field_name.split("_")) + "Enum"


def build_enums(ontology: dict) -> dict[str, type[enum.Enum]]:
    """Um `enum.Enum` por campo `"type": "categorical"` de `ontology["fields"]`,
    chaveado pelo `"name"` do campo. `density` (`"type": "integer"`) nunca
    aparece no dict retornado.
    """
    enums: dict[str, type[enum.Enum]] = {}
    for field in ontology["fields"]:
        if field["type"] != "categorical":
            continue
        members = {value.upper(): value for value in field["values"]}
        enums[field["name"]] = enum.Enum(_enum_class_name(field["name"]), members)
    return enums


def _field_by_name(ontology: dict, name: str) -> dict:
    return next(field for field in ontology["fields"] if field["name"] == name)


_ONTOLOGY = load_ontology()
_ENUMS = build_enums(_ONTOLOGY)

FunctionEnum = _ENUMS["function"]
LoopEnum = _ENUMS["loop"]
EvidenceTypeEnum = _ENUMS["evidence_type"]
ScaleEnum = _ENUMS["scale"]

_DENSITY_FIELD = _field_by_name(_ONTOLOGY, "density")


class WindowAnnotation(BaseModel):
    """Anotacao de uma janela, um campo por entrada de `ontology["fields"]`."""

    function: FunctionEnum
    loop: LoopEnum
    scale: ScaleEnum
    density: int = Field(ge=_DENSITY_FIELD["min"], le=_DENSITY_FIELD["max"])
    evidence_type: EvidenceTypeEnum | None = None
