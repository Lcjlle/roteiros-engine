# roteiro-engine

Sistema de produção de roteiros para canais de YouTube baseado em **perfis estruturados**, extraídos de corpus anotado em vez de inferidos por prompt.

Um canal de referência entra. Um arquivo de configuração sai. A partir dele, roteiros novos são gerados de forma repetível e verificável — sem que o sistema reanalise o canal a cada execução.

---

## O problema

Os sistemas existentes de "automação de YouTube com IA" seguem todos o mesmo desenho: um prompt longo em prosa pede a um modelo que analise um canal e escreva um roteiro parecido, tudo na mesma execução.

Isso falha por um motivo estrutural, não por falta de capricho no prompt: **a especificação vive em prosa que o modelo reinterpreta do zero a cada vez**. Prosa interpretada duas vezes dá dois resultados. O output é plausível, mas não é reprodutível — e o que não é reprodutível não escala para um canal, muito menos para vários.

O segundo defeito é consequência do primeiro: pedir "faça engenharia reversa deste roteiro" produz um ensaio interpretativo. De um roteiro só, você tem n=1 de cada decisão estrutural — não dá para distinguir o que é padrão do canal do que foi escolha daquele tema.

## A ideia central

Duas inversões resolvem os dois defeitos.

**1. Anotar em vez de analisar.** Em vez de pedir descoberta livre, entrega-se ao modelo um esquema fechado — lista fixa de campos e valores — e pede-se rotulagem. Modelos são muito mais confiáveis escolhendo de uma lista do que inventando categorias. Trinta análises livres dão trinta textos incomparáveis; trinta anotações contra o mesmo esquema dão uma tabela que se pode somar.

**2. Separar construção de perfil da execução.** O perfil é construído uma vez por canal, é lento, é verificado por um humano e vira arquivo. A execução lê esse arquivo como parâmetro e nunca o rederiva. É por isso que rodar um segundo canal é trocar um arquivo, não reescrever o sistema.

```
CONSTRUÇÃO DO PERFIL          │  EXECUÇÃO
lenta · uma vez por canal     │  rápida · toda vez
verificada por humano         │  automática
produz: perfil.json           │  consome: perfil.json
```

## O que o sistema entrega

**Por canal, uma vez:**
- `perfil.json` — distribuições, faixas e sequências que descrevem a gramática do canal
- corpus anotado — 30 roteiros segmentados e rotulados, reutilizável
- relatório de concordância — a prova de que o perfil é confiável

**Por vídeo, quantas vezes quiser:**
- plano estruturado (blocos com função, escala, alvo de palavras)
- roteiro final
- relatório de verificação (aprovado/reprovado por critério, com valores medidos)
- opcionalmente: locução, prompts de imagem, MP4 montado

---

## Arquitetura em módulos

Sete módulos. Cada um tem uma responsabilidade, uma entrada e uma saída em disco. Nenhum módulo chama o outro diretamente — todos se comunicam por arquivo, o que permite rodar, inspecionar e refazer qualquer etapa isoladamente.

### M1 · Coleta

Monta o corpus a partir de um canal.

- **Entrada:** ID do canal
- **Saída:** `corpus/<canal>/raw/*.json` + `manifesto.csv`
- **Ferramentas:** [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) (MIT) para legendas; [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) (Unlicense) para enumerar vídeos e metadados; [`whisperX`](https://github.com/m-bain/whisperX) (BSD-2) só quando não há legenda
- **Não faz:** limpeza semântica, seleção editorial. O cru fica intocado.

### M2 · Segmentação

Transforma texto corrido em unidades anotáveis.

- **Entrada:** transcrições cruas
- **Saída:** `segmentado/*.jsonl` — uma linha por bloco, com timestamp e contagem de palavras
- **Ferramentas:** [`wtpsplit`](https://github.com/segment-any-text/wtpsplit) (MIT, suporta PT-BR) para fronteiras de sentença em texto sem pontuação; `nltk.tokenize.texttiling` (Apache-2.0) ou [`textsplit`](https://github.com/chschock/textsplit) para blocos topicais; [`segeval`](https://github.com/cfournie/segmentation.evaluation) (BSD-3) para medir a qualidade do corte
- **Por que importa:** transcrição não é roteiro. Não tem parágrafo, não tem fronteira de seção. A segmentação é onde a anotação mais erra — por isso ela é módulo próprio, com métrica própria.

### M3 · Ontologia

A lista fechada de campos e valores. **Não é código — é o ativo intelectual do projeto.**

- **Entrada:** trabalho humano
- **Saída:** `schema/ontologia.v1.json` + `codebook.md`
- **Ferramentas:** nenhuma. Esquemas acadêmicos (Labov & Waletzky, Freytag, [turning points](https://github.com/ppapalampidi/SUMMER)) servem de inspiração conceitual, mas todos medem estrutura de ficção, não decisões de roteiro educativo.
- **Por que não existe pronto:** nenhum repositório publicou uma ontologia de decisões autorais para vídeo educativo. Esta parte se escreve, uma vez, à mão.

### M4 · Anotação

Aplica a ontologia ao corpus.

- **Entrada:** blocos segmentados + ontologia
- **Saída:** `anotado/*.jsonl`
- **Ferramentas:** [`doccano`](https://github.com/doccano/doccano) (MIT) para a anotação humana de referência; [`instructor`](https://github.com/567-labs/instructor) (MIT) para forçar saída JSON validada por Pydantic no lote automático
- **Duas passadas:** humana em 5 vídeos (o gold), automática nos 25 restantes.

### M5 · Validação

Decide se o corpus anotado é confiável.

- **Entrada:** anotação automática + gold humano
- **Saída:** `relatorio_concordancia.md`
- **Ferramentas:** [`simpledorff`](https://github.com/LightTag/simpledorff) ou `krippendorff` para Krippendorff's α; `nltk.metrics.agreement` para kappa
- **Este é o portão principal do sistema.** Abaixo de α = 0,667, o perfil que sair é ruído com aparência de dado. O módulo tem poder de veto sobre o M6.

### M6 · Agregação

Transforma anotações em configuração.

- **Entrada:** corpus anotado e validado
- **Saída:** `perfis/<canal>.perfil.json`
- **Ferramentas:** `pandas`; [`textstat`](https://github.com/textstat/textstat) (MIT) para legibilidade; [`faststylometry`](https://pypi.org/project/faststylometry/) opcional para impressão estilística
- **Regra:** guarda **faixas**, não médias isoladas. "Primeiro payoff entre 28% e 36%" é utilizável; "em média 32%" não diz o que é aceitável.

### M7 · Geração e verificação

O motor de execução.

- **Entrada:** tema + perfil
- **Saída:** `saidas/<id>/plano.json`, `roteiro.md`, `verificacao.md`
- **Ferramentas:** `instructor` de novo, agora na direção inversa (mesmo schema, gerando em vez de rotulando); verificação em Python puro, sem LLM
- **Duas etapas obrigatórias:** primeiro o plano (blocos vazios com função e alvo de palavras), validado contra o perfil em código; só depois a prosa, bloco a bloco. Gerar o roteiro inteiro em uma chamada sempre produz texto que ignora o perfil.

### M8 · Produção *(opcional, última prioridade)*

Roteiro → vídeo.

- **Ferramentas:** TTS à escolha; [`MoviePy`](https://github.com/Zulko/moviepy) (MIT) ou `ffmpeg-python` para montagem
- **Referência de arquitetura:** [`MoneyPrinterTurbo`](https://github.com/harry0703/MoneyPrinterTurbo) (MIT) tem uma camada de montagem decente e vale forkar. A camada de roteiro dele é um prompt genérico — é exatamente o que este projeto substitui.
- **Ordem obrigatória:** locução primeiro. O áudio define a duração real; imagens cronometradas antes disso desperdiçam dinheiro.

---

## Fluxo completo

```
        ┌─────────────── CONSTRUÇÃO DO PERFIL ───────────────┐

canal ──▶ M1 coleta ──▶ M2 segmenta ──▶ M4 anota ──▶ M5 valida
                                            ▲            │
                                            │            │ α ≥ 0,667?
                                     M3 ontologia        │
                                     (humano)            ▼
                                                    M6 agrega
                                                         │
                                                         ▼
                                                   perfil.json
        ┌──────────────────── EXECUÇÃO ─────────┐         │
                                                          │
tema ──▶ M7 plano ──▶ verifica ──▶ prosa ──▶ verifica ◀───┘
                          │                      │
                          └── reprova ───────────┘
                                                         │
                                                         ▼
                                                    M8 produção
```

## Portões de qualidade

O sistema tem seis condições objetivas de avanço. Nenhuma é opinião.

| Portão | Critério | Se falhar |
|---|---|---|
| Segmentação | Pk ≤ 0,4 contra gold | segmentar semiautomático |
| Ontologia | < 10% de blocos em "outro"/dúvida | simplificar a lista |
| Autoconcordância | α ≥ 0,8 humano × humano | codebook está vago |
| **Concordância** | **α ≥ 0,667 modelo × humano** | **remover o campo problemático** |
| Perfil | reconhecível como o canal | corpus incoerente ou ontologia rasa |
| Roteiro | ≥ 90% dos critérios | reescrever blocos afetados |

O verificador do último portão também serve de calibração: rode-o nos 30 vídeos originais do canal. Eles deveriam passar. Se os vídeos reais reprovam, as faixas do perfil estão erradas.

---

## Estrutura de pastas

```
roteiro-engine/
├── schema/          ontologia, codebook, formato do perfil
├── corpus/          raw · segmentado · anotado, por canal
├── gold/            anotação humana de referência
├── perfis/          <canal>.perfil.json
├── src/             os módulos
└── saidas/          plano, roteiro, verificação, assets
```

## Decisões de projeto

**Por que arquivo em vez de banco (parcialmente superado — ver `_docs/decisions.md#1`).** O corpus é pequeno (dezenas de vídeos) e o valor de poder abrir qualquer etapa num editor de texto supera a conveniência de query. Versionado em git, o histórico do `schema/` explica por que cada categoria existe. `schema/`, `codebook.md` e `perfis/<canal>.perfil.json` continuam arquivo por esse motivo. O estado operacional do pipeline (manifesto de corpus, anotações por bloco, runs de concordância e de geração) passou a viver em Postgres (`src/db.py`, `migrations/`) — a razão está registrada em `_docs/decisions.md`, não aqui.

**Por que o esquema é a fonte da verdade.** Prompt, codebook e código leem `ontologia.v1.json`. Nada de listas duplicadas em prosa dentro de um prompt — é exatamente assim que os sistemas divergem de si mesmos com o tempo.

**Por que verificação em Python e não por LLM.** Contagem, posição percentual, distribuição, presença de termo proibido — tudo isso é computável e binário. Modelo avaliando a própria saída infla a nota. Julgamento de LLM fica reservado ao que não tem métrica.

**Por que voz não vira regra.** Cadência, humor e ritmo de frase não sobrevivem a virar lista de instruções — viram caricatura. O perfil tem duas metades: a estrutural (regras e faixas numéricas) e a estilística (trechos exemplares curtos, usados como referência de tom). Tratar as duas com o mesmo mecanismo é o erro mais comum.

**Por que estrutura é replicável e redação não.** Ordem de funções, faixas de duração e tipos de evidência são gramática de formato, e formato não é obra. Metáforas assinadas, bordões e formulações específicas são obra. A lista `proibicoes` de cada perfil existe para manter essa separação explícita — ver `politica_editorial.md`.

---

## Glossário

**Ontologia / esquema fechado** — a lista fixa de campos e valores permitidos. O anotador escolhe dela; nunca inventa.

**Codebook** — as definições em prosa de cada valor, com exemplos positivos e negativos. É o que faz humano e modelo concordarem.

**Gold standard** — a anotação humana de referência contra a qual a automática é medida.

**Krippendorff's α** — medida de concordância entre anotadores. ≥ 0,667 é o limiar mínimo aceitável; ≥ 0,8 é bom.

**Perfil** — o arquivo de configuração agregado do canal. Distribuições, faixas, sequências típicas.

**Bloco** — a unidade de anotação. Um trecho de roteiro com uma função narrativa única.

**Loop** — lacuna de informação aberta no espectador. O perfil rastreia onde abrem e onde fecham.

---

## Licenças das dependências

Todas as ferramentas escolhidas são permissivas (MIT, BSD, Apache-2.0, Unlicense) e compatíveis com uso comercial. Três exclusões deliberadas:

- `TextMachina` — CC-BY-NC-ND (não comercial, sem derivados)
- `gpt_annotate`, `core-stories` — sem arquivo LICENSE (todos os direitos reservados por padrão)
- `ScreenPy` — licença ambígua e abandonado desde ~2017

Verificar sempre o arquivo LICENSE do repositório, não o README nem fontes secundárias. Ver `LICENCAS.md`.

---

## Estado

Planejamento. Nada implementado ainda. O plano de execução em dez fases está em `plano_implementacao.md`.

**Próximo passo:** Fase 0 — três decisões em `DECISOES.md` (canal de referência, duração-alvo, uso comercial).
