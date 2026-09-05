"""Fase transversal (`_docs/decisions.md#22`): gera `_docs/estado.md` e o
indice PT-BR no topo de `_docs/decisions.md` a partir de `schema/portoes.json`
e dos `fase*_gate.json`/`manifesto.csv` reais - nunca a mao.

Quatro camadas (`_docs/decisions.md#22`): `schema/portoes.json` e quem grava
o portao e a constante; este modulo so le e renderiza. Nenhum limiar muda de
valor aqui.

Uso:

    uv run python -m src.estado --write   # regenera e escreve os dois arquivos
    uv run python -m src.estado --check   # regenera em memoria e compara com
                                           # o que esta commitado; sai 1 se
                                           # divergir (mesma postura do
                                           # TEST_COUNTS/alembic check da CI)

O bloco de metadados (`commit`, `gerado em`) e a secao de issues abertas no
GitHub nao entram na comparacao de `--check`: o primeiro muda a cada commit
por definicao (o SHA do commit que vai conter este arquivo so existe depois
de o arquivo ja estar escrito - comparar contra ele seria sempre falso) e a
segunda depende de estado externo ao repositorio (issues podem abrir/fechar
sem nenhum commit novo). O que `--check` de fato verifica - e o que
`_docs/decisions.md#22` realmente pede - e que a tabela de portoes e o
indice de decisoes, os dois derivados de dado versionado, batem exatamente
com o que esta commitado.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src import amostragem, coleta, janelas, sentencia
from src.coleta import ROLE_HOLDOUT, ROLE_PROFILE, expected_word_count

REPO_ROOT = Path(__file__).resolve().parent.parent
PORTOES_PATH = REPO_ROOT / "schema/portoes.json"
ESTADO_PATH = REPO_ROOT / "_docs/estado.md"
DECISIONS_PATH = REPO_ROOT / "_docs/decisions.md"
PLANO_PATH = REPO_ROOT / "_docs/plano_implementacao.md"
CORPUS_DIR = REPO_ROOT / "corpus"

FORMULA_SOURCE_MODULES = (janelas, coleta, sentencia, amostragem)

PORTOES_TABLE_START = "<!-- PORTOES_TABLE_START -->"
PORTOES_TABLE_END = "<!-- PORTOES_TABLE_END -->"
DECISIONS_INDEX_START = "<!-- DECISIONS_INDEX_START -->"
DECISIONS_INDEX_END = "<!-- DECISIONS_INDEX_END -->"


# ----------------------------------------------------------------------------
# 1. O indice de _docs/decisions.md - dado, nao inferencia mecanica
# ----------------------------------------------------------------------------
#
# `_docs/decisions.md#22`/`#24`: cada `Status:` e conferido lendo o texto
# real da entrada, um por um - nunca por proximidade temporal, nunca so pelo
# titulo. Essa checagem e humana por natureza (e o que este mesmo issue #14
# fez, entrada por entrada, antes de escrever a tabela abaixo); o que este
# modulo automatiza e a renderizacao e a checagem de referencias penduradas
# contra o resultado ja conferido, nao a conferencia em si.

DECISIONS_INDEX: tuple[dict, ...] = (
    {
        "number": 1,
        "phase": "transversal",
        "sentence": (
            "Postgres entra no stack ao lado do arquivo, nao no lugar dele - schema/, "
            "codebook.md e perfis/ continuam arquivo; estado operacional pode virar tabela, "
            "decisao de issue futura."
        ),
        "status": "vigente",
    },
    {
        "number": 2,
        "phase": "transversal",
        "sentence": (
            "Isolamento de teste: banco `<db>_test` dedicado por worktree, cada teste roda numa "
            'transacao com rollback (`join_transaction_mode="create_savepoint"`).'
        ),
        "status": "vigente",
    },
    {
        "number": 3,
        "phase": 1,
        "sentence": (
            "Corpus do Fase 1 de @Zenn0009 aceito com 21 videos (nao 30) depois do bloqueio de "
            "IP no video 22/30 - reducao autorizada pelo dono, nao bug."
        ),
        "status": 'parcialmente superseded por #4 (o piso ">= 21" videos para @Zenn0009)',
    },
    {
        "number": 4,
        "phase": 1,
        "sentence": (
            "Corpus de @Zenn0009 completado para 30 via fallback whisperX (GPU, batch_size=4, um "
            "subprocesso por video) em vez de esperar o bloqueio de IP das legendas ceder."
        ),
        "status": "vigente",
    },
    {
        "number": 5,
        "phase": 1,
        "sentence": (
            "whisperX continua fallback, nao vira caminho padrao de coleta - legenda continua "
            "primeira tentativa mesmo sabendo que o bloqueio de IP vai se repetir a cada canal "
            "novo."
        ),
        "status": "vigente",
    },
    {
        "number": 6,
        "phase": 1,
        "sentence": (
            "Sorteio de holdout: semente fixa 42, alvo 5 videos, piso 4 - abaixo disso o canal "
            "reprova o criterio pratico em vez de encolher mais."
        ),
        "status": "vigente",
    },
    {
        "number": 7,
        "phase": 1,
        "sentence": (
            "Manifesto ganha coluna `role` (`profile`/`holdout`), em ingles por ser "
            "identificador de dado novo, mesmo o resto do manifesto sendo PT-BR por divida "
            "aceita."
        ),
        "status": "vigente",
    },
    {
        "number": 8,
        "phase": 1,
        "sentence": (
            "`WORDS_PER_MINUTE` de `src/coleta.py` corrigido de 140 para 150, para bater com o "
            "texto do portao da Fase 1 que sempre disse ~150 palavras/minuto."
        ),
        "status": "vigente",
    },
    {
        "number": 9,
        "phase": 1,
        "sentence": (
            "Corpus de @MackExplains7 fechado: 30 `profile` + 5 `holdout`, whisperX nos 30 "
            "`profile` depois do mesmo bloqueio de IP de @Zenn0009 se repetir."
        ),
        "status": "vigente",
    },
    {
        "number": 10,
        "phase": 2,
        "sentence": (
            "Fase 2 grooming: storage em arquivo (nao Postgres), modelo `sat-3l-sm` do wtpsplit, "
            "`SAMPLE_SEED = 42`, escopo desta passada e so @MackExplains7."
        ),
        "status": "vigente",
    },
    {
        "number": 11,
        "phase": 2,
        "sentence": (
            "Portao da Fase 2, criterio 3, medido FAIL real contra @MackExplains7 (106-141 "
            "janelas/video) - contingencia do plano (baixar `WINDOW_MAX_WORDS`) tentada e medida "
            "pior, causa raiz identificada como `WINDOW_MAX_SENTENCES` combinado com as "
            "sentencas reais do canal."
        ),
        "status": "vigente",
    },
    {
        "number": 12,
        "phase": 2,
        "sentence": (
            "Bandas fixas do criterio 3 (`GATE_MIN/MAX_WINDOWS_PER_VIDEO = 25/60`) substituidas "
            "por uma banda proporcional a duracao, `GATE_WINDOWS_PER_MINUTE = 5.6 +-40%`."
        ),
        "status": "superseded por #14",
    },
    {
        "number": 13,
        "phase": 2,
        "sentence": (
            "`group_windows()` passa a perseguir ativamente `WINDOW_MIN_SENTENCES` antes de "
            "fechar uma janela nao-final, aceitando estourar `WINDOW_MAX_WORDS` ate "
            "`GATE_MAX_WINDOW_WORDS` para chegar la - correcao de especificacao, nao decisao "
            "nova."
        ),
        "status": "vigente",
    },
    {
        "number": 14,
        "phase": 2,
        "sentence": (
            "Criterio 3 do portao da Fase 2 reestruturado em 3a/3b (invariantes, tolerancia "
            "zero), 3c (termometro do canal, `blocking: false`, <= 15%) e 3d (tolerancia, banda "
            "recalibrada para `GATE_WINDOWS_PER_MINUTE = 4.86 +-40%`)."
        ),
        "status": "vigente",
    },
    {
        "number": 15,
        "phase": 2,
        "sentence": (
            "Issue #8 (`sentence_cut` FAIL): causa raiz fixada na sentenciacao (M2), nao no "
            "portao de janelas - confianca de fronteira do SaT sozinha nao discrimina os casos."
        ),
        "status": "vigente",
    },
    {
        "number": 16,
        "phase": 3,
        "sentence": (
            "Grooming da Fase 3: @Zenn0009 ratificado como canal do teste de transferencia, "
            "receita deterministica de ~20 janelas (2 videos, semente 42), par de videos do "
            "teste de cobertura reaproveitado da Fase 2 (`lkLwp9o7Djk`/`5unhHRFkC7I`, 205 "
            "janelas, teto absoluto de 20), formato de citacao do codebook (citacao literal + "
            "`window_id`)."
        ),
        "status": "vigente",
    },
    {
        "number": 17,
        "phase": 2,
        "sentence": (
            "Criterio 1 do portao da Fase 2 passou exatamente no limite (5 de 50) - aceito como "
            "pass, registrado, nao remedido nem reamostrado."
        ),
        "status": "vigente",
    },
    {
        "number": 18,
        "phase": "transversal",
        "sentence": (
            "Politica de idioma: a tabela do README estava errada em tres pontos (os arquivos "
            "reais estavam certos) - tabela reclassificada, nada traduzido."
        ),
        "status": "vigente",
    },
    {
        "number": 19,
        "phase": 3,
        "sentence": (
            "Issue #11 (tie-breaker de fronteira de `function`): reescrito para exigir zero "
            "lookahead e zero contagem de palavras, depois de dois FAILs seguidos de QA na mesma "
            "classe de defeito."
        ),
        "status": (
            'parcialmente superseded por #20 (a frase "prior windows in the same video" da regra '
            "de pivo; classificacao de boundary de 5unhHRFkC7I:j0075; taxa e lista de janelas de "
            "fronteira confirmadas, 5/205 -> 6/205)"
        ),
    },
    {
        "number": 20,
        "phase": 3,
        "sentence": (
            "Tie-breaker de fronteira de `function` reancorado ao contexto real que o anotador "
            'recebe na chamada (3 janelas anteriores, nao o video inteiro); "developed before" '
            "operacionalizado como semantico, nunca lexical."
        ),
        "status": "vigente",
    },
    {
        "number": 21,
        "phase": 6,
        "sentence": (
            "`scale` fica em v1 e a Fase 6 (`M7`) agrega `scale_trajectory` por terco narrativo "
            "do video, nunca como distribuicao marginal - decidido durante a Fase 3, medido "
            "antes de a Fase 6 ser groomada."
        ),
        "status": "vigente",
    },
    {
        "number": 22,
        "phase": "transversal",
        "sentence": (
            "Documentacao ganha quatro camadas com prazo de validade declarado: portoes e estado "
            "viram dado (`schema/portoes.json`, `_docs/estado.md` gerado), documentos narrativos "
            'param de ser lidos como estado vivo - "um numero, um lugar".'
        ),
        "status": (
            "parcialmente superseded por #24 (a definicao binaria de Status no campo decision_ref)"
        ),
    },
    {
        "number": 23,
        "phase": "transversal",
        "sentence": (
            "Duas correcoes de processo: `fase-N` e regra de issue de fase, nao de toda issue; "
            '"main e para... os docs" so vale para o conteudo da documentacao, nao para a '
            "ferramenta que a gera."
        ),
        "status": "vigente",
    },
    {
        "number": 24,
        "phase": "transversal",
        "sentence": (
            "Indice de `_docs/decisions.md` ganha um terceiro `Status`: `parcialmente superseded "
            "por #N (fragmento)`, alem de vigente/superseded - o binario do #22 nao dava conta "
            "do caso #19/#20."
        ),
        "status": "vigente",
    },
)


def decisions_status_by_number() -> dict[int, str]:
    return {entry["number"]: entry["status"] for entry in DECISIONS_INDEX}


# ----------------------------------------------------------------------------
# 2. schema/portoes.json
# ----------------------------------------------------------------------------


def load_portoes(path: Path = PORTOES_PATH) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


UNQUALIFIED_SUPERSEDED_RE = re.compile(r"^superseded por #\d+$")
DECISIONS_REF_RE = re.compile(r"^_docs/decisions\.md#(\d+)[a-z]?$")
PLANO_REF_RE = re.compile(r"^_docs/plano_implementacao\.md:(\d+)(?:-(\d+))?$")


def check_decision_refs(gates: list[dict], plano_path: Path = PLANO_PATH) -> list[str]:
    """`_docs/decisions.md#22`: rejeita um `decision_ref` cujo alvo (a) nao
    existe, (b) e um `plano:LINE` alem do fim real do arquivo, ou (c) resolve
    a uma entrada cujo `Status:` no indice gerado e o `superseded por #N`
    **desqualificado** (`_docs/decisions.md#24`: `parcialmente superseded por
    #N (fragmento)` passa - so a forma sem qualificacao nao passa).
    """
    problems: list[str] = []
    statuses = decisions_status_by_number()
    plano_line_count = len(plano_path.read_text(encoding="utf-8").splitlines())

    for gate in gates:
        for ref in gate.get("decision_ref", []):
            m = DECISIONS_REF_RE.match(ref)
            if m:
                number = int(m.group(1))
                status = statuses.get(number)
                if status is None:
                    problems.append(
                        f"{gate['id']}: decision_ref {ref!r} nao existe em _docs/decisions.md"
                    )
                elif UNQUALIFIED_SUPERSEDED_RE.match(status):
                    problems.append(
                        f"{gate['id']}: decision_ref {ref!r} aponta para uma entrada com "
                        f"Status: {status!r} (superseded, sem qualificacao) - alvo morto"
                    )
                continue

            m = PLANO_REF_RE.match(ref)
            if m:
                line = int(m.group(2) or m.group(1))
                if line > plano_line_count:
                    problems.append(
                        f"{gate['id']}: decision_ref {ref!r} aponta para a linha {line}, "
                        f"mas _docs/plano_implementacao.md tem {plano_line_count} linhas"
                    )
                continue

            problems.append(
                f"{gate['id']}: decision_ref {ref!r} nao bate com nenhum formato reconhecido"
            )

    return problems


def check_formula_params(gates: list[dict], modules=FORMULA_SOURCE_MODULES) -> list[str]:
    """`_docs/decisions.md#22`: falha se os `params` de um gate `kind:
    "formula"` divergirem da constante correspondente em `src/*.py`."""
    problems: list[str] = []
    for gate in gates:
        threshold = gate["threshold"]
        if threshold.get("kind") != "formula":
            continue
        for name, value in threshold["params"].items():
            found = False
            for module in modules:
                if hasattr(module, name):
                    found = True
                    real_value = getattr(module, name)
                    if real_value != value:
                        problems.append(
                            f"{gate['id']}: params[{name!r}] = {value!r} em schema/portoes.json, "
                            f"mas {module.__name__}.{name} = {real_value!r}"
                        )
                    break
            if not found:
                problems.append(
                    f"{gate['id']}: params[{name!r}] nao foi encontrado em nenhum de "
                    f"{[m.__name__ for m in modules]}"
                )
    return problems


# ----------------------------------------------------------------------------
# 3. Medicao - le o artefato real de cada portao, nunca decide o limiar
# ----------------------------------------------------------------------------


@dataclass
class Measurement:
    exists: bool
    passed: bool | None
    display: str


def _iter_channels(corpus_dir: Path = CORPUS_DIR) -> list[str]:
    if not corpus_dir.is_dir():
        return []
    return sorted(p.name for p in corpus_dir.iterdir() if p.is_dir())


def _measure_manifesto_gate(gate: dict, channel: str) -> Measurement:
    path = REPO_ROOT / gate["artifact"].format(channel=channel)
    if not path.exists():
        return Measurement(False, None, "declarado, nao medido")

    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    threshold = gate["threshold"]
    gate_id = gate["id"]

    if gate_id == "fase1-profile-row-floor":
        value = sum(1 for r in rows if r.get("role", ROLE_PROFILE) == ROLE_PROFILE)
        return Measurement(True, value >= threshold["value"], f"{value} linhas profile")

    if gate_id == "fase1-holdout-row-floor":
        value = sum(1 for r in rows if r.get("role", ROLE_PROFILE) == ROLE_HOLDOUT)
        return Measurement(True, value >= threshold["value"], f"{value} linhas holdout")

    if gate_id == "fase1-word-count-floor":
        ratios = []
        for row in rows:
            if row.get("role", ROLE_PROFILE) != ROLE_PROFILE:
                continue
            duration_s = float(row["duracao_s"])
            expected = expected_word_count(duration_s)
            if expected:
                ratios.append(int(row["contagem_palavras"]) / expected)
        if not ratios:
            return Measurement(False, None, "declarado, nao medido")
        value = min(ratios)
        return Measurement(True, value >= threshold["value"], f"pior razao: {value:.1%}")

    raise ValueError(f"gate desconhecido para medicao via manifesto: {gate_id}")  # pragma: no cover


def _measure_json_pointer_gate(gate: dict, channel: str | None) -> Measurement:
    artifact = gate["artifact"].format(channel=channel) if channel else gate["artifact"]
    path = REPO_ROOT / artifact
    if not path.exists():
        return Measurement(False, None, "declarado, nao medido")

    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    pointer = gate.get("artifact_pointer")
    node = data[pointer] if pointer else data
    gate_id = gate["id"]

    if gate_id == "fase2-oversized-window-parity":
        a, b = node["n_janelas_grandes"], node["n_sentencas_grandes"]
        return Measurement(True, node["passed"], f"{a} janelas vs {b} sentencas")

    if gate_id == "fase2-nonlast-single-window-residual":
        return Measurement(True, node["passed"], f"residuo={node['residuo']}")

    if gate_id == "fase2-nonlast-single-window-ratio":
        return Measurement(True, node["passed"], f"{node['nonlast_single_ratio']:.1%}")

    if gate_id == "fase2-window-rate-band":
        return Measurement(
            True,
            node["passed"],
            "todos os videos dentro da banda" if node["passed"] else "video(s) fora da banda",
        )

    if gate_id == "fase3-outro-duvida-coverage":
        return Measurement(
            True,
            node["passed"],
            f"{node['n_outro_or_duvida']}/{gate['threshold']['denominator']}",
        )

    if gate_id == "fase6-schema-valid":
        return _measure_schema_valid(path)

    # Fase 4/5/5C: script proprio ainda nao existe (`_docs/plano_implementacao.md`
    # nao os construiu por este issue) - le uma chave "passed" generica se um
    # dia o arquivo existir, sem assumir uma forma que ainda nao foi decidida.
    if isinstance(node, dict) and "passed" in node:
        return Measurement(True, node["passed"], json.dumps(node, ensure_ascii=False))
    return Measurement(
        True, None, "medido (estrutura nao reconhecida por este gerador - ver artefato)"
    )


def _measure_schema_valid(perfil_path: Path) -> Measurement:
    schema_path = REPO_ROOT / "schema/perfil.schema.json"
    if not schema_path.exists():
        return Measurement(
            False, None, "declarado, nao medido (schema/perfil.schema.json ainda nao existe)"
        )
    try:
        import jsonschema
    except ImportError:
        return Measurement(
            True, None, "medido (validacao requer o pacote jsonschema, nao instalado)"
        )

    with perfil_path.open(encoding="utf-8") as fh:
        instance = json.load(fh)
    with schema_path.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    try:
        jsonschema.validate(instance, schema)
    except jsonschema.ValidationError as exc:
        return Measurement(True, False, f"invalido: {exc.message}")
    return Measurement(True, True, "valido")


def measure_gate(gate: dict, channel: str | None) -> Measurement:
    if gate["evaluation"] == "human_judgment":
        result_ref = gate.get("result_ref") or []
        if result_ref:
            return Measurement(True, None, f"registrado em {'; '.join(result_ref)}")
        return Measurement(False, None, "declarado, nao medido")

    artifact = gate["artifact"]
    if artifact is None:
        return Measurement(False, None, "declarado, nao medido")
    if artifact.endswith(".csv"):
        return _measure_manifesto_gate(gate, channel)
    return _measure_json_pointer_gate(gate, channel)


# ----------------------------------------------------------------------------
# 4. Renderizacao
# ----------------------------------------------------------------------------


def render_threshold(threshold: dict) -> str:
    kind = threshold["kind"]
    if kind == "qualitative":
        return threshold["statement"]
    if kind == "formula":
        params = ", ".join(f"{k}={v}" for k, v in threshold["params"].items())
        return f"{threshold['expression']} [{params}]"
    if kind == "bound":
        op = threshold["op"]
        value = threshold["value"]
        unit = threshold["unit"]
        denominator = threshold.get("denominator")
        rhs = f"{value}/{denominator}" if denominator else str(value)
        return f"{op} {rhs} {unit}"
    raise ValueError(f"threshold.kind desconhecido: {kind!r}")  # pragma: no cover


def _status_cell(measurement: Measurement) -> str:
    if not measurement.exists:
        return measurement.display
    if measurement.passed is True:
        return f"passou ({measurement.display})"
    if measurement.passed is False:
        return f"falhou ({measurement.display})"
    return measurement.display


def render_portoes_table(portoes: dict) -> str:
    header = "| Fase | Gate | Metrica | Limite | Tipo | Escopo | Status |"
    sep = "|---|---|---|---|---|---|---|"
    rows = [header, sep]

    channels = _iter_channels()
    for gate in portoes["gates"]:
        threshold_cell = render_threshold(gate["threshold"]).replace("|", "\\|")
        metric_cell = gate["metric"].replace("|", "\\|")
        targets: list[str | None] = channels if gate["scope"] == "per_channel" else [None]
        if not targets:
            targets = [None]
        for channel in targets:
            measurement = measure_gate(gate, channel)
            gate_label = f"`{gate['id']}`" + (f" ({channel})" if channel else "")
            rows.append(
                f"| {gate['phase']} | {gate_label} | {metric_cell} | {threshold_cell} | "
                f"{gate['type']} | {gate['scope']} | {_status_cell(measurement)} |"
            )
    return "\n".join(rows)


def render_decisions_index(entries: tuple[dict, ...] = DECISIONS_INDEX) -> str:
    blocks = []
    for entry in entries:
        phase_label = (
            f"Fase {entry['phase']}" if isinstance(entry["phase"], int) else entry["phase"]
        )
        header = f"**#{entry['number']}** ({phase_label}) - {entry['sentence']}"
        blocks.append(f"{header}\nStatus: {entry['status']}")
    return "\n\n".join(blocks)


def _git_head(repo_root: Path = REPO_ROOT) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "desconhecido"


def _open_phase_issues(repo: str = "Lcjlle/roteiros-engine") -> str:
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--json",
                "number,title,labels",
                "--limit",
                "200",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        issues = json.loads(result.stdout)
    except Exception as exc:
        return (
            f"nao foi possivel consultar issues abertas no GitHub agora ({exc.__class__.__name__})."
        )

    by_phase: dict[str, list[str]] = {}
    for issue in issues:
        labels = [label["name"] for label in issue.get("labels", [])]
        phase_labels = [label for label in labels if re.match(r"^fase-\d+$", label)]
        for phase_label in phase_labels or ["sem fase-N"]:
            by_phase.setdefault(phase_label, []).append(f"#{issue['number']} {issue['title']}")

    if not by_phase:
        return "nenhuma issue aberta."

    lines = []
    for phase_label in sorted(by_phase):
        lines.append(f"- **{phase_label}**: " + "; ".join(by_phase[phase_label]))
    return "\n".join(lines)


def render_estado_md(portoes: dict) -> str:
    generated_at = datetime.now(UTC).isoformat()
    head = _git_head()
    open_issues = _open_phase_issues()
    portoes_table = render_portoes_table(portoes)

    return f"""# Estado do projeto

**Este arquivo e gerado. Nao edite a mao.** Regenere com
`uv run python -m src.estado --write` a partir de `schema/portoes.json`, dos
`fase*_gate.json`/`manifesto.csv` reais, do commit atual e das issues abertas
no GitHub - ver `_docs/decisions.md#22`. `uv run python -m src.estado --check`
e o que a CI roda para garantir que este arquivo nunca fica desatualizado
comparado ao dado real.

<!-- METADATA_START -->
- commit: `{head}`
- gerado em: {generated_at}
<!-- METADATA_END -->

## Portoes

A fonte de cada numero abaixo e `schema/portoes.json` - nunca edite um limiar
aqui, edite la e regenere.

{PORTOES_TABLE_START}
{portoes_table}
{PORTOES_TABLE_END}

## Fases abertas (por label `fase-N`)

<!-- OPEN_ISSUES_START -->
{open_issues}
<!-- OPEN_ISSUES_END -->
"""


def _extract_block(text: str, start_marker: str, end_marker: str) -> str | None:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end < start:
        return None
    return text[start + len(start_marker) : end].strip("\n")


def _splice_decisions_index(decisions_text: str, index_markdown: str) -> str:
    block = f"{DECISIONS_INDEX_START}\n\n{index_markdown}\n\n{DECISIONS_INDEX_END}"
    if DECISIONS_INDEX_START in decisions_text and DECISIONS_INDEX_END in decisions_text:
        before = decisions_text[: decisions_text.index(DECISIONS_INDEX_START)]
        after = decisions_text[
            decisions_text.index(DECISIONS_INDEX_END) + len(DECISIONS_INDEX_END) :
        ]
        return before + block + after

    # Primeira geracao: injeta logo depois do paragrafo de abertura do
    # arquivo (antes da primeira entrada numerada, "## 1. ...").
    marker = "\n## 1. "
    idx = decisions_text.index(marker)
    return decisions_text[:idx] + f"\n## Indice\n\n{block}\n" + decisions_text[idx:]


# ----------------------------------------------------------------------------
# 5. CLI
# ----------------------------------------------------------------------------


def write() -> None:
    portoes = load_portoes()
    ESTADO_PATH.write_text(render_estado_md(portoes), encoding="utf-8")

    decisions_text = DECISIONS_PATH.read_text(encoding="utf-8")
    index_markdown = render_decisions_index()
    DECISIONS_PATH.write_text(
        _splice_decisions_index(decisions_text, index_markdown), encoding="utf-8"
    )


def check() -> int:
    portoes = load_portoes()
    problems = []

    problems += check_formula_params(portoes["gates"])
    problems += check_decision_refs(portoes["gates"])

    fresh_estado = render_estado_md(portoes)
    fresh_table = _extract_block(fresh_estado, PORTOES_TABLE_START, PORTOES_TABLE_END)
    committed_estado = ESTADO_PATH.read_text(encoding="utf-8") if ESTADO_PATH.exists() else ""
    committed_table = _extract_block(committed_estado, PORTOES_TABLE_START, PORTOES_TABLE_END)
    if fresh_table != committed_table:
        problems.append(
            "_docs/estado.md: a tabela de portoes commitada nao bate com a "
            "regenerada a partir de schema/portoes.json - rode "
            "`uv run python -m src.estado --write` e commite."
        )

    fresh_index = render_decisions_index()
    committed_decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    committed_index = _extract_block(
        committed_decisions, DECISIONS_INDEX_START, DECISIONS_INDEX_END
    )
    if fresh_index.strip() != (committed_index or "").strip():
        problems.append(
            "_docs/decisions.md: o indice gerado commitado nao bate com o "
            "regenerado - rode `uv run python -m src.estado --write` e "
            "commite."
        )

    if problems:
        print(
            "::error::estado.md/decisions.md estao desatualizados ou "
            "schema/portoes.json tem referencias invalidas."
        )
        for problem in problems:
            print(f"  {problem}")
        return 1

    print(
        "schema/portoes.json, _docs/estado.md e o indice de _docs/decisions.md estao consistentes."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="regenera e escreve os arquivos")
    group.add_argument(
        "--check", action="store_true", help="compara o gerado com o commitado, sem escrever"
    )
    args = parser.parse_args(argv)

    if args.write:
        write()
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
