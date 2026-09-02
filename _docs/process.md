- Tasks are GitHub issues, on `Lcjlle/roteiros-engine`
- Commit regularly

Labels

- `fase-N` - a issue pertence a Fase N de `_docs/plano_implementacao.md`
  (0 a 10). Toda issue carrega exatamente uma
- `blocked` - o portao da fase anterior ainda nao passou, ou `DECISOES.md`
  ainda tem um item "em aberto" que a issue precisa

Background

- `_docs/decisions.md` - as chamadas tecnicas ja feitas, com o motivo. Ler
  antes de gromear ou implementar, e nao reabrir uma decisao sem muda-la la
  primeiro
- `DECISOES.md` - as tres decisoes de produto da Fase 0 (canal, duracao-alvo,
  uso comercial). Sao do dono do projeto, nao do PM - nenhuma issue de
  Fase 1 em diante e groomada enquanto uma estiver "em aberto"
- `_docs/plano_implementacao.md` e `_docs/blueprint.md` - o plano de dez
  fases e o levantamento de ferramentas. Referencia, nao backlog - onde
  discordarem de `_docs/decisions.md` ou de uma issue, perdem

Roles

- PM - groom uma tarefa antes de alguem implementar, segue `_docs/team/pm.md`
- Engineer - implementa uma tarefa groomada, segue
  `_docs/team/software-engineer.md`
- QA - confere o resultado contra os criterios de aceite e contra o portao
  numerico da fase, segue `_docs/team/qa-engineer.md`


Orchestrator

A sessao principal e o orchestrator. Ela lanca o PM, o engineer e o QA como
subagentes. Ela mesma nao groom, nao implementa e nao testa.

O orchestrator possui tres coisas que os subagentes nao veem: a ordem de
dependencia do backlog (a ordem das fases, e dentro de uma fase, entre
issues), as worktrees, e a fila de merge.


Trabalhando em paralelo

O trabalho roda em ondas. Uma onda e um conjunto de issues que podem ser
construidas ao mesmo tempo sem esperar uma pela outra.

- Ate 5 agentes rodam ao mesmo tempo
- Toda issue de uma onda ganha sua propria worktree git e seu proprio branch
- Nada e implementado no checkout principal. Main e para grooming,
  integracao e os docs

Uma issue so entra numa onda quando todas estas condicoes valem:

- Toda issue da qual ela depende esta fechada e mergeada na main
- O portao da fase anterior em `_docs/plano_implementacao.md` passou (nao so
  "a issue anterior fechou" - o numero do portao foi medido e ficou dentro
  do limite)
- Nenhuma outra issue da mesma onda adiciona migration na mesma tabela
- Nenhuma outra issue da mesma onda escreve no mesmo arquivo ou diretorio
  sob `corpus/<canal>/`, `gold/<canal>/`, `perfis/`, ou `schema/` para o
  mesmo canal
- O orchestrator leu a secao Constraints da issue e sabe quais arquivos e
  tabelas compartilhados ela toca

Tudo o mais espera a proxima onda. Uma onda e frequentemente menor que 5
porque o backlog fica sem trabalho independente, nao porque o limite foi
atingido - isso e normal, nao empurre uma onda para preenche-la.


Worktrees

Uma issue, uma worktree, um branch:

    git worktree add ../wt/<issue> -b issue-<issue> main

Cada worktree e um checkout completo e precisa da propria preparacao antes de
um agente tocar nela:

- `uv sync` - a worktree tem seu proprio `.venv`
- `.env` copiado do checkout principal, com `DATABASE_URL` apontado para um
  banco proprio, `roteiros_wt<issue>`
- `CREATE DATABASE roteiros_wt<issue>` dentro do container Postgres. Se o
  nome ja estiver em uso, escolha um novo em vez de derrubar o existente
- `uv run alembic upgrade head` contra esse banco, antes de qualquer teste

A parte do banco nao e opcional. `.env` esta no `.gitignore` e `src/db.py`
le `DATABASE_URL` de la (via `load_dotenv()`), entao cada worktree fica com
seu proprio banco. Duas worktrees compartilhando um `DATABASE_URL` derrubam
dados uma da outra no meio de um run, e as falhas parecem bugs impossiveis
no codigo em vez do que realmente sao.

Ha uma pegadinha que vale saber. Uma variavel de ambiente real vence o
`load_dotenv()`, por design - e isso que permite a CI nao carregar `.env`
nenhum. Entao se o terminal que abriu a sessao exporta `DATABASE_URL`, isso
esconde silenciosamente o `.env` de toda worktree e coloca todas de volta no
mesmo banco.

A guarda contra isso: rode comandos com o banco nomeado explicitamente -
`DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/roteiros_wt<issue> uv run pytest`
- e confirme antes de um agente comecar, nao depois de reportar uma falha
misteriosa: `uv run python -c "import os; print(os.environ['DATABASE_URL'])"`
precisa imprimir o banco da propria worktree.

Isolamento de teste: `tests/conftest.py` cria `<banco>_test` a partir de
`DATABASE_URL` e roda cada teste numa transacao com rollback - ver
`_docs/decisions.md#2`. Um teste que usa `db_session` nunca deixa estado
visivel pro proximo teste nem pro banco de desenvolvimento da worktree.

Uma suite por vez dentro de uma worktree. O banco e por worktree, nao por
processo, entao dois runs de `pytest` comecados juntos na mesma worktree
disputam o mesmo banco por baixo um do outro. Isso produz uma dispersao de
falhas que parece uma regressao real e nao e - repita sozinho antes de
acreditar num run que falhou de forma estranha.

O mesmo vale para qualquer coisa lenta - um script de anotacao em lote
rodando 1.350 chamadas de LLM (Fase 5), uma transcricao com `whisperX`, um
run de CI. Faca polling com um teto, e se nunca chegar, diga isso.
"Nao terminou em dois minutos" e um achado, e muitas vezes um FAIL. Silencio
nao e.

Nunca `pkill -f pytest` para limpar. Cada worktree roda sua propria suite
contra seu proprio banco, entao esse padrao alcanca o run de outro agente e
mata no meio de um teste - a vitima entao reporta uma suite abortada que
parece um branch quebrado e nao e. Mate um job de fundo pelo id que a
ferramenta deu, ou deixe terminar.

Um agente por worktree por vez. O banco e isolado por worktree, nao por
agente, entao um engineer ainda terminando numa worktree e um QA comecando
na mesma worktree compartilham um banco e derrubam dados um do outro. Um
implementador commita, faz push, e so depois o orchestrator aponta um QA
para essa worktree.

Isso vale para o orchestrator tambem. Uma suite morta por rodar muito tempo
nao necessariamente para - o processo `pytest` filho pode sobreviver ao
comando que o lancou, ainda segurando o banco. Comecar um segundo run entao
e a mesma auto-colisao. Antes de comecar um run numa worktree, confirme que
nao ha `pytest` vivo nela (`pgrep -af pytest`); uma falha em massa estranha
e repetida uma vez, sozinha e limpa, antes de ser acreditada.

Postgres em si fica um container unico. Bancos dentro dele sao baratos; um
segundo container nao e.

Uma worktree mergeada fica onde esta. Reuse-a para a proxima issue que cair
na mesma area, ou deixe-a parada.


Destrutivo trava o run

O harness confere comandos que destroem coisas e pede aprovacao de quem esta
rodando a sessao. Isso e o comportamento certo, mas para o trabalho todo ate
alguem estar no teclado. Uma onda de cinco agentes pode ficar parada a noite
inteira num `rm`.

Entao nada neste processo deleta. Nem worktrees, nem branches, nem arquivos
temporarios, nem dados de `corpus/`/`gold/`/`perfis/`.

- Restaure um arquivo que voce mudou de proposito com `git checkout -- <path>`
  ou `git restore <path>`, nunca copiando-o para outro lugar e apagando a
  copia
- Escreva arquivos temporarios no scratchpad da sessao, fora do repositorio,
  nunca em `/tmp` e nunca do lado do codigo
- Deixe worktrees e branches no lugar quando uma issue fecha

Se algo genuinamente precisa ser removido, essa e a decisao do usuario. Diga
o que deveria sair e por que, e deixe a pessoa rodar o comando.


Integracao

Branches mergeiam um de cada vez, nunca em paralelo, em ordem de
dependencia:

1. Rebase o branch na main atual
2. Rode a suite inteira e o linter de novo, na worktree, depois do rebase
3. Se a issue for a ultima da fase, rode tambem o script de portao da fase
   (`src/verifica.py` ou o que `_docs/plano_implementacao.md` nomear) e
   confirme que o numero medido passa no limite
4. Merge na main so se os passos acima estiverem limpos
5. Push na main
6. Feche a issue
7. Rebase todo branch ainda aberto da onda na nova main

O passo 7 e o que mantem a onda honesta. O segundo branch a mergear esta
sendo testado contra codigo que seu autor nunca viu, entao roda de novo
contra o resultado mergeado antes de ser confiado.

O passo 5 nao e burocracia. Um commit local e invisivel: quem e dono do
projeto abre o GitHub, nao ve nada, e nao tem como distinguir uma sessao
trabalhando de uma parada. Faca push da main assim que ela se mover.

Engineers fazem push do proprio branch tambem, assim que ele tiver um commit,
e de novo depois de cada rodada de correcao do QA.

Uma vez que o orchestrator faz rebase de um branch, o historico dele nao bate
mais com o de origin, e todo push depois disso e um force push - que trava e
espera aprovacao humana. Entao depois de um rebase o engineer para de fazer
push e diz isso; o orchestrator mergeia e empurra a main, e a main carrega o
trabalho. Ninguem force-pusha para consertar o branch.

Rebase e acao exclusiva do orchestrator - nunca vai numa instrucao de tarefa
pro engineer, nem "so pra pegar uma decisao nova da main". Se um engineer
precisa enxergar algo que acabou de entrar na main (ex.: uma entrada nova em
`_docs/decisions.md`), cole o conteudo direto no contexto da tarefa dele. Um
engineer instruido a rebasear a propria branch cai exatamente no caso da
regra acima - historico diverge, push vira force-push - e `_docs/team/
software-engineer.md` proibe force-push sem excecao, entao ele fica preso
entre a instrucao e a propria regra. Aconteceu uma vez (Issue #1, retry):
o orchestrator mandou `git rebase origin/main`, o SWE seguiu, forcou o push
pra resolver. Nao repita.

Conflitos se concentram em poucos arquivos compartilhados -
`schema/ontologia.v1.json`, `schema/codebook.md`, `src/db.py`,
`migrations/` (a cadeia de revisoes do Alembic, se duas issues da mesma
onda gerarem migration - ver a condicao de entrada em onda acima), `AGENTS.md`,
`.env.example`, `_docs/decisions.md`. O orchestrator resolve na integracao.


Lifecycle

1. Escolher a proxima onda: issues abertas cujas dependencias estao todas
   mergeadas e cujo portao da fase anterior ja passou
2. PM groom cada issue nao groomada da onda
3. Preparar uma worktree por issue, depois lancar um engineer por issue, em
   paralelo
4. QA verifica cada uma na sua propria worktree, em paralelo, assim que seu
   engineer termina - QA nao espera a onda inteira
5. Em FAIL, volta ao passo 3 so para essa issue, com o comentario do QA como
   entrada. O resto da onda continua
6. Em PASS, integra esse branch pela fila de merge e fecha a issue
7. Deixa a worktree no lugar
8. Repete ate o backlog esvaziar

Rules

- Uma issue por worktree, um engineer por issue
- Nao pule o passo 2, mesmo quando a tarefa parece obvia
- O engineer nao fecha a issue, o QA nao conserta o codigo
- Nao commita ate os testes passarem
- Um agente fica dentro da propria worktree. Ler a main e permitido,
  escrever nela ou em outra worktree nao e
- So o orchestrator mergeia, fecha issues, e decide sobre remover worktrees
