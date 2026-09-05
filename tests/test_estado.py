"""Testes de `src/estado.py` (Issue #14, `_docs/decisions.md#22`):

- `schema/portoes.json` nao diverge dos `fase*_gate.json`/`manifesto.csv`
  reais, das constantes de `src/*.py`, nem tem `decision_ref` pendurado.
- `_docs/estado.md` e o indice de `_docs/decisions.md` batem exatamente com
  o que `--write` regeneraria - a mesma postura do `TEST_COUNTS`/`alembic
  check` da CI, aqui como teste de suite em vez de passo de workflow.
"""

from __future__ import annotations

import json

from src import estado

# --------------------------------------------------------------------------
# check_formula_params
# --------------------------------------------------------------------------


class TestCheckFormulaParams:
    def test_real_portoes_json_has_no_formula_divergence(self):
        portoes = estado.load_portoes()
        assert estado.check_formula_params(portoes["gates"]) == []

    def test_detects_param_diverging_from_src_constant(self):
        gates = [
            {
                "id": "fake-gate",
                "threshold": {
                    "kind": "formula",
                    "params": {"GATE_WINDOWS_PER_MINUTE": 999.0},
                    "expression": "n/a",
                    "unit": "n/a",
                },
            }
        ]
        problems = estado.check_formula_params(gates)
        assert len(problems) == 1
        assert "fake-gate" in problems[0]
        assert "999.0" in problems[0]

    def test_undefined_param_is_flagged_not_silently_skipped(self):
        gates = [
            {
                "id": "fake-gate",
                "threshold": {
                    "kind": "formula",
                    "params": {"NOT_A_REAL_CONSTANT": 1},
                    "expression": "n/a",
                    "unit": "n/a",
                },
            }
        ]
        problems = estado.check_formula_params(gates)
        assert len(problems) == 1
        assert "NOT_A_REAL_CONSTANT" in problems[0]

    def test_non_formula_gates_are_ignored(self):
        gates = [{"id": "g", "threshold": {"kind": "bound", "op": ">=", "value": 1, "unit": "x"}}]
        assert estado.check_formula_params(gates) == []


# --------------------------------------------------------------------------
# check_decision_refs
# --------------------------------------------------------------------------


class TestCheckDecisionRefs:
    def test_real_portoes_json_has_no_dangling_or_superseded_ref(self):
        portoes = estado.load_portoes()
        assert estado.check_decision_refs(portoes["gates"]) == []

    def test_rejects_ref_to_nonexistent_decision(self):
        gates = [{"id": "g", "decision_ref": ["_docs/decisions.md#9999"]}]
        problems = estado.check_decision_refs(gates)
        assert len(problems) == 1
        assert "nao existe" in problems[0]

    def test_rejects_ref_past_plano_eof(self):
        gates = [{"id": "g", "decision_ref": ["_docs/plano_implementacao.md:999999"]}]
        problems = estado.check_decision_refs(gates)
        assert len(problems) == 1
        assert "999999" in problems[0]

    def test_rejects_unqualified_superseded_target(self):
        # #12 -> Status: superseded por #14 (sem qualificacao) no indice real.
        gates = [{"id": "g", "decision_ref": ["_docs/decisions.md#12"]}]
        problems = estado.check_decision_refs(gates)
        assert len(problems) == 1
        assert "superseded" in problems[0]

    def test_accepts_partially_superseded_target(self):
        # #19 -> "parcialmente superseded por #20 (...)" - #24's accepted gap:
        # passa mecanicamente mesmo citando um fragmento morto do #19.
        gates = [{"id": "g", "decision_ref": ["_docs/decisions.md#19"]}]
        assert estado.check_decision_refs(gates) == []

    def test_accepts_vigente_target(self):
        gates = [{"id": "g", "decision_ref": ["_docs/decisions.md#14"]}]
        assert estado.check_decision_refs(gates) == []

    def test_letter_suffix_resolves_to_the_entry(self):
        gates = [{"id": "g", "decision_ref": ["_docs/decisions.md#16c"]}]
        assert estado.check_decision_refs(gates) == []

    def test_unrecognized_format_is_flagged(self):
        gates = [{"id": "g", "decision_ref": ["DECISOES.md#4"]}]
        problems = estado.check_decision_refs(gates)
        assert len(problems) == 1
        assert "nao bate com nenhum formato" in problems[0]


# --------------------------------------------------------------------------
# render_threshold
# --------------------------------------------------------------------------


class TestRenderThreshold:
    def test_bound_with_denominator(self):
        text = estado.render_threshold(
            {"kind": "bound", "op": "<=", "value": 5, "denominator": 50, "unit": "windows"}
        )
        assert text == "<= 5/50 windows"

    def test_bound_without_denominator(self):
        text = estado.render_threshold({"kind": "bound", "op": ">=", "value": 30, "unit": "rows"})
        assert text == ">= 30 rows"

    def test_qualitative_returns_statement_verbatim(self):
        text = estado.render_threshold({"kind": "qualitative", "statement": "the owner decides"})
        assert text == "the owner decides"

    def test_formula_includes_params(self):
        text = estado.render_threshold(
            {"kind": "formula", "expression": "f(x)", "params": {"A": 1, "B": 2}, "unit": "u"}
        )
        assert text == "f(x) [A=1, B=2]"


# --------------------------------------------------------------------------
# measure_gate - manifesto.csv (Fase 1)
# --------------------------------------------------------------------------


def _write_manifesto(path, rows):
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["id", "titulo", "duracao_s", "contagem_palavras", "fonte", "role"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestMeasureManifestoGate:
    def test_profile_row_floor_pass_and_fail(self, tmp_path, monkeypatch):
        monkeypatch.setattr(estado, "REPO_ROOT", tmp_path)
        rows = [
            {
                "id": f"v{i}",
                "titulo": "t",
                "duracao_s": "600",
                "contagem_palavras": "1500",
                "fonte": "legenda",
                "role": "profile",
            }
            for i in range(30)
        ]
        _write_manifesto(tmp_path / "corpus/chan/manifesto.csv", rows)
        gate = {
            "id": "fase1-profile-row-floor",
            "artifact": "corpus/{channel}/manifesto.csv",
            "evaluation": "automatic",
            "threshold": {"kind": "bound", "op": ">=", "value": 30, "unit": "rows"},
        }
        m = estado.measure_gate(gate, "chan")
        assert m.exists and m.passed is True

        _write_manifesto(tmp_path / "corpus/short/manifesto.csv", rows[:10])
        m2 = estado.measure_gate(gate, "short")
        assert m2.exists and m2.passed is False

    def test_missing_manifesto_is_declared_not_measured(self, tmp_path, monkeypatch):
        monkeypatch.setattr(estado, "REPO_ROOT", tmp_path)
        gate = {
            "id": "fase1-holdout-row-floor",
            "artifact": "corpus/{channel}/manifesto.csv",
            "evaluation": "automatic",
            "threshold": {"kind": "bound", "op": ">=", "value": 4, "unit": "rows"},
        }
        m = estado.measure_gate(gate, "ghost")
        assert m.exists is False
        assert m.passed is None
        assert m.display == "declarado, nao medido"

    def test_word_count_floor_uses_the_worst_profile_row(self, tmp_path, monkeypatch):
        monkeypatch.setattr(estado, "REPO_ROOT", tmp_path)
        rows = [
            {
                "id": "good",
                "titulo": "t",
                "duracao_s": "600",
                "contagem_palavras": "1500",
                "fonte": "legenda",
                "role": "profile",
            },
            {
                "id": "bad",
                "titulo": "t",
                "duracao_s": "600",
                "contagem_palavras": "10",
                "fonte": "legenda",
                "role": "profile",
            },
            {
                "id": "holdout-untouched",
                "titulo": "t",
                "duracao_s": "600",
                "contagem_palavras": "0",
                "fonte": "",
                "role": "holdout",
            },
        ]
        _write_manifesto(tmp_path / "corpus/chan/manifesto.csv", rows)
        gate = {
            "id": "fase1-word-count-floor",
            "artifact": "corpus/{channel}/manifesto.csv",
            "evaluation": "automatic",
            "threshold": {"kind": "bound", "op": ">=", "value": 0.6, "unit": "ratio"},
        }
        m = estado.measure_gate(gate, "chan")
        assert m.exists and m.passed is False
        assert "pior razao: 0.7%" == m.display


# --------------------------------------------------------------------------
# measure_gate - fase*_gate.json (artifact_pointer)
# --------------------------------------------------------------------------


class TestMeasureJsonPointerGate:
    def test_reads_named_sub_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr(estado, "REPO_ROOT", tmp_path)
        artifact = tmp_path / "corpus/chan/fase2_gate.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_text(
            json.dumps({"3a": {"n_janelas_grandes": 3, "n_sentencas_grandes": 3, "passed": True}})
        )
        gate = {
            "id": "fase2-oversized-window-parity",
            "artifact": "corpus/{channel}/fase2_gate.json",
            "artifact_pointer": "3a",
            "evaluation": "automatic",
        }
        m = estado.measure_gate(gate, "chan")
        assert m.exists and m.passed is True

    def test_missing_artifact_is_declared_not_measured(self, tmp_path, monkeypatch):
        monkeypatch.setattr(estado, "REPO_ROOT", tmp_path)
        gate = {
            "id": "fase2-oversized-window-parity",
            "artifact": "corpus/{channel}/fase2_gate.json",
            "artifact_pointer": "3a",
            "evaluation": "automatic",
        }
        m = estado.measure_gate(gate, "chan")
        assert m.exists is False
        assert m.display == "declarado, nao medido"


class TestMeasureHumanJudgmentGate:
    def test_with_result_ref_reports_where_it_is_recorded(self):
        gate = {"id": "g", "evaluation": "human_judgment", "result_ref": ["_docs/decisions.md#17"]}
        m = estado.measure_gate(gate, "chan")
        assert m.exists is True
        assert "decisions.md#17" in m.display

    def test_without_result_ref_is_declared_not_measured(self):
        gate = {"id": "g", "evaluation": "human_judgment", "result_ref": []}
        m = estado.measure_gate(gate, "chan")
        assert m.exists is False
        assert m.display == "declarado, nao medido"


# --------------------------------------------------------------------------
# Regeneracao - o mesmo que a CI roda em `--check`
# --------------------------------------------------------------------------


class TestGeneratedFilesMatchCommitted:
    def test_estado_md_portoes_table_matches_committed_copy(self):
        portoes = estado.load_portoes()
        fresh = estado.render_estado_md(portoes)
        fresh_table = estado._extract_block(
            fresh, estado.PORTOES_TABLE_START, estado.PORTOES_TABLE_END
        )
        committed = estado.ESTADO_PATH.read_text(encoding="utf-8")
        committed_table = estado._extract_block(
            committed, estado.PORTOES_TABLE_START, estado.PORTOES_TABLE_END
        )
        assert fresh_table == committed_table

    def test_decisions_md_index_matches_committed_copy(self):
        fresh_index = estado.render_decisions_index()
        committed = estado.DECISIONS_PATH.read_text(encoding="utf-8")
        committed_index = estado._extract_block(
            committed, estado.DECISIONS_INDEX_START, estado.DECISIONS_INDEX_END
        )
        assert fresh_index.strip() == (committed_index or "").strip()

    def test_check_cli_exits_zero_against_committed_state(self):
        assert estado.check() == 0
