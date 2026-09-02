Sistema de producao de roteiros de YouTube por perfil estruturado de canal.
Ver `README.md` para a ideia e `_docs/plano_implementacao.md` para as dez
fases do plano.

Documents

- `_docs/process.md` - como o trabalho e organizado
- `_docs/plano_implementacao.md` - as dez fases, portoes e entregaveis
- `_docs/decisions.md` - decisoes tecnicas tomadas ao longo do grooming
- `DECISOES.md` - as tres decisoes de produto da Fase 0 (canal, duracao-alvo,
  uso comercial). Nada da Fase 1 em diante comeca antes desse arquivo estar
  preenchido

Commands

- `uv sync` - instala as dependencias
- `uv run pytest` - a suite inteira
- `uv run pytest tests/test_x.py` - um arquivo de teste
- `uv run ruff check . && uv run ruff format --check .` - lint e format,
  rodar antes de commitar

Rules

- Python e a unica linguagem. Sem frontend, sem servidor web, sem banco de
  dados - o sistema le e escreve arquivo (`_docs/blueprint.md`, secao
  "Decisoes de projeto", explica por que).
- Dependencias sao fixadas exatamente em `pyproject.toml` (`==`, nao `>=`).
  Nao adicionar uma sem perguntar - ver a licenca em `_docs/blueprint.md`
  antes de trazer qualquer biblioteca nova para dentro do projeto.
- Configuracao vem do ambiente. Uma chave de API nova e uma variavel de
  ambiente e uma linha em `.env.example`, nunca hardcoded.
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
├── corpus/          raw · segmentado · anotado, por canal
├── gold/             anotacao humana de referencia, por canal
├── perfis/          <canal>.perfil.json
├── src/              os modulos (coleta, segmenta, anota, valida, agrega,
                       gera, verifica)
├── saidas/          <video_id>/plano.json, roteiro.md, verificacao.md
└── tests/            a suite
```

Portoes de qualidade

Cada fase do plano tem um portao numerico objetivo (Pk, cobertura de
ontologia, Krippendorff's alpha, % de criterios). Um QA que aprova uma fase
sem rodar o script de verificacao daquela fase e reportar o numero medido
nao fez QA - ver `_docs/plano_implementacao.md` para o portao de cada fase e
`_docs/team/qa-engineer.md` para como isso vira veredito.

CI

`.github/workflows/ci.yml` roda em todo push, em pull requests contra `main`,
e sob demanda. Um job: `uv sync --locked`, ambos os checks do ruff, depois a
suite inteira.

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
- Reproduza um run de CI localmente com um comando:
  `uv sync --locked && uv run ruff check . && uv run ruff format --check . && uv run pytest -rs`
  O `-rs` e o ponto: lista todo skip, que o CI transforma em falha.
