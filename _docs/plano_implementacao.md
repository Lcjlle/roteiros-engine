# Plano de Implementação — Sistema de Roteiros por Perfil de Canal

**Versão 3.0** · Substitui a v2.0

---

## Precedência

Este documento é **referência, não backlog**. Onde discordar de `_docs/decisions.md` ou de uma issue groomada, ele perde. Ver `_docs/process.md`.

Onde a v3.0 propõe algo que **conflita** com uma decisão registrada, o conflito está marcado com ⚠️ e precisa de entrada nova em `decisions.md` antes de virar issue.

---

## Changelog v2.0 → v3.0

Três mudanças de premissa, todas confirmadas pelo dono do projeto.

**1. Política de idioma explícita.** O corpus e a saída são em **inglês**; a comunicação com humanos é em **PT-BR**. Isso não é detalhe de estilo — determina em que língua cada artefato é escrito, e a mistura errada degrada a anotação. Ver a seção "Política de idioma", que é normativa.

**Consequência que atravessa tudo:** os identificadores da ontologia passam a ser em inglês (`hook`, não `gancho`), porque rótulo, definição e texto anotado precisam estar na mesma língua.

**2. Ontologia global, não por canal.** Uma única `schema/ontologia.vN.json` serve todos os canais. As diferenças entre canais vivem nas distribuições do perfil, não no vocabulário. Isso preserva a comparabilidade entre canais, que é o ativo de rodar vários.

**3. Multi-canal é operação normal, não teste de escala.** A antiga Fase 10 ("segundo canal") deixa de ser prova de conceito e vira o modo de uso do sistema. O primeiro canal deixa de ser "o canal do projeto" e passa a ser **o canal do qual a ontologia é derivada** — o que muda o critério de escolha.

**Consequências de estado:**

- `zenn0009` passa a ser **fixture de validação do M1**, não corpus de perfil. Foi usado para testar a coleta e cumpriu esse papel.
- O ⚠️ do holdout da v2.0 **está resolvido e removido**: com um canal maior, reservam-se 4–5 vídeos fora da seleção dos 30. Sem carvar do corpus do perfil.
- A recalibração PT-BR da Fase 6 passo 4 **deixa de existir**. Corpus em inglês, `textstat` calibrado para inglês, saída em inglês.

**Correção de erro da v2.0:** a Fase 2 mandava passar `pt` ao `wtpsplit`. É `en`.

---

## Política de idioma

**Esta seção é normativa.** A regra em uma frase:

> **Se é lido pela máquina ou entra num prompt, é inglês. Se é lido só por humano, é PT-BR.**

### Inglês, obrigatoriamente

| Artefato | Por quê |
|---|---|
| `schema/codebook.md` — definições, exemplos, regras de desempate | é injetado no prompt de anotação, sobre texto em inglês |
| `schema/ontologia.vN.json` — nomes de campo e valores | viram identificadores de dado e chaves do prompt |
| prompts de anotação e de geração | mesma língua do texto anotado e do texto gerado |
| `tone_examples` e `forbidden` no perfil | são trechos literais do corpus |
| roteiros gerados, em `saidas/` | é o produto |
| identificadores de código: variáveis, funções, colunas, docstrings, nomes de teste | convivem com os identificadores de dado |

### PT-BR

| Artefato | Por quê |
|---|---|
| `README.md`, `_docs/plano_implementacao.md`, `_docs/blueprint.md` | leitura humana |
| `_docs/decisions.md`, `DECISOES.md` | leitura humana |
| `_docs/process.md`, `_docs/team/*` | leitura humana e de agentes que operam em PT-BR |
| corpo de issues, comentários de QA, mensagens de commit | leitura humana |
| prosa dos relatórios de concordância e de fusão | leitura humana |
| mensagens de CLI e log destinadas a você | leitura humana |

Os **números e nomes de campo** dentro de um relatório em PT-BR continuam em inglês, porque são identificadores. Um relatório diz "a função `hook` ficou em 4,2% dos blocos", não "a função gancho".

### Bilíngue, com precedência declarada

**`schema/codebook.md`** é o único artefato bilíngue. Cada entrada tem:

- **definição normativa em inglês** — é o que vai para o prompt
- **glosa em PT-BR**, marcada explicitamente como não normativa — é o que você usa para pensar

> Onde a glosa PT-BR divergir da definição EN, **a definição EN vence**. A glosa não é traduzida automaticamente nem mantida em sincronia por ferramenta; se você alterar a definição, altere a glosa no mesmo commit.

Essa regra precisa estar escrita dentro do próprio `codebook.md`, não só aqui. Divergência silenciosa entre as duas metades é o modo de falha esperado.

### Dívida aceita

Os diretórios já commitados são em português: `corpus/`, `perfis/`, `saidas/`, `schema/ontologia.v1.json`. **Não vale renomear.** Nomes de caminho não entram em prompt nem viram identificador de dado, e o churn de renomear atingiria `process.md`, `decisions.md`, testes e o histórico. Fica registrado como inconsistência conhecida e aceita, para ninguém "consertar" isso depois num commit grande.

---

## Estado das fases

Ver o cabeçalho `**Estado:**` logo abaixo de cada `## Fase N` mais abaixo - fases 0-3 executadas, fases 4-10 intenção, não executada. Não repetido aqui como tabela para não virar uma segunda cópia que pode divergir da primeira.

### Fase 0 resolvida

Os dois itens que a substituição v3.0 abriu além das três decisões
originais estão preenchidos em `DECISOES.md`:

1. **Canal de referência definitivo:** `@MackExplains7` (`DECISOES.md#4`).
   Destrava a Fase 3 — mas só depois que a Fase 1 e a Fase 2 rodarem sobre
   ele; a decisão de qual canal não substitui o corpus real.
2. **Modelo de anotação:** Claude Sonnet 5 (`DECISOES.md#5`). Destrava a
   Fase 5.

**Aplicado nesta substituição:** `DECISOES.md#1` trazia uma afirmação
falsa sobre recalibração de legibilidade e palavras-por-minuto para
português. Corrigida — corpus e saída são em inglês, as métricas se
aplicam diretamente. Ver "Correções aplicadas na substituição oficial
v3.0" mais abaixo.

---

**Decidido:** `@MackExplains7` (`DECISOES.md#4`). Os critérios abaixo são
a referência usada para a escolha e continuam valendo para julgar canais
futuros — a verificação prática deles contra `@MackExplains7` (`yt-dlp
--flat-playlist --dump-json`, contagem real de vídeos, formato) acontece
quando a issue de Fase 1 desse canal rodar, do jeito que aconteceu para
`@Zenn0009` na Issue #1.

## Como escolher o canal de referência

Mudou na v3.0, e foi a decisão mais consequente do grupo — resolvida acima.

Com ontologia global e multi-canal como norma, o primeiro canal não é "o canal do projeto" — é **aquele de que a ontologia será derivada**. Ela vai ser aplicada a todos os outros.

**Critério: o mais representativo do formato que você pretende rodar, não o de melhor desempenho.** Um canal atípico produz uma ontologia que não transfere, e você só descobre no terceiro canal, quando reanotar tudo custa caro.

Requisitos práticos:

- 40 ou mais vídeos longos, para sobrarem 4–5 de holdout depois de selecionar 30 (`zenn0009` tinha 34, o que era apertado)
- formato consistente ao longo do tempo
- inglês
- **de preferência, escolha dois canais do mesmo formato e olhe amostras dos dois antes de congelar a ontologia.** Uma ontologia derivada de um canal só tende a codificar idiossincrasias dele como se fossem estrutura do formato. Não precisa anotar os dois; basta ler ~20 janelas do segundo e conferir se as categorias cobrem.

---

## Princípios que não se negociam

**1. O esquema é a fonte da verdade.** Categorias, campos e valores vivem em `schema/ontologia.vN.json`. Prompt, documentação e código *leem* esse arquivo.

**2. Anotar não é analisar.** O modelo escolhe de uma lista fechada. Se precisou de prosa livre, falta um campo no esquema.

**3. Perfil e execução são processos separados.** O perfil se constrói uma vez, é verificado, vira arquivo. A execução lê o arquivo e nunca o rederiva.

**4. O que dá para medir, mede-se em código.** Julgamento de LLM fica só para o que não tem métrica.

**5. Toda etapa persiste seu resultado e é reexecutável isoladamente.** Onde persiste segue `decisions.md#1`: lido por humano e congelado por fase é arquivo; estado operacional consultável pode ser tabela.

**6. Uma ontologia, muitos perfis.** *(Novo na v3.0.)* A diferença entre canais é numérica, não categórica. Se um canal exigir vocabulário novo, isso é uma versão nova da ontologia aplicada a todos — não um dialeto local.

---

## Custo de uma versão nova da ontologia

Consequência direta do princípio 6, e vale ter na frente antes da Fase 3.

Anotar um canal são ~3.600 chamadas de LLM. Com N canais já perfilados, subir de `v1` para `v2` significa reanotar **todos** os corpus, senão os perfis deixam de ser comparáveis — que era o motivo de ter ontologia global.

Com 5 canais, isso são ~18.000 chamadas e um dia de run. Não é proibitivo, mas é um evento planejado, não um ajuste de tarde.

Três defesas:

- **Cada perfil grava `ontology_version`.** Já está no contrato de dados. Perfil de versão diferente não é comparável e o código deve recusar comparar.
- **Corpus anotado é guardado, não descartado.** Reanotar exige as janelas, não a coleta de novo.
- **A Fase 3 merece o cuidado desproporcional** que este plano já pede. É mais barato passar duas semanas na ontologia do que reanotar cinco canais.

---

## Convenções

- **Encoding:** UTF-8 sem BOM.
- **IDs:** `video_id` é o ID do YouTube. `sent_id` é `<video_id>:s0000`, `janela_id` é `<video_id>:j0000`, `bloco_id` é `<video_id>:b0000`.
- **Tempo:** segundos em float, relativos ao início do vídeo.
- **Nulos:** ausente = não se aplica. `null` = aplica-se mas indeterminado. Nunca omitir silenciosamente.
- **Versionamento:** todo artefato derivado carrega `ontology_version` e `generated_at` (ISO 8601) — ver `README.md`, Convenções. Os nomes em português (`versao_ontologia`/`gerado_em`) nunca existiram nos artefatos reais, só nesta frase.
- **Idioma:** ver a seção normativa acima.

---

## Contratos de dados

Forma lógica, independente de storage. Se a entidade virar tabela, os campos são colunas; se ficar em arquivo, são chaves. **Os nomes são os mesmos nos dois casos e são em inglês.**

### Vídeo bruto — `corpus/<canal>/raw/<video_id>.json`

```json
{
  "video_id": "abc12345678",
  "channel_id": "...",
  "title": "...",
  "published_at": "2024-03-12",
  "duration_s": 612.4,
  "language": "en",
  "source": "caption|whisperx",
  "chunks": [{"start_s": 0.0, "dur_s": 3.2, "text": "..."}],
  "collected_at": "2026-08-28T14:00:00Z"
}
```

### Sentença

```
sent_id · video_id · idx · start_s · end_s · text · n_words
```

### Janela — a unidade de anotação

```
window_id · video_id · idx · sent_ids[] · start_s · end_s
text · n_words · n_sentences · pos_pct
```

`pos_pct` = `start_s / duration_s`. **Persistido, nunca enviado ao prompt.** Ver Fase 5A.

### Anotação de janela

```
window_id · function · loop · scale · evidence_type · density
votes{} · consensus · annotator · ontology_version · annotated_at
```

### Bloco — derivado por fusão

```
block_id · video_id · idx · window_ids[] · function
start_s · end_s · n_windows · n_words
pos_start_pct · pos_end_pct · smoothed
```

---

## Fase 0 — Decisões

**Estado:** executado

**Decididas:** duração-alvo (10–12 min), uso não comercial, canal-fixture usado para validar a coleta (`@Zenn0009`), canal de referência definitivo (`@MackExplains7`, `DECISOES.md#4`) e modelo de anotação (Claude Sonnet 5, `DECISOES.md#5`).

**Correção já aplicada em `DECISOES.md`:** o item 1 afirmava que métricas precisam de recalibração para PT-BR. Corrigido nesta substituição — corpus e saída são em inglês, `textstat` e as métricas de ritmo se aplicam diretamente. A comunicação do projeto com humanos continua em PT-BR — ver a política de idioma acima.

---

## Fase 1 — Coleta

**Estado:** executado

Código implementado e validado contra o canal-fixture `zenn0009` (30 vídeos: 21 legenda, 9 whisperX). Ver `decisions.md#3` e `#4`.

**O que muda na v3.0:** a Fase 1 deixa de ser "rodou uma vez" e passa a ser **rodada uma vez por canal**. Quatro ajustes decorrem disso.

### 1. Reservar holdout na seleção

Selecione 30 para o perfil e **reserve 4–5 vídeos elegíveis fora dessa seleção**, marcados `holdout` no manifesto. Não toque neles até a Fase 8.

Motivo: o portão da Fase 8 exige que vídeos reais do canal passem no verificador. Se o verificador for calibrado contra os mesmos vídeos que geraram o perfil, o teste passa sempre e não vale nada.

**Sorteie o holdout entre os elegíveis, não pegue a cauda.** Pegar os 4 de menor view count torna o holdout um teste de material atípico, o que enviesa a calibração.

Isso exige que o canal tenha ~40 vídeos longos, e é por isso que esse número entrou no critério de escolha.

### 2. Resolvido: whisperX segue fallback, não vira padrão

O bloqueio de IP das legendas não foi acidente; é o comportamento normal do endpoint sob coleta em lote, e não cedeu com espera (`decisions.md#3`, `#4`). Com N canais, você vai bater nele toda vez.

`decisions.md#4` já mediu a alternativa: 99,2% e 99,64% de concordância lexical entre whisperX e legenda, nos dois extremos de duração, com as diferenças em homófonos e grafia de números. O endpoint de áudio nunca foi bloqueado.

A proposta era inverter a lógica de `collect_transcript()` — whisperX como caminho padrão, legenda como atalho oportunista. **O dono do projeto recusou**: legenda continua padrão, whisperX continua fallback. Quando um canal novo bater no mesmo bloqueio de IP, a resposta é a mesma da Fase 1 do `zenn0009`: transcrever os vídeos que falharam localmente com whisperX, não mudar o código. Ver `decisions.md#5`.

**Consequência:** as duas lições de `decisions.md#4` continuam requisito de código só quando whisperX é de fato usado, não como padrão de todo run: `batch_size` parametrizado (4 em GPU de 6GB) e **um subprocesso por vídeo**, porque a memória do modelo anterior não é liberada no mesmo processo.

### 3. Homogeneidade de fonte

Se o corpus misturar legenda e whisperX — o caso normal, dado o item 2 acima —, a checagem de contaminação da Fase 6 é obrigatória para todo canal futuro, não só para `zenn0009`.

### 4. Seleção em canal jovem

`decisions.md#1` documenta o recuo da regra dos 6 meses. Vale registrar o efeito residual: num canal onde todos os vídeos têm menos de 6 meses, ranquear por views absolutas favorece os mais antigos do conjunto, que tiveram mais tempo de acumular. Se o canal definitivo for maduro, o problema não aparece. Se for jovem de novo, considere views por dia desde a publicação.

**Portão da Fase 1:** 30 linhas `profile` no manifesto + 4–5 linhas `holdout`; nenhuma transcrição abaixo de 60% da contagem de palavras esperada para a duração (~150 palavras/minuto em inglês).

---

## Fase 2 — Sentenciação

**Estado:** executado

> **Executado** contra `@MackExplains7` (`_docs/decisions.md#10`-`#17`; portão medido em `corpus/mackexplains7/fase2_gate.json`, 3.103 janelas, `passed: true`). Não dependia da ontologia nem do canal definitivo, e foi por isso que pôde rodar antes deles.

**Objetivo:** transformar texto corrido em sentenças, e agrupá-las em janelas de anotação.

**Ferramenta:** `wtpsplit` (MIT). Só ela. `TextTiling`, `textsplit` e `segeval` saíram do projeto na v2.0.

### Passos

**1. Sentenças.** Modelo SaT do `wtpsplit` sobre o texto corrido, com código de idioma **`en`**. Legenda automática do YouTube não tem pontuação confiável; saída de whisperX vem pontuada. Rode o mesmo caminho nos dois para não criar duas classes de sentença no corpus.

**2. Reatribua timestamps.** Cada sentença herda o `start_s` do chunk onde seu primeiro caractere caiu e o `end_s` do chunk onde terminou. **Use offsets acumulados, nunca busca por texto** — busca falha em silêncio quando uma frase se repete no vídeo.

**3. Janelas.** Agrupe sentenças consecutivas, sem sobreposição:

> Acumule sentenças até **35 palavras** ou **4 sentenças**, o que vier primeiro. Mínimo de 2 sentenças, exceto a última do vídeo.

Ajuste o limiar **uma vez, para o corpus inteiro**, e registre em `decisions.md`. Nunca por vídeo.

**4. Calcule `pos_pct`** e persista.

### Por que não segmentar por tópico aqui

TextTiling mede coesão lexical, proxy de mudança de assunto. A ontologia precisa de mudança de função. São sinais diferentes e frequentemente ortogonais, e há dependência circular: a fronteira funcional só é conhecida depois da rotulagem.

Se a janela de 2–4 sentenças um dia se mostrar má unidade, a contingência **não** é TextTiling — é EDU/RST (`isanlp_rst`), porque EDUs são unidades funcionais de discurso.

### Portão da Fase 2

| # | Critério | Limite | Como medir |
|---|---|---|---|
| 1 | janelas com duas funções narrativas distintas | ≤ 5 em 50 | amostra aleatória com semente fixa, de 2 vídeos, julgada por humano |
| 2 | sentenças cortadas no meio de oração | 0 na mesma amostra | mesma amostra, humano |
| 3 | janelas fora da faixa estrutural | 0 | automático, nos 30: nenhuma > 60 palavras; nenhuma < 2 sentenças exceto a última de cada vídeo; 25–60 janelas por vídeo |

A semente da amostra vai na issue, para que QA meça a mesma amostra que o engineer.

O critério 1 exige julgar "função narrativa" antes da ontologia existir. Isso é intencional e suficiente: você não precisa da lista fechada para perceber que uma janela mudou de assunto e de propósito no meio. Se ficar ambíguo demais, é sinal de que o limiar de palavras está alto.

### Issues sugeridas

- **F2-a** — `src/sentencia.py`: wtpsplit (`en`) sobre os raw, reatribuição por offset. Critério: portão 3 passa.
- **F2-b** — `src/janelas.py`: agrupamento determinístico e `pos_pct`. Depende de F2-a; onda separada.
- **F2-c** — script de amostragem com semente e o relatório que o QA preenche.

**Tempo estimado:** 1 dia.

---

## Fase 3 — A ontologia autoral

**Estado:** executado

> **Executado** sobre o canal de referência definitivo, `@MackExplains7` (`DECISOES.md#4`, Issue #11, `main@4c3e165`). Os exemplos do codebook saem do corpus dele — a decisão de qual canal não substitui o corpus real.

**Esta é a fase que decide o projeto**, e na v3.0 ela decide mais do que antes: a ontologia é global e vai ser aplicada a todos os canais futuros.

`schema/ontologia.v1.json` e `schema/codebook.md` estão na lista de conflito de `process.md`. **Uma issue só, sem paralelismo.**

### Os seis testes de cada campo

1. **Observável** — decidível olhando o texto, sem saber o assunto.
2. **Fechado** — conjunto finito e enumerado.
3. **Mutuamente exclusivo** — se dois valores podem ser ambos verdadeiros, são dois campos.
4. **Agregável** — faz sentido contar ou tirar média entre 30 vídeos.
5. **Decidível em janela** — decidível em 2–4 sentenças mais contexto anterior. Categorias que exigem ver o vídeo inteiro não sobrevivem; reformule em termos locais ou corte.
6. **Transferível entre canais** — novo na v3.0. A categoria descreve o *formato* ou aquele canal específico? Se você não consegue imaginá-la aplicada a outro canal do mesmo gênero, ela é idiossincrasia e vai atrapalhar quando o segundo perfil chegar.

### Proposta de partida

Identificadores em inglês. A coluna PT é glosa, não é o valor armazenado.

**`function`** (obrigatório, valor único):

| valor (EN) | glosa PT-BR (não normativa) |
|---|---|
| `hook` | abre lacuna de informação; não entrega nada ainda |
| `promise` | declara o que o vídeo vai entregar |
| `context` | informação necessária antes do argumento |
| `escalation` | aumenta a aposta, a estranheza ou a urgência |
| `mechanism` | explica como algo funciona |
| `evidence` | apresenta dado, estudo ou caso concreto |
| `objection` | levanta contra-argumento ou limitação |
| `resolution` | fecha uma lacuna aberta antes |
| `implication` | estende para consequências maiores |
| `transition` | apenas move de um tópico a outro |
| `cta` | pede ação ao espectador |

**`loop`**: `opens` · `closes` · `holds` · `none`

**`evidence_type`** (só quando `function=evidence`): `study` · `statistic` · `case` · `analogy` · `authority`

**`scale`**: `individual` · `human` · `planetary` · `cosmic` · `abstract`

**`density`** (inteiro 0–2): conceitos novos introduzidos na janela.

Cinco a sete campos bastam.

### O codebook bilíngue

Para cada valor:

- **Definition** (EN, normativa, uma frase operacional)
- **Two positive examples** (EN, do corpus real)
- **One negative example** (EN) — o caso que parece mas não é, com uma frase dizendo por quê
- **Tie-breaker** (EN) contra o valor vizinho mais confundível
- **Glosa PT-BR** — marcada `<!-- não normativo -->`, para você pensar

O cabeçalho do `codebook.md` declara a precedência: onde a glosa divergir da definição, a definição EN vence.

O exemplo negativo e o tie-breaker são o que mais elevam a concordância na Fase 5. São a parte trabalhosa e a que paga.

### Formato de `schema/ontologia.v1.json`

```json
{
  "version": "v1",
  "created_at": "2026-09-XX",
  "annotation_unit": "window",
  "corpus_language": "en",
  "fields": [
    {
      "name": "function",
      "type": "categorical",
      "required": true,
      "values": ["hook","promise","context","escalation","mechanism",
                 "evidence","objection","resolution","implication",
                 "transition","cta"]
    },
    {
      "name": "evidence_type",
      "type": "categorical",
      "required": false,
      "condition": "function == 'evidence'",
      "values": ["study","statistic","case","analogy","authority"]
    },
    {"name": "density", "type": "integer", "required": true, "min": 0, "max": 2}
  ]
}
```

Prompt e classes Pydantic são **gerados a partir deste arquivo**. Um teste que compara os `Enum` gerados com o JSON pega divergência antes de virar dado ruim.

### Passos

1. Escreva a v0 a partir da proposta.
2. **Teste de cobertura:** classifique à mão as janelas de 1 vídeo. Conte quantas caíram em "outro" ou em dúvida.
3. Revise. Repita com um segundo vídeo.
4. **Teste de transferência:** leia ~20 janelas de um segundo canal do mesmo formato e confira se as categorias cobrem. Não precisa anotar; precisa não encontrar buracos óbvios.
5. Escreva o `codebook.md` completo, bilíngue.
6. Congele.

**Portão da Fase 3:** em 2 vídeos classificados à mão, **< 10% das janelas** em "outro" ou dúvida genuína. Se não passar, simplifique.

### Issues sugeridas

- **F3-a** — escrever `ontologia.v1.json` + `codebook.md` (humana, dono do projeto, não paralelizável).
- **F3-b** — `src/schema_loader.py`: carregar ontologia, gerar `Enum` Pydantic, teste de consistência JSON↔Enum.
- **F3-c** — script que mede o portão.

**Tempo estimado:** 1–2 semanas.

---

## Fase 4 — Gold standard

**Estado:** intenção, não executado

**Ferramenta:** `doccano` (MIT).

O ⚠️ do holdout da v2.0 **saiu**: o split continua 5 gold + 25 batch, e o holdout vem de fora dos 30 (Fase 1).

### Passos

1. Projeto de **classificação de texto** no doccano (a unidade já vem segmentada).
2. Importe as janelas dos 5 vídeos `gold`, com `window_id` como metadado. **Os rótulos na interface são os identificadores em inglês** — resista a traduzir a UI, ou você anota contra um vocabulário e o modelo contra outro.
3. Rótulos gerados de `ontologia.v1.json`. Se a ferramenta não suportar múltiplos campos por item, um projeto por campo.
4. Anote os 5 com o codebook aberto.
5. Espere 48h e **reanote 1 vídeo sem consultar a primeira anotação**.
6. Persista em `gold/<canal>/`.

### Armadilhas

- Não anote os 5 de uma sentada. Cansaço vira ruído sistemático, pior que ruído aleatório porque não se cancela na média.
- Anote na ordem do vídeo. A função de uma janela depende do que veio antes.

**Portão da Fase 4:** autoconcordância (Krippendorff's α) **≥ 0,8**, por campo. Se você não bate 0,8 consigo mesmo, nenhum modelo vai bater, e o codebook está vago.

**Tempo estimado:** 3–4 dias.

---

## Fase 5 — Anotação, fusão e validação

**Estado:** intenção, não executado

**Ferramentas:** `instructor` (MIT) sobre Pydantic; `simpledorff` ou `krippendorff`.

### 5A — Anotação

**1. Classes Pydantic geradas da ontologia** (F3-b).

**2. Prompt montado do codebook**, todo em inglês:
- **System:** papel do anotador + definitions, positive/negative examples, tie-breakers.
- **User:** as **3 janelas anteriores** (só texto, sem rótulos) como contexto, depois a janela a classificar.
- **Output:** um objeto. Teste um campo por chamada vs. todos juntos; separado costuma dar α melhor e custar mais.

**3. Não passe `pos_pct` no prompt.** Se o modelo sabe que a janela está a 3% do vídeo, responde `hook` pela posição e não pelo texto, e o perfil confirmaria a estrutura que você injetou. Circularidade.

**4. Não passe os rótulos das janelas anteriores.** Cascata de erro, e o voto majoritário perde sentido porque as execuções deixam de ser independentes.

**5.** `temperature = 0`, **3 execuções** por janela, voto majoritário. Sem maioria → `consensus: false` → revisão manual. Essas janelas costumam apontar categoria mal definida.

**Custo:** 25 vídeos × ~40 janelas × 3 ≈ 3.000 chamadas, mais ~600 nos gold para validação. **~3.600 por canal.** Aplica-se a regra de polling com teto de `process.md`. **O runner precisa ser retomável por `window_id`** — uma interrupção no meio não pode custar o run inteiro. É o argumento mais forte para as anotações irem para tabela.

### 5B — Validação

**Antes de processar os 25.** Rode nos 5 gold e meça.

1. **α por campo, no nível de janela.** Medir depois da fusão infla o número, porque a fusão apaga discordâncias.
2. **Matriz de confusão por categoria.** O α agregado esconde qual categoria está quebrada.
3. **Registre o run** (modelo, versão da ontologia, data, α por campo).

**Portão da Fase 5 — o mais importante do plano:** **α ≥ 0,667 por campo, no nível de janela.**

Se um campo não passar: (1) reescreva definição e tie-breaker, reanote — duas tentativas; (2) funda os dois valores que se confundem; (3) remova o campo.

Um campo não confiável contamina o perfil em silêncio, e você descobre meses depois sem saber por quê.

### 5C — Fusão

**Regra:** janelas consecutivas com o mesmo `function` formam um bloco.

**Suavização** (escrever em `schema/regras_fusao.md` antes de rodar):

> Uma sequência de comprimento 1 cercada dos dois lados por sequências de comprimento ≥ 2 com a **mesma** função é absorvida pelos vizinhos. Passada única, esquerda para direita. Sequências de comprimento ≥ 2 nunca são suavizadas. Janelas com `consensus: false` não disparam suavização.

Exemplo: `mechanism, mechanism, evidence, mechanism, mechanism` → a `evidence` isolada é absorvida.
Contraexemplo: `mechanism, evidence, evidence, mechanism` → nada muda; três blocos.

Determinística e com **teste unitário obrigatório**, incluindo os casos de borda (início e fim de vídeo, sem vizinho dos dois lados).

**Portão 5C:** taxa de suavização **≤ 15%**. Acima disso é ontologia confusa, não ruído.

### Issues sugeridas

- **F5-a** — `src/anota.py`: runner retomável, 3 execuções, voto majoritário.
- **F5-b** — `src/valida.py`: α por campo, matriz de confusão, persistência do run.
- **F5-c** — validação nos gold e medição do portão. **Bloqueia F5-d.**
- **F5-d** — anotação em lote dos 25.
- **F5-e** — `src/funde.py` + `regras_fusao.md` + testes.

**Tempo estimado:** 1 a 1,5 semana **por canal**.

---

## Fase 6 — Agregação do perfil

**Estado:** intenção, não executado

**Ferramentas:** `pandas`; `textstat` (MIT); `faststylometry` opcional.

**A recalibração PT-BR da v2.0 saiu.** Corpus e saída em inglês; `textstat` se aplica diretamente.

### Estrutura de `perfis/<canal>.perfil.json`

```json
{
  "channel_id": "...",
  "ontology_version": "v1",
  "generated_at": "2026-10-XXT12:00:00Z",
  "corpus": {"n_videos": 30, "n_windows": 1187, "n_blocks": 412,
             "sources": {"caption": 21, "whisperx": 9}},
  "annotator": {"model": "...", "alpha_by_field": {"function": 0.71}},

  "structure": {
    "typical_sequence": ["hook","promise","context","escalation","mechanism",
                         "evidence","objection","resolution","implication","cta"],
    "frequent_variants": [["hook","context","promise"]],
    "function_distribution": {"mechanism": [0.22, 0.31], "evidence": [0.10, 0.18]},
    "position_pct": {"hook": [0.00, 0.06], "first_resolution": [0.28, 0.36]},
    "blocks_per_video": [11, 18],
    "windows_per_block": {"mechanism": [2, 5], "transition": [1, 2]}
  },

  "pacing": {
    "words_per_block": {"mechanism": [60, 140]},
    "words_per_minute": [145, 168],
    "density_by_third": [[0.8,1.4],[1.1,1.8],[0.6,1.2]]
  },

  "loops": {"opened_per_video": [3, 6], "mean_distance_pct": 0.22,
            "closure_required": true},

  "evidence": {"type_distribution": {"statistic": [0.3,0.5], "case": [0.2,0.4]},
               "blocks_per_video": [3, 7]},

  "style": {
    "readability": {"metric": "flesch_reading_ease", "range": [52, 66]},
    "words_per_sentence": [12, 19],
    "scale_trajectory": {
      "first_third": {"human": [0.50, 0.65], "individual": [0.15, 0.25], "planetary": [0.10, 0.20], "abstract": [0.02, 0.08]},
      "middle_third": {"human": [0.75, 0.85], "individual": [0.10, 0.18], "abstract": [0.02, 0.06]},
      "final_third": {"human": [0.40, 0.55], "abstract": [0.20, 0.32], "individual": [0.05, 0.12], "planetary": [0.08, 0.15]}
    }
  },

  "tone_examples": {"hook": ["<short literal excerpt>"], "mechanism": ["..."]},
  "forbidden": ["<signature metaphor>", "<catchphrase>"],

  "diagnostics": {"smoothing_rate": 0.07,
                  "confused_pairs": {"escalation|context": 0.04}}
}
```

### Passos

1. Agregue a partir de blocos e anotações validados.

2. **Faixas por percentil 20–80**, não mínimo–máximo. Com 30 vídeos, mín. e máx. são quase sempre outliers, e faixas construídas com eles ficam largas demais para reprovar qualquer coisa na Fase 8.

3. **Cheque contaminação por fonte**, se o corpus misturar legenda e whisperX — o caso normal, já que whisperX segue fallback e não padrão (`decisions.md#5`). `decisions.md#4` mediu 99%+ de concordância lexical, mas as diferenças eram grafia de números e homófonos — e grafia afeta `readability` e `words_per_sentence`. Compare as métricas de `style` dos dois subconjuntos antes de fechar. Este passo é obrigatório para todo canal, não opcional.

4. **Preencha `tone_examples` e `forbidden` à mão.** São as duas metades que não se agregam. `tone_examples`: 2–3 trechos curtos por função, escolhidos por você. Voz se transmite por exemplo; virar regra vira caricatura.

5. Valide contra `schema/perfil.schema.json`.

**Portão da Fase 6:** schema valida **e** você lê o perfil e reconhece o canal nele. O segundo critério é subjetivo de propósito e é do dono, não do QA.

**Tempo estimado:** 3–4 dias.

---

## Fase 7 — Motor de geração

**Estado:** intenção, não executado

**1. Plano antes da prosa.** A primeira chamada produz blocos vazios:

```json
{"idx":0,"function":"hook","scale":"human","density":1,
 "loop":"opens","target_words":70,
 "objective":"what this block should change in the viewer's understanding"}
```

`objective` é a única saída em prosa livre do sistema, e é em inglês como o resto do prompt.

**2. Valide o plano contra o perfil em código** antes de escrever prosa. Corrigir um plano custa uma chamada; corrigir um roteiro custa vinte.

**3. Escreva bloco a bloco.** Uma chamada por bloco, recebendo o plano, os blocos já escritos, o alvo de palavras e a lista `forbidden`.

**4. Voz vem de exemplo.** 2–3 entradas de `tone_examples` **da mesma função**, marcadas como referência de tom e não de conteúdo.

**A armadilha central:** gerar o roteiro inteiro em uma chamada. Sempre produz texto que ignora o perfil, porque o perfil é restrição fraca comparado ao prior de "como se escreve um roteiro".

**Tempo estimado:** 1 semana.

---

## Fase 8 — Verificador automático

**Estado:** intenção, não executado

**Python puro, sem LLM.**

| # | Critério | Fonte no perfil |
|---|---|---|
| 1 | distribuição de funções | `structure.function_distribution` |
| 2 | número de blocos | `structure.blocks_per_video` |
| 3 | posição das funções-chave | `structure.position_pct` |
| 4 | todo loop fecha | `loops.closure_required` |
| 5 | distância de fechamento | `loops.mean_distance_pct` |
| 6 | palavras por bloco | `pacing.words_per_block` |
| 7 | contagem total ±10% | `DECISOES.md` |
| 8 | termos proibidos (busca literal e por lema) | `forbidden` |
| 9 | legibilidade | `style.readability` |
| 10 | densidade por terço | `pacing.density_by_third` |

O critério 8 volta a ser busca literal, porque corpus e saída são a mesma língua.

Saída: relatório com aprovado/reprovado **e o valor medido**. O valor medido é o que permite depurar.

**Loop de correção:** reescreve **só os blocos afetados**, máximo 3 tentativas. Depois disso, regenera da Fase 7 passo 1.

**Calibração anticircular:** rode nos 4–5 vídeos de holdout reservados na Fase 1, depois no corpus. Eles deveriam passar. **Se os vídeos reais do canal reprovam no próprio verificador, as faixas do perfil estão erradas** — provavelmente mín–máx em vez de percentis.

`src/verifica.py` é o script de portão que `process.md` nomeia no passo 4 da fila de merge.

**Portão:** ≥ 90% dos critérios.

**Tempo estimado:** 3–5 dias.

---

## Fase 9 — Produção do vídeo

**Estado:** intenção, não executado

**Só quando a Fase 8 estiver estável por vários roteiros.**

**Ordem obrigatória: locução primeiro.** O áudio define a duração real; imagens cronometradas antes disso desperdiçam dinheiro.

1. **TTS** → áudio + duração real por bloco.
2. **Alinhamento** com `whisperX` se precisar de timing por palavra. As lições de `batch_size` e subprocesso de `decisions.md#4` valem aqui.
3. **Imagens** — prompts derivados dos blocos. Comece gerando o pacote e rodando manualmente.
4. **Montagem** com `MoviePy` (MIT) ou `ffmpeg-python`.

**Tempo estimado:** 1–2 semanas.

---

## Fase 10 — Operação multi-canal

**Estado:** intenção, não executado

> **Reenquadrada na v3.0.** Não é mais teste de escala; é o modo normal.

Para cada canal novo: Fases 1, 2, 4, 5 e 6, **sem tocar em `src/`**. Se precisar mudar código, algo que deveria ser parâmetro virou premissa.

**A ontologia não muda por canal.** As Fases 3, 7, 8 e 9 são feitas uma vez e servem todos.

**Sinais de que a ontologia não transferiu:** taxa de suavização > 15%; α < 0,667 em algum campo; muitas janelas em dúvida.

Nesse caso, avalie se é (a) ontologia insuficiente — então `v2` **aplicada a todos, com reanotação de todos os corpus**; ou (b) canal fora do formato — então o canal sai, não a ontologia entra. A opção (b) é mais frequente do que parece, e muito mais barata.

**Regra de comparabilidade:** perfis com `ontology_version` diferentes não são comparáveis, e o código deve recusar compará-los em vez de produzir número errado.

---

## Portões de qualidade, em uma tabela

O limiar em vigor de cada portão vive em `schema/portoes.json`; a leitura sempre-atual, validada por CI contra esse arquivo, é a tabela de portões renderizada em `_docs/estado.md` - não repita o número aqui, esta tabela existe só para orientar por que cada portão existe.

| Fase | Portão | Por que existe |
|---|---|---|
| 1 | Corpus coletado (linhas `profile`/`holdout`, cobertura de palavras) | canal pequeno demais ou transcrição ruim não sustenta um perfil |
| 2 | Estrutura das janelas de anotação | janela grande demais, com duas funções, ou cortada no meio confunde o anotador antes mesmo de a ontologia existir |
| 3 | Cobertura da ontologia | categoria demais em "outro"/dúvida é ontologia incompleta |
| 4 | Autoconcordância humana | codebook vago não sobrevive nem a você mesmo lendo duas vezes |
| **5** | **Concordância modelo × humano** | **é o portão principal do sistema — abaixo dele o perfil é ruído com aparência de dado** |
| 5C | Taxa de suavização da fusão | suavizar demais indica ontologia confusa, não ruído |
| 6 | Schema válido + reconhecimento do dono | perfil malformado ou canal irreconhecível não deveria virar arquivo congelado |
| 8 | Critérios do verificador | fora do escopo desta issue — Issue #13 já reabriu esse portão antes de virar dado |

---

## Riscos e mitigação

| Risco | Sinal | O que fazer |
|---|---|---|
| Ontologia colada no primeiro canal | α despenca no segundo canal | teste de transferência da Fase 3 passo 4 |
| Versão nova da ontologia | precisa reanotar N canais | orçar como evento; guardar corpus anotado |
| Ontologia subjetiva demais | α trava abaixo de 0,5 | menos campos, definições mais operacionais |
| Categoria não decidível em janela | α baixo só nela | reformular em termos locais ou cortar |
| Circularidade na anotação | perfil limpo demais | conferir se `pos_pct` vazou para o prompt |
| Verificador circular | tudo passa na Fase 8 | holdout de fora dos 30 |
| Codebook divergindo entre EN e PT | anotação não bate com o que você espera | EN é normativo; glosa no mesmo commit |
| Bloqueio de IP recorrente | 429 em todo canal novo | esperado (`decisions.md#5`): transcrever localmente com whisperX os vídeos que falharem |
| Corpus de duas fontes | métricas de estilo divergem | normalizar antes de agregar |
| Run interrompido | 3.600 chamadas perdidas | runner retomável por `window_id` |
| Roteiro passa e é chato | você não assistiria | verificador cobre estrutura, não voz |

---

## O que NÃO fazer

- **Não misture idiomas dentro de um prompt.** Codebook, texto e rótulo na mesma língua.
- **Não traduza os identificadores da ontologia.** Nem na UI do doccano.
- **Não crie ontologia por canal.** Mata a comparabilidade, que é o ativo de rodar vários.
- **Não reintroduza segmentação topical.** A contingência é EDU/RST.
- **Não passe `pos_pct` nem rótulos anteriores no prompt de anotação.**
- **Não meça α depois da fusão.**
- **Não use o modelo mais caro para anotar.**
- **Não construa a Fase 9 primeiro.**
- **Não compare perfis de versões diferentes de ontologia.**

---

## Correções aplicadas na substituição oficial v3.0 (2026-09-02)

`README.md`, `_docs/blueprint.md` e este arquivo foram substituídos pelo
conteúdo das versões v3.0. As correções que a v3.0 apontava como pendentes
em outros documentos foram aplicadas no mesmo commit:

| Arquivo | Trecho antigo | Trecho novo |
|---|---|---|
| `DECISOES.md` §1, último parágrafo | afirmava que legibilidade e wpm precisam de recalibração para PT | corpus e saída em inglês; métricas se aplicam diretamente; ver política de idioma |
| `_docs/team/pm.md` (l.12) | `Do not soften "Pk <= 0.4" into...` | `Do not soften "<= 5 de 50 janelas com duas funções" into...` |
| `_docs/task-template.md` (l.11) | `(e.g. "Pk <= 0.4 against the 3-video gold" or` | `(e.g. "<= 5 de 50 janelas com duas funções, semente 42" or` |
| `_docs/process.md` (l.116) | `1.350 chamadas de LLM (Fase 5)` | `~3.600 chamadas de LLM (Fase 5)` |
| `README.md` na main | `Estado: Planejamento. Nada implementado ainda.` | conteúdo do README v3.0 |

---

## Próximo passo

Fases 0, 1, 2 e 3 concluídas. A Fase 1 rodou contra os dois canais (`_docs/decisions.md#3`, `#4`, `#9`); a Fase 2 fechou o portão inteiro contra `@MackExplains7` (critérios 1/2 por julgamento humano na Issue #10, 5 de 50 e 0 de 50, depois da correção de sentenciação da Issue #9; critérios 3a/3b/3c/3d automáticos em `corpus/mackexplains7/fase2_gate.json`, 30 vídeos, 3.103 janelas, `passed: true`); e a Fase 3 fechou o portão de cobertura sobre o mesmo canal (Issue #11, `main@4c3e165`; `corpus/mackexplains7/fase3_gate.json`, 205 janelas, 0 em "outro"/dúvida contra o teto de 20).

**Próxima onda:** a Fase 4 — Gold standard. Nenhuma issue existe ainda para ela.

**Fora da onda, sem bloquear a Fase 4:** Issue #6 (Fase 8 — métricas de perfil por taxa/minuto) e Issue #5 (dívida de dev-infra). A #5 toca `_docs/decisions.md` e `_docs/process.md`, ambos na lista de conflito.
