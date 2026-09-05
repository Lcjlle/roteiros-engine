# roteiros-engine

Sistema de produção de roteiros para canais de YouTube baseado em **perfis estruturados**, extraídos de corpus anotado em vez de inferidos por prompt.

Um canal de referência entra. Um arquivo de configuração sai. A partir dele, roteiros novos são gerados de forma repetível e verificável, sem que o sistema reanalise o canal a cada execução. O sistema é projetado para rodar **vários canais** com um mesmo motor e uma mesma ontologia.

**Arquitetura v3.0.** Changelog e plano de execução em `_docs/plano_implementacao.md`. Decisões técnicas em `_docs/decisions.md` — onde este README discordar dele, ele perde.

---

## Política de idioma

**Normativa. Leia antes de escrever qualquer arquivo do projeto.**

> **Se é lido pela máquina ou entra num prompt, é inglês. Se é lido só por humano, é PT-BR.**

O corpus e os roteiros gerados são em **inglês**. A comunicação do projeto com humanos é em **PT-BR**.

| Inglês, obrigatoriamente | PT-BR |
|---|---|
| `schema/codebook.md` (definições, exemplos, tie-breakers) | `README.md`, `_docs/plano_implementacao.md`, `_docs/blueprint.md` |
| `schema/ontologia.vN.json` (nomes de campo e valores) | `DECISOES.md`, `_docs/process.md`, `AGENTS.md` |
| prompts de anotação e de geração | corpo de issues, comentários de QA, mensagens de commit |
| `tone_examples` e `forbidden` no perfil | prosa dos relatórios de concordância e fusão |
| roteiros em `saidas/` | **docstrings e comentários dentro do código** |
| identificadores de código: variáveis, funções, colunas, nomes de teste | mensagens de CLI e log destinadas a você |
| `_docs/team/*` e `_docs/task-template.md` — instrução operacional que entra literalmente no prompt de um agente | — |
| `_docs/decisions.md` — ver `_docs/decisions.md#18` | — |

Números e nomes de campo dentro de um texto em PT-BR permanecem em inglês, porque são identificadores. Um relatório diz "a função `hook` ficou em 4,2% dos blocos".

**O teste que decide um caso novo.** O texto é *vocabulário do sistema* — algo que o modelo precisa escolher, produzir ou casar exatamente? Então é inglês. É *explicação para o dono do projeto* — narrativa, justificativa, diagnóstico? Então é PT-BR. Não use "um agente vai ler isso" como critério: agentes leem o repositório inteiro, inclusive tudo que está em PT-BR. `_docs/team/*` é inglês porque é instrução operacional colada dentro do prompt de um agente; docstrings são PT-BR porque são explicação ao lado do código, enquanto os identificadores que elas descrevem seguem em inglês.

**`schema/codebook.md` é o único artefato bilíngue.** Cada entrada tem definição normativa em inglês e glosa em PT-BR marcada como não normativa. **Onde divergirem, a definição EN vence.** Não há sincronização automática: alterou a definição, altere a glosa no mesmo commit. Essa regra também vive no cabeçalho do próprio codebook.

**Dívida aceita:** os diretórios já commitados são em português (`corpus/`, `perfis/`, `saidas/`, `schema/ontologia.v1.json`). Não vale renomear — nomes de caminho não entram em prompt nem viram identificador de dado, e o churn atingiria `process.md`, `decisions.md`, testes e histórico. Registrado aqui para ninguém "consertar" isso num commit grande.

---

## Estado

Ver o cabeçalho `**Estado:**` de cada fase em `_docs/plano_implementacao.md`, e a tabela de portões sempre-atual em `_docs/estado.md` (gerado, `_docs/decisions.md#22`) — este README não mantém uma narrativa própria por fase para não virar uma segunda cópia que diverge da primeira.

Resumo: Fases 0-3 executadas (Fase 3 via Issue #11, `main@4c3e165`); Fase 4 — Gold standard é o próximo passo, sem issue ainda; Fases 5-10 não iniciadas.

---

## O problema

Os sistemas existentes de "automação de YouTube com IA" seguem todos o mesmo desenho: um prompt longo em prosa pede a um modelo que analise um canal e escreva um roteiro parecido, tudo na mesma execução.

Isso falha por um motivo estrutural, não por falta de capricho no prompt: **a especificação vive em prosa que o modelo reinterpreta do zero a cada vez**. Prosa interpretada duas vezes dá dois resultados. O output é plausível, mas não é reprodutível, e o que não é reprodutível não escala para um canal, muito menos para vários.

O segundo defeito é consequência do primeiro: pedir "faça engenharia reversa deste roteiro" produz um ensaio interpretativo. De um roteiro só, você tem n=1 de cada decisão estrutural, e não dá para distinguir o que é padrão do canal do que foi escolha daquele tema.

## A ideia central

Quatro inversões resolvem o problema.

**1. Anotar em vez de analisar.** Em vez de pedir descoberta livre, entrega-se ao modelo um esquema fechado (lista fixa de campos e valores) e pede-se rotulagem. Modelos são muito mais confiáveis escolhendo de uma lista do que inventando categorias. Trinta análises livres dão trinta textos incomparáveis; trinta anotações contra o mesmo esquema dão uma tabela que se pode somar.

**2. Anotar fino e fundir depois.** A unidade de anotação é uma **janela** de 2 a 4 sentenças, não um bloco pré-segmentado. O bloco emerge da fusão de janelas consecutivas com a mesma função. A fronteira deixa de ser decisão prévia e vira consequência da anotação.

**3. Separar construção de perfil da execução.** O perfil é construído uma vez por canal, é lento, é verificado por um humano e vira arquivo. A execução lê esse arquivo como parâmetro e nunca o rederiva. Rodar um segundo canal é trocar um arquivo, não reescrever o sistema.

**4. Uma ontologia, muitos perfis.** O vocabulário de anotação é global e versionado. A diferença entre canais é numérica (distribuições, faixas), não categórica. É isso que torna dois perfis comparáveis.

```
CONSTRUÇÃO DO PERFIL          │  EXECUÇÃO
lenta · uma vez por canal     │  rápida · toda vez
verificada por humano         │  automática
produz: perfil.json           │  consome: perfil.json

ONTOLOGIA: uma só, versionada, compartilhada por todos os canais
```

## Por que a fronteira não é decidida antes

A decisão de projeto mais fácil de reverter por engano.

Algoritmos de segmentação topical (TextTiling, C99, textsplit) detectam mudança de **assunto**, medindo queda de coesão lexical. A ontologia precisa de mudança de **função narrativa**. Os dois sinais não coincidem:

- Um `hook` e a `promise` seguinte falam do mesmo assunto com o mesmo vocabulário. Nenhum algoritmo topical os separa.
- Um bloco longo de `mechanism` varia bastante de léxico ao explicar as partes de um processo, e seria cortado no meio sem razão funcional.

Não é questão de ajustar parâmetro; o algoritmo está otimizando outra coisa. E há dependência circular: se a fronteira é definida pela mudança de função, não dá para segmentar antes de saber quais são as funções.

Por isso o pipeline produz **sentenças** (M2), anota **janelas** (M4) e deriva **blocos** por fusão (M6).

Se a janela de 2–4 sentenças um dia se mostrar má unidade, a contingência **não** é TextTiling — é segmentação por EDU (`isanlp_rst`), porque EDUs são unidades funcionais de discurso. Ver `_docs/blueprint.md`, Peça 1.

## O que o sistema entrega

**Uma vez, para todos os canais:**
- `schema/ontologia.vN.json` + `schema/codebook.md` — o vocabulário de anotação
- o motor de geração e o verificador

**Por canal:**
- `perfis/<canal>.perfil.json` — distribuições, faixas e sequências que descrevem a gramática do canal
- corpus anotado — sentenças, janelas, anotações e blocos, guardados para eventual reanotação
- run de concordância — a prova de que o perfil é confiável
- relatório de fusão — diagnóstico da saúde da ontologia naquele canal

**Por vídeo:**
- plano estruturado, roteiro final, relatório de verificação com valores medidos
- opcionalmente: locução, prompts de imagem, MP4 montado

---

## Arquitetura em módulos

Nove módulos. Cada um tem uma responsabilidade, uma entrada e uma saída persistida. Nenhum chama o outro diretamente; comunicam-se por artefato persistido, o que permite rodar, inspecionar e refazer qualquer etapa isoladamente.

**Por canal:** M1, M2, M4, M5, M6, M7. **Uma vez, para todos:** M3, M8, M9.

### M1 · Coleta — *por canal*

- **Entrada:** ID do canal
- **Saída:** `corpus/<canal>/raw/*.json` + manifesto
- **Ferramentas:** [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) (MIT); [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) (Unlicense) para enumerar; [`whisperX`](https://github.com/m-bain/whisperX) (BSD-2) — dependência real desde `_docs/decisions.md#4`
- **Seleciona 30 para o perfil e reserva 4–5 de holdout**, sorteados entre os elegíveis e intocados até o M8. O holdout é o que impede a calibração do verificador de ser circular.
- **Crítico:** preserva o `start_s` de cada chunk. Os timestamps voltam no M7 e no M9.
- **Resolvido — whisperX segue fallback:** o bloqueio de IP das legendas é comportamento normal do endpoint sob coleta em lote, não incidente, e vai se repetir a cada canal — mas o dono do projeto optou por manter legenda como caminho padrão e whisperX como fallback, tratando o bloqueio como esperado em vez de mudar `collect_transcript()`. Ver `_docs/decisions.md#5`.

### M2 · Sentenciação — *por canal*

- **Entrada:** transcrições cruas
- **Saída:** sentenças e janelas
- **Ferramenta:** [`wtpsplit`](https://github.com/segment-any-text/wtpsplit) (MIT), com código de idioma **`en`**
- **Regra de janela:** acumule sentenças até 35 palavras ou 4 sentenças, o que vier primeiro; mínimo de 2
- **Reatribuição de timestamp:** por offset acumulado, nunca por busca de texto — busca falha em silêncio quando uma frase se repete
- **Não faz:** segmentação topical
- **Saíram do projeto:** `TextTiling`, [`textsplit`](https://github.com/chschock/textsplit), [`segeval`](https://github.com/cfournie/segmentation.evaluation)

### M3 · Ontologia — *uma vez, para todos os canais*

A lista fechada de campos e valores. **Não é código; é o ativo intelectual do projeto.**

- **Entrada:** trabalho humano
- **Saída:** `schema/ontologia.vN.json` + `schema/codebook.md`
- **Identificadores em inglês** (`hook`, não `gancho`), porque rótulo, definição e texto anotado precisam estar na mesma língua
- **Seis testes por campo:** observável, fechado, mutuamente exclusivo, agregável, **decidível em janela**, **transferível entre canais**. Os dois últimos são o que mais elimina categorias.
- **Também define** o que faz um bloco terminar. Isso é definição de codebook, não parâmetro de algoritmo.
- **Custo de uma versão nova:** subir de `v1` para `v2` obriga a reanotar todos os corpus já perfilados, senão os perfis deixam de ser comparáveis. Com 5 canais, ~18.000 chamadas. É evento planejado, não ajuste de tarde — e é por isso que esta fase merece semanas.
- **Aviso de processo:** os dois arquivos estão na lista de conflito de `_docs/process.md`. Uma issue só, sem paralelismo.

### M4 · Anotação — *por canal*

- **Entrada:** janelas + ontologia
- **Saída:** anotações por janela
- **Ferramentas:** [`doccano`](https://github.com/doccano/doccano) (MIT) para a referência humana; [`instructor`](https://github.com/567-labs/instructor) (MIT) para saída JSON validada por Pydantic no lote
- **Duas passadas:** humana em 5 vídeos (~200 janelas), automática nos 25 restantes com 3 execuções e voto majoritário
- **Duas proibições no prompt:** não passar `pos_pct` (circularidade) nem os rótulos das janelas anteriores (cascata de erro)
- **Prompt inteiramente em inglês.** Não traduza os rótulos nem na UI do doccano, ou você anota contra um vocabulário e o modelo contra outro.
- **Runner retomável por `window_id`.** São ~3.600 chamadas por canal.

### M5 · Validação — *por canal*

- **Entrada:** anotação automática + gold humano
- **Saída:** run de concordância
- **Ferramentas:** [`simpledorff`](https://github.com/LightTag/simpledorff) ou `krippendorff`
- **Mede no nível de janela**, nunca depois da fusão — a fusão apaga discordâncias e infla o número
- **Reporta matriz de confusão por categoria**, porque o α agregado esconde qual categoria está quebrada
- **Portão principal do sistema.** Abaixo de α = 0,667, o perfil é ruído com aparência de dado. Tem poder de veto sobre o M6.

### M6 · Fusão — *por canal*

- **Entrada:** anotações validadas
- **Saída:** blocos + relatório de fusão
- **Regra:** janelas consecutivas de mesmo `function` formam um bloco. Uma janela isolada cercada dos dois lados pela mesma função é absorvida (suavização), em passada única.
- **Determinística e testável.** Teste unitário obrigatório com os casos de borda.
- **Diagnóstico:** taxa de suavização acima de 15% indica ontologia confusa, não ruído.

### M7 · Agregação — *por canal*

- **Entrada:** blocos e anotações validados
- **Saída:** `perfis/<canal>.perfil.json`
- **Ferramentas:** `pandas`; [`textstat`](https://github.com/textstat/textstat) (MIT); [`faststylometry`](https://pypi.org/project/faststylometry/) opcional
- **Faixas por percentil 20–80**, não mínimo–máximo. Com 30 vídeos, mín. e máx. são quase sempre outliers, e faixas construídas com eles ficam largas demais para reprovar qualquer coisa no M8.
- **Grava `ontology_version`.** Perfis de versões diferentes não são comparáveis, e o código deve recusar compará-los.
- **Preenchimento manual:** `tone_examples` e `forbidden` não se agregam.

### M8 · Geração e verificação — *uma vez, para todos*

- **Entrada:** tema + perfil
- **Saída:** plano, roteiro, relatório de verificação
- **Ferramentas:** `instructor` na direção inversa; verificação em Python puro, sem LLM
- **Duas etapas obrigatórias:** primeiro o plano (blocos vazios com função e alvo de palavras), validado contra o perfil em código; só depois a prosa, bloco a bloco. Gerar o roteiro inteiro em uma chamada sempre produz texto que ignora o perfil.
- **Correção cirúrgica:** critério reprovado reescreve só os blocos afetados, máximo 3 vezes.
- `src/verifica.py` é o script de portão que `_docs/process.md` nomeia no passo 4 da fila de merge.

### M9 · Produção *(opcional, última prioridade)*

- **Ferramentas:** TTS à escolha; [`MoviePy`](https://github.com/Zulko/moviepy) (MIT) ou `ffmpeg-python`
- **Referência de arquitetura:** [`MoneyPrinterTurbo`](https://github.com/harry0703/MoneyPrinterTurbo) (MIT) tem montagem decente e vale forkar. A camada de roteiro dele é um prompt genérico, exatamente o que este projeto substitui.
- **Ordem obrigatória:** locução primeiro.

---

## Fluxo completo

```
   ontologia global (M3) ──────┬──────────────┬──────────────┐
                               │              │              │
        ┌── POR CANAL ─────────┼──────────────┼──────────────┼───────┐
                               ▼              ▼              ▼
canal ─▶ M1 coleta ─▶ M2 sentencia ─▶ M4 anota ─▶ M5 valida ─▶ M6 funde ─▶ M7 agrega
             │                                       │                          │
             │ holdout (4–5)                         │ α ≥ 0,667?               │
             │  reservado                            └── reprova ──┐            │
             │                                                     │            ▼
             │                                                     │     perfil.json
             │       ┌────────────── EXECUÇÃO ──────────────┐      │            │
             │                                                     │            │
             │  tema ─▶ M8 plano ─▶ verifica ─▶ prosa ─▶ verifica ◀─────────────┘
             │                          │            │
             └──────────────────────────┴────────────┴──▶ calibração anticircular
                                                                   │
                                                                   ▼
                                                            M9 produção
```

## Portões de qualidade

O limiar em vigor de cada portão vive em `schema/portoes.json`; a leitura sempre-atual, validada por CI, é a tabela de portões renderizada em `_docs/estado.md` - não repita o número aqui.

| Portão | Onde | Por que existe |
|---|---|---|
| Corpus | M1 | canal pequeno demais ou transcrição ruim não sustenta um perfil |
| Sentenciação | M2 | janela grande demais, com duas funções, ou cortada no meio confunde o anotador antes mesmo de a ontologia existir |
| Ontologia | M3 | categoria demais em "outro"/dúvida é ontologia incompleta |
| Autoconcordância | M4 | codebook vago não sobrevive nem a você mesmo lendo duas vezes |
| **Concordância** | **M5** | **é o portão principal do sistema — abaixo dele o perfil é ruído com aparência de dado** |
| Fusão | M6 | suavizar demais indica ontologia confusa, não ruído |
| Perfil | M7 | perfil malformado ou canal irreconhecível não deveria virar arquivo congelado |
| Roteiro | M8 | fora do escopo desta issue — Issue #13 já reabriu esse portão antes de virar dado |

**Calibração anticircular do M8:** rode o verificador nos vídeos de holdout e depois no corpus. Eles deveriam passar. Se os vídeos reais reprovam, as faixas do perfil estão erradas. Sem holdout, esse teste é circular e não vale nada — daí ele ser reservado já no M1.

---

## Onde cada coisa é persistida

`_docs/decisions.md#1` divide o storage. O critério: **se é lido por humano, revisado em diff e congelado por fase, é arquivo. Se é estado operacional consultável, pode ser tabela.**

| Arquivo versionado | Postgres (conforme a issue definir) |
|---|---|
| `schema/ontologia.vN.json` | manifesto de corpus |
| `schema/codebook.md` | anotações por janela |
| `perfis/<canal>.perfil.json` | runs de concordância |
| `gold/<canal>/` | runs de geração |
| `corpus/<canal>/raw/` | sentenças e janelas derivadas |

Qual entidade vira tabela é decisão da issue que a introduzir, registrada em `decisions.md`. O argumento mais forte para as anotações irem para tabela é operacional: o run do M4 são ~3.600 chamadas e precisa ser retomável por `window_id`.

## Estrutura de pastas

```
roteiros-engine/
├── DECISOES.md                    decisões de produto (do dono)
├── _docs/
│   ├── decisions.md               decisões técnicas — vence este README
│   ├── plano_implementacao.md     as dez fases
│   ├── blueprint.md               levantamento de ferramentas
│   ├── process.md                 squad, worktrees, fila de merge
│   └── team/                      pm · software-engineer · qa-engineer
├── schema/                        ontologia · codebook · perfil.schema · regras_fusao
├── corpus/<canal>/                raw · derivados
├── gold/<canal>/                  anotação humana de referência
├── perfis/                        <canal>.perfil.json
├── src/                           os módulos · db.py
├── migrations/                    Alembic
└── tests/
```

## Convenções

- UTF-8 sem BOM.
- IDs: `<video_id>:s0000` sentença, `:j0000` janela, `:b0000` bloco.
- Tempo em segundos float, relativo ao início do vídeo.
- Campo ausente = não se aplica. Campo `null` = aplica-se mas indeterminado.
- Todo artefato derivado carrega `ontology_version` e `generated_at`.
- Os nomes de campo são os mesmos em arquivo e em tabela, e são em inglês.

## Decisões de projeto

**Por que arquivo e banco, não um ou outro** *(`_docs/decisions.md#1`)*. O valor de abrir qualquer etapa num editor de texto supera a conveniência de query — para os artefatos que humanos leem e revisam. `schema/`, `codebook.md` e `perfis/` continuam arquivo por esse motivo, versionados em git, onde o histórico explica por que cada categoria existe. O estado operacional passou a viver em Postgres porque a isolação por worktree do squad depende de cada worktree possuir um recurso real e descartável.

**Por que uma ontologia só.** Ontologia por canal fragmentaria o vocabulário e mataria a comparabilidade entre perfis, que é o ativo de rodar vários canais. O custo é real e conhecido: uma versão nova obriga a reanotar todos os corpus. É por isso que o M3 recebe semanas e um teste explícito de transferência entre canais.

**Por que o esquema é a fonte da verdade.** Prompt, codebook e código leem `ontologia.vN.json`. Nada de listas duplicadas em prosa dentro de um prompt; é exatamente assim que os sistemas divergem de si mesmos com o tempo. Isso é testável: um teste que compara os `Enum` gerados com o JSON pega a divergência antes de virar dado ruim.

**Por que a janela não sabe onde está.** `pos_pct` é persistido mas não entra no prompt. Se o modelo souber que a janela está a 3% do vídeo, responde `hook` pela posição e não pelo texto, e o perfil confirmaria a estrutura que você mesmo injetou. Circularidade.

**Por que verificação em Python e não por LLM.** Contagem, posição percentual, distribuição, presença de termo proibido: tudo computável e binário. Modelo avaliando a própria saída infla a nota.

**Por que voz não vira regra.** Cadência, humor e ritmo de frase não sobrevivem a virar lista de instruções; viram caricatura. O perfil tem duas metades: a estrutural (faixas numéricas) e a estilística (`tone_examples`, trechos curtos usados como referência). Tratar as duas com o mesmo mecanismo é o erro mais comum.

**Por que estrutura é replicável e redação não.** Ordem de funções, faixas de duração e tipos de evidência são gramática de formato, e formato não é obra. Metáforas assinadas, bordões e formulações específicas são obra. A lista `forbidden` de cada perfil mantém a separação explícita. Ver `politica_editorial.md`.

---

## Glossário

**Ontologia / esquema fechado** — a lista fixa de campos e valores permitidos, global e versionada. O anotador escolhe dela; nunca inventa.

**Codebook** — as definições de cada valor, com exemplos positivos, negativos e regras de desempate. Bilíngue, com o inglês normativo. É o que faz humano e modelo concordarem.

**Sentença** — a menor unidade, produzida pelo `wtpsplit`.

**Janela** — 2 a 4 sentenças consecutivas. É a **unidade de anotação**.

**Bloco** — sequência de janelas consecutivas com a mesma função, produzida por fusão. É a **unidade de análise e de geração**.

**Fusão** — o passo que agrupa janelas em blocos.

**Suavização** — regra que absorve uma janela isolada cercada pela mesma função dos dois lados. Sua taxa é diagnóstico da ontologia.

**Gold standard** — a anotação humana de referência contra a qual a automática é medida.

**Holdout** — 4–5 vídeos reservados fora dos 30 do perfil, para calibrar o verificador sem circularidade.

**Fixture** — corpus usado para validar código, não para gerar perfil. `zenn0009` é o fixture do M1.

**Krippendorff's α** — medida de concordância entre anotadores. ≥ 0,667 é o mínimo aceitável; ≥ 0,8 é bom.

**Perfil** — o arquivo de configuração agregado de um canal.

**Loop** — lacuna de informação aberta no espectador. O perfil rastreia onde abrem e onde fecham.

---

## Licenças das dependências

O projeto é **não comercial** (`DECISOES.md#3`), mas as ferramentas escolhidas são permissivas de qualquer forma (MIT, BSD, Apache-2.0, Unlicense), o que preserva a opção de mudar isso. Três exclusões mantidas:

- `TextMachina` — CC-BY-NC-ND (não comercial, sem derivados)
- `gpt_annotate`, `core-stories` — sem arquivo LICENSE
- `ScreenPy` — licença ambígua e abandonado desde ~2017

Verificar sempre o arquivo LICENSE do repositório, não o README nem fontes secundárias.

`whisperx==3.8.6` (BSD-2-Clause) é dependência real desde `_docs/decisions.md#4`, com o custo de `uv sync` puxar `torch` e as wheels `nvidia-cu12-*` mesmo em uso CPU-only.

---

## Documentos ainda por escrever

`schema/ontologia.v1.json` e `schema/codebook.md` (M3) · `schema/regras_fusao.md` (M6) · `schema/perfil.schema.json` (M7) · `politica_editorial.md` · `LICENCAS.md`
