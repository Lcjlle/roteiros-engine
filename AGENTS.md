Sistema de producao de roteiros de YouTube por perfil estruturado de canal.
Ver `README.md` para a ideia e `_docs/plano_implementacao.md` para as dez
fases do plano.

Documents

- `_docs/process.md` - como o trabalho e organizado
- `_docs/plano_implementacao.md` - as dez fases, portoes e entregaveis
- `_docs/decisions.md` - decisoes tecnicas tomadas ao longo do grooming
- `DECISOES.md` - as decisoes de produto da Fase 0; descricao completa no
  proprio arquivo. Nada da Fase 1 em diante comeca antes desse arquivo
  estar preenchido

Commands

- `docker compose up -d db` - Postgres, precisa estar de pe antes de
  qualquer coisa tocar no banco
- `uv sync` - instala as dependencias
- `uv run alembic upgrade head` - aplica migrations
- `uv run alembic revision --autogenerate -m "..."` - gera uma migration a
  partir da diferenca entre `src/db.py`/os modelos e o banco
- `uv run alembic check` - falha se existe mudanca de modelo sem migration
  gerada. Rodar antes de commitar, o equivalente a
  `manage.py makemigrations --check --dry-run`
- `uv run pytest` - a suite inteira
- `uv run pytest tests/test_x.py` - um arquivo de teste
- `uv run ruff check . && uv run ruff format --check .` - lint e format,
  rodar antes de commitar

Rules

- Python e a unica linguagem. Sem frontend, sem servidor web.
- Postgres e a infraestrutura de estado do pipeline (`src/db.py`,
  `migrations/`) - ver `_docs/decisions.md` para o que vive em tabela versus
  o que continua sendo arquivo versionado em `schema/`, `corpus/`, `gold/`,
  `perfis/`. `_docs/blueprint.md` ainda descreve o raciocinio original
  "arquivo em vez de banco"; a decisao que o superpoe esta em
  `_docs/decisions.md`.
- Um teste que precisa do banco pede a fixture `db_session`
  (`tests/conftest.py`). Roda numa `<banco>_test` propria, dentro de uma
  transacao com rollback no fim - nunca escreve no banco de desenvolvimento
  da worktree, nunca deixa estado pro proximo teste. Ver
  `_docs/decisions.md#2`.
- Dependencias sao fixadas exatamente em `pyproject.toml` (`==`, nao `>=`).
  Nao adicionar uma sem perguntar - ver a licenca em `_docs/blueprint.md`
  antes de trazer qualquer biblioteca nova para dentro do projeto.
- Configuracao vem do ambiente. `DATABASE_URL`, uma chave de API nova - cada
  uma e uma variavel de ambiente e uma linha em `.env.example`, nunca
  hardcoded. `DATABASE_URL` usa o esquema `postgresql+psycopg://`, nao
  `postgres://` - SQLAlchemy nao traduz o segundo como o `dj-database-url`
  do Django faz.
- Commitar regularmente.

Principios que nao se negociam (de `_docs/plano_implementacao.md`)

- **O esquema e a fonte da verdade.** Categorias, campos e valores permitidos
  vivem em `schema/ontologia.v1.json`, versionado. Prompt, codebook e codigo
  leem esse arquivo - nunca duplicam a lista em prosa.
- **Anotar nao e analisar.** O modelo escolhe de uma lista fechada. Se um
  passo pede "descubra os padroes", falta um campo no esquema, nao falta
  criatividade no prompt.
- **Perfil e execucao sao processos separados.** O perfil se constroi uma
  vez por canal, e verificado por humano, e vira `perfis/<canal>.perfil.json`.
  A execucao le esse arquivo e nunca o rederiva.
- **O que da para medir, mede-se em codigo.** Contagem, posicao percentual,
  distribuicao, termo proibido - tudo isso e Python puro em
  `src/verifica.py`, nunca julgamento de LLM. Julgamento de modelo fica
  reservado ao que genuinamente nao tem metrica.

Estrutura do projeto

```
roteiros-engine/
├── schema/          ontologia, codebook, formato do perfil
├── corpus/          raw · segmentado · anotado, por canal (o que fica arquivo)
├── gold/             anotacao humana de referencia, por canal
├── perfis/          <canal>.perfil.json (versionado, congelado por fase)
├── migrations/      Alembic - uma migration por mudanca de tabela
├── src/              db.py (engine/Base) + os modulos do pipeline (coleta,
                       segmenta, anota, valida, agrega, gera, verifica)
├── saidas/          <video_id>/plano.json, roteiro.md, verificacao.md
└── tests/            a suite
```

Portoes de qualidade

Cada fase do plano tem um portao numerico objetivo (portao 3a-3d da Fase 2,
cobertura de ontologia, Krippendorff's alpha, % de criterios). Um QA que
aprova uma fase
sem rodar o script de verificacao daquela fase e reportar o numero medido
nao fez QA - ver `_docs/plano_implementacao.md` para o portao de cada fase e
`_docs/team/qa-engineer.md` para como isso vira veredito.

CI

`.github/workflows/ci.yml` roda em todo push, em pull requests contra `main`,
e sob demanda. Um job, com um service container Postgres: `uv sync --locked`,
`uv run alembic upgrade head`, `uv run alembic check`, ambos os checks do
ruff, depois a suite inteira.

- Um teste pulado (skip) quebra o build. A suite escreve um relatorio JUnit e
  um passo depois dele falha o job se algum teste foi pulado, imprimindo o
  node id e o motivo.
- Um teste removido da colecao tambem quebra o build. A forma da suite fica
  fixada em `TEST_COUNTS` no proprio workflow: uma linha por arquivo de
  teste, `basename count`. Toda branch que adiciona, remove ou renomeia um
  arquivo de teste, ou muda quantos testes um arquivo roda, edita a linha
  correspondente no mesmo commit.
- Nao edite `TEST_COUNTS` a mao. Regenere o bloco inteiro a partir da
  colecao atual e cole, no mesmo commit que mudou a suite:
  ```
  uv run python -c "import collections,pytest
  class P:
      def pytest_collection_finish(self, session):
          c=collections.Counter(i.nodeid.split('::',1)[0].rsplit('/',1)[-1] for i in session.items)
          [print(f'{n} {c[n]}') for n in sorted(c)]
  raise SystemExit(pytest.main(['--collect-only','-p','no:cacheprovider'],plugins=[P()]))" 2>/dev/null
  ```
- `_docs/estado.md` e o indice de `_docs/decisions.md` sao gerados de
  `schema/portoes.json` (`_docs/decisions.md#22`) e a CI falha se o
  commitado divergir do regenerado - mesma postura do `TEST_COUNTS`. Nao
  edite os dois a mao. Regenere e commite no mesmo commit que mudou
  `schema/portoes.json` ou qualquer `fase*_gate.json`/`manifesto.csv`:
  ```
  uv run python -m src.estado --write
  ```
  `uv run python -m src.estado --check` roda a mesma comparacao que a CI
  roda, sem escrever nada.
- Reproduza um run de CI localmente com um comando (com `db` de pe):
  `uv sync --locked && uv run alembic upgrade head && uv run alembic check && uv run python -m src.estado --check && uv run ruff check . && uv run ruff format --check . && uv run pytest -rs`
  O `-rs` e o ponto: lista todo skip, que o CI transforma em falha.
