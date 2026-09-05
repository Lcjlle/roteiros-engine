"""Testes de `src/schema_loader.py` (Issue #16, `_docs/plano_
implementacao.md:436`, F3-b).

Os dois primeiros testes provam que os Enums gerados por `build_enums` sao
genuinamente derivados de `schema/ontologia.v1.json` a cada execucao, e nao
uma lista Python paralela que por acaso bate com o arquivo de hoje: o
primeiro le o arquivo real de forma independente (seu proprio
`json.loads`) e compara contra o resultado de `build_enums`; o segundo
modifica uma copia do arquivo em `tmp_path` e prova que o valor novo
aparece no Enum resultante.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from src.schema_loader import (
    ONTOLOGY_PATH,
    EvidenceTypeEnum,
    WindowAnnotation,
    build_enums,
    load_ontology,
)

# --------------------------------------------------------------------------
# Consistencia - arquivo real
# --------------------------------------------------------------------------


class TestBuildEnumsMatchesRealFile:
    def test_every_categorical_field_enum_matches_independent_json_read(self):
        ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
        enums = build_enums(load_ontology())

        categorical_fields = {
            field["name"]: set(field["values"])
            for field in ontology["fields"]
            if field["type"] == "categorical"
        }

        assert set(enums) == set(categorical_fields)
        for field_name, expected_values in categorical_fields.items():
            member_values = {member.value for member in enums[field_name]}
            assert member_values == expected_values

    def test_density_never_a_key(self):
        enums = build_enums(load_ontology())
        assert "density" not in enums


# --------------------------------------------------------------------------
# Consistencia - prova dinamica (regressao contra hardcode)
# --------------------------------------------------------------------------


class TestBuildEnumsIsGenuinelyDynamic:
    def test_new_value_appended_to_a_copy_shows_up_in_the_rebuilt_enum(self, tmp_path):
        ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
        for field in ontology["fields"]:
            if field["name"] == "loop":
                field["values"].append("bogus_value")
                break

        tmp_copy = tmp_path / "ontologia.v1.json"
        tmp_copy.write_text(json.dumps(ontology), encoding="utf-8")

        enums = build_enums(load_ontology(path=tmp_copy))

        assert "bogus_value" in {member.value for member in enums["loop"]}


# --------------------------------------------------------------------------
# WindowAnnotation - payloads validos/invalidos
# --------------------------------------------------------------------------


class TestWindowAnnotationValidation:
    def _valid_payload(self) -> dict:
        return {"function": "hook", "loop": "opens", "scale": "individual", "density": 1}

    def test_valid_payload_without_evidence_type(self):
        annotation = WindowAnnotation(**self._valid_payload())
        assert annotation.density == 1
        assert annotation.evidence_type is None

    def test_out_of_enum_function_rejected(self):
        payload = self._valid_payload()
        payload["function"] = "not_a_real_function"
        with pytest.raises(ValidationError):
            WindowAnnotation(**payload)

    def test_out_of_range_density_rejected(self):
        payload = self._valid_payload()
        payload["density"] = 3
        with pytest.raises(ValidationError):
            WindowAnnotation(**payload)

    def test_missing_required_scale_rejected(self):
        payload = self._valid_payload()
        del payload["scale"]
        with pytest.raises(ValidationError):
            WindowAnnotation(**payload)


class TestWindowAnnotationEvidenceTypeOptional:
    def test_without_evidence_type_validates(self):
        annotation = WindowAnnotation(function="evidence", loop="holds", scale="human", density=0)
        assert annotation.evidence_type is None

    def test_with_valid_evidence_type_validates(self):
        annotation = WindowAnnotation(
            function="evidence",
            loop="holds",
            scale="human",
            density=0,
            evidence_type="study",
        )
        assert annotation.evidence_type == EvidenceTypeEnum.STUDY
