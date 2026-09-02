# Blueprint de repositórios open-source para um sistema de produção de roteiros educativos em escala

## TL;DR
- **A sua arquitetura (perfil lento + verificado por humano × execução rápida e repetível) é sólida e cada peça técnica já tem ferramenta pronta e madura** — segmentação de texto, saída JSON validada, anotação de corpus, transcrições, estilometria, montagem de vídeo. O que NÃO existe pronto é a peça central: a *ontologia autoral fechada* do seu nicho e o repo que faça o combo completo "perfil de um canal → gerar roteiros novos". Isso você terá de escrever.
- **Priorize um núcleo de bibliotecas permissivas e vivas:** `youtube-transcript-api` (MIT) + `yt-dlp` (Unlicense) para o corpus, `wtpsplit`/TextTiling para segmentar, `doccano` (MIT) para anotar segundo o seu esquema fechado, `instructor` (MIT) ou `outlines` para forçar JSON conforme schema, `simpledorff`/`krippendorff` para medir concordância, `textstat` (MIT) + estilometria para o perfil estilístico, e `MoviePy` (MIT) para montagem. Todos com licença comercial-friendly.
- **Cuidado com os "sistemas prontos de YouTube":** MoneyPrinterTurbo (MIT, 113k estrelas) e ShortGPT (MIT, semi-abandonado) servem como referência de pipeline e como montadores, mas nenhum implementa a sua abordagem de perfil estruturado — são geradores "tema→vídeo" de qualidade genérica. Use-os para peças de montagem, não para a inteligência do roteiro.

## Key Findings

**1. Não há repositório único que faça o combo que você quer.** A busca confirma que o espaço é fragmentado entre (a) ferramentas de *extração* de estilo/estrutura e (b) ferramentas de *geração* condicionada. Os matches mais próximos do loop "extrair perfil → salvar JSON → gerar texto novo" são projetos pequenos e de nicho voltados a artigos ou mensagens pessoais (ex.: Qusto/TextScript, cosmos-makers/writer-persona, shannhk/writing-style-extractor), não a roteiros de canal. Existe também um paper descrevendo exatamente esse pipeline de duas etapas ("Author Writing Sheet" → geração), mas é método acadêmico, não repositório mantido. Isso valida a sua decisão de construir o motor você mesmo — e reforça que o valor do seu sistema está exatamente na peça que ninguém empacotou.

**2. A ontologia autoral não existe pronta.** Existem esquemas de anotação narrativa acadêmicos (Labov & Waletzky, Freytag, Story Intention Graph de Elson, turning points de Papalampidi), mas todos medem estrutura de *ficção/enredo*, não decisões autorais de um roteiro educativo de YouTube (gancho, promessa, prova, tangente, CTA, recapitulação etc.). Você usará esses esquemas como inspiração conceitual, mas a lista fechada de campos será sua.

**3. Toda a "plataforma" ao redor da ontologia é bem servida por software maduro e permissivo.** Transcrição, segmentação, anotação, validação de JSON, concordância entre anotadores e montagem de vídeo têm bibliotecas ativas e MIT/BSD/Apache.

## Details

### Peça 1 — Segmentação de texto/discurso em unidades

O seu corpus virá de transcrições sem pontuação limpa nem parágrafos, então você precisa de duas coisas: restaurar fronteiras de sentença e depois segmentar por tópico/unidade.

- **segment-any-text/wtpsplit** — https://github.com/segment-any-text/wtpsplit — Modelos SaT/WtP para segmentar texto em sentenças/unidades de forma robusta mesmo *sem pontuação*, em 85 idiomas (inclui português). Python, PyTorch/ONNX. 1,3k estrelas; Release 2.2.1 em 11 de abril de 2026 (por markus583). Licença **MIT**. **Resolve:** transformar a transcrição crua em unidades limpas antes de anotar. **Dificuldade:** baixa-média — `pip install wtpsplit`, poucas linhas.
- **TextTiling** (implementação clássica) — disponível dentro do **NLTK** (`nltk.tokenize.texttiling`), licença Apache-2.0, e em variantes como **riedlma/topictiling** (LDA) e **chschock/textsplit** (embeddings). **Resolve:** segmentação topical não supervisionada (quebra onde o assunto muda). **Dificuldade:** baixa via NLTK; média nas variantes.
- **Segmentação por discurso/RST (EDU):** **tchewik/isanlp_rst** — https://github.com/tchewik/isanlp_rst — parser RST multilíngue **com suporte a português do Brasil**, retorna árvore de unidades discursivas elementares (EDUs) com relações. **Resolve:** segmentação fina e rotulagem de relações retóricas, caso você queira granularidade abaixo do parágrafo. **Dificuldade:** média-alta (Docker recomendado). Para conversão de formatos RST há **amir-zeldes/rst2dep** (pip).
- **Avaliação:** **cfournie/segmentation.evaluation** (`segeval`, PyPI) — métricas Pk, WindowDiff, Boundary Similarity e coeficientes de concordância entre anotadores para segmentação. Licença **BSD-3-Clause**, estável. **Resolve:** medir se a segmentação automática bate com a sua segmentação-ouro.

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
- **dottxt-ai/outlines** — geração com *constrained decoding* (mascara tokens inválidos, garante schema no nível do token). ~12k estrelas, Apache-2.0. **Melhor quando** você roda modelos locais (transformers/llama.cpp/vLLM) e quer throughput alto sem retries. **Dificuldade:** média.
- **Structured Outputs nativos** (OpenAI `strict: true`, Anthropic tool_use) cobrem o caso 80% sem lib extra, se você já usa esses provedores.
- **Pydantic-AI** — se depois quiser evoluir para "agentes" com ferramentas; hoje, overkill.

### Peça 5 — Anotação de corpus com LLM em lote + concordância

- **npangakis/gpt_annotate** — https://github.com/npangakis/gpt_annotate — pacote que anota texto em lote com GPT, roda cada item várias vezes, e **compara com rótulos humanos (gold standard)**. **Porém:** **sem arquivo de licença** (todos os direitos reservados por padrão) e inativo (~2023). Use como referência de metodologia, não como dependência comercial.
- **LLMAnnotationResearch/llm-annotation-framework** — código do paper de Wharton "The Use of LLMs to Annotate Data" com *sensitivity checks*. Bom como guia metodológico de validação.
- **Concordância entre anotadores:** **simpledorff** (Krippendorff's alpha em uma linha sobre DataFrame), a lib **krippendorff**, e **nltk.metrics.agreement** (Cohen/Fleiss kappa). **Resolvem:** medir se o LLM-anotador concorda com o humano acima do limiar aceitável (α ≥ 0,667 por Krippendorff; α ≥ 0,8 ideal). Este é o seu portão de qualidade para dizer "o perfil é confiável".
- **Frameworks de apoio:** `llmClassificR`, `gpt_annotate` e vários pipelines "LLM-as-annotator" recentes confirmam a prática de rodar o modelo com `temperature` baixa e validar por auto-concordância + amostra humana.

### Peça 6 — Pipeline de transcrições do YouTube

- **jdepoix/youtube-transcript-api** — https://github.com/jdepoix/youtube-transcript-api — pega transcrições/legendas (inclusive autogeradas, com tradução) sem API key nem browser. 8k estrelas, release v1.2.4 de 29 de janeiro de 2026 (ativo), licença **MIT**. **Resolve:** montar o corpus de um canal rapidamente. **Dificuldade:** baixa. Cuidado: uso em escala esbarra em limites de IP (relatos de ~100-200 req/hora por IP) e pode exigir revisão legal para uso comercial.
- **yt-dlp/yt-dlp** — https://github.com/yt-dlp/yt-dlp — baixa legendas (`--write-subs`/`--write-auto-subs`), metadados e áudio de vídeos, playlists e canais inteiros. Licença **Unlicense** (domínio público) no código-fonte; note que binários empacotados via PyInstaller incluem código GPLv3+. **Resolve:** enumerar todos os vídeos de um canal e obter legendas/áudio em massa.
- **m-bain/whisperX** — https://github.com/m-bain/whisperx — quando não há legenda, transcreve com Whisper + *forced alignment* (wav2vec2) para timestamps por palavra (±50 ms), com diarização opcional. ~23,6k estrelas, licença **BSD-2-Clause** (o arquivo LICENSE lista apenas duas condições — retenção do aviso de copyright em código-fonte e em binário — sem cláusula de propaganda, ao contrário do que alguns secundários afirmam; portanto é comercial-friendly). **Resolve:** alinhar texto e áudio quando você precisar de timing preciso (ex.: para cortar o vídeo por segmento). **Dificuldade:** média (GPU recomendada). Alternativas: `stable-ts`, `aeneas` (forced alignment leve).

### Peça 7 — Métricas de texto para o perfil estilístico

- **textstat/textstat** — https://github.com/textstat/textstat — legibilidade (Flesch, Flesch-Kincaid, Gunning-Fog, SMOG etc.), contagem de sílabas, densidade — com suporte a variantes de idioma. ~1,4k estrelas, **MIT**, mantido. **Resolve:** dimensões objetivas do perfil (nível de leitura, comprimento médio de frase). **Dificuldade:** baixa.
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

**Estágio 0 — Prova de conceito (1–2 fins de semana).** Escolha 10–20 vídeos de UM canal de referência. Baixe as transcrições com `youtube-transcript-api` (fallback `yt-dlp` → `whisperX` se não houver legenda). Limpe e segmente com `wtpsplit` + TextTiling. *Benchmark para avançar:* você consegue produzir um JSONL com um segmento por linha, legível.

**Estágio 1 — Ontologia + gold standard (o passo insubstituível, feito por você).** Escreva a v0 da sua lista fechada de funções de roteiro (ex.: `gancho`, `promessa`, `contexto`, `prova`, `exemplo`, `tangente`, `recapitulação`, `transição`, `CTA`). Anote manualmente ~5 vídeos no **doccano**. *Benchmark:* a ontologia cobre >90% dos segmentos sem precisar de "outros"; se não, revise a lista antes de escalar.

**Estágio 2 — Anotação assistida por LLM + validação.** Use `instructor` para rotular o resto do corpus contra a ontologia (JSON validado, `temperature` baixa, 3 execuções). Meça a concordância LLM×humano com `simpledorff`. *Benchmark decisivo:* Krippendorff's α ≥ 0,667 no seu gold standard. Abaixo disso, o rótulo automático não é confiável — melhore as definições da ontologia (não o modelo) e repita. Este é o gatilho que muda tudo: só agregue o perfil quando passar o limiar.

**Estágio 3 — Agregação do perfil (JSON).** Agregue as anotações validadas em estatísticas: distribuição e ordem típica das funções, duração média por função, arco de sentimento (`core-stories`/léxico próprio), legibilidade (`textstat`), impressão estilométrica (`faststylometry`). Salve como o `profile.json` versionado — imite o padrão de engenharia do canlab (esquema versionado, agregação separada da anotação).

**Estágio 4 — Motor de execução.** Um script que lê `profile.json` e, via `instructor`/`outlines`, gera um novo roteiro estruturado (mesma ontologia) respeitando as distribuições do perfil. *Benchmark:* rode o roteiro gerado pelo mesmo anotador do Estágio 2 e verifique se a distribuição de funções bate com o perfil (distância baixa).

**Estágio 5 — Montagem.** TTS + `MoviePy` (ou fork das partes de montagem do MoneyPrinterTurbo) para roteiro→vídeo. Só automatize esta etapa depois que a qualidade do roteiro estiver estável.

**O que mudaria a rota:** se a concordância do Estágio 2 nunca passar de ~0,5 mesmo com ontologia revisada, o problema é que suas categorias são subjetivas demais — simplifique para menos campos e mais objetivos. Se você precisar de timing por palavra para cortes, priorize `whisperX` desde o Estágio 0.

## Caveats
- **Nenhum repo faz o combo completo.** Os matches mais próximos (projetos tipo "extrair perfil de estilo → gerar texto", como Qusto/TextScript e cosmos-makers/writer-persona) são pequenos, de nicho, voltados a artigos/mensagens e de manutenção incerta; trate-os como inspiração, não como fundação.
- **Licenças a evitar para uso comercial:** `TextMachina` (Genaios) é **CC-BY-NC-ND-4.0 — não comercial e sem derivados**; `gpt_annotate` e `core-stories` **não têm arquivo de licença** (por padrão, todos os direitos reservados); `ScreenPy` tem licença ambígua; ferramentas em **R** como `stylo`/`syuzhet` são GPL. Verifique o arquivo LICENSE antes de embutir qualquer um em produto pago.
- **`whisperX`:** o LICENSE é **BSD-2-Clause** (comercial-friendly, sem cláusula de propaganda) — alguns blogs secundários erram ao chamá-lo de Apache ou BSD-4; confie no arquivo LICENSE do repositório.
- **Limites de scraping do YouTube:** obtenção em massa de transcrições pode violar Termos de Serviço em escala e bater em limites de IP; para uso comercial, revise a base legal e considere a API oficial de legendas quando aplicável.
- **Qualidade dos "money printers":** repositórios de automação de YouTube com muitas estrelas frequentemente priorizam volume sobre qualidade editorial; você já percebeu isso, e a evidência confirma — a etapa de roteiro deles é um único prompt genérico.
- **Contagens de estrelas e datas** são aproximadas (agosto de 2026) e mudam; algumas licenças tinham sinais conflitantes entre fontes e foram sinalizadas para verificação direta no arquivo LICENSE.
- **Português:** wtpsplit e isanlp_rst suportam PT-BR; a maioria das ferramentas de estilometria/legibilidade é calibrada para inglês — valide as métricas antes de confiar nelas em português.