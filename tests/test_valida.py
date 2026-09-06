"""Testes de `src/valida.py` (alpha de Krippendorff por campo, Issue #22,
`_docs/decisions.md#28(d)/(e)` e `#29(d)/(h)`).

Nenhum teste aqui le `gold/mackexplains7/round{1,2}/*.worksheet.jsonl`
reais, nem gera `round1.gold.json`/`round2.gold.json`/`fase4_gate.json`
reais - so fixtures sinteticas em `tmp_path` ou dados Python inline
(`_docs/decisions.md#28(d)`'s proprio requisito de teste, e a Issue #22
que consome esta decisao)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest
from nltk.metrics.agreement import AnnotationTask, binary_distance
from nltk.probability import FreqDist

from src import valida
from src.schema_loader import load_ontology

APPROX = 1e-5


def _round(records: list[dict]) -> dict:
    return {"generated_at": "2026-01-01T00:00:00Z", "ontology_version": "v1", "records": records}


def _record(window_id: str, **fields) -> dict:
    base = {
        "window_id": window_id,
        "video_id": "V",
        "function": "hook",
        "loop": "none",
        "evidence_type": None,
        "scale": "individual",
        "density": 0,
    }
    base.update(fields)
    return base


# --------------------------------------------------------------------------
# `compute_field_alpha` - casos de degenerescencia (item 4 da issue, 7 casos
# separados, nunca um unico teste parametrizado opaco)
# --------------------------------------------------------------------------


class TestComputeFieldAlphaDegenerate:
    def test_zero_eligible_units_returns_none(self):
        round1 = _round([_record("w1", function="hook")])
        round2 = _round([])

        assert valida.compute_field_alpha(round1, round2, "function") is None

    def test_eligible_population_all_one_category_returns_none_never_one(self):
        round1 = _round(
            [_record("w1", loop="none"), _record("w2", loop="none"), _record("w3", loop="none")]
        )
        round2 = _round(
            [_record("w1", loop="none"), _record("w2", loop="none"), _record("w3", loop="none")]
        )

        result = valida.compute_field_alpha(round1, round2, "loop")

        assert result is None

    def test_evidence_type_applicable_answer_without_comparable_unit_returns_none(self):
        # round1 codifica function=evidence + evidence_type; round2 codifica
        # function=hook na mesma janela, entao evidence_type nao se aplica
        # ao lado de round2 - nenhuma unidade fica comparavel.
        round1 = _round([_record("w1", function="evidence", evidence_type="study")])
        round2 = _round([_record("w1", function="hook", evidence_type=None)])

        assert valida.compute_field_alpha(round1, round2, "evidence_type") is None

    def test_raw_dataset_has_ratings_but_no_unit_reaches_two_valid_returns_none(self):
        # Janelas de round1 e round2 nunca coincidem - cada uma tem so 1
        # avaliacao valida, nenhuma chega a elegibilidade (>= 2).
        round1 = _round([_record("w1", function="hook"), _record("w2", function="cta")])
        round2 = _round([_record("w3", function="hook"), _record("w4", function="cta")])

        assert valida.compute_field_alpha(round1, round2, "function") is None

    def test_single_eligible_unit_with_two_categories_computes_normally(self):
        round1 = _round([_record("w1", function="hook")])
        round2 = _round([_record("w1", function="cta")])

        result = valida.compute_field_alpha(round1, round2, "function")

        assert result is not None
        assert result == pytest.approx(0.0, abs=APPROX)

    def test_multiple_units_and_categories_computes_via_annotation_task_alpha(self):
        round1 = _round(
            [
                _record("w1", function="hook"),
                _record("w2", function="cta"),
                _record("w3", function="hook"),
                _record("w4", function="objection"),
            ]
        )
        round2 = _round(
            [
                _record("w1", function="hook"),
                _record("w2", function="cta"),
                _record("w3", function="cta"),
                _record("w4", function="objection"),
            ]
        )

        result = valida.compute_field_alpha(round1, round2, "function")

        assert result == pytest.approx(0.6666666666666667, abs=APPROX)

    def test_perfect_legitimate_agreement_with_two_categories_returns_exactly_one(self):
        round1 = _round([_record("w1", function="hook"), _record("w2", function="cta")])
        round2 = _round([_record("w1", function="hook"), _record("w2", function="cta")])

        result = valida.compute_field_alpha(round1, round2, "function")

        assert result == 1.0


class TestComputeFieldAlphaDensityOrdinal:
    def test_density_field_computes_via_ordinal_distance_not_nominal(self):
        round1 = _round(
            [
                _record("w1", density=0),
                _record("w2", density=1),
                _record("w3", density=2),
                _record("w4", density=0),
                _record("w5", density=2),
            ]
        )
        round2 = _round(
            [
                _record("w1", density=0),
                _record("w2", density=1),
                _record("w3", density=1),
                _record("w4", density=0),
                _record("w5", density=2),
            ]
        )

        ordinal_result = valida.compute_field_alpha(round1, round2, "density")
        # A mesma discordancia w3 (2 vs 1) medida como se `density` fosse
        # nominal (binary_distance) daria um alpha diferente do ordinal -
        # prova que o campo realmente usa a distancia ordinal, nao o
        # default nominal da biblioteca.
        eligible_data = [
            ("round1", "w1", 0),
            ("round2", "w1", 0),
            ("round1", "w2", 1),
            ("round2", "w2", 1),
            ("round1", "w3", 2),
            ("round2", "w3", 1),
            ("round1", "w4", 0),
            ("round2", "w4", 0),
            ("round1", "w5", 2),
            ("round2", "w5", 2),
        ]
        nominal_result = AnnotationTask(eligible_data, distance=binary_distance).alpha()

        assert ordinal_result != pytest.approx(nominal_result, abs=APPROX)
        assert ordinal_result == pytest.approx(0.889795918367347, abs=APPROX)


# --------------------------------------------------------------------------
# `density_ordinal_distance` + `AnnotationTask` - matriz de referencia de
# Klaus Krippendorff, "Computing Krippendorff's Alpha-Reliability"
# (Annenberg School for Communication, University of Pennsylvania,
# 2011.1.25; https://www.asc.upenn.edu/sites/default/files/2021-03/
# Computing%20Krippendorff's%20Alpha-Reliability.pdf), Secao C/D, 4
# coders x 12 unidades, valores 1-5, missing = "." - hardcoded diretamente
# do artigo (validado rodando `AnnotationTask.alpha()` e conferindo
# nominal ~= 0.743421 antes de commitar, `_docs/decisions.md#28(d)`),
# nunca copiado do pacote `krippendorff` (GPL-3.0) rejeitado por essa
# mesma decisao.
# --------------------------------------------------------------------------

KRIPPENDORFF_2011_MATRIX = {
    "A": [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
    "B": [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
    "C": [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None],
    "D": [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None],
}


def _krippendorff_2011_triples() -> list[tuple[str, str, int]]:
    return [
        (coder, f"u{i}", value)
        for coder, values in KRIPPENDORFF_2011_MATRIX.items()
        for i, value in enumerate(values)
        if value is not None
    ]


def _eligible(triples: list[tuple[str, str, int]]) -> tuple[list[tuple[str, str, int]], FreqDist]:
    """Mantem somente as unidades com >= 2 avaliacoes validas e constroi o
    marginal exatamente sobre essas ratings - a mesma regra de
    elegibilidade que `compute_field_alpha` aplica."""
    by_unit: dict[str, dict[str, int]] = defaultdict(dict)
    for coder, item, value in triples:
        by_unit[item][coder] = value
    eligible_units = {item: ratings for item, ratings in by_unit.items() if len(ratings) >= 2}
    eligible_triples = [
        (coder, item, value)
        for item, ratings in eligible_units.items()
        for coder, value in ratings.items()
    ]
    eligible_freq = FreqDist(
        value for ratings in eligible_units.values() for value in ratings.values()
    )
    return eligible_triples, eligible_freq


class TestKrippendorff2011Reference:
    def test_nominal_alpha_matches_published_value(self):
        triples, _ = _eligible(_krippendorff_2011_triples())

        alpha = AnnotationTask(triples, distance=binary_distance).alpha()

        assert alpha == pytest.approx(0.743421, abs=APPROX)

    def test_ordinal_alpha_via_density_ordinal_distance_matches_published_value(self):
        triples, freq = _eligible(_krippendorff_2011_triples())

        alpha = AnnotationTask(triples, distance=valida.density_ordinal_distance(freq)).alpha()

        assert alpha == pytest.approx(0.815388, abs=APPROX)

    def test_interval_alpha_matches_published_value(self):
        # Distancia intervalar simples (c-k)**2, usada so como segundo
        # cheque, independente, de que a fiacao AnnotationTask/alpha() em
        # si esta correta - isolando bugs do fechamento ordinal de bugs de
        # fiacao (`_docs/decisions.md#28(d)`).
        triples, _ = _eligible(_krippendorff_2011_triples())

        alpha = AnnotationTask(triples, distance=lambda a, b: (a - b) ** 2).alpha()

        assert alpha == pytest.approx(0.849107, abs=APPROX)


class TestEligibleMarginalsRequiredForOrdinalDistance:
    def test_raw_marginals_do_not_reproduce_the_published_ordinal_alpha(self):
        """Regressao: se a implementacao computasse a distancia ordinal
        com os marginais brutos (todas as avaliacoes validas, inclusive
        de unidades depois descartadas por < 2 avaliacoes - aqui, a
        unidade `u11`, avaliada so por `B`), o alpha ordinal resultante
        nao bateria com o valor publicado. So os marginais elegiveis
        reproduzem 0.815388 (`_docs/decisions.md#28(d)`, correcao)."""
        raw_triples = _krippendorff_2011_triples()
        raw_freq = FreqDist(value for _, _, value in raw_triples)
        eligible_triples, eligible_freq = _eligible(raw_triples)

        assert dict(raw_freq) != dict(eligible_freq)

        wrong_alpha = AnnotationTask(
            eligible_triples, distance=valida.density_ordinal_distance(raw_freq)
        ).alpha()
        correct_alpha = AnnotationTask(
            eligible_triples, distance=valida.density_ordinal_distance(eligible_freq)
        ).alpha()

        assert wrong_alpha != pytest.approx(0.815388, abs=APPROX)
        assert correct_alpha == pytest.approx(0.815388, abs=APPROX)


# --------------------------------------------------------------------------
# `write_fase4_gate`
# --------------------------------------------------------------------------


def _gate_records(loop_values: list[str]) -> list[dict]:
    specs = [
        ("w0", "hook", "individual", 0),
        ("w1", "cta", "human", 1),
        ("w2", "hook", "individual", 0),
        ("w3", "evidence", "planetary", 2),
        ("w4", "cta", "human", 1),
    ]
    return [
        {
            "window_id": window_id,
            "video_id": "V",
            "function": function,
            "loop": loop,
            "evidence_type": "study" if function == "evidence" else None,
            "scale": scale,
            "density": density,
        }
        for (window_id, function, scale, density), loop in zip(specs, loop_values, strict=True)
    ]


def _write_gold_round(path: Path, records: list[dict]) -> None:
    path.write_text(json.dumps(_round(records)), encoding="utf-8")


class TestWriteFase4Gate:
    def test_passes_when_all_four_required_fields_meet_threshold(self, tmp_path):
        records = _gate_records(["opens", "closes", "opens", "holds", "closes"])
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "fase4_gate.json"

        payload = valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        assert payload["passed"] is True
        assert "escalation" not in payload
        for field in valida.REQUIRED_ALPHA_FIELDS:
            assert payload["alpha"][field] == pytest.approx(1.0)
        assert json.loads(out_path.read_text(encoding="utf-8")) == payload

    def test_fails_with_escalation_ladder_when_a_required_field_is_degenerate(self, tmp_path):
        records = _gate_records(["none"] * 5)
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "fase4_gate.json"

        payload = valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        assert payload["passed"] is False
        assert payload["alpha"]["loop"] is None
        assert payload["escalation"]["failing_fields"] == ["loop"]
        assert payload["escalation"]["next_step"] == valida.ESCALATION_LADDER

    def test_evidence_type_never_enters_passed_even_when_its_own_alpha_is_none(self, tmp_path):
        records = _gate_records(["opens", "closes", "opens", "holds", "closes"])
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "fase4_gate.json"

        payload = valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        # so a janela w3 tem function == evidence nas duas rodadas, e as
        # duas codificam "study" - 1 unidade elegivel, 1 categoria: None.
        assert payload["alpha"]["evidence_type"] is None
        assert payload["passed"] is True

    def test_threshold_is_read_from_portoes_json_not_hardcoded(self, tmp_path):
        real_gates = json.loads(Path("schema/portoes.json").read_text(encoding="utf-8"))["gates"]
        expected_threshold = next(g for g in real_gates if g["id"] == "fase4-self-agreement-alpha")[
            "threshold"
        ]["value"]

        records = _gate_records(["opens", "closes", "opens", "holds", "closes"])
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "fase4_gate.json"

        payload = valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        assert payload["threshold"] == expected_threshold

    def test_occurrence_counts_include_zero_count_categories(self, tmp_path):
        records = _gate_records(["opens", "closes", "opens", "holds", "closes"])
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "fase4_gate.json"

        payload = valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        # "promise" nunca ocorre nos registros sinteticos, mas continua
        # presente com contagem zero - alpha alto de `function` nao pode
        # esconder que uma categoria nunca foi exercitada (Issue #12(a),
        # `_docs/decisions.md#28(c)`).
        assert payload["occurrence_counts"]["function"]["promise"] == 0
        assert payload["occurrence_counts"]["function"]["hook"] == 2
        assert payload["occurrence_counts"]["function"]["cta"] == 2

    def test_ontology_version_read_from_schema_never_hardcoded(self, tmp_path):
        records = _gate_records(["opens", "closes", "opens", "holds", "closes"])
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "fase4_gate.json"

        payload = valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        assert payload["ontology_version"] == load_ontology()["version"]

    def test_creates_parent_directories(self, tmp_path):
        records = _gate_records(["opens", "closes", "opens", "holds", "closes"])
        round1_path, round2_path = tmp_path / "round1.gold.json", tmp_path / "round2.gold.json"
        _write_gold_round(round1_path, records)
        _write_gold_round(round2_path, records)
        out_path = tmp_path / "nested" / "dir" / "fase4_gate.json"

        valida.write_fase4_gate(round1_path, round2_path, "V", out_path)

        assert out_path.exists()
