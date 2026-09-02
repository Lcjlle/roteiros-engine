# Decisoes da Fase 0

Tres decisoes de produto, tomadas pelo dono do projeto antes de qualquer
issue de Fase 1 em diante ser groomada. Ver `_docs/plano_implementacao.md`,
Fase 0, para os criterios de cada uma.

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
da issue #1). Importa na Fase 6: legibilidade e palavras-por-minuto
calibradas para ingles nao transferem para portugues sem recalibracao (ver
`_docs/plano_implementacao.md`, Fase 6, passo 4).

## 2. Duracao-alvo do roteiro gerado

Status: **decidido**.

10 a 12 minutos.

## 3. Uso comercial

Status: **decidido**.

Nao comercial. `TextMachina` (CC-BY-NC-ND) e repositorios sem arquivo
`LICENSE` (`gpt_annotate`, `core-stories`) continuam de fora como
dependencia mesmo assim - ver `_docs/decisions.md` se algum dia isso mudar.

---

Portao: as tres decisoes estao preenchidas. Em uma frase: um sistema que
gera roteiros de 10-12 min no perfil do canal @Zenn0009, para uso nao
comercial. Issue #1 (Fase 1 - Coleta) pode ser aberta e groomada.
