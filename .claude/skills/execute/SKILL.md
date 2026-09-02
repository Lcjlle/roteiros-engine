---
name: execute
description: Run the roteiros-engine squad pipeline - groom, implement, test, integrate, repeat
disable-model-invocation: true
---

# Execute Development Pipeline

Run the squad process for roteiros-engine. Before starting, read `_docs/process.md` for the full workflow, and confirm `DECISOES.md` has no item "em aberto" — nothing past Fase 0 runs while one does.

**Argument:** `[numero-de-issues]` — quantas issues por onda (default: 1). O backlog é sequencial por fase (`_docs/plano_implementacao.md`), então a maioria das ondas vai ter 1 issue por natureza, não pelo limite de 5 do processo.

## Steps

### 1. Escolher a onda
`gh issue list --label "!blocked"` (ou filtrar manualmente issues sem `blocked`). Pegue as elegíveis — dependências fechadas+mergeadas na main, e o portão da fase anterior (`_docs/plano_implementacao.md`) já medido e dentro do limite — até `$1` (default 1).

### 2. PM Grooming
Para cada issue da onda que ainda não segue o formato de `_docs/task-template.md`, lance o agente **pm** (`_docs/team/pm.md`). Não pule mesmo se a issue já parecer pronta.

### 3. Preparar worktrees
Para cada issue:
```
git worktree add ../wt/<issue> -b issue-<issue> main
cd ../wt/<issue> && uv sync
cp .env-do-checkout-principal .env  # ajustar DATABASE_URL pra roteiros_wt<issue>
# CREATE DATABASE roteiros_wt<issue> dentro do container Postgres
uv run alembic upgrade head
```
Confirme antes de lançar qualquer agente: `uv run python -c "import os; print(os.environ['DATABASE_URL'])"` imprime o banco da própria worktree, e `pgrep -af pytest` não mostra suite viva ali.

### 4. Implementar (paralelo)
Lance o agente **software-engineer** (`_docs/team/software-engineer.md`) por issue, na worktree correspondente. Nunca dois agentes na mesma worktree ao mesmo tempo.

### 5. QA
Assim que o engineer reporta pronto e a branch está pushada, lance o agente **qa-engineer** (`_docs/team/qa-engineer.md`) na mesma worktree.

### 6. Tratar resultado do QA
- **PASS**: segue pra integração
- **FAIL**: relança um novo **software-engineer** com o comentário do QA como entrada, depois relança QA. Máximo 2 tentativas; se continuar falhando, reporta ao usuário

### 7. Integração
Só um branch por vez, em ordem de dependência, dentro da worktree:
1. Rebase na main atual
2. Suite completa + `ruff check`/`format --check` + `alembic check`, de novo, depois do rebase
3. Se a issue fecha uma fase: roda o script de portão, confirma o número contra `_docs/plano_implementacao.md`
4. Merge na main só se tudo limpo
5. Push na main
6. Fecha a issue
7. Rebase todo branch ainda aberto da onda na nova main

### 8. Repetir
Volta ao passo 1. Continua até não haver mais issue elegível.

**IMPORTANTE:** O orchestrator nunca groom, nunca implementa, nunca testa. Só lança agentes, gerencia worktrees, resolve a fila de merge. Nada neste processo deleta — worktree, branch e banco ficam onde estão quando a issue fecha.
