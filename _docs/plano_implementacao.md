# Plano de Implementação — Sistema de Roteiros por Perfil de Canal

**Versão 1.0** — plano de trabalho, não especificação final. Espera-se que a Fase 3 mude o resto.

---

## Como usar este plano

Dez fases. Cada uma tem **objetivo, ferramentas, passos, entregável e portão de saída**. O portão é a condição objetiva para avançar — se não passar, você volta e corrige, não segue em frente. Essa disciplina é a diferença entre o seu sistema e os prompts que você já descartou.

Fases 0 a 6 constroem o **perfil**. Fases 7 a 9 constroem a **execução**. A Fase 10 testa se a separação realmente funciona.

Não pule a Fase 3. Ela é a única parte que não pode ser terceirizada para ferramenta ou modelo, e é a que determina a qualidade de tudo depois.

---

## Princípios que não se negociam

Se algum passo do plano contradisser um destes, o princípio ganha.

**1. O esquema é a fonte da verdade.** Categorias, campos e valores permitidos vivem em um arquivo JSON versionado. Prompt, documentação e código *leem* esse arquivo. Nada de listas duplicadas em prosa dentro de um prompt — é assim que os sistemas divergem.

**2. Anotar não é analisar.** O modelo escolhe de uma lista fechada. Nunca "descubra os padrões deste roteiro". Se você precisou de prosa livre, é sinal de que falta um campo no esquema.

**3. Perfil e execução são processos separados.** O perfil se constrói uma vez, é verificado por você, e vira arquivo. A execução lê o arquivo e nunca o rederiva. Se você se pegar reanalisando o canal no meio da geração, a arquitetura quebrou.

**4. O que dá para medir, mede-se em código.** Contagem, posição percentual, distribuição, presença de fonte, lista de termos proibidos — tudo isso é Python, não julgamento de LLM. Julgamento de modelo fica só para o que não tem métrica.

---

## Estrutura do projeto

```
roteiro-engine/
├── schema/
│   ├── ontologia.v1.json          # a lista fechada (Fase 3)
│   ├── codebook.md                 # definições em prosa p/ humanos e p/ prompt
│   └── perfil.schema.json          # formato do arquivo de perfil
├── corpus/
│   └── <canal_id>/
│       ├── raw/                    # transcrições cruas + metadados
│       ├── segmentado/             # JSONL, 1 segmento por linha
│       └── anotado/                # JSONL com rótulos
├── perfis/
│   └── <canal_id>.perfil.json      # saída da Fase 6
├── gold/
│   └── <canal_id>/                 # anotação humana de referência
├── src/
│   ├── coleta.py
│   ├── segmenta.py
│   ├── anota.py
│   ├── valida.py                   # concordância
│   ├── agrega.py
│   ├── gera.py
│   └── verifica.py                 # portão automático do output
└── saidas/
    └── <video_id>/
```

Use `git` desde o primeiro dia, mesmo sozinho. O histórico do `schema/` é o que te deixa entender por que uma categoria existe.

---

## Fase 0 — Decisões antes de escrever código

**Objetivo:** eliminar as três ambiguidades que travariam o trabalho depois.

**Decida e anote em `DECISOES.md`:**

1. **Qual canal de referência.** Um só, para começar. Critérios: ≥30 vídeos longos publicados, formato consistente (não pode ser um canal que mudou de fórmula no meio), legendas disponíveis, e um formato que você realmente queira fazer. Se o canal for em inglês e você produz em português, anote isso — vai importar na Fase 6.

2. **Qual é a unidade de saída do seu sistema.** Roteiro de 8 min? 12? Isso define o alvo de contagem de palavras e a estrutura esperada. Não deixe em aberto.

3. **Uso comercial ou não.** Define quais licenças você pode tocar. Se comercial, você já está impedido de usar `TextMachina` (CC-BY-NC-ND) e deve evitar qualquer repo sem arquivo LICENSE.

**Entregável:** `DECISOES.md` com três respostas.

**Portão:** você consegue dizer em uma frase o que o sistema produz e para quem.

---

## Fase 1 — Corpus

**Objetivo:** 30 transcrições limpas do canal de referência, com metadados.

**Ferramentas:** `youtube-transcript-api` (MIT), `yt-dlp` (Unlicense) como fallback, `whisperX` (BSD-2) só se não houver legenda.

**Passos:**

1. Liste os vídeos do canal com `yt-dlp --flat-playlist --dump-json`. Guarde ID, título, duração, data, views.
2. Selecione 30. **Não pegue os mais recentes** — pegue os de melhor desempenho relativo (views ÷ inscritos na época, ou simplesmente os 30 mais vistos entre vídeos com mais de 6 meses). Você quer aprender o que funciona, não o que foi publicado.
3. Baixe legendas com `youtube-transcript-api`. Salve o JSON cru com timestamps em `corpus/<canal>/raw/`.
4. Só use `whisperX` para vídeos sem legenda. É a etapa cara; evite se puder.
5. Limpeza mínima: remova marcações `[Música]`, `[Aplausos]`, junte fragmentos de legenda em texto corrido preservando o timestamp de início de cada trecho.

**Armadilhas:**
- Rodar as 30 requisições em sequência rápida derruba seu IP. Ponha `sleep` de alguns segundos entre chamadas.
- Legenda automática do YouTube não tem pontuação confiável. Não tente consertar agora — a Fase 2 resolve.
- Guarde o cru intocado. Toda limpeza gera arquivo novo.

**Entregável:** 30 arquivos em `raw/` + um `manifesto.csv` com uma linha por vídeo (id, título, duração, palavras, fonte da transcrição).

**Portão:** o manifesto tem 30 linhas e nenhuma transcrição tem menos de 60% da contagem esperada de palavras para a duração (sinal de legenda truncada).

---

## Fase 2 — Segmentação

**Objetivo:** transformar texto corrido em unidades anotáveis.

**Ferramentas:** `wtpsplit` (MIT, suporta PT-BR) para sentenças; `nltk.tokenize.texttiling` (Apache-2.0) ou `textsplit` para blocos topicais; `segeval` (BSD-3) para avaliar.

**Passos:**

1. **Sentenças primeiro.** `wtpsplit` recupera fronteiras de frase mesmo sem pontuação. Saída: lista de sentenças com timestamp de início.
2. **Blocos depois.** Agrupe sentenças em blocos topicais. Comece com TextTiling; se os cortes ficarem ruins, teste `textsplit` (baseado em embeddings).
3. **Estabeleça a regra de corte por escrito** antes de olhar os resultados. Sugestão inicial: um bloco termina quando muda a pergunta ativa, quando muda a escala do assunto, ou quando entra uma restrição/objeção nova. Escreva no `codebook.md`.
4. **Segmente 3 vídeos à mão** — literalmente marcando onde você acha que os blocos terminam. Isso é seu gold de segmentação.
5. Compare automático vs. manual com `segeval` (métricas Pk e WindowDiff).

**Armadilhas:**
- Blocos muito pequenos (uma frase) tornam a anotação inútil; muito grandes (3 minutos) escondem a estrutura. Mire em 6 a 20 blocos por vídeo de 10 min e ajuste os parâmetros até cair nessa faixa.
- Se o automático nunca chegar perto do seu gold, aceite: segmente semiautomático (a máquina propõe, você corrige no doccano). É mais lento, mas é honesto.

**Entregável:** `segmentado/*.jsonl`, uma linha por bloco com `video_id`, `bloco_id`, `inicio_s`, `fim_s`, `texto`, `n_palavras`.

**Portão:** Pk ≤ 0,4 contra o seu gold de 3 vídeos, **ou** decisão explícita de segmentar semiautomático.

---

## Fase 3 — A ontologia autoral

**Esta é a fase que decide o projeto.** Reserve tempo real, não um fim de tarde.

**Objetivo:** uma lista fechada de campos e valores que descreve *decisões de roteiro*, não conteúdo.

### Como projetar

Cada campo deve satisfazer quatro testes. Se falhar em um, não entra:

- **Observável** — dá para decidir olhando só o bloco e o que veio antes. "Este bloco é engraçado" falha; "este bloco introduz uma objeção" passa.
- **Fechado** — o conjunto de valores é finito e enumerado. Sem campo de texto livre.
- **Mutuamente exclusivo** — dois valores não podem ser ambos verdadeiros para o mesmo bloco. Se puderem, são dois campos, não um.
- **Agregável** — faz sentido contar, somar ou tirar média entre 30 vídeos. Se a resposta só faz sentido dentro de um vídeo, não serve para o perfil.

### Ponto de partida sugerido (adapte ao seu nicho)

**Campo `funcao`** (obrigatório, valor único):
- `gancho` — abre uma lacuna; ainda não entrega nada
- `promessa` — declara o que o vídeo vai entregar
- `contexto` — informação necessária antes do argumento
- `escalada` — aumenta a aposta ou a estranheza do problema
- `mecanismo` — explica *como* algo funciona
- `evidencia` — apresenta dado, estudo ou caso concreto
- `objecao` — levanta contra-argumento ou complicação
- `resolucao` — fecha uma lacuna aberta antes
- `implicacao` — estende o resultado para consequências maiores
- `transicao` — só move de um tópico a outro
- `cta` — pede ação ao espectador

**Campo `loop`** (valor único): `abre` / `fecha` / `mantem` / `nenhum`

**Campo `evidencia_tipo`** (só se `funcao=evidencia`): `estudo` / `dado_numerico` / `caso_concreto` / `analogia` / `autoridade`

**Campo `escala`** (valor único): `individual` / `humano` / `planetario` / `cosmico` / `abstrato`

**Campo `densidade_conceitual`** (0–2): quantos conceitos novos o bloco introduz.

Cinco a sete campos é o suficiente. Mais que isso derruba a concordância na Fase 5.

### Passos

1. Escreva a v0 com base na lista acima, cortando o que não faz sentido no seu nicho e acrescentando o que falta.
2. **Teste de cobertura:** pegue um vídeo já segmentado e classifique cada bloco à mão. Conte quantos blocos você precisou marcar como "outro" ou ficou em dúvida entre dois valores.
3. Revise. Repita com um segundo vídeo.
4. Escreva o `codebook.md`: para cada valor, uma definição de uma frase, dois exemplos positivos e **um exemplo negativo** (o caso que parece mas não é). O exemplo negativo é o que mais melhora a concordância depois.
5. Congele como `schema/ontologia.v1.json`.

**Entregável:** `ontologia.v1.json` + `codebook.md`.

**Portão:** em dois vídeos classificados à mão, menos de 10% dos blocos caem em "outro" ou em dúvida genuína entre dois valores. Se não passar, o problema é a ontologia — simplifique, não force.

---

## Fase 4 — Gold standard

**Objetivo:** anotação humana de referência contra a qual você mede tudo.

**Ferramenta:** `doccano` (MIT) — roda com `pip install doccano` ou Docker, interface web.

**Passos:**

1. Configure um projeto de classificação de sequências no doccano, importando os blocos como JSONL.
2. Crie os rótulos a partir de `ontologia.v1.json`.
3. Anote **5 vídeos completos** você mesmo, com o codebook aberto ao lado.
4. Deixe passar 48h e **reanote 1 desses vídeos sem olhar a primeira anotação**. Compare. Essa é sua concordância consigo mesmo — o teto de qualidade possível do sistema.
5. Exporte para `gold/<canal>/`.

**Armadilhas:**
- Não anote os 5 de uma sentada. O cansaço vira ruído sistemático.
- Se você discordar de si mesmo em mais de 20% dos blocos, o codebook está vago — conserte antes de seguir.

**Entregável:** 5 vídeos anotados + o número da sua autoconcordância.

**Portão:** autoconcordância (Krippendorff's α) ≥ 0,8. Se você não bate 0,8 consigo mesmo, um modelo não vai bater com você.

---

## Fase 5 — Anotação em lote + validação

**Objetivo:** anotar os 25 vídeos restantes por LLM, com prova de que é confiável.

**Ferramentas:** `instructor` (MIT, 13k estrelas, muito ativo) sobre Pydantic; `simpledorff` ou `krippendorff` para concordância.

**Passos:**

1. Modele a ontologia como classe Pydantic com `Enum` para cada campo. O `instructor` valida e refaz automaticamente quando a saída viola o schema.
2. O prompt de anotação é montado **a partir do codebook**, não escrito à mão. Ele recebe: o bloco, os dois blocos anteriores (contexto), e as definições. Pede um objeto só.
3. `temperature=0`. Rode **3 vezes** cada bloco e tome o voto majoritário. Blocos sem maioria vão para revisão manual — eles são informativos, geralmente indicam categoria mal definida.
4. **Antes de anotar os 25**, rode o modelo nos 5 do gold. Meça α entre modelo e humano com `simpledorff`.
5. Só então processe o resto.

**Custo estimado:** 30 vídeos × ~15 blocos × 3 execuções ≈ 1.350 chamadas curtas. Com um modelo pequeno, é barato. Não use o modelo mais caro aqui — teste o menor que passe no portão.

**Entregável:** `anotado/*.jsonl` para os 30 vídeos + relatório de concordância.

**Portão — este é o mais importante do plano:** α ≥ 0,667 entre modelo e gold humano, por campo. Se um campo específico não passar, **remova esse campo** ou reescreva sua definição no codebook e reanote. Não avance com um campo não confiável; ele contamina o perfil silenciosamente.

---

## Fase 6 — Agregação do perfil

**Objetivo:** transformar 30 anotações em um arquivo de configuração.

**Ferramentas:** `pandas`; `textstat` (MIT) para legibilidade; `faststylometry` opcional.

**O que o perfil contém:**

```
estrutura:
  - sequência típica de funções (a ordem mais comum e as variantes)
  - distribuição: % de blocos por função
  - posição percentual média de cada função (onde no vídeo ela aparece)
  - nº de loops abertos por vídeo; distância média entre abrir e fechar
  - nº de blocos por vídeo (média e faixa)
ritmo:
  - palavras por bloco (média, desvio, faixa)
  - palavras por minuto falado
  - densidade conceitual por terço do vídeo
evidencia:
  - distribuição de tipos de evidência
  - blocos de evidência por vídeo
estilo:
  - legibilidade (textstat)
  - comprimento médio de frase
  - trajetória de escala (individual→cósmico ou o padrão que aparecer)
proibicoes:
  - termos/construções recorrentes do canal que NÃO devem ser reproduzidos
```

**Passos:**

1. Calcule tudo com `pandas` a partir do JSONL anotado.
2. **Guarde faixas, não médias isoladas.** "Primeiro payoff entre 28% e 36%" é utilizável; "em média 32%" não diz se 15% é aceitável.
3. Grave como `perfis/<canal>.perfil.json`, com um campo `versao_ontologia` apontando para `ontologia.v1.json`.
4. **Recalibre para português se o canal for em inglês.** Palavras por minuto e legibilidade não transferem. Meça em algumas transcrições de canais brasileiros do mesmo formato e ajuste.
5. Preencha `proibicoes` à mão: as metáforas e bordões específicos daquele canal que você não vai reproduzir.

**Entregável:** `perfil.json` validado contra `perfil.schema.json`.

**Portão:** você consegue ler o perfil e reconhecer o canal nele. Se as distribuições parecem genéricas ("30% contexto, 25% mecanismo"), ou a ontologia é rasa ou os 30 vídeos não são coerentes entre si.

---

## Fase 7 — Motor de geração

**Objetivo:** dado um tema e um perfil, produzir um roteiro estruturado.

**Ferramentas:** `instructor` de novo (mesmo schema, direção inversa).

**Passos:**

1. **Gere o plano antes da prosa.** A primeira chamada produz uma lista de blocos vazios: função, escala, densidade alvo, palavras alvo, o que este bloco deve mudar no entendimento do espectador. Nada de texto final ainda.
2. Valide o plano contra o perfil **em código** (Fase 8) antes de escrever uma palavra de prosa.
3. **Escreva bloco a bloco**, passando o plano completo e os blocos já escritos. Uma chamada por bloco, com o alvo de palavras daquele bloco.
4. Voz e tom vêm de **exemplos**, não de regras: inclua no prompt 2–3 blocos reais do canal *da mesma função*, marcados claramente como referência de tom e não de conteúdo, junto com a lista `proibicoes`.

**Armadilha central:** a tentação de gerar o roteiro inteiro em uma chamada. Ela sempre produz um texto que ignora o perfil e obedece o instinto do modelo. A separação plano→prosa é o que faz a diferença.

**Entregável:** `saidas/<id>/roteiro.json` (blocos estruturados) + `roteiro.md` (texto corrido).

**Portão:** o roteiro passa na Fase 8.

---

## Fase 8 — Verificador automático

**Objetivo:** portão de qualidade que não depende de o modelo se autoavaliar.

**Tudo em Python puro, sem LLM:**

- distribuição de funções dentro das faixas do perfil
- todo loop aberto é fechado antes do fim
- posição percentual das funções-chave dentro da faixa
- palavras por bloco dentro da faixa
- contagem total dentro do alvo (±10%)
- nenhum termo da lista `proibicoes` presente
- legibilidade dentro da faixa
- densidade conceitual por terço dentro da faixa

Saída: um relatório com aprovado/reprovado por critério e o valor medido.

**Loop de correção:** critério reprovado → reescreve **só os blocos afetados**, não o roteiro inteiro. Máximo 3 tentativas; depois disso, o problema é o plano, e vale regenerar da Fase 7 passo 1.

**Portão:** ≥90% dos critérios aprovados.

**Nota:** esse verificador é também sua métrica de progresso. Rode-o nos 30 vídeos originais do canal — eles deveriam passar. Se os vídeos reais reprovam no seu próprio verificador, suas faixas estão erradas.

---

## Fase 9 — Produção do vídeo

**Só entre aqui quando a Fase 8 estiver estável por vários roteiros seguidos.**

**Ordem obrigatória:** locução primeiro. O áudio define a duração real; imagens cronometradas antes disso desperdiçam dinheiro. Esse é o único ponto do `master_prompt.txt` original que vale importar inteiro.

1. **TTS** → arquivo de áudio + duração real por bloco.
2. **Alinhamento** com `whisperX` se precisar de timing por palavra.
3. **Imagens** — prompts derivados dos blocos, um a cada N segundos. Comece gerando o pacote de prompts e rodando manualmente no seu gerador preferido; automatize só depois.
4. **Montagem** com `MoviePy` (MIT) ou `ffmpeg-python`. Fork as partes de montagem do MoneyPrinterTurbo se quiser acelerar — a montagem deles é decente, o roteiro é que não.

**Entregável:** MP4 + mapa de caminhos dos assets.

---

## Fase 10 — Segundo canal

**Objetivo:** provar que a arquitetura escala.

Repita as Fases 1, 2, 4, 5 e 6 com outro canal — **sem tocar em `src/`**. Se você precisar mudar código para o segundo canal, o que deveria ser parâmetro virou premissa em algum lugar; conserte antes de ir para o terceiro.

A ontologia pode precisar de ajuste se o nicho for muito diferente. Nesse caso, versione: `ontologia.v2.json`, e o perfil aponta para a versão que usou.

**Portão:** dois perfis, um motor, zero código duplicado.

---

## Cronograma realista

| Fase | Trabalho | Tempo estimado |
|---|---|---|
| 0 | decisões | 1 dia |
| 1 | corpus | 2–3 dias |
| 2 | segmentação | 3–5 dias |
| **3** | **ontologia** | **1–2 semanas** |
| 4 | gold standard | 3–4 dias |
| 5 | anotação + validação | 1 semana |
| 6 | agregação | 3–4 dias |
| 7 | motor | 1 semana |
| 8 | verificador | 3–5 dias |
| 9 | produção | 1–2 semanas |
| 10 | segundo canal | 3–5 dias |

**Total: 2 a 3 meses** em ritmo de projeto paralelo. A Fase 3 parecer desproporcional é intencional — ela é.

---

## Riscos e mitigação

| Risco | Sinal | O que fazer |
|---|---|---|
| Ontologia subjetiva demais | α trava abaixo de 0,5 na Fase 5 | Menos campos, definições mais operacionais. Corte o campo problemático. |
| Canal de referência inconsistente | perfil com faixas larguíssimas | Reduza o corpus aos vídeos do mesmo subformato. |
| Segmentação ruim contamina tudo | anotações não fazem sentido ao revisar | Volte à Fase 2. Semiautomático é aceitável. |
| Roteiro passa no verificador mas é chato | você mesmo não assistiria | O verificador cobre estrutura, não voz. Reforce os exemplos de tom na Fase 7. |
| Métricas em inglês aplicadas ao português | legibilidade com valores estranhos | Recalibre na Fase 6 com corpus em PT. |
| Bloqueio de IP no YouTube | erros 429 | `sleep` entre requisições; rode a coleta ao longo de dias. |

---

## O que NÃO fazer

- **Não construa a Fase 9 primeiro.** É a mais divertida e a menos importante. Sem roteiro bom, o vídeo bonito não serve.
- **Não use o modelo mais caro para anotar.** Anotação contra lista fechada é tarefa fácil; teste o menor que passe no portão.
- **Não deixe o modelo avaliar a própria saída** onde existe métrica computável. Autoavaliação de LLM infla.
- **Não reproduza formulação verbal do canal de referência.** Estrutura é gramática, redação é obra. Mantenha a lista `proibicoes` e leve-a a sério.
- **Não escale para 3 canais antes de a Fase 10 passar limpa** com 2.
- **Não invista em `gpt_annotate`, `core-stories` ou `ScreenPy` como dependência** — nenhum tem licença clara e nenhum é mantido. Leia-os como referência e escreva o seu.

---

## Próximo passo concreto

Fase 0. Três decisões, um arquivo de texto, hoje. A Fase 1 depende inteiramente delas.
