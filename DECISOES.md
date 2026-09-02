# Decisoes da Fase 0

Tres decisoes de produto, tomadas pelo dono do projeto antes de qualquer
issue de Fase 1 em diante ser groomada. Ver `_docs/plano_implementacao.md`,
Fase 0, para os criterios de cada uma.

## 1. Canal de referencia

Status: **decidido**.

Canal: https://www.youtube.com/@Zenn0009

Criterios (>=30 videos longos publicados, formato consistente, legendas
disponiveis, um formato que valha a pena reproduzir): **nao verificados
aqui** - `yt-dlp` nao esta disponivel neste ambiente e a pagina do canal nao
foi inspecionada. A Fase 1 (Coleta) audita isso de qualquer forma: seu
portao exige um manifesto com 30 linhas e nenhuma transcricao abaixo de 60%
da contagem esperada de palavras. Se o canal nao passar, a Fase 1 falha e
este item volta a "em aberto".

Idioma do canal: **nao registrado ainda**. Confirmar na Fase 1 e anotar
aqui - importa na Fase 6 se o canal for em ingles e a producao em
portugues (recalibracao de legibilidade/palavras-por-minuto).

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
