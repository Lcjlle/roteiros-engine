# Blueprint de repositórios open-source para um sistema de produção de roteiros educativos em escala

> **Nota de revisão — arquitetura v3.0.** Este documento é o levantamento de ferramentas que fundamentou as escolhas do projeto. Os fatos sobre licenças, atividade e capacidade de cada repositório continuam válidos. O que mudou foi o **uso**: a recomendação original de segmentar com `wtpsplit` **+ TextTiling** foi revertida, porque TextTiling detecta mudança de tópico por coesão lexical e a ontologia do projeto precisa de mudança de função narrativa. A arquitetura passou a anotar janelas de 2–4 sentenças e derivar blocos por fusão. Pontos afetados marcados com **[REVISTO v2.0]**.
>
> **Idioma (v3.0):** o corpus e os roteiros gerados são em **inglês**; a comunicação do projeto com humanos é em **PT-BR**. Este documento é PT-BR. As ressalvas sobre calibração de ferramentas para português deixaram de se aplicar ao corpus — ver **[REVISTO v3.0]**.
>
> **Multi-canal (v3.0):** rodar vários canais é o modo normal de operação, com **uma ontologia global versionada**. Isso muda o peso de algumas escolhas: o que é feito uma vez para todos os canais (ontologia, motor, verificador) tolera custo alto; o que é feito por canal (coleta, sentenciação, anotação) precisa ser barato e previsível.
>
> Precedência: este documento perde para `_docs/decisions.md` e para uma issue groomada. Ver `_docs/process.md`. Onde ele descreve algo que já aconteceu de outro jeito na prática (ex.: o bloqueio de IP do YouTube), a marcação **[CONFIRMADO EM PRODUÇÃO]** aponta a entrada de `decisions.md` correspondente.

## TL;DR
- **A sua arquitetura (perfil lento + verificado por humano × execução rápida e repetível) é sólida e cada peça técnica já tem ferramenta pronta e madura** — segmentação de texto, saída JSON validada, anotação de corpus, transcrições, estilometria, montagem de vídeo. O que NÃO existe pronto é a peça central: a *ontologia autoral fechada* do seu nicho e o repo que faça o combo completo "perfil de um canal → gerar roteiros novos". Isso você terá de escrever.
- **Priorize um núcleo de bibliotecas permissivas e vivas:** `youtube-transcript-api` (MIT) + `yt-dlp` (Unlicense) para o corpus, `wtpsplit` para sentenciar (**[REVISTO v2.0]** — TextTiling descartado), `doccano` (MIT) para anotar segundo o seu esquema fechado, `instructor` (MIT) ou `outlines` para forçar JSON conforme schema, `nltk.metrics.agreement` (Apache-2.0) para medir concordância, `textstat` (MIT) + estilometria para o perfil estilístico, e `MoviePy` (MIT) para montagem. Todos com licença comercial-friendly.
- **Cuidado com os "sistemas prontos de YouTube":** MoneyPrinterTurbo (MIT, 113k estrelas) e ShortGPT (MIT, semi-abandonado) servem como referência de pipeline e como montadores, mas nenhum implementa a sua abordagem de perfil estruturado — são geradores "tema→vídeo" de qualidade genérica. Use-os para peças de montagem, não para a inteligência do roteiro.

## Key Findings

**1. Não há repositório único que faça o combo que você quer.** A busca confirma que o espaço é fragmentado entre (a) ferramentas de *extração* de estilo/estrutura e (b) ferramentas de *geração* condicionada. Os matches mais próximos do loop "extrair perfil → salvar JSON → gerar texto novo" são projetos pequenos e de nicho voltados a artigos ou mensagens pessoais (ex.: Qusto/TextScript, cosmos-makers/writer-persona, shannhk/writing-style-extractor), não a roteiros de canal. Existe também um paper descrevendo exatamente esse pipeline de duas etapas ("Author Writing Sheet" → geração), mas é método acadêmico, não repositório mantido. Isso valida a sua decisão de construir o motor você mesmo — e reforça que o valor do seu sistema está exatamente na peça que ninguém empacotou.

**2. A ontologia autoral não existe pronta.** Existem esquemas de anotação narrativa acadêmicos (Labov & Waletzky, Freytag, Story Intention Graph de Elson, turning points de Papalampidi), mas todos medem estrutura de *ficção/enredo*, não decisões autorais de um roteiro educativo de YouTube (gancho, promessa, prova, tangente, CTA, recapitulação etc.). Você usará esses esquemas como inspiração conceitual, mas a lista fechada de campos será sua.

**3. Toda a "plataforma" ao redor da ontologia é bem servida por software maduro e permissivo.** Transcrição, segmentação, anotação, validação de JSON, concordância entre anotadores e montagem de vídeo têm bibliotecas ativas e MIT/BSD/Apache.

## Details

### Peça 1 — Segmentação de texto/discurso em unidades

**[REVISTO v2.0]** O corpus vem de transcrições sem pontuação confiável. A versão original desta seção assumia duas etapas: restaurar fronteiras de sentença e depois segmentar por tópico. **A segunda etapa foi eliminada do projeto.**

Motivo: segmentação topical mede queda de coesão lexical, proxy de mudança de assunto. As fronteiras que a ontologia precisa são de mudança de função narrativa. Um `gancho` e a `promessa` seguinte compartilham vocabulário e nunca seriam separados; um bloco longo de `mecanismo` varia de léxico e seria cortado sem razão funcional. Além disso há dependência circular: a fronteira funcional só é conhecida depois da rotulagem.

A arquitetura vigente usa apenas o primeiro item abaixo. Os demais ficam registrados como levantamento, e porque continuam corretos para quem tiver o problema que eles resolvem.

- **segment-any-text/wtpsplit** — https://github.com/segment-any-text/wtpsplit — Modelos SaT/WtP para segmentar texto em sentenças/unidades de forma robusta mesmo *sem pontuação*, em 85 idiomas (inclui português). Python, PyTorch/ONNX. 1,3k estrelas; Release 2.2.1 em 11 de abril de 2026 (por markus583). Licença **MIT**. **Resolve:** transformar a transcrição crua em sentenças antes de anotar. **Dificuldade:** baixa-média — `pip install wtpsplit`, poucas linhas. **Status no projeto: ADOTADO, e é a única ferramenta de segmentação usada.** As janelas de anotação são formadas por regra determinística sobre as sentenças (até 35 palavras ou 4 sentenças, mínimo 2), não por algoritmo. **[REVISTO v3.0]** O código de idioma é **`en`** — o corpus é em inglês. A v2.0 deste plano dizia `pt`, o que era erro.
- **NÃO ADOTADO — TextTiling** (implementação clássica) — disponível dentro do **NLTK** (`nltk.tokenize.texttiling`), licença Apache-2.0, e em variantes como **riedlma/topictiling** (LDA) e **chschock/textsplit** (embeddings). **Resolve:** segmentação topical não supervisionada (quebra onde o assunto muda). **Dificuldade:** baixa via NLTK; média nas variantes. **Por que saiu:** o projeto precisa de fronteira funcional, não topical.
- **Segmentação por discurso/RST (EDU):** **tchewik/isanlp_rst** — https://github.com/tchewik/isanlp_rst — parser RST multilíngue **com suporte a português do Brasil**, retorna árvore de unidades discursivas elementares (EDUs) com relações. **Resolve:** segmentação fina e rotulagem de relações retóricas, caso você queira granularidade abaixo do parágrafo. **Dificuldade:** média-alta (Docker recomendado). Para conversão de formatos RST há **amir-zeldes/rst2dep** (pip). **Status no projeto: alternativa oficial de contingência.** Se a janela de 2–4 sentenças se mostrar má unidade de anotação (α baixo na Fase 5 mesmo com codebook revisado), o caminho é EDU/RST — não TextTiling — porque EDUs são unidades funcionais de discurso e não meramente topicais.
- **NÃO ADOTADO — Avaliação:** **cfournie/segmentation.evaluation** (`segeval`, PyPI) — métricas Pk, WindowDiff, Boundary Similarity e coeficientes de concordância entre anotadores para segmentação. Licença **BSD-3-Clause**, estável. **Resolve:** medir se a segmentação automática bate com a sua segmentação-ouro. **Por que saiu:** sem segmentação topical, não há o que avaliar. Além disso, Pk depende do comprimento médio de segmento, o que tornava o portão `Pk ≤ 0,4` da v1.0 não comparável entre configurações — ele foi substituído por um portão amostral (≤ 5 de 50 janelas com duas funções).

### Peça 2 — Anotação narrativa e esquemas de anotação

Aqui está o coração do seu "corpus anotado com esquema fechado".

- **doccano/doccano** — https://github.com/doccano/doccano — ferramenta de anotação web open-source para classificação de texto, sequence labeling e seq2seq. 10,7k estrelas, último release v1.8.5, pacote conda-forge atualizado em 20 de fevereiro de 2026 (ativa). Licença **MIT**. **Resolve:** exatamente a interface para você (ou revisores humanos) aplicar a sua lista fixa de campos/categorias a cada segmento; importa/exporta JSONL. **Dificuldade:** baixa-média — roda via `pip`/Docker, UI amigável para não-engenheiro. É a recomendação principal para o passo de anotação manual/verificação.
- **INCEpTION** — mais poderoso (anotação linguística profunda, ligação a base de conhecimento, sugestões automáticas) mas bem mais pesado (Java, servidor). Considere só se precisar de recursos avançados; para esquema fechado simples, doccano ganha.
- **Label Studio** — alternativa multimodal robusta (Python SDK), mas a edição comunitária **não inclui métricas de concordância entre anotadores** (ficam no plano pago), o que importa para o seu controle de qualidade.
- **Esquemas de referência conceitual (não são código plug-and-play):** o esquema de Labov & Waletzky + pirâmide de Freytag consolidado por Ouyang/McKeown; **Story Intention Graph** (Elson); **plot units** (Lehnert); e o dataset de *turning points* de Papalampidi. Use-os como cardápio de ideias para desenhar a SUA ontologia — nenhum é sobre roteiro educativo.

### Peça 3 — Análise de roteiro / screenplay

- **ppapalampidi/SUMMER** e **ppapalampidi/GraphTP** — https://github.com/ppapalampidi/SUMMER — código dos papers de *turning point identification* e sumarização por estrutura narrativa latente (EMNLP 2019/ACL 2020/AAAI 2021). **Resolve:** conceito de segmentar uma narrativa em unidades temáticas (setup, complicações, clímax, desfecho) e identificar momentos-chave — diretamente transferível para "mapear a estrutura recorrente de um canal". **Dificuldade:** alta (código de pesquisa, PyTorch).
- **drwiner/ScreenPy** — https://github.com/drwiner/ScreenPy — parser/anotador de roteiros que extrai cabeçalhos de cena, diálogos, direções e faz desambiguação de sentido de verbos (FrameNet/WordNet). **Porém:** apenas 42 estrelas, **abandonado (~2017)** e licença ambígua (README diz MIT, mas o arquivo LICENSE pode não existir). Útil como referência de design, arriscado como dependência.
- Para roteiros formatados em Fountain/FDX há parsers dedicados, mas o seu material é transcrição, não screenplay formatado — provavelmente não se aplica.

### Peça 4 — LLM com saída estruturada e validada (o "motor de execução")

Esta é a peça mais madura de todas e o coração do seu passo de execução rápida.

- **567-labs/instructor** — https://github.com/567-labs/instructor — força qualquer LLM a devolver JSON validado por um modelo **Pydantic**; injeta o schema, valida e faz *retry* automático com a mensagem de erro. 13.069 estrelas (snapshot maio/2026, ecosyste.ms), último push 2026-05-24, licença **MIT**, muito ativo, funciona com 15+ provedores. **Resolve:** tanto (a) rotular seu corpus contra a taxonomia fechada em lote, quanto (b) o motor de geração que lê o perfil JSON e emite roteiros estruturados. **Recomendação principal** — é a escolha mais simples para quem "se vira em Python".
- **pydantic/pydantic** — https://github.com/pydantic/pydantic — validação de dados e modelagem via type hints; é a lib que `instructor` (linha acima) valida contra, e a que `src/schema_loader.py` (Issue #16) usa diretamente para gerar `WindowAnnotation` a partir de `schema/ontologia.v1.json`. ~24k estrelas, licença **MIT**, ativo. Citada antes só de passagem dentro da entrada do `instructor`; linha própria adicionada quando virou dependência direta do repositório (`pyproject.toml`), não só transitiva.
- **dottxt-ai/outlines** — geração com *constrained decoding* (mascara tokens inválidos, garante schema no nível do token). ~12k estrelas, Apache-2.0. **Melhor quando** você roda modelos locais (transformers/llama.cpp/vLLM) e quer throughput alto sem retries. **Dificuldade:** média.
- **Structured Outputs nativos** (OpenAI `strict: true`, Anthropic tool_use) cobrem o caso 80% sem lib extra, se você já usa esses provedores.
- **Pydantic-AI** — se depois quiser evoluir para "agentes" com ferramentas; hoje, overkill.

### Peça 5 — Anotação de corpus com LLM em lote + concordância

- **npangakis/gpt_annotate** — https://github.com/npangakis/gpt_annotate — pacote que anota texto em lote com GPT, roda cada item várias vezes, e **compara com rótulos humanos (gold standard)**. **Porém:** **sem arquivo de licença** (todos os direitos reservados por padrão) e inativo (~2023). Use como referência de metodologia, não como dependência comercial.
- **LLMAnnotationResearch/llm-annotation-framework** — código do paper de Wharton "The Use of LLMs to Annotate Data" com *sensitivity checks*. Bom como guia metodológico de validação.
- **Concordância entre anotadores:** **simpledorff** (Krippendorff's alpha em uma linha sobre DataFrame), a lib **krippendorff** (linha abaixo, NÃO ADOTADO — GPL-3.0), e **nltk.metrics.agreement** (Cohen/Fleiss kappa). **Resolvem:** medir se o LLM-anotador concorda com o humano acima do limiar aceitável (α ≥ 0,667 por Krippendorff; α ≥ 0,8 ideal). Este é o seu portão de qualidade para dizer "o perfil é confiável".
- **nltk/nltk — `nltk.metrics.agreement.AnnotationTask`** — https://github.com/nltk/nltk — implementação de coeficientes de concordância entre anotadores (Krippendorff's α, Cohen's κ, Scott's π, Bennett-Albert-Goldstein S) via `AnnotationTask(data, distance=...)`, onde `distance` é uma função pura de dois argumentos — ao contrário do `krippendorff` do PyPI (linha abaixo, NÃO ADOTADO), não expõe um parâmetro `level_of_measurement='ordinal'` pronto; a distância ordinal de `density` (`schema/ontologia.v1.json`) é implementada pelo próprio projeto como uma closure sobre os marginais observados do dataset, não uma função pura de dois inteiros (`_docs/decisions.md#28(d)`, com a citação exata do código-fonte que fundamenta essa exigência). Licença **Apache-2.0** (confirmada no `LICENSE.txt` do repositório). **Resolve:** o α de todos os cinco campos da ontologia — os quatro nominais com a distância binária padrão da lib, `density` com a closure ordinal do projeto — para os dois portões de concordância (`fase4-self-agreement-alpha`, `fase5-model-human-agreement-alpha`, `schema/portoes.json`). **Status no projeto: ADOTADO, `_docs/decisions.md#28(d)` — linha registrada aqui antes de qualquer `uv add nltk` acontecer de verdade, mesmo processo já seguido para `pydantic` (linha 59 acima) quando ela virou dependência direta do repositório.**
- **NÃO ADOTADO — GPL-3.0:** **pln-fing-udelar/fast-krippendorff** — https://github.com/pln-fing-udelar/fast-krippendorff — implementação rápida do alpha de Krippendorff (`krippendorff.alpha(reliability_data=..., level_of_measurement=...)`), incluindo o nível `ordinal` que uma escala censurada como `density` (`schema/ontologia.v1.json`) exigiria. Licença **GPL-3.0** (confirmada no `LICENSE.txt` do repositório e no classifier do PyPI — diferente de todo o resto do núcleo permissivo desta lista, e o motivo da rejeição). **Por que saiu:** copyleft foge do núcleo permissivo desta lista, e fecharia uma porta que `DECISOES.md` item 3 ("ver `_docs/decisions.md` se algum dia isso mudar") deixa explicitamente aberta — se a decisão de uso não-comercial for revista um dia, GPL-3.0 vira bloqueio real, não só ressalva. `_docs/decisions.md#28(d)` reverte a adoção anterior desta lib e decide `nltk.metrics.agreement.AnnotationTask` (linha acima) com uma distância ordinal implementada pelo próprio projeto no lugar do nível `ordinal` embutido aqui.
- **Frameworks de apoio:** `llmClassificR`, `gpt_annotate` e vários pipelines "LLM-as-annotator" recentes confirmam a prática de rodar o modelo com `temperature` baixa e validar por auto-concordância + amostra humana.

### Peça 6 — Pipeline de transcrições do YouTube

- **jdepoix/youtube-transcript-api** — https://github.com/jdepoix/youtube-transcript-api — pega transcrições/legendas (inclusive autogeradas, com tradução) sem API key nem browser. 8k estrelas, release v1.2.4 de 29 de janeiro de 2026 (ativo), licença **MIT**. **Resolve:** montar o corpus de um canal rapidamente. **Dificuldade:** baixa. Cuidado: uso em escala esbarra em limites de IP (relatos de ~100-200 req/hora por IP) e pode exigir revisão legal para uso comercial. **[CONFIRMADO EM PRODUÇÃO]** O bloqueio aconteceu na Fase 1, no vídeo 22 de 30, e **não se resolveu esperando** — `youtube_transcript_api` e o download de legendas do `yt-dlp` seguiram `IpBlocked`/`429` em retestes. Ver `_docs/decisions.md#3` e `#4`.
- **yt-dlp/yt-dlp** — https://github.com/yt-dlp/yt-dlp — baixa legendas (`--write-subs`/`--write-auto-subs`), metadados e áudio de vídeos, playlists e canais inteiros. Licença **Unlicense** (domínio público) no código-fonte; note que binários empacotados via PyInstaller incluem código GPLv3+. **Resolve:** enumerar todos os vídeos de um canal e obter legendas/áudio em massa.
- **m-bain/whisperX** — https://github.com/m-bain/whisperx — quando não há legenda, transcreve com Whisper + *forced alignment* (wav2vec2) para timestamps por palavra (±50 ms), com diarização opcional. ~23,6k estrelas, licença **BSD-2-Clause** (o arquivo LICENSE lista apenas duas condições — retenção do aviso de copyright em código-fonte e em binário — sem cláusula de propaganda, ao contrário do que alguns secundários afirmam; portanto é comercial-friendly). **Resolve:** alinhar texto e áudio quando precisar de timing preciso, e transcrever quando não há legenda. **Dificuldade:** média (GPU recomendada). Alternativas: `stable-ts`, `aeneas` (forced alignment leve).

  **[CONFIRMADO EM PRODUÇÃO]** `whisperx==3.8.6` é **dependência real do projeto**, não fallback opcional — foi o que completou o corpus de 21 para 30 vídeos quando o bloqueio de IP não cedeu (o endpoint de áudio nunca foi bloqueado). Três achados operacionais, todos em `_docs/decisions.md#4`: (a) `batch_size=16` estoura VRAM em GPU de 6GB; `4` roda em ~4GB, e o consumo é dominado pelo modelo, não pela duração do áudio; (b) chamar o transcritor para um segundo vídeo no mesmo processo estoura mesmo em `batch_size=4`, porque a memória do primeiro modelo não é liberada — a correção é **um subprocesso por vídeo**, não batch menor; (c) qualidade conferida contra as legendas existentes nos dois extremos de duração deu 99,2% e 99,64% de concordância lexical, com as diferenças em homófonos e grafia de números. Custo permanente: `uv sync` puxa `torch` e as wheels `nvidia-cu12-*` mesmo em uso CPU-only.

  **[RESOLVIDO v3.0]** A proposta de promover whisperX a caminho padrão de coleta foi levantada e **recusada pelo dono do projeto**: legenda continua o caminho padrão, whisperX continua fallback, e o bloqueio de IP recorrente é tratado como esperado, resolvido por transcrição local caso a caso — como já ocorreu em `_docs/decisions.md#4`. Ver `_docs/decisions.md#5`.

### Peça 7 — Métricas de texto para o perfil estilístico

- **textstat/textstat** — https://github.com/textstat/textstat — legibilidade (Flesch, Flesch-Kincaid, Gunning-Fog, SMOG etc.), contagem de sílabas, densidade — com suporte a variantes de idioma. ~1,4k estrelas, **MIT**, mantido. **Resolve:** dimensões objetivas do perfil (nível de leitura, comprimento médio de frase). **Dificuldade:** baixa. **[REVISTO v3.0] Aplica-se diretamente:** corpus e saída são em inglês, que é a língua para a qual os índices clássicos (Flesch, Flesch-Kincaid, SMOG) foram calibrados. A recalibração para português que as versões anteriores exigiam **não é mais necessária**.
- **Estilometria:** **faststylometry** (Burrows' Delta, PyPI, ativo) para "distância de estilo" entre roteiros; **stylo** (é R, mas é o padrão-ouro do campo); **StyloMetrix** (vetores estilométricos multilíngues). **Resolvem:** capturar a "impressão digital" do canal (frequência de palavras funcionais, riqueza lexical). **Dificuldade:** média.
- **Arco emocional / sentimento ao longo do texto:** **andyreagan/core-stories** — https://github.com/andyreagan/core-stories — código do paper de Reagan et al. (2016) sobre as "seis formas básicas" de arcos emocionais + hedonometer. **Porém:** 34 estrelas, **sem licença** (artefato de reprodução), não é lib empacotada. Alternativa em R muito usada: **syuzhet** (Jockers). **Resolve:** medir a trajetória de sentimento/energia ao longo de um vídeo — uma dimensão forte do "ritmo" de um canal. Implementar você mesmo com um léxico + janela deslizante é viável.
- **Coerência semântica entre sentenças / surprisal:** via embeddings (sentence-transformers) e modelos de linguagem — construção própria simples.

### Peça 8 — Sistemas completos de geração de vídeo YouTube (avaliação cética)

- **harry0703/MoneyPrinterTurbo** — https://github.com/harry0703/MoneyPrinterTurbo — pipeline tema→vídeo (LLM escreve roteiro, busca clipes de estoque no Pexels, TTS, legendas, BGM, render). 113k estrelas, **MIT**, muito ativo (release v1.3.4 publicado em 12 de agosto de 2026). **Avaliação honesta:** excelente como *referência de arquitetura de montagem* e para as etapas TTS/legenda/render; a inteligência do roteiro é genérica (um prompt de LLM), exatamente o que você quer *substituir* pelo seu motor baseado em perfil. Sem autenticação embutida, depende de chaves de terceiros. **Não superestime** — o nome é marketing; ela não "imprime dinheiro" nem produz qualidade editorial.
- **RayVentura/ShortGPT** — https://github.com/RayVentura/ShortGPT — framework experimental de automação de Shorts/TikTok. ~7,4k estrelas, **MIT**, mas **semi-dormente** (pouca atividade em 2026). Bom como código para *forkar*, ruim como dependência de produção.
- **FujiwaraChoki/MoneyPrinter** (o original) — mais simples, Ollama-first; qualidade básica.
- **Veredito:** use estes como fonte de trechos de montagem (a lógica MoviePy + TTS + legenda), não como o cérebro do sistema.

### Peça 9 — Montagem programática de vídeo em Python

- **Zulko/moviepy** — https://github.com/zulko/moviepy — biblioteca de edição de vídeo (cortes, concatenação, títulos, composição, efeitos). 14,9k estrelas, **MIT**, v2.2.1 lançado em 21 de maio de 2025 (mantida, porém o README pede "maintainers wanted", sinal de banda baixa). **Resolve:** a montagem final roteiro→vídeo. **Dificuldade:** média (pode ser lenta em arquivos grandes; depende de FFmpeg).
- **ffmpeg-python** / **python-ffmpeg** — wrappers finos sobre FFmpeg, melhores para processamento/conversão em escala. **vidgear** — ativo, cheio de recursos.
- **Remotion** (React/JS) e **Revideo** — montagem "declarativa" com qualidade broadcast, mas em JS/TypeScript, não Python — mencionados como opção se você aceitar sair do Python para o render final.

### Comparação com o blueprint que você já conhece (canlab/narrative_feature_annotations)
Ele acerta a *arquitetura de dados* (corpus anotado segundo-a-segundo, esquema versionado, HDF5 para agregação), que você deve imitar. Mas a ontologia dele é perceptual (propriedades do estímulo para neuroimagem), não autoral. A analogia certa é: mantenha o *padrão de engenharia*, troque *toda a lista de features* pela sua ontologia de decisões de roteiro.

## Glossário de termos de busca (inglês) + queries prontas

**Segmentação de texto/discurso**
- *topic segmentation* / *text segmentation* — dividir texto onde muda o assunto.
- *TextTiling*, *C99*, *GraphSeg* — algoritmos clássicos de segmentação topical.
- *discourse segmentation* / *elementary discourse units (EDU)* — quebrar em unidades mínimas de discurso.
- *Rhetorical Structure Theory (RST) parsing* — árvore de relações retóricas entre trechos.
- *sentence boundary detection* / *punctuation restoration* — recuperar fronteiras de frase em texto sem pontuação.
- *event segmentation* / *narrative boundary detection* — fronteiras de evento em narrativa.

**Anotação narrativa e esquemas**
- *narrative structure annotation*, *story arc*, *plot units*, *narrative schema*, *event structure*.
- *Labov and Waletzky*, *Freytag pyramid*, *Story Intention Graph*, *turning point identification*.
- *closed annotation scheme* / *codebook* / *tagset* / *ontology* — sua lista fixa de categorias.
- *corpus annotation tool* — brat, doccano, INCEpTION, Label Studio, Potato.

**Screenplay / roteiro**
- *screenplay parsing*, *scene segmentation*, *beat detection*, *three-act structure*, *story analytics*.

**LLM saída estruturada**
- *structured output*, *constrained decoding*, *grammar-constrained generation*, *JSON schema enforcement*, *function calling*, *guided generation*.

**Anotação por LLM + concordância**
- *LLM-as-annotator*, *LLM annotation*, *automatic text annotation*.
- *inter-annotator agreement (IAA)*, *inter-rater reliability (IRR)*, *Krippendorff's alpha*, *Cohen's kappa*, *Fleiss' kappa*, *gold standard validation*.

**Transcrições**
- *YouTube transcript API*, *subtitle extraction*, *forced alignment*, *word-level timestamps*, *ASR*, *speaker diarization*.

**Perfil estilístico**
- *stylometry*, *authorship attribution*, *Burrows' Delta*, *readability metrics*, *lexical density*, *type-token ratio*, *emotional arc*, *sentiment trajectory*, *surprisal*.

**Vídeo**
- *programmatic video editing*, *video composition*, *non-linear editing*, *text-to-video pipeline*.

**Queries prontas para o GitHub (barra de busca)**
- `topic segmentation language:Python stars:>50 pushed:>2024-01-01`
- `discourse segmentation RST language:Python stars:>20`
- `"structured output" OR "constrained decoding" LLM language:Python stars:>500 pushed:>2025-01-01`
- `LLM annotation "inter-annotator" language:Python`
- `youtube transcript language:Python stars:>100 pushed:>2025-01-01`
- `stylometry OR "authorship attribution" language:Python stars:>30`
- `"emotional arc" OR syuzhet sentiment story language:Python`
- `screenplay parser scene language:Python`
- `text-to-video OR "video automation" language:Python stars:>1000`
- No **Papers with Code**: busque "text segmentation", "turning point identification", "story structure"; no **Google Scholar**: os termos acadêmicos acima entre aspas.

## Recommendations

**Estágio 0 — Corpus e sentenciação. [REVISTO v2.0]** Escolha 30 vídeos de UM canal de referência, selecionados por desempenho relativo e não por data. Baixe as transcrições com `youtube-transcript-api` (fallback `yt-dlp` → `whisperX`), preservando os timestamps de cada trecho. Sentencie com `wtpsplit` e agrupe em janelas de 2–4 sentenças por regra determinística. *Benchmark para avançar:* uma janela por linha, sem sentenças cortadas no meio de oração e com no máximo 10% das janelas contendo duas funções narrativas óbvias, em amostra de 50.

**Estágio 1 — Ontologia + gold standard (o passo insubstituível, feito por você).** Escreva a v0 da sua lista fechada de funções de roteiro (ex.: `gancho`, `promessa`, `contexto`, `prova`, `exemplo`, `tangente`, `recapitulação`, `transição`, `CTA`). Anote manualmente ~5 vídeos no **doccano**. *Benchmark:* a ontologia cobre >90% das janelas sem precisar de "outros"; se não, revise a lista antes de escalar. **[REVISTO v2.0]** Acrescente um quinto critério de projeto a cada campo: além de observável, fechado, mutuamente exclusivo e agregável, ele precisa ser **decidível olhando 2–4 sentenças**. Categorias que exigem ver o vídeo inteiro (como `recapitulacao`) não sobrevivem ao formato de janela e precisam ser reformuladas em termos locais ou cortadas.

**Estágio 2 — Anotação assistida por LLM + validação.** Use `instructor` para rotular o resto do corpus contra a ontologia (JSON validado, `temperature` baixa, 3 execuções). Meça a concordância LLM×humano com `simpledorff`. **[REVISTO v2.0]** Meça **no nível de janela**, nunca depois da fusão em blocos: a fusão apaga discordâncias e infla o número. E não passe a posição percentual da janela no prompt — o modelo responderia pela posição e não pelo texto, e o perfil confirmaria a estrutura que você mesmo injetou. O volume real é de ~3.600 chamadas, não 1.350, então o runner precisa ser retomável. *Benchmark decisivo:* Krippendorff's α ≥ 0,667 no seu gold standard, por campo. Abaixo disso, o rótulo automático não é confiável — melhore as definições da ontologia (não o modelo) e repita. Este é o gatilho que muda tudo: só agregue o perfil quando passar o limiar.

**Estágio 3 — Fusão e agregação do perfil (JSON). [REVISTO v2.0]** Antes de agregar, funda janelas consecutivas de mesma função em blocos, aplicando a regra de suavização de `schema/regras_fusao.md`. Registre a taxa de suavização: acima de 15% é diagnóstico de ontologia confusa, não ruído aceitável. Só então agregue as anotações validadas em estatísticas: distribuição e ordem típica das funções, duração média por função, arco de sentimento (`core-stories`/léxico próprio), legibilidade (`textstat`), impressão estilométrica (`faststylometry`). Salve como o `profile.json` versionado — imite o padrão de engenharia do canlab (esquema versionado, agregação separada da anotação).

**Estágio 4 — Motor de execução.** Um script que lê `profile.json` e, via `instructor`/`outlines`, gera um novo roteiro estruturado (mesma ontologia) respeitando as distribuições do perfil. *Benchmark:* rode o roteiro gerado pelo mesmo anotador do Estágio 2 e verifique se a distribuição de funções bate com o perfil (distância baixa).

**Estágio 5 — Montagem.** TTS + `MoviePy` (ou fork das partes de montagem do MoneyPrinterTurbo) para roteiro→vídeo. Só automatize esta etapa depois que a qualidade do roteiro estiver estável.

**O que mudaria a rota:** se a concordância do Estágio 2 nunca passar de ~0,5 mesmo com ontologia revisada, o problema é que suas categorias são subjetivas demais — simplifique para menos campos e mais objetivos. Se você precisar de timing por palavra para cortes, priorize `whisperX` desde o Estágio 0.

## Caveats
- **Nenhum repo faz o combo completo.** Os matches mais próximos (projetos tipo "extrair perfil de estilo → gerar texto", como Qusto/TextScript e cosmos-makers/writer-persona) são pequenos, de nicho, voltados a artigos/mensagens e de manutenção incerta; trate-os como inspiração, não como fundação.
- **Licenças a evitar para uso comercial:** `TextMachina` (Genaios) é **CC-BY-NC-ND-4.0 — não comercial e sem derivados**; `gpt_annotate` e `core-stories` **não têm arquivo de licença** (por padrão, todos os direitos reservados); `ScreenPy` tem licença ambígua; ferramentas em **R** como `stylo`/`syuzhet` são GPL; a lib Python **`krippendorff`** (Peça 5) também é **GPL-3.0** — mesma família de cautela, mas esse foi exatamente o motivo pelo qual `_docs/decisions.md#28(d)` a rejeitou (**NÃO ADOTADA**, ver a linha própria dela acima), não uma ressalva aceita sobre uma lib que este projeto usa: um copyleft real é um bloqueio de fato, não uma nota de rodapé, caso a decisão de uso não-comercial (`DECISOES.md` item 3) seja revista um dia. Verifique o arquivo LICENSE antes de embutir qualquer um em produto pago.
- **`whisperX`:** o LICENSE é **BSD-2-Clause** (comercial-friendly, sem cláusula de propaganda) — alguns blogs secundários erram ao chamá-lo de Apache ou BSD-4; confie no arquivo LICENSE do repositório.
- **[CONFIRMADO EM PRODUÇÃO] Limites de scraping do YouTube:** este risco se materializou na Fase 1 e custou 9 vídeos, resolvidos por whisperX local (`_docs/decisions.md#3`, `#4`). Obtenção em massa de transcrições pode violar Termos de Serviço em escala e bater em limites de IP; para uso comercial, revise a base legal e considere a API oficial de legendas quando aplicável.
- **Qualidade dos "money printers":** repositórios de automação de YouTube com muitas estrelas frequentemente priorizam volume sobre qualidade editorial; você já percebeu isso, e a evidência confirma — a etapa de roteiro deles é um único prompt genérico.
- **Contagens de estrelas e datas** são aproximadas (agosto de 2026) e mudam; algumas licenças tinham sinais conflitantes entre fontes e foram sinalizadas para verificação direta no arquivo LICENSE.
- **[REVISTO v2.0] Segmentação topical não serve a este projeto.** A recomendação original de `wtpsplit` + TextTiling assumia que fronteira de tópico aproximaria fronteira de função. Não aproxima. Registrado aqui para que a decisão não seja revertida por engano meses depois — a contingência correta é EDU/RST, não TextTiling.
- **[REVISTO v3.0] Idioma:** o corpus e a saída do projeto são em **inglês**, então a ressalva original (métricas de legibilidade calibradas para inglês, exigindo validação em PT) **deixou de se aplicar**. Ela volta a valer se algum dia um canal em português entrar — e nesse caso a recalibração é por canal, não global. `wtpsplit` e `isanlp_rst` suportam PT-BR, o que mantém essa porta aberta.
- **[NOVO v3.0] Ontologia global vs. multi-canal:** os esquemas de anotação narrativa listados na Peça 2 são todos concebidos para um corpus homogêneo. Aplicar uma ontologia única a vários canais é decisão deste projeto, não algo que a literatura resolva — e o custo aparece quando ela precisa de versão nova, porque todos os corpus já anotados precisam ser reanotados para continuarem comparáveis.
