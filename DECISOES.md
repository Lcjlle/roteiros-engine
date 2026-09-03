# Decisoes da Fase 0

Decisoes de produto, tomadas pelo dono do projeto antes de qualquer issue
de Fase 1 em diante ser groomada - as tres originais da Fase 0
(canal-fixture, duracao-alvo, uso comercial) mais duas que a substituicao
oficial v3.0 introduziu (canal de referencia definitivo, modelo de
anotacao). Ver `_docs/plano_implementacao.md`, Fase 0, para os criterios de
cada uma.

## 1. Canal de referencia

Status: **decidido**.

Canal: https://www.youtube.com/@Zenn0009

Criterios (>=30 videos longos publicados, formato consistente, legendas
disponiveis, um formato que valha a pena reproduzir): **verificados na
Fase 1 (issue #1), achado registrado aqui**. `yt-dlp --flat-playlist
--dump-json` contra o canal real mostra 34 videos na aba `/videos`, todos
com duracao >= 180s (nenhum short), formato consistente (video explicativo
curto, tipicamente 7-13 min, um "efeito"/pergunta por titulo), e legenda
automatica em ingles disponivel (`youtube-transcript-api` confirmado
funcionando em 21 dos 30 videos selecionados antes da coleta real bater
num bloqueio de IP do YouTube - ver o comentario de fechamento da issue #1
para os detalhes). O canal tem exatamente 34 videos longos, o minimo para
o portao de 30 caber com folga de 4.

Achado que nao estava previsto: o canal e jovem - o video mais antigo
listado data de ~5 meses antes da coleta (2026-09-02), ou seja **nenhum
video tem mais de 6 meses**. A regra de selecao da Fase 1
("melhor desempenho relativo... entre videos com mais de 6 meses")
portanto nao tem nenhum video elegivel sob a leitura estrita; `src/coleta.py`
implementa o recuo explicito que o proprio plano permite ("ou simplesmente
os 30 mais vistos"): quando menos de 30 videos passam no filtro de 6 meses,
a selecao usa o conjunto inteiro de videos longos, sempre ranqueado por
views - continua nao sendo "os 30 mais recentes", so muda o tamanho do
grupo elegivel. Ver `tests/test_coleta.py::TestSelectVideos` para os testes
desse comportamento.

Idioma do canal: **ingles** (titulos e legenda confirmados na coleta real
da issue #1). Idioma dos roteiros gerados: ingles. `textstat` e as metricas
de ritmo (palavras por minuto) sao calibradas para ingles e se aplicam
diretamente - a recalibracao para portugues que este item previa deixou de
ser necessaria. A comunicacao do projeto com humanos continua em PT-BR (ver
a politica de idioma normativa em `_docs/plano_implementacao.md`).

## 2. Duracao-alvo do roteiro gerado

Status: **decidido**.

10 a 12 minutos.

## 3. Uso comercial

Status: **decidido**.

Nao comercial. `TextMachina` (CC-BY-NC-ND) e repositorios sem arquivo
`LICENSE` (`gpt_annotate`, `core-stories`) continuam de fora como
dependencia mesmo assim - ver `_docs/decisions.md` se algum dia isso mudar.

## 4. Canal de referencia definitivo (a ontologia e derivada dele)

Status: **decidido**.

Canal: https://www.youtube.com/@MackExplains7

Distinto do item 1: `@Zenn0009` e o canal-fixture que validou o codigo de
coleta (M1/Fase 1) e nao e mais tratado como o canal do qual a ontologia
sai - essa e a redefinicao da v3.0 (ver `_docs/plano_implementacao.md`,
"Como escolher o canal de referencia"). `@MackExplains7` e o canal
definitivo para a Fase 3.

**Nao verificado ainda:** os criterios praticos da Fase 1 (>=40 videos
longos elegiveis, formato consistente, legenda em ingles disponivel) nao
foram confirmados contra este canal via `yt-dlp --flat-playlist
--dump-json`, do jeito que a Issue #1 verificou `@Zenn0009` e registrou o
achado aqui (item 1 acima). Isso so acontece quando a issue de Fase 1 para
`@MackExplains7` for aberta, groomada e rodar de fato - nao assuma que ja
passou no portao so porque o canal foi escolhido.

## 5. Modelo de anotacao

Status: **decidido**.

Claude Sonnet 5 (Anthropic) - usado pelo runner de anotacao da Fase 5
(`instructor` sobre este modelo) e gravado em `perfis/<canal>.perfil.json`
-> `annotator.model`, para o perfil ser reproduzivel.

---

Portao: as cinco decisoes estao preenchidas. Em uma frase: um sistema que
gera roteiros de 10-12 min no perfil do canal @MackExplains7 (canal
definitivo, item 4), anotado com Claude Sonnet 5 (item 5), para uso nao
comercial. @Zenn0009 segue como fixture que ja validou apenas o codigo de
coleta (M1/Fase 1) - a anotacao (Fase 4/5) ainda nao rodou contra nenhum
canal. Issue #1 (Fase 1 - Coleta) ja rodou contra `@Zenn0009`; a proxima
issue de Fase 1 roda contra `@MackExplains7` e pode ser aberta e groomada.
