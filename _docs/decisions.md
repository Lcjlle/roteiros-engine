# Decisions

Calls made while grooming the backlog - technical and scope decisions, not
the three product decisions in `DECISOES.md`. Settled here so issues stop
re-litigating them.

Where this file and `_docs/plano_implementacao.md` or `_docs/blueprint.md`
disagree, this file wins.

## Indice

<!-- DECISIONS_INDEX_START -->

**#1** (transversal) - Postgres entra no stack ao lado do arquivo, não no lugar dele - schema/, codebook.md e perfis/ continuam arquivo; estado operacional pode virar tabela, decisão de issue futura.
Status: vigente

**#2** (transversal) - Isolamento de teste: banco `<db>_test` dedicado por worktree, cada teste roda numa transação com rollback (`join_transaction_mode="create_savepoint"`).
Status: vigente

**#3** (Fase 1) - Corpus da Fase 1 de @Zenn0009 aceito com 21 vídeos (não 30) depois do bloqueio de IP no vídeo 22/30 - redução autorizada pelo dono, não bug.
Status: parcialmente superseded por #4 (o piso ">= 21" vídeos para @Zenn0009)

**#4** (Fase 1) - Corpus de @Zenn0009 completado para 30 via fallback whisperX (GPU, batch_size=4, um subprocesso por vídeo) em vez de esperar o bloqueio de IP das legendas ceder.
Status: vigente

**#5** (Fase 1) - whisperX continua fallback, não vira caminho padrão de coleta - legenda continua primeira tentativa mesmo sabendo que o bloqueio de IP vai se repetir a cada canal novo.
Status: vigente

**#6** (Fase 1) - Sorteio de holdout: semente fixa 42, alvo 5 vídeos, piso 4 - abaixo disso o canal reprova o critério prático em vez de encolher mais.
Status: vigente

**#7** (Fase 1) - Manifesto ganha coluna `role` (`profile`/`holdout`), em inglês por ser identificador de dado novo, mesmo o resto do manifesto sendo PT-BR por dívida aceita.
Status: vigente

**#8** (Fase 1) - `WORDS_PER_MINUTE` de `src/coleta.py` corrigido de 140 para 150, para bater com o texto do portão da Fase 1 que sempre disse ~150 palavras/minuto.
Status: vigente

**#9** (Fase 1) - Corpus de @MackExplains7 fechado: 30 `profile` + 5 `holdout`, whisperX nos 30 `profile` depois do mesmo bloqueio de IP de @Zenn0009 se repetir.
Status: vigente

**#10** (Fase 2) - Fase 2 grooming: storage em arquivo (não Postgres), modelo `sat-3l-sm` do wtpsplit, `SAMPLE_SEED = 42`, escopo desta passada é só @MackExplains7.
Status: vigente

**#11** (Fase 2) - Portão da Fase 2, critério 3, medido FAIL real contra @MackExplains7 (106-141 janelas/vídeo) - contingência do plano (baixar `WINDOW_MAX_WORDS`) tentada e medida pior, causa raiz identificada como `WINDOW_MAX_SENTENCES` combinado com as sentenças reais do canal.
Status: vigente

**#12** (Fase 2) - Bandas fixas do critério 3 (`GATE_MIN/MAX_WINDOWS_PER_VIDEO = 25/60`) substituídas por uma banda proporcional à duração, `GATE_WINDOWS_PER_MINUTE = 5.6 +-40%`.
Status: superseded por #14

**#13** (Fase 2) - `group_windows()` passa a perseguir ativamente `WINDOW_MIN_SENTENCES` antes de fechar uma janela não-final, aceitando estourar `WINDOW_MAX_WORDS` até `GATE_MAX_WINDOW_WORDS` para chegar lá - correção de especificação, não decisão nova.
Status: vigente

**#14** (Fase 2) - Critério 3 do portão da Fase 2 reestruturado em 3a/3b (invariantes, tolerância zero), 3c (termômetro do canal, `blocking: false`, <= 15%) e 3d (tolerância, banda recalibrada para `GATE_WINDOWS_PER_MINUTE = 4.86 +-40%`).
Status: vigente

**#15** (Fase 2) - Issue #8 (`sentence_cut` FAIL): causa raiz fixada na sentenciação (M2), não no portão de janelas - confiança de fronteira do SaT sozinha não discrimina os casos.
Status: vigente

**#16** (Fase 3) - Grooming da Fase 3: @Zenn0009 ratificado como canal do teste de transferência, receita determinística de ~20 janelas (2 vídeos, semente 42), par de vídeos do teste de cobertura reaproveitado da Fase 2 (`lkLwp9o7Djk`/`5unhHRFkC7I`, 205 janelas, teto absoluto de 20), formato de citação do codebook (citação literal + `window_id`).
Status: vigente

**#17** (Fase 2) - Critério 1 do portão da Fase 2 passou exatamente no limite (5 de 50) - aceito como pass, registrado, não remedido nem reamostrado.
Status: vigente

**#18** (transversal) - Política de idioma: a tabela do README estava errada em três pontos (os arquivos reais estavam certos) - tabela reclassificada, nada traduzido.
Status: vigente

**#19** (Fase 3) - Issue #11 (tie-breaker de fronteira de `function`): reescrito para exigir zero lookahead e zero contagem de palavras, depois de dois FAILs seguidos de QA na mesma classe de defeito.
Status: parcialmente superseded por #20 (a frase "prior windows in the same video" da regra de pivô; classificação de boundary de 5unhHRFkC7I:j0075; taxa e lista de janelas de fronteira confirmadas, 5/205 -> 6/205)

**#20** (Fase 3) - Tie-breaker de fronteira de `function` reancorado ao contexto real que o anotador recebe na chamada (3 janelas anteriores, não o vídeo inteiro); "developed before" operacionalizado como semântico, nunca lexical.
Status: vigente

**#21** (Fase 6) - `scale` fica em v1 e a Fase 6 (`M7`) agrega `scale_trajectory` por terço narrativo do vídeo, nunca como distribuição marginal - decidido durante a Fase 3, medido antes de a Fase 6 ser groomada.
Status: vigente

**#22** (transversal) - Documentação ganha quatro camadas com prazo de validade declarado: portões e estado viram dado (`schema/portoes.json`, `_docs/estado.md` gerado), documentos narrativos param de ser lidos como estado vivo - "um número, um lugar".
Status: parcialmente superseded por #24 (a definição binária de Status no campo decision_ref)

**#23** (transversal) - Duas correções de processo: `fase-N` é regra de issue de fase, não de toda issue; "main é para... os docs" só vale para o conteúdo da documentação, não para a ferramenta que a gera.
Status: vigente

**#24** (transversal) - Índice de `_docs/decisions.md` ganha um terceiro `Status`: `parcialmente superseded por #N (fragmento)`, além de vigente/superseded - o binário do #22 não dava conta do caso #19/#20.
Status: vigente

**#25** (transversal) - `schema/portoes.json` ganha um registro de papel por canal (`channels`) e um filtro `applies_to_roles` por portão `per_channel`; `result_ref` de portão `human_judgment` vira por canal, sem herança entre canais; a seção `Fases abertas` de `_docs/estado.md` ganha uma ressalva de obsolescência gerada a partir do mesmo timestamp do bloco de metadados; `_docs/decisions.md` ganha uma regra real de fronteira para correção in-place de uma entrada já publicada.
Status: parcialmente superseded por #27 (fragmento: o exemplo de codigo inline do (a)(3))

**#26** (transversal) - `scripts/pin_worktree_database.py` fixa o `DATABASE_URL` de cada worktree via um `sitecustomize.py` gerado, iniciando a convenção do diretório `scripts/` para tooling de dev-infra avulso.
Status: vigente

**#27** (transversal) - Exemplo de código do `#25(a)(3)` parcialmente superseded pelo `exists=False` real da Issue #15 (primeiro uso real da regra de correção in-place do `#25(d)`); `fase1-profile-row-floor` em @Zenn0009 reconfirmado como mecanismo já decidido pelo `#25(a)`, não achado novo; falha silenciosa do `gh issue list` em `_open_phase_issues()` registrada como vão aceito, distinto do drift do `#25(c)`.
Status: vigente

**#28** (Fase 4) - Orçamento de contexto da Fase 4↔Fase 5 (bundle de 3 janelas de contexto + alvo) garantido por construção via uma única função de geração de bundle, compartilhada entre o exportador de gold da Fase 4 e o prompt builder da Fase 5; o alfa de `density` passa a usar uma distância ordinal de Krippendorff implementada pelo próprio projeto como closure, consumida por `nltk.metrics.agreement.AnnotationTask` (Apache-2.0), rejeitando o pacote `krippendorff` (GPL-3.0).
Status: vigente

**#29** (Fase 4) - Mecanismo de anotação-ouro da Fase 4 tornado concreto: `doccano` descartado em favor de um worksheet JSONL com `display_id`/`window_id` em arquivos separados, nomes de módulo fixados (`src/context_budget.py`, `src/valida.py`), o scan de candidatos a `cta` e o sorteio do gold/reanotação de `#28(c)` calculados como exemplo verificável contra `@MackExplains7` (8/30 candidatos, sorteio de exemplo) para as acceptance criteria da issue #18 - a seleção oficial continua sendo entregável dessa issue, não desta entrada -, e `evidence_type` excluído do `passed` binário de `fase4-self-agreement-alpha`.
Status: vigente

<!-- DECISIONS_INDEX_END -->

## 1. Postgres joins the stack, alongside file - not instead of it

`src/db.py` (SQLAlchemy) and `migrations/` (Alembic) are real infrastructure
now: `compose.yaml` runs a `db` service, and the squad's worktree isolation
(`_docs/process.md`) uses one database per worktree, `roteiros_wt<issue>`,
the same pattern `retroloop` uses.

This does not reopen `_docs/blueprint.md`'s "Por que arquivo em vez de
banco". `schema/ontologia.v1.json`, `codebook.md`, and
`perfis/<canal>.perfil.json` stay versioned files - they are read by humans,
diffed in review, and frozen per phase on purpose. What moves to Postgres is
whichever operational, queryable pipeline state a future issue's engineer
decides belongs there (corpus manifest, per-block annotations, agreement
runs, generation runs) - no table is defined yet, because no issue past
Fase 0 has been groomed.

Why: the squad process this project adopted (`_docs/process.md`) is ported
from `retroloop`, and its parallel-worktree QA/Engineer isolation depends on
each worktree owning a real, disposable resource a suite can write to
without colliding with another agent's run. A file-only design achieves the
same isolation only by convention (no two issues in a wave touch the same
path) - which still holds for `corpus/`/`gold/`/`perfis/`/`schema/` - but a
database gives that isolation for free for anything relational, the same way
it does for `retroloop`.

Open, deliberately: which entities actually live in a table. That is for
the first issue that adds a database model to decide and log here, not for
this scaffolding pass. Test isolation strategy is resolved - see item 2
below.

## 2. Test isolation: dedicated `_test` database, transaction-per-test rollback

`tests/conftest.py` derives `<db>_test` from `DATABASE_URL` (so a worktree's
own `roteiros_wt<issue>` gets its own `roteiros_wt<issue>_test`), creates it
if missing, and migrates it to head once per pytest session
(`db_engine` fixture). Each test that needs the database requests
`db_session`, which opens a connection, begins a transaction, and binds the
`Session` with `join_transaction_mode="create_savepoint"` - `commit()`
inside a test only commits a savepoint, and teardown rolls the outer
transaction back. Postgres DDL is transactional, so even a `CREATE TABLE`
inside a test vanishes with it. `tests/test_db_isolation.py` proves this
against a real database, not mocks.

Why: this is the documented SQLAlchemy 2.0 pattern for test isolation
("Joining a Session into an External Transaction"), and it is faster than
recreating the schema per test while giving every test the same guarantee
`pytest-django` gives retroloop for free - no test's writes are visible to
another test, or to the worktree's real `DATABASE_URL`.

Tests that never request `db_session` open no database connection at all,
so collecting the suite - and CI's `TEST_COUNTS` gate - never needs
Postgres up.

## 3. Fase 1 corpus size: 21 videos, not 30 - authorized reduction, not a bug fix

QA FAILed Issue #1 correctly: `corpus/zenn0009/manifesto.csv` did not exist
(0 rows vs. the 30 the issue's gate requires), because `collect()` only
writes the manifest after every selected video succeeds, and video 22/30
hit a real YouTube per-IP rate limit (`IpBlocked`) that did not clear during
the run - exactly the risk `_docs/blueprint.md` names ("~100-200 req/hora
por IP"). 21 real raw+clean transcript pairs are committed and correct.

The project owner authorized proceeding with the 21 videos actually
collected instead of blocking on all 30. This is a scope call, not
something QA or the Engineer may decide alone.

What changes: `collect()` writes `manifesto.csv` for however many videos it
successfully fetched, not only when all 30 succeed. The Fase 1 gate for
*this* corpus is **>= 21 rows** (the count already verified real and
committed - not a floor of 1, and not "whatever collect() happens to
produce"), none below 60% of expected word count. A run that produces fewer
than 21 rows is a FAIL, even under this relaxed gate - the waiver covers
"not all 30", not "any number". The fixed "30" in
`_docs/plano_implementacao.md` and in Issue #1's acceptance criteria is
superseded by this entry for `@Zenn0009`, specifically by ">= 21".

Consequence flagged, not solved here: Fase 4/5 of `_docs/plano_implementacao.md`
assume a 30-video corpus (5 gold + 25 batch-annotated). Whoever grooms the
Fase 4 issue re-derives that split from the actual corpus size at the time
(`corpus/zenn0009/manifesto.csv` row count), not from the plan's literal
numbers. If the IP block clears later and someone reruns collection to grow
the corpus toward 30, that is additive and fine; nothing here forbids it.

## 4. Corpus completed to 30 via whisperX (GPU) instead of waiting out the IP block

Resolves the consequence flagged in item 3. The YouTube IP block on the
legenda endpoints (`youtube_transcript_api` and `yt-dlp`'s subtitle
download - both confirmed still `IpBlocked`/`429` when retested) never
cleared. Audio download is a separate YouTube endpoint and was never
blocked, so the project owner authorized using the existing `whisperX`
fallback (already designed into `collect_transcript()`, previously unused
because it wasn't needed) to transcribe the 9 remaining videos locally on
GPU instead of waiting.

What changed to make this real, not hypothetical:

- `whisperx==3.8.6` added to `pyproject.toml` (BSD-2-Clause, confirmed
  against PyPI metadata and `_docs/blueprint.md`). This is a real
  dependency now, not the "not installed by default" fallback the original
  docstring in `fetch_via_whisperx` described - `tests/test_coleta.py`'s
  "no dependency" test now mocks the absence via `sys.modules` instead of
  relying on a genuinely missing package. Cost: `uv sync` pulls `torch`
  and the `nvidia-cu12-*` wheels even for CPU-only use of this repo, and
  CI's `uv sync --locked` will too - this is the real, ongoing weight of
  keeping whisperX available, not a one-time cost paid only on this
  machine.
- Real bug found and fixed: `fetch_via_whisperx` hardcoded
  `model.transcribe(audio, batch_size=16)`. On a 6GB VRAM GPU (RTX 4050
  laptop, `large-v2`, `int8_float16`) that OOMs every time - confirmed
  before the fix, on a real video. `batch_size` is now a parameter
  (`WHISPERX_BATCH_SIZE = 4` default), measured at ~4GB peak VRAM
  (`nvidia-smi`, in-process polling thread, not `torch.cuda.max_memory_allocated()`
  which only sees PyTorch's own allocator and undercounts CTranslate2's
  native CUDA memory by ~15x) across both the shortest (238s) and longest
  (777s) videos in the corpus - VRAM use is dominated by the model, not
  the audio length.
- Real bug found and fixed in the *collection script*, not in `src/`:
  calling `fetch_via_whisperx` for a second video in the same process
  OOM'd even at `batch_size=4` - GPU memory from the first video's model
  was never released. Fix was process isolation, one subprocess per video
  (fresh CUDA context each time), not a smaller batch size. Anyone
  scripting whisperX over a batch of videos again needs the same
  isolation; a future issue that wires this into `src/coleta.py` proper
  should decide where that isolation boundary lives (per-video subprocess
  inside `collect()`, most likely).
- Quality check before trusting the output: compared whisperX's
  transcript against the existing legenda transcript, word-for-word, on
  both the shortest and longest video already in the corpus (the two
  extremes). 99.2% and 99.64% lexical agreement (`difflib.SequenceMatcher`
  on normalized tokens) - the differences were homophones and number
  spelling, not factual drift.

`corpus/zenn0009/manifesto.csv` now has all 30 rows the plan's Fase 1
asks for: 21 `legenda`, 9 `whisperX`. Item 3's `>= 21` floor is
superseded by this - the corpus is complete, so Fase 4/5 can use the
plan's literal 5 gold + 25 batch split without re-deriving it.

## 5. whisperX stays fallback, not promoted to default collection path

`_docs/plano_implementacao.md` (v3.0 migration) and `_docs/blueprint.md`
flagged an open proposal: since multi-canal is now normal operation, the
YouTube caption-endpoint IP block from item 3/4 will recur on every new
channel, so invert `collect_transcript()` to try whisperX first and treat
captions as an opportunistic shortcut.

The project owner declined this for now: **captions remain the default
path, whisperX remains the fallback**, unchanged from the current
`collect_transcript()` behavior. If a future channel's collection run hits
the same `IpBlocked`/`429` wall `zenn0009` did, the operator resolves it the
same way item 4 already did - fall back to whisperX locally for the videos
that failed, not a code change.

Consequence: the Fase 6 source-contamination check (comparing `style`
metrics between `legenda` and `whisperX` subsets when a corpus mixes both)
stays a real requirement for every future channel, not something whisperX
defaulting would have eliminated. `README.md` M1, `_docs/blueprint.md` Peça
6, and `_docs/plano_implementacao.md` Fase 1 item 2 are updated to point
here instead of carrying the proposal as still open.

## 6. Holdout draw: fixed seed 42, target 5, floor 4

Grooming Issue #2 (Fase 1 against `@MackExplains7`) hit a gap: the plan
mandates drawing holdout videos at random from the eligible pool, forbids
taking the tail by lowest `view_count`, and allows a range of "4-5" - but
names neither a count nor a seed. Without both, QA cannot reproduce the
same sample the engineer drew, and an underdetermined "4 or 5" makes the
result depend on an arbitrary runtime choice instead of a rule.

Decision: `HOLDOUT_SEED = 42`, target holdout size 5 (top of the plan's
range), falling back to 4 only if the eligible pool (after removing the 30
`profile` picks) has fewer than 5 videos left. If the eligible pool has
fewer than 34 total (30 profile + 4 minimum holdout), the run fails the
practical channel criterion (`DECISOES.md#4`) instead of silently
shrinking further - same posture as the `>= 21`/`>= 30` floor precedent in
item 3.

## 7. Manifest gains an English `role` column (`profile`/`holdout`)

Same grooming pass. The manifest's existing columns (`id`, `titulo`,
`duracao_s`, `contagem_palavras`, `fonte`) are PT-BR, covered by
`_docs/plano_implementacao.md`'s "Dívida aceita" clause - but that clause
covers only what was already committed before the v3.0 language policy,
not a new column being added now. The plan's normative language policy
requires English for code identifiers, including columns. Decision: the
new column is named `role`, with literal values `profile`/`holdout`.

## 8. `WORDS_PER_MINUTE` in `src/coleta.py` corrected from 140 to 150

Same grooming pass found a real, previously undocumented discrepancy:
`src/coleta.py` has used `WORDS_PER_MINUTE = 140` since Issue #1, while
`_docs/plano_implementacao.md`'s Fase 1 gate has always stated "~150
palavras/minuto em inglês" verbatim, with no entry here reconciling the
two. Per the plan's own precedence rule ("onde discordar de
`_docs/decisions.md`... ele perde"), absent an override here the plan's
number governs, and Issue #2 has to copy the gate verbatim - so the
constant moves to 150 to match.

This does not reopen or invalidate `@Zenn0009`'s already-passed Fase 1
gate: recomputed at 150 wpm, the worst-case transcript there (119.1% of
expected word count at 140 wpm per Issue #1's closing comment) is still
comfortably above the 60% floor. `corpus/zenn0009/*` is not touched by
this change.

## 9. `@MackExplains7` Fase 1 corpus: 30 profile + 5 holdout, whisperX for all 30

Resolves items 6/7/8 for real. `yt-dlp --flat-playlist --dump-json`
against `@MackExplains7` found 65 eligible long-form videos (well above
the 34-video floor item 6 requires), consistent question-style format,
and English auto-captions listed as available - but the same YouTube
caption-endpoint IP block from items 3/4/5 was still in effect
(`youtube_transcript_api` and `yt-dlp`'s subtitle endpoint both returned
`IpBlocked`/`HTTP 429` for every one of the 30 `profile` videos tried).
Per item 5, this is not a code change: the operator ran the existing
whisperX fallback (GPU, `batch_size=4`, one subprocess per video, same
isolation as item 4) for all 30 `profile` videos. The 5 `holdout` videos
were never transcribed, per the plan.

`corpus/mackexplains7/manifesto.csv` has 30 `profile` rows (all `fonte`
`whisperX`) + 5 `holdout` rows. Worst-case `profile` word ratio: 90.2% of
expected at 150 wpm (`6SapuAcHmDk`), comfortably above the 60% floor.
`DECISOES.md#4`'s "não verificado ainda" note is resolved with this run's
measured numbers.

## 10. Fase 2 storage stays file, `sat-3l-sm` as the starting SaT model, `SAMPLE_SEED = 42`, scope is `@MackExplains7` only

Grooming Issue #3 (Fase 2 - Sentenciação e janelas) left open exactly the
kind of gap `_docs/team/pm.md` has the PM close, not hand to the engineer:
one storage call `README.md`'s "Onde cada coisa é persistida" table lists
as "Postgres (conforme a issue definir)" without deciding, and two
thresholds `_docs/plano_implementacao.md` names a tool for but not a
specific value.

**(a) Storage: file, not Postgres.** `corpus/<canal>/sentences/<video_id>.json`
and `corpus/<canal>/windows/<video_id>.json` are versioned files, same
shape as `raw/<video_id>.json`. Item 1's argument for Postgres is
operational resumability - a job that can be interrupted mid-run and needs
to pick up by key, which is why M4's ~3,600 annotation calls will need a
table. Sentenciação/janelamento for ~30 videos is local, deterministic,
and has no network calls once `raw/` exists: a failed run just reruns from
the same `raw/` input and gets the same output, so there is nothing to
resume. Same file-vs-table criterion this file already applied to
`manifesto.csv` (item 3's precedent, never reopened).

**(b) wtpsplit model: `sat-3l-sm`.** The plan names the tool (`wtpsplit`,
item unchanged) and the language code (`en`) but not which SaT checkpoint.
`sat-3l-sm` (3 transformer layers, the general-purpose "-sm" checkpoint) is
the starting point for speed over `sat-12l-sm` (12 layers, higher
accuracy, slower). Contingency: if the Fase 2 gate's criterion 2
(sentences cut mid-clause) shows a real problem in the human-judged
sample, switch to `sat-12l-sm` and rerun `python -m src.sentencia` -
offset reattachment does not change, only the split boundaries do. Not a
call to make before that sample report is filled in.

**(c) `SAMPLE_SEED = 42`.** Same seed value and the same reason as
`HOLDOUT_SEED` (item 6): `src/amostragem.py`'s video/window draw for the
Fase 2 gate's criteria 1/2 has to be reproducible, so QA measures the
exact same 2 videos and 50 windows the engineer measured, not a fresh
draw.

**(d) Scope: `@MackExplains7` only, this pass.** Fase 2 runs against
`corpus/mackexplains7/` because that is the channel that unblocks Fase 3
(`DECISOES.md#4`). `@Zenn0009` already served its purpose as the Fase 1
collection fixture (item 3/4) and is not reprocessed here; its manifest
also predates the `role` column (item 7), so a future run against it would
need `run()` to treat a missing `role` as `profile` first - out of scope
for Issue #3.

## 11. Fase 2 gate, criterion 3: measured FAIL against `@MackExplains7`, and it is not fixable by the plan's stated contingency - flagged, not silently patched

`uv run python -m src.janelas` against the real `corpus/mackexplains7/sentences/`
(30 `profile` videos, generated by `uv run python -m src.sentencia`, `sat-3l-sm`)
produces 3,664 windows and criterion 3 **FALHOU** on all 30 videos: every one
has more than `GATE_MAX_WINDOWS_PER_VIDEO = 60` windows (106-141, at the
shipped `WINDOW_MAX_WORDS = 35`), plus 18 windows over `GATE_MAX_WINDOW_WORDS = 60`
words and 1,479 non-last windows below `WINDOW_MIN_SENTENCES = 2`.

Issue #3's own contingency text says: if criterion 3 fails, lower
`WINDOW_MAX_WORDS` from 35 to 25 and rerun `run()` (no re-sentencing). This
was evaluated against the real data (`group_windows`/`window_records`, the
shipped functions, not a rewrite) before touching the constant, and it makes
the failure **strictly worse**, not better: at 25 words, the corpus produces
114-188 windows/video (vs. 106-141 at 35) and 2,927 problems (vs. 1,527).
That is expected once you look at the failure mode - almost every video
already fails by having **too many, too small** windows, not too few, too
big ones. Lowering the word ceiling shrinks windows further and makes more
of them, moving further from the 25-60 target, not toward it. The plan's
contingency was written for the opposite failure mode (windows too large)
and does not apply here.

**Root cause, evidenced, not guessed:** the binding constraint isn't
`WINDOW_MAX_WORDS` at all - it's the fixed `WINDOW_MAX_SENTENCES = 4`
(unrelated to the "adjust the word limiar" contingency in the plan, and not
a value Issue #3 authorizes an engineer to change) combined with how many
sentences `@MackExplains7`'s videos actually contain. Every video's raw
sentence count divided by 4 (the hard floor on window count regardless of
`WINDOW_MAX_WORDS`, since a window can never exceed 4 sentences) already
exceeds 60 for 20 of the 30 videos (up to `ceil(322/4) = 81` for the
longest), and this floor is unaffected by *any* value of `WINDOW_MAX_WORDS` -
confirmed by sweeping the real functions from `WINDOW_MAX_WORDS = 25` through
`150`: `videos_out_of_range` never drops below 20, and `max_windows` floors
at 81 (`pJYm-8WQbEE`, 322 sentences) because the run always hits the
4-sentence cap before the word cap once `WINDOW_MAX_WORDS` is large enough.

**Why the corpus has this many sentences per video:** `_docs/plano_implementacao.md`'s
Fase 0 target duration is 10-12 minutes (`plano_implementacao.md` line 234).
`@MackExplains7`'s actual `profile` videos run 1,039-1,586 s (17-26 minutes,
`corpus/mackexplains7/sentences/*.json`'s `duration_s`) - roughly double the
planning assumption the 25-60-windows-per-video / 60-words-per-window
bounds were sized against. **Median sentence length here is 11 words (mean
13.82, rounds to 14 - the original text of this entry said "median... 14
words", conflating the two; corrected in place, `sat-3l-sm`, verified
against the real output, not assumed);** at `WINDOW_MAX_SENTENCES = 4` that
puts a natural window size around 44-55 words (median x4 to mean x4), close
to the gate's own per-window ceiling - there is no room left to also shrink
window *count* into `[25, 60]` for a video this long without either raising
`GATE_MAX_WINDOWS_PER_VIDEO` or raising `WINDOW_MAX_SENTENCES`, neither of
which this issue's acceptance criteria authorize an engineer to change
unilaterally. This correction does not touch the causal argument two
paragraphs above (`ceil(sentence_count / 4)` already exceeding 60 for 20 of
30 videos) - that argument never depended on this number.

**What this entry does and does not decide.** It does not change
`WINDOW_MAX_WORDS`, `WINDOW_MAX_SENTENCES`, or any `GATE_*` constant -
`src/janelas.py` ships with the exact values Issue #3's acceptance criteria
specify (`35`/`4`/`2`/`60`/`25`/`60`), and `corpus/mackexplains7/windows/*.json`
is the real, un-doctored output of running them, gate result FALHOU as
measured. Silently picking a different `WINDOW_MAX_WORDS` to make the
printed line say PASSOU, when the evidence above shows no value of that one
constant can, would misreport the measured gate - worse than reporting a
true FAIL. This is flagged on Issue #3 for the project owner/PM to resolve
(likely candidates: raise `GATE_MAX_WINDOWS_PER_VIDEO`, raise
`WINDOW_MAX_SENTENCES`, or accept that this channel's window density is
higher than the plan assumed and re-derive the gate's bounds from it) -
it is a scope/threshold call, not something `_docs/team/software-engineer.md`
has an engineer decide alone. Resolved by item #12 (bounds re-derivation),
item #13 (`group_windows()` construction fix), and item #14 (criterion 3
restructured into 3a-3d) below.

## 12. Fase 2 gate, criterion 3: bounds re-derived from real video duration, not fixed constants

Context (full detail lands with `issue-3`'s own `decisions.md#10`/`#11` on
merge - not duplicated here): item #10 fixed Fase 2's storage/model/seed
calls; item #11 measured the plan's fixed `25-60 janelas por vídeo`
(criterion 3, `_docs/plano_implementacao.md` line 312) FAILing on all 30
`@MackExplains7` `profile` videos (106-141 windows/video measured), traced
the binding constraint to `WINDOW_MAX_SENTENCES=4` combined with this
channel's real sentence counts (not fixable by the plan's own
`WINDOW_MAX_WORDS` contingency, confirmed worse when tried: 114-188/video),
and flagged that the fixed 25-60 range itself was sized for Fase 0's
10-12 minute target duration (line 234) while `@MackExplains7`'s real
videos run 17-26 minutes - roughly double. This entry resolves that flag:
re-derive criterion 3's bounds from the channel's real duration/density,
per the project owner's decision that the fix is a re-derivation, not the
plan's contingency and not a change to `WINDOW_MAX_SENTENCES`.

**Measured** (30 `profile` videos, `corpus/mackexplains7/sentences/` and
`corpus/mackexplains7/windows/*.json`, real un-doctored pipeline output,
`WINDOW_MAX_WORDS=35`/`WINDOW_MAX_SENTENCES=4` unchanged):

- duration: mean 22.43 min, median 22.15 min, range 17.32-26.43 min
- sentences/video: mean 246.4, median 266, range 123-322
- windows/video: mean 122.1, median 121.5, range 106-141
- windows-per-minute (windows/video ÷ duration_min, the unit the new gate
  is expressed in): mean 5.48, median 5.62, range 4.17-6.76, stdev 0.53
  (coefficient of variation ~9.6%)

The per-minute rate is close to constant across videos whose durations
differ by 50% (17 to 26 minutes) - same generation code, same speech
cadence - which is exactly the condition under which a per-minute rate,
not a fixed per-video count, is the correct unit for a gate meant to
generalize past this one batch.

**Decision:** `GATE_MIN_WINDOWS_PER_VIDEO`/`GATE_MAX_WINDOWS_PER_VIDEO`
(fixed `25`/`60`) are removed from `src/janelas.py` and replaced by a
duration-scaled band:

```
GATE_WINDOWS_PER_MINUTE = 5.6       # real measured median, rounded
GATE_WINDOWS_PER_MINUTE_BAND = 0.4  # +-40% multiplicative tolerance

low(duration_s)  = ceil(duration_min * GATE_WINDOWS_PER_MINUTE * (1 - GATE_WINDOWS_PER_MINUTE_BAND))
high(duration_s) = floor(duration_min * GATE_WINDOWS_PER_MINUTE * (1 + GATE_WINDOWS_PER_MINUTE_BAND))
```

Criterion 3's per-video window-count check becomes `low(duration_s) <=
n_windows <= high(duration_s)` instead of the flat `25 <= n <= 60`. The
other two legs of criterion 3 (no window over `GATE_MAX_WINDOW_WORDS=60`
words; no non-last window under `WINDOW_MIN_SENTENCES=2` sentences) are
unchanged, and so are criteria 1/2 (human-judged, untouched by this entry).

Verified against the real data: all 30 videos pass with real margin - the
closest video sits 18-21 windows inside its own computed band, not 0-5 -
so this is not a ceiling the 30 videos define by construction. A video
whose window density genuinely halved or nearly doubled relative to this
channel's measured cadence would still fail the gate.

**Why not the other two options considered:**

- *Raise `WINDOW_MAX_SENTENCES`* - out of scope by the project owner's own
  ruling: it would change the annotation unit itself (window construction),
  not just the gate that measures it. Not reopened here.
- *Raise the fixed constants to cover the measured 106-141* (e.g. to
  `100-150`) - rejected: a flat band sized only to what this specific run
  measured has no real detection power going forward. Any output, including
  a genuinely mis-segmented video, would only need to land in that same
  fixed range regardless of its own length, and the band would need
  silently re-widening every time a longer or shorter video entered the
  corpus. The duration-scaled band generalizes to any video length without
  redefinition, and keeps real power to fail a video that does not match
  the channel's measured cadence.

This does not reopen `WINDOW_MAX_WORDS=35`/`WINDOW_MAX_SENTENCES=4` (the
window-construction constants) or gate criteria 1/2. Only criterion 3's
per-video window-count check - `_docs/plano_implementacao.md` line 312,
row 3 of the gate table - is superseded by this entry, per the file's own
precedence rule (line 8 above).

## 13. `group_windows()` construction rule: actively pursue `WINDOW_MIN_SENTENCES` before closing a non-last window - spec correction, not a new decision

Found by direct measurement against the real pipeline output
(`/home/leandro/code/wt/3/corpus/mackexplains7/windows/*.json`, 30
`profile` videos, 3,664 windows total) - a different leg of criterion 3
than item #12, and unrelated to item #11's already-closed
`WINDOW_MAX_WORDS` contingency question.

**Root cause.** Issue #3's `group_windows()` spec (and the engineer's
implementation of it, which matches the spec exactly) only closes a
window when adding the next sentence would exceed `WINDOW_MAX_WORDS=35`
or when `WINDOW_MAX_SENTENCES=4` is reached - it never actively pursues
`WINDOW_MIN_SENTENCES=2` before closing. `_docs/plano_implementacao.md`
line 294 ("Minimo de 2 sentencas, exceto a ultima do video") states the
minimum as prose, but the issue never translated it into a construction
step - only into `check_gate()`'s passive check, which reports the
violation after the fact instead of the construction step avoiding it.
This is not the engineer's bug: the spec was implemented exactly as
written; the gap is in the spec itself, the exact kind grooming is
supposed to close before an engineer builds against it.

**Measured** (30 `profile` videos, real un-doctored pipeline output,
`WINDOW_MAX_WORDS=35`/`WINDOW_MAX_SENTENCES=4` unchanged, pre-fix
algorithm):

- 1,479 of 3,664 windows (40%) are non-last windows with exactly 1
  sentence, violating `WINDOW_MIN_SENTENCES=2`
- median word count of those 1,479 windows: 27 (close to the 35-word
  construction ceiling)
- 18 windows exceed `GATE_MAX_WINDOW_WORDS=60` words - these are the
  pre-existing, intentional, already-tested exception (a single sentence
  whose own word count already exceeds `WINDOW_MAX_WORDS`), untouched by
  this entry
- root cause confirmed numerically: median sentence length is 11-14
  words against a 35-word ceiling, so almost any 2nd sentence added to a
  20-34-word first sentence overflows `max_words`, closing the window at
  1 sentence

Not confused with, and explicitly out of scope for this entry: the
single-oversized-sentence case above - already documented in issue #3,
already tested, stays exactly as-is.

**Decision.** `group_windows()` actively pursues `WINDOW_MIN_SENTENCES`
before closing a non-last window, accepting overflow past
`WINDOW_MAX_WORDS` up to (never beyond) `GATE_MAX_WINDOW_WORDS` to get
there:

```python
def group_windows(sentences, max_words=WINDOW_MAX_WORDS, max_sentences=WINDOW_MAX_SENTENCES,
                   min_sentences=WINDOW_MIN_SENTENCES, gate_max_words=GATE_MAX_WINDOW_WORDS):
    windows = []
    current = []
    current_words = 0
    for sentence in sentences:
        if current:
            reached_max_sentences = len(current) >= max_sentences
            oversized_single = len(current) == 1 and current_words > max_words
            would_overflow = current_words + sentence["n_words"] > max_words
            would_exceed_gate = current_words + sentence["n_words"] > gate_max_words
            reached_min = len(current) >= min_sentences
            should_close = (
                reached_max_sentences
                or oversized_single
                or (would_overflow and (reached_min or would_exceed_gate))
            )
            if should_close:
                windows.append(current)
                current = []
                current_words = 0
        current.append(sentence)
        current_words += sentence["n_words"]
    if current:
        windows.append(current)
    return windows
```

A non-last window may only close before the next sentence is considered
when it already reached `max_sentences`; or it is a 1-sentence window
whose lone sentence already exceeds `max_words` (unchanged exception -
closes immediately, never tries to pull more); or adding the next
sentence would overflow `max_words` **and** the current window already
reached `min_sentences`; or adding it would exceed
`GATE_MAX_WINDOW_WORDS`. Outside those cases, the window keeps
accumulating past `max_words` - up to, never beyond, `gate_max_words` -
until it reaches `min_sentences`, then normal `max_words`/`max_sentences`
logic resumes for the rest of that window.
The last window of a video is untouched: same exception as
before, may still end below `min_sentences`, including at exactly 1
sentence (e.g. a single sentence left over right after the previous
window just closed - already the documented/tested case, nothing new).

**Measured effect of the fix**, simulated in-memory against the same real
sentence data (`/home/leandro/code/wt/3/corpus/mackexplains7/sentences/*.json`,
read-only, no files written, no code changed to produce this measurement):

- non-last 1-sentence windows: 1,479 -> 360 (-76%). Of the 360 remaining:
  263 are the unchanged single-oversized-sentence case (`n_words > 35` on
  its own); 97 are windows that could not reach `min_sentences` because
  doing so would have exceeded `GATE_MAX_WINDOW_WORDS=60` - a new,
  legitimate exception this entry adds, not a residual bug
- windows exceeding `GATE_MAX_WINDOW_WORDS=60`: 18 -> 18 (unchanged) -
  the fix caps overflow acceptance at `gate_max_words`, not unbounded
- total windows: 3,664 -> 3,106 (-15.2%); windows/video mean 122.1 ->
  103.5, median 121.5 -> 104.0

An uncapped version of this fix was tried first and rejected: letting a
non-last window keep accumulating toward `min_sentences` with no ceiling
on the resulting word count did drop 1-sentence windows further, to 199,
but pushed windows exceeding `GATE_MAX_WINDOW_WORDS=60` from 18 to 104 -
trading one gate-3 violation for a much larger one. The version above,
capped at `gate_max_words`, is the one that ships: it closes the
min-sentences gap without introducing new gate-3 word-count violations.

**Consequence flagged, not solved here.** Item #12's
`GATE_WINDOWS_PER_MINUTE=5.6`/`GATE_WINDOWS_PER_MINUTE_BAND=0.4` band was
derived from window counts produced by the *pre-fix* `group_windows()`
(mean 5.48 windows/minute). Re-measuring window counts under the
corrected algorithm above gives a lower per-minute rate (mean 4.66,
median 4.86), and 3 of the 30 videos fall outside item #12's
already-published band when checked against the corrected counts:
`6SapuAcHmDk` (80 windows vs. band [83, 192]), `McXn53SKXYg` (84 vs.
[87, 202]), `f59QqKgwuq0` (78 vs. [79, 184]). This is not re-opened or
re-derived here - issue #3's own fallback already covers it: if
criterion 3 still fails with the corrected window counts, that goes back
to the PM, not adjusted ad-hoc by the engineer. Whoever runs the
corrected pipeline for real reports the actual `check_gate()` result;
a failure on these grounds is a fresh finding, not a signal to patch
`src/janelas.py` on the spot.

**Why this is a spec correction, not a new threshold decision.**
`_docs/plano_implementacao.md` line 294 already states the minimum in
prose ("minimo de 2 sentencas, exceto a ultima do video"); issue #3's
original `group_windows()` description never translated it into an
active construction step, only into `check_gate()`'s passive check - the
exact kind of gap `_docs/team/pm.md` has the PM close before an engineer
builds against it. No new number is introduced: `min_sentences` reuses
the existing `WINDOW_MIN_SENTENCES=2` and the overflow ceiling reuses the
existing `GATE_MAX_WINDOW_WORDS=60`, both already decided (the plan and
item #10's constants, respectively). This does not reopen
`WINDOW_MAX_WORDS=35`/`WINDOW_MAX_SENTENCES=4`/`WINDOW_MIN_SENTENCES=2`
themselves, and is independent of item #12 (which corrects the gate's
per-video window-count band - a different leg of criterion 3).

## 14. Fase 2 gate, criterion 3 restructured into 3a-3d: invariant where the algorithm controls the outcome, tolerance where the corpus does

Final call from the project owner, closing the thread items #11/#12/#13 left
open on criterion 3, and superseding the flat "0" reading of
`_docs/plano_implementacao.md` line 312 for good - not just the window-count
band item #12 already superseded. The plan packed three different kinds of
claim into one "0" limit: a word ceiling, a minimum-sentence rule, and a
per-video window-count band. Some of those the algorithm fully determines
(zero tolerance is correct); one of them the corpus's own sentence-length
distribution determines (a tolerance is the only honest way to state it).
That conflation - not anything wrong in `group_windows()`/`check_gate()` -
is why item #11 measured a FAIL no retuning of `WINDOW_MAX_WORDS` could fix,
and why item #12's proportional band still needed a rate correction after
item #13's construction fix changed the window count (3,664 -> 3,106).

**3a - INVARIANT.** Number of windows with `n_words > GATE_MAX_WINDOW_WORDS`
in the whole corpus == number of sentences with `n_words >
GATE_MAX_WINDOW_WORDS` in the whole corpus, read from `sentences/*.json`
(the denominator `windows/*.json` alone cannot supply: a multi-sentence
window's total can never exceed `gate_max_words` under `group_windows()`, so
the only way a window exceeds it is by relaying one already-oversized
sentence). Measured: 18 == 18. Zero tolerance, stronger than any percentage
band: if grouping ever produces an oversized window that is not just
relaying an already-oversized sentence, this fails immediately, regardless
of how small the count.

```python
def check_3a(sentences_by_video, windows_by_video):
    n_big_sentences = sum(
        1 for sents in sentences_by_video.values() for s in sents
        if s["n_words"] > GATE_MAX_WINDOW_WORDS
    )
    n_big_windows = sum(
        1 for wins in windows_by_video.values() for w in wins
        if w["n_words"] > GATE_MAX_WINDOW_WORDS
    )
    return n_big_sentences == n_big_windows
```

**3b - INVARIANT.** Every non-last 1-sentence window is explained by (i) its
lone sentence already exceeding `WINDOW_MAX_WORDS` on its own, or (ii) a
forced close because the next sentence would have pushed the window past
`GATE_MAX_WINDOW_WORDS`. Unexplained residual (total non-last 1-sentence
windows minus (i) minus (ii)) == 0. Measured: 360 - 263 - 97 = 0.

```python
def check_3b(sentences_by_video, windows_by_video):
    residual = 0
    for video_id, windows in windows_by_video.items():
        sents = sentences_by_video[video_id]
        for w in windows[:-1]:  # exclude the last window of each video
            if w["n_sentences"] != 1:
                continue
            explained = w["n_words"] > WINDOW_MAX_WORDS  # case (i)
            if not explained:
                next_idx = sents.index_of(w["sent_ids"][-1]) + 1  # next sentence, by idx
                next_words = sents[next_idx]["n_words"]
                explained = w["n_words"] + next_words > GATE_MAX_WINDOW_WORDS  # case (ii)
            if not explained:
                residual += 1
    return residual == 0
```

**3c - TOLERANCE, channel thermometer, not an algorithm gate.** Non-last
1-sentence windows <= 15% of the whole corpus's total window count.
Measured: 360/3106 = 11.6%.

```python
def check_3c(windows_by_video, threshold=0.15):
    total = sum(len(w) for w in windows_by_video.values())
    nonlast_one = sum(
        1 for windows in windows_by_video.values() for w in windows[:-1]
        if w["n_sentences"] == 1
    )
    return nonlast_one <= threshold * total
```

3c is not a construction-algorithm gate - 3a/3b already cover that
exhaustively and with zero tolerance. It measures whether *this channel's*
sentences are too long for the 2-4-sentence window unit to work at all. A
future channel that blows through 15% with real margin is the trigger to
re-evaluate the annotation unit (EDU/RST) for that channel **before**
annotating it, not after - a new function 3c adds that the original plan
did not have: the plan's own EDU/RST contingency
(`_docs/plano_implementacao.md` line 304) only fires after Fase 5 (expensive,
post-annotation); 3c gives the same signal earlier, per-channel, for free,
from data Fase 2 already produces.

**3d - TOLERANCE, proportional duration band, recalibrated in this same
pass.** Item #12 calibrated `GATE_WINDOWS_PER_MINUTE=5.6` from the 3,664
windows the *pre-#13-fix* algorithm produced. Item #13's fix changed the
corpus to 3,106 windows and already flagged that this shifts the real rate.
Recalibrated median windows/minute, verified independently in this entry -
not copied from the orchestrator's number blind, reproduced directly against
`corpus/mackexplains7/sentences/*.json` (30/30 `profile` videos, item #13's
`group_windows()` simulated in-memory, `n_windows / (duration_s / 60)` per
video, median across the 30): **4.860732900739404**, matching the
orchestrator's independently-reported figure exactly. Rounded to
**`GATE_WINDOWS_PER_MINUTE = 4.86`** (one more significant digit than item
#12's `5.6` - this is a recalibration of an already-published constant, not
a first cut, so the extra digit is warranted). `GATE_WINDOWS_PER_MINUTE_BAND`
stays `0.4`. Verified (read-only, against the real corrected
`windows/*.json`/`sentences/*.json`): all 30 videos pass `ceil(duration_min
* 4.86 * 0.6) <= n_windows <= floor(duration_min * 4.86 * 1.4)` - closest
margin is 6 windows (`pJYm-8WQbEE`: 111 windows, band [51, 117]), not a band
sized to just barely contain the corpus. Per the project owner's explicit
instruction: if any video had fallen outside this band under independent
verification, the band would not have been widened ad-hoc - none did.

**Why this is a restructuring, not a threshold negotiation.** 3a and 3b keep
the plan's original zero tolerance, because the algorithm fully determines
both outcomes (an oversized window can only come from an oversized sentence;
a non-last 1-sentence window can only come from one of two named,
deterministic causes) - relaxing either into a percentage would hide a real
regression. 3c and 3d are not things `group_windows()` controls in
isolation - they are properties of how long this channel's real sentences
are relative to the fixed window-construction constants
(`WINDOW_MAX_WORDS=35`, `WINDOW_MAX_SENTENCES=4`), so a corpus-level
tolerance, not a "0", is the only honest way to gate them. The error was in
the plan's own framing, not in the implementation: criteria 1 and 2 were
already stated as tolerances (`<= 5 em 50`, judged sample); only criterion 3
demanded absolute zero over a quantity whose mathematical minimum, given
this corpus's real sentence lengths, is 18 (item 3a's own denominator) - not
a defect `group_windows()`/`check_gate()` could have avoided at any
threshold setting (item #11's sweep already showed that).

**whisperX vs. legenda investigation - not answerable in this corpus.** The
5 most problematic videos under the pre-3a/3b framing (`McXn53SKXYg`,
`z1StpnRL4k4`, `qsBitnO8djE`, `6SapuAcHmDk`, `f59QqKgwuq0`) are all
`fonte=whisperX` - but so are all 30 `profile` videos in
`corpus/mackexplains7/manifesto.csv` (item #9: whisperX for all 30, because
the caption-endpoint IP block never cleared for this channel, re-confirmed
here via a fresh `csv.DictReader` pass over the real manifest: 30/30
`profile` rows `fonte=whisperX`, 0 `legenda`). There is no `profile` video
with `fonte=legenda` in this corpus to compare against, so "does whisperX
transcription quality explain the problematic videos, versus legenda" has no
answerable comparison here - a real, structural absence of a control group
for this channel, not a null result to force a conclusion from. Recorded so
a future channel with a mixed `profile` corpus (both sources) is the first
place this comparison becomes possible.

**Rejected, not reopened:**

- *Raise `WINDOW_MAX_WORDS`/`GATE_MAX_WINDOW_WORDS` together* - already
  tried and measured worse: at 45/80 there is still ~4% non-last
  1-sentence windows and 127 windows exceed 60 words.
- *Switch to EDU/RST now* - premature: 88.4% of windows already have >= 2
  sentences and 99.4% are <= 60 words under the corrected algorithm; the
  2-4-sentence unit works with a tail, it is not broken. 3c (above) is the
  mechanism that would trigger this reconsideration per-channel in the
  future, not a decision to do it now.

This does not reopen `WINDOW_MAX_WORDS=35`/`WINDOW_MAX_SENTENCES=4`/
`WINDOW_MIN_SENTENCES=2` (item #13's construction constants) or criteria 1/2
(human-judged, untouched). It supersedes item #12's
`GATE_WINDOWS_PER_MINUTE=5.6` with `4.86`, and supersedes the flat
zero-tolerance reading of `_docs/plano_implementacao.md` line 312 with the
3a/3b/3c/3d split above, per this file's own precedence rule (line 8).

### Addendum: persist gate result to file

The 3a/3b/3c/3d result must be persisted as
`corpus/<channel>/fase2_gate.json`, not left only in the stdout log of a
run that already passed. Comparing a future channel against this channel
requires reading the measured gate result again; a transient run log is not
a durable comparison artifact. The file records `generated_at`, `n_videos`,
`n_windows`, `passed`, and the construction/gate constants in force:
`WINDOW_MAX_WORDS`, `WINDOW_MAX_SENTENCES`, `WINDOW_MIN_SENTENCES`,
`GATE_MAX_WINDOW_WORDS`, `GATE_WINDOWS_PER_MINUTE`, and
`GATE_WINDOWS_PER_MINUTE_BAND`. Persisting those constants is required so
the result remains interpretable after any future recalibration.

Its sub-results are `3a` (`n_sentencas_grandes`, `n_janelas_grandes`,
`passed`, and `problems`), `3b` (`residuo` and `passed`), `3c`
(`nonlast_single_ratio`, its `threshold`, and `passed`), and `3d`
(`passed` and the per-video `problems` list, empty when every video is
inside the band). This file is diagnostic persistence, not a change to the
gate: 3c remains measured but non-blocking exactly as decided above.

When the Fase 3+ `perfis/<canal>.perfil.json` schema is built, its
`diagnostics` object must include this `nonlast_single_ratio` alongside
`smoothing_rate`. That schema and field are not implemented by this
addendum; this records the intended future placement only.

## 15. Issue #8 (fase2_sample.md `sentence_cut` FAIL): root cause fixed at
sentenciacao (M2), not at the window-gate; SaT boundary confidence alone
does not discriminate; automated-scanner-plus-agent-review named as future
direction, not implemented now

Resolves Issue #8. `lkLwp9o7Djk:j0095` (1/50, Issue #4's human sample)
traced to `wtpsplit.SaT("sat-3l-sm").split()` itself, reproduced live
against `raw/lkLwp9o7Djk.json`'s real joined text (238 chunks) -
`src/janelas.py::group_windows()` only inherits a sentence boundary
already wrong, it never creates one. A punctuation-only heuristic sweep of
the full corpus (30 videos, 7,392 sentences) found 28 candidates (sentence
not ending in `.`/`!`/`?`, excluding each video's last sentence); read
individually against the following sentence, 22 are genuinely
syntactically open (same defect class as `j0095`), 6 are false positives
(grammatically complete despite trailing comma/no terminal punctuation -
e.g. comma-spliced independent clauses, a `because`-clause already closed).
Of the 22, 12 land exactly on a window's last sentence - the same
`sentence_cut`-visible position `j0095` occupies.

**Project owner's decision:** fix the root cause in sentenciacao (a new
issue, `src/sentencia.py` only) before unblocking Fase 3. Explicitly
rejected for now: relaxing criterion 2's `== 0` tolerance, raising
`WINDOW_MAX_WORDS`/`WINDOW_MAX_SENTENCES`/`GATE_MAX_WINDOW_WORDS`, and
migrating to EDU/RST. Also explicitly rejected: a rule of the shape "ends
in a comma => merge with the next sentence" - the 6 false positives above
are the counter-evidence; that rule would regress all six. The 28
classified cases (22 open / 6 false positive, with individual rationale)
are the required regression fixture for whatever fix ships.

**Measured during this grooming, so the fix issue does not have to
re-derive it:** `SaT.predict_proba()` exposes a per-character boundary
probability. Extracted the model's own confidence at each of the 28
candidate boundaries (same live-reproduction method as above, real
`raw/*.json` text, real model) - it does **not** cleanly separate the two
classes: open-case probabilities range 0.145-0.991 (mean 0.531, n=22),
false-positive probabilities range 0.403-0.983 (mean 0.669, n=6), heavily
overlapping (e.g. `f59QqKgwuq0:s0016`, open, p=0.885, higher than 4 of the
6 false positives). A bare confidence-threshold retune of the SaT split
decision is therefore not a viable standalone fix either, same conclusion
as the punctuation-only rule - ruled out here so the implementation issue
does not spend a cycle rediscovering it. Whatever mechanism the
implementation issue lands on needs a real syntactic/lexical signal beyond
either single feature, or a combination of features validated against the
28-case fixture with zero regressions on the 6 false positives.

**Future direction, registered per the project owner's explicit
instruction - not implemented by this entry or scoped into the
implementation issue:** an automated scanner that flags suspicious
sentence/window boundaries corpus-wide, reviewed first by an agent, only
escalating genuinely ambiguous cases to a human. This is a shape for a
*future* issue (plausibly generalizing the 3c-style corpus-level
thermometer this project already uses for window density,
`_docs/decisions.md#14`, to sentence-boundary quality) - no issue number
assigned yet, nothing to implement now.

## 16. Fase 3 grooming: `@Zenn0009` accepted as the transferability-test channel, deterministic sampling recipe reused from Fase 2 tooling, codebook example format, coverage-test video pair

Grooming the single Fase 3 issue (`_docs/plano_implementacao.md` lines
328-436) left four real technical gaps `_docs/team/pm.md` has the PM close
rather than hand to the engineer with a fork still in it. None of these are
product decisions - `DECISOES.md` names which channel the ontology is
*derived from* (`@MackExplains7`, item 4) and is silent on which channel
serves the Fase 3 sixth test (transferability); the PM was explicitly
asked to make that call by inspecting the real corpora, not to guess on
the project owner's behalf.

**(a) `@Zenn0009` serves as the second-channel transferability check.**
Read `corpus/mackexplains7/raw/z1StpnRL4k4.limpo.json` and
`corpus/zenn0009/raw/{5tjzei0JOL8,FqLPYQRs6Sk}.limpo.json` directly (real
transcript text, not summaries). Both channels are the same *format*: a
single narrator, English-language, hook-first YouTube explainer that opens
on a concrete scene or claim ("Your heart just stopped...", "In the 9th
century..."), builds an escalating narrative citing studies/historical
cases as evidence ("A 2022 study published in... PLOS One", "That man was
Howard Moskowitz"), and resolves toward an implication - exactly the
`function` vocabulary this issue's ontology proposes (hook, escalation,
evidence, mechanism, resolution, implication). Titling is the same
question/"effect" convention on both (`DECISOES.md#1`/`#4`). The one real
difference is average length - `@MackExplains7` `profile` videos run
17.3-26.4 min (`_docs/decisions.md#12`), `@Zenn0009` runs ~4.0-13.0 min
(`corpus/zenn0009/manifesto.csv`, `ZJai7C3tb1M` 238s to `gEnnt7fDn5Y` 778s)
- but duration is not a format attribute the six tests (line 336-344 of
the plan) test for; a category that survives "decidible in a 2-4 sentence
window" does not care how many windows the video has. This is a technical
finding, not a product decision, and it is a *format* finding, not a
redefinition of `DECISOES.md#4` ("o canal do qual a ontologia sai") - the
ontology's fields and codebook examples still all come from
`@MackExplains7`, only the transfer check's ~20 windows come from
`@Zenn0009`.

**Ratified by the project owner, addendum in place (round 2 amendment, Issue
#11).** What changes here is the status of (a) above, not its content: it was
a technical call the PM made while grooming; the project owner now ratifies
it explicitly, for a reason worth recording because it also sets the limit of
what the transfer test can prove.

**Why ratified.** A second channel that resembles `@MackExplains7` too
closely would pass trivially and prove nothing - the six-test evaluation
would find no gap because there was never a real chance to find one.
`@Zenn0009` shares the format (a) already establishes (single narrator,
English, hook-first, question-style titling) and diverges on the two axes
that matter for a transfer test: duration (`@MackExplains7` 17.3-26.4 min vs.
`@Zenn0009` ~4.0-13.0 min) and subject domain (behavioral-effects explainers
vs. history/science explainers) - the right kind of distance, not too close,
not a different format. It is also already collected, cleaned, and committed
(Fase 1, items #3/#4), so using it costs nothing further; picking any other
channel now would reopen a Fase 1 collection pass from zero, with a real,
previously-hit risk of repeating the YouTube per-IP caption block items
#3/#4/#9 already document.

**The limit of what this test proves - more load-bearing than the reason
above.** This test proves the ontology's categories are not idiosyncratic to
`@MackExplains7` specifically - that a second channel, same format, different
domain and duration, produces windows the same `function`/`scale`/`evidence_type`
vocabulary can code without inventing new values. It does **not** prove the
ontology generalizes across *format*: an interview, a multi-narrator video, a
listicle, or a channel fronted by more than one presenter are untested by this
check, because `@Zenn0009` is the same format as `@MackExplains7` on purpose
(per (a) above). Real format generalization is only tested for free the day a
second channel with a genuinely different format enters the corpus - nothing
in this issue substitutes for that. Any future citation of this transfer test
as evidence the ontology generalizes beyond format is a misreading of what was
actually measured here.

**(b) Deterministic recipe to produce those ~20 windows, verified during
grooming (scratch directory, not committed).** `@Zenn0009` has no
`sentences/`/`windows/` yet - Fase 2 was scoped to `@MackExplains7` only
(`_docs/decisions.md#10d`). Producing them needs zero new code:
`src.sentencia.run()` treats a missing `role` column as `profile`
(`row.get("role", ROLE_PROFILE)`, `src/sentencia.py:676`; `src.coleta.check_gate`
does the same at `src/coleta.py:505`), and `src.sentencia.run()`/`src.janelas.run()`
already accept `manifest_path`/`raw_dir`/`sentences_dir`/`windows_dir` as
parameters instead of their `corpus/mackexplains7` module-level defaults.

**Correction, in place** (same posture as item #11's median/mean fix - the
decision is unchanged, only a factual claim inside its justification was
wrong): the original text of this paragraph credited the `role` defaulting to
`src.coleta.read_manifesto` at `src/coleta.py:476`. That is false, and
checkable in one read - `read_manifesto` is a bare `csv.DictReader` and
returns exactly the columns the file has. The recipe below is unaffected,
because it is `sentencia.run()` that filters. `read_manifesto` is
deliberately left as-is rather than changed to make the old sentence true:
injecting a default there would hide from every future consumer that
`corpus/zenn0009/manifesto.csv` genuinely predates the `role` column (item
#7). The absence should stay visible at the read boundary, and each consumer
should pick its own default explicitly.
Verified live against the real `corpus/zenn0009/raw/` (30 videos, scratch
output directory, deleted after verifying, nothing committed by this
entry):

```python
from pathlib import Path
from src.sentencia import run as sentencia_run
from src.janelas import run as janelas_run
from src.amostragem import sample_videos, sample_windows

sentencia_run(
    manifest_path=Path("corpus/zenn0009/manifesto.csv"),
    raw_dir=Path("corpus/zenn0009/raw"),
    sentences_dir=Path("corpus/zenn0009/sentences"),
)
janelas_run(
    sentences_dir=Path("corpus/zenn0009/sentences"),
    windows_dir=Path("corpus/zenn0009/windows"),
)
video = sample_videos(windows_dir=Path("corpus/zenn0009/windows"), seed=42, n_videos=1)
windows = sample_windows(video, windows_dir=Path("corpus/zenn0009/windows"), seed=42, n_windows=20)
```

All 30 videos sentence/window cleanly (no errors - `role` defaulting makes
every row `profile`, which is correct here: `@Zenn0009` was never split
into profile/holdout). The seed-42 draw picked `ZJai7C3tb1M` ("The
Pratfall Effect", 238s, the shortest video in the manifest) with 20 windows
`ZJai7C3tb1M:j0000` through `:j0022`.

**Correction, in place (same posture as the `read_manifesto` fix above and
item #11's median/mean fix): the original text of this paragraph said "56
windows total in that video."** That is false - `ZJai7C3tb1M` has 24 windows
total, not 56; 56 is `Dw2Pifv1JrM`'s window count, from the round-2 draw
below, transposed here by mistake. Checkable two ways: 773 words in the
video's sentences at the corpus-wide rate of 32.92 words/window
(`102,138 words / 3,103 windows` from the Fase 2 corpus,
`_docs/decisions.md#14`'s `3a` denominator) gives ~23 windows, and 20 windows
sampled without replacement from a pool of 56 landing entirely within
`j0000`-`j0022` (the first 23 slots) has probability 2.25e-12 - both point to
24, not 56. The sample itself is unaffected: 20 windows without replacement
from 24 available is still a valid draw, just a tighter margin than the
original text implied.

The engineer's real run must produce and
commit `corpus/zenn0009/sentences/*.json` and `corpus/zenn0009/windows/*.json`
for real (this entry only proves the recipe works) - re-running the same
seed against the same committed input is expected to reproduce the same
video/window draw; if it does not, the mismatch itself is worth flagging,
not silently accepted.

**Correction, in place (round 2 amendment, Issue #11) - sample size, not the
recipe.** The draw above used `n_videos=1`, which the project owner is
reopening on a real asymmetry: fixing an undersized transfer sample now costs
one line in the recipe; discovering in Fase 5 that the ontology does not
transfer costs a full `v2` and re-annotating the whole batch (~3,600 calls,
`_docs/decisions.md#3`/`#9`'s corpus scale). A single 238s video
(`ZJai7C3tb1M`, the shortest in the `@Zenn0009` manifest) gives 20 windows too
little runway to exercise most of the `function` vocabulary - "no gap found"
there risks meaning "no opportunity to find one," not "the ontology holds."

What changes: `sample_videos(..., n_videos=1)` becomes
`sample_videos(..., n_videos=2)`, same seed 42, same 20-window total via
`sample_windows`'s existing per-video quota (`n_windows // len(video_ids)`,
with its documented backfill if either video has too few windows -
`src/amostragem.py`). Re-run live (scratch directory outside the repository
and outside `/tmp`, deleted after verifying, nothing committed by this entry -
same posture as the original verification above): the seed-42 draw over the
real `corpus/zenn0009/windows/` now returns `["ZJai7C3tb1M", "Dw2Pifv1JrM"]`.
`ZJai7C3tb1M` has 24 windows available and `Dw2Pifv1JrM` has 56 - both
comfortably above the quota of 10, so the split is the plain
`n_windows // len(video_ids)` quota, no backfill triggered:

- `ZJai7C3tb1M` ("The Pratfall Effect", 238s / ~4.0min - the same shortest
  video the round-1 draw picked): `j0000`, `j0002`, `j0003`, `j0004`, `j0007`,
  `j0008`, `j0009`, `j0019`, `j0020`, `j0022`.
- `Dw2Pifv1JrM` ("What Did Surgery Feel Like Before Anesthesia?", 547s /
  ~9.1min - well above the manifest's median duration, not another short
  video): `j0001`, `j0002`, `j0005`, `j0013`, `j0014`, `j0027`, `j0032`,
  `j0035`, `j0038`, `j0053`.

Flagged, not hidden: the two videos are not equally short - `Dw2Pifv1JrM`
sits in the upper third of `@Zenn0009`'s 29-video duration range (238-778s),
so this draw did not land on the failure mode the project owner named as a
reason to escalate rather than hand-pick a replacement pair. Had it landed
there, this entry would report that fact for the project owner to decide, not
swap in a different pair or re-seed - same posture item #17 already sets for
near-miss gate results.

What does not change: (a)'s channel choice, (c)'s coverage-test video pair
(`lkLwp9o7Djk`/`5unhHRFkC7I`, untouched, still `n_videos=2` from Fase 2's own
default), (d)'s codebook citation format, and `SAMPLE_SEED = 42` everywhere it
is already used. The engineer's real run must still produce and commit
`corpus/zenn0009/sentences/*.json` and `corpus/zenn0009/windows/*.json` for
real (this entry only re-proves the recipe); re-running the same seed against
the same committed input is expected to reproduce this same two-video,
20-window draw.

**(c) Fase 3 coverage-test video pair: reuse the Fase 2 human-sample draw.**
The plan's steps 2-3 (line 424-425) name "1 vídeo" then "um segundo vídeo"
without naming them or a seed. `src.amostragem.sample_videos()` (default
`seed=42, n_videos=2`, `_docs/decisions.md#10c`) against
`corpus/mackexplains7/windows/` deterministically returns
`["lkLwp9o7Djk", "5unhHRFkC7I"]` - verified live, the same two videos
already used for the Fase 2 gate's criteria 1/2 human sample
(`corpus/mackexplains7/fase2_sample.md`), same function and seed, no new
draw invented. Video 1 = `lkLwp9o7Djk` (98 windows), video 2 =
`5unhHRFkC7I` (107 windows) - 205 windows combined, so the phase gate's
"< 10% das janelas" is < 20.5, i.e. **at most 20 of 205** windows may land
in "outro"/dúvida genuína. This is the exact number the issue's gate
criterion copies verbatim, per `_docs/team/pm.md`'s "do not soften" rule.

**(d) Codebook example format: verbatim quote + `window_id`, not
paraphrase.** The plan asks for "two positive examples... from the real
corpus" and "one negative example" per value (line 381-382) but not a
storage format. Decision: every example in `schema/codebook.md` is a
verbatim quote of a window's `text` field plus its `window_id` (e.g.
`z1StpnRL4k4:j0000`), never a paraphrase - so a reader can open
`corpus/mackexplains7/windows/<video_id>.json` and verify the citation
against the real corpus, the same falsifiability standard
`_docs/decisions.md#15` already applied to the sentence-boundary fixture.

None of this reopens `DECISOES.md#4` (the ontology is still derived from
`@MackExplains7` alone) or touches any already-frozen Fase 2 artifact
(`corpus/mackexplains7/fase2_gate.json`, `fase2_sample.md`,
`sentences/`, `windows/` stay read-only inputs to Fase 3).

## 17. Fase 2 gate criterion 1 passed at exactly its limit (5/50) - accepted as a pass, recorded, not re-measured

Issue #10's human judgement of `corpus/mackexplains7/fase2_sample.md` (50
windows, `SAMPLE_SEED = 42`, videos `lkLwp9o7Djk`/`5unhHRFkC7I`, judged fresh
after Issue #9's sentence-boundary fix, not reused from Issue #4) returned
`sentence_cut = sim` on 0 of 50 - criterion 2 passed with full margin - and
`two_functions = sim` on exactly 5 of 50. Criterion 1's threshold is `<= 5 em
50`. It passed with **zero margin**.

The five flagged windows, so this entry is checkable against the committed
sample rather than taken on trust: `lkLwp9o7Djk:j0027`, `lkLwp9o7Djk:j0054`,
`lkLwp9o7Djk:j0064`, `5unhHRFkC7I:j0054`, `5unhHRFkC7I:j0075`.

`_docs/plano_implementacao.md` (Fase 2, criterion 1) reads a window carrying
two distinct narrative functions as a signal that the word threshold may be
too high. **Project owner's decision: accept the result as a pass, record the
zero margin here, and do not re-measure, re-sample, or lower
`WINDOW_MAX_WORDS`.** Reasons, in order:

- A pass at the threshold is a pass. Re-drawing the sample after seeing the
  number is the mirror image of the softening `_docs/team/pm.md` forbids, and
  it would spend the seed-42 reproducibility that is the only reason QA can
  re-measure exactly what the engineer measured.
- Lowering `WINDOW_MAX_WORDS` is the contingency item #11 already measured as
  strictly worse for this corpus (2,927 problems at 25 vs. 1,527 at 35) and
  item #14 closed for good. Nothing here reopens it.
- The five flagged windows are not noise to be tuned away - they are the
  population Fase 3 exists to handle. A window carrying two functions is a
  window whose `function` label is genuinely contested, which is what the
  codebook's tie-breakers are for.

**Carried into Fase 3 as an input, not as a blocker.** Whoever writes
`schema/codebook.md` reads those five `window_id`s in `fase2_sample.md`
before writing the tie-breakers: they are the cheapest real examples of the
boundary cases the tie-breakers have to decide, from the same corpus and the
same two videos Fase 3's coverage test already uses (item #16c).

**What would reopen this.** Not this entry alone. If Fase 3's own coverage
gate (`< 10%` of the 205 windows in "outro"/genuine doubt, i.e. at most 20 -
item #16c) also lands at or near its limit, that *pair* of near-misses is
evidence about the annotation unit rather than about either gate, and it goes
back to the project owner as an EDU/RST question - not to an engineer, and
not as a threshold adjustment. A single near-miss on one gate is a number to
record, which is what this entry does.

## 18. Language policy: the README table was wrong in three places, the files were right - reclassify the table, translate nothing

The v3.0 language policy is normative and unchanged in intent: **machine-facing
or prompt-bound text is English; text whose only reader is the project owner is
PT-BR.** An audit of the repository against that policy's own table
(`README.md`, "Política de idioma") found three mismatches. In all three the
file is right and the table was wrong, so the table moves and no file is
translated.

**Measured, not assumed** (word-frequency pass over each file, plus an AST pass
over `src/*.py` for docstrings):

| Artifact | Table said | File actually is | Resolution |
|---|---|---|---|
| `_docs/decisions.md` | PT-BR | English (1,028 EN markers vs. 2 PT) | table -> English |
| `_docs/team/*.md`, `_docs/task-template.md` | PT-BR | English (all four) | table -> English |
| docstrings in `src/*.py` | English | PT-BR (51 of 52; `src/db.py`'s module docstring is the lone English one) | table -> PT-BR |

Consistent with the table already, left untouched: 99 test names (English),
code identifiers (English), `README.md`/`plano_implementacao.md`/`blueprint.md`/
`process.md`/`AGENTS.md`/`DECISOES.md`/issues/commits (PT-BR).

**Why each file is right and the table was wrong.**

- `_docs/team/*` and `_docs/task-template.md` are not documentation *about* the
  squad - they are the operating instructions pasted verbatim into a PM's,
  engineer's or QA agent's prompt. They are prompt-bound by construction, which
  the policy already sends to English.
- `_docs/decisions.md` is the boundary case, and it lands in English on
  content, not on convenience: it is near-entirely constants, function names,
  measured numbers and file paths - all of which the policy mandates in English
  anyway - and it is cited *by identifier* (`#14`, `#16b`) from issue bodies,
  commit messages and module docstrings. A PT-BR wrapper around English
  identifiers is the worst of both. Translating it would also break every
  existing citation and produce a ~900-line diff across 18 entries settled in
  closed issues.
- Docstrings are the mirror argument. They are prose sitting next to the code,
  explaining to the project owner what a function does and why - exactly the
  "explanation for a human" side of the policy. They are not vocabulary the
  model has to choose from, unlike the ontology labels, the annotation prompt,
  or the generated script. The *identifiers* they describe stay English, which
  is what the policy was actually protecting.

**Operational test for future cases, so this does not get re-litigated per
file.** Ask whether the text is *system vocabulary* - something a model must
choose, emit, or match exactly (ontology labels, field names and values,
annotation and generation prompts, code identifiers, test names, an agent's
own operating instructions). If yes, English. Otherwise it is *explanation for
the project owner* - narrative, rationale, diagnosis - and it is PT-BR.
Explicitly **not** the test: "an agent will read this." Agents read the whole
repository, PT-BR included; that criterion would send everything to English and
is why the original table drifted.

**Scope: zero translation in either direction.** No file changes language under
this entry. The only edit is the `README.md` table plus the paragraph stating
the test above. `src/db.py`'s English module docstring is left as-is - a
one-line inconsistency is not worth a commit, and it corrects itself the next
time that file is edited for a real reason.

**Escape hatch, if reading `_docs/decisions.md` in English ever becomes a real
cost:** add a PT-BR index at the top of the file - one line per entry, entry
number plus what it decided - not a translation of the entries. That keeps the
citations, the numbers and the diff history intact while restoring
skimmability. Not done now, because 18 entries have been read in English
without friction.

## 19. Issue #11 (`function` boundary-window tie-breaker): rewritten to require zero lookahead and zero word count, after two straight QA FAILs on the same defect class - rework cycle stopped, not sent back a third time

Issue #11 (Fase 3 ontology) FAILed QA twice in a row on the same item: the
`function` tie-breaker for a window whose content straddles two topics.
Commit `98a66e8` (v1) coded by whichever clause carries "more new
information, more words" - two unranked criteria that can point opposite
ways. Commit `9d1182c` (v2, the engineer's own fix after the first FAIL)
dropped "more new information" and coded by word count alone: default to
the closing clause, the opening clause wins only with strictly more words.
QA's second FAIL measured v2 mechanically against the real, already-committed
worksheet (`corpus/mackexplains7/fase3_coverage.md`, worktree
`/home/leandro/code/wt/11`, counts independently reproduced from the real
window text in this entry) and found two rows where the rule as written and
the recorded label disagree:

| window | closing clause (words) | opening clause (words) | v2 rule says | recorded label | recorded label reads as |
|---|---|---|---|---|---|
| `5unhHRFkC7I:j0064` | 20 (cats) | 7 (horses) | closing | `promise` | opening |
| `lkLwp9o7Djk:j0076` | 12 | 16 | opening | `objection` | closing |

In both, the worksheet's `justificativa` column is blank - neither row was
ever recognized as a boundary window when originally classified.

**Root cause, not fixable by a third word-count variant.** The engineer
identified it correctly on the second round: `5unhHRFkC7I:j0054` was cited
in the v1 tie-breaker's own text as a resolved boundary case and turns out
not to be one at all - a finding neither QA nor the project owner had made.
The deeper problem the engineer's fix did not reach: v1/v2's shared
*definition* of a boundary window - "its final sentence(s) preview specific
content the next window then develops" - requires reading the next window.
Verified directly against the plan before writing this entry:
`_docs/plano_implementacao.md` line 342 ("decidível em janela - decidível em
2-4 sentenças mais **contexto anterior**"; only prior context is licensed,
nothing about the next window) and `README.md` M4 ("não passar `pos_pct`
... nem os rótulos das janelas anteriores" - the prompt is built to forbid
leakage in the *other* direction, and never grants next-window access
either). The real Fase 5 annotator - the one this codebook is actually
written for - only ever sees a window plus prior context. A tie-breaker
built on a definition that requires the next window cannot be applied
consistently by that annotator, independent of which countable signal
(word count, sentence count, anything else) sits on top of the definition.
The two FAILs are symptom, not cause: `98a66e8`/`9d1182c` both defined the
problem in terms only the person writing the codebook - who has the whole
transcript - can evaluate.

**Second, independent defect in the same two commits.** Coding by word
count is a third instance, on this project, of a countable surface trace
standing in for semantic judgment - the same failure class `#14` (the
sentence-boundary punctuation heuristic, 6 of 28 candidates were false
positives) and `#15` (SaT split-confidence threshold, open-case
probabilities 0.145-0.991 overlapping false-positive probabilities
0.403-0.983) already measured and rejected on this project. Replacing
"more new information" with word count removed the conflict between two
signals (v1's defect) but not the category error of using a countable
proxy at all.

**Decision: Direction A, no new field.** `schema/codebook.md`'s general
tie-breaker for `function`'s boundary case (currently the "General
tie-breaker adopted for every genuine boundary window" paragraph in the
worktree draft) is replaced with:

> A window may contain content that concludes an established topic and a
> trailing pivot that opens a new one. Detecting the pivot never requires
> the next window: a trailing pivot exists when the window's final
> sentence(s) name or introduce a specific subject, claim, or event that is
> not otherwise developed earlier in this window or by prior windows in the
> same video - a bare transitional phrase with no new specific content
> ("Let's go further," "there's one more thing") is not a pivot. When a
> window contains such a pivot, code `function` for the content the window
> concludes, never for the content it only opens or previews - regardless
> of relative word count, sentence count, or which half reads as more
> salient. A window with no internal pivot is coded normally, from its own
> content as a whole.

This removes both defects together: the pivot test reads only the window's
own text and what the video has already established, never what comes
after (no lookahead); and "always the closing content" is unconditional,
so no count of any kind enters the decision.

**Why not Direction B (a new structural-pivot field).** Rejected as
disproportionate to what the corpus actually shows, and inconsistent with
how every other field-3 (mutual exclusivity) collision in this same
codebook was already resolved. Reading all 205 rows of
`corpus/mackexplains7/fase3_coverage.md` (worktree, read-only) for a
genuine within-window pivot under the test above finds five confirmed
cases - `lkLwp9o7Djk:j0027`, `lkLwp9o7Djk:j0064`, `lkLwp9o7Djk:j0076`,
`5unhHRFkC7I:j0064`, `5unhHRFkC7I:j0075` - a 2.4% (5/205) rate, plus two
borderline candidates, `5unhHRFkC7I:j0017` and `5unhHRFkC7I:j0039`, flagged
here for the next engineering round to resolve under the same test, not
decided by this entry. `loop`'s `opens`/`closes` collision
(`5unhHRFkC7I:j0024`, 1/205) and `evidence_type`'s two collisions
(`study`/`statistic`, `case`/`authority`) were resolved the same way, in
the same codebook, on the stated reasoning that a rule "does not recur
nearly as pervasively as `transition` did... and a single rule fully
resolves it" - which applies here at a comparable rate. A new field would
need its own six-test defense, its own worksheet column, its own
`fase3_gate.json` thermometer, and its own line in every one of the
~3,600-per-channel Fase 5 annotation calls, to carry a signal `function`'s
own deterministic tie-breaker already resolves. `_docs/plano_implementacao.md`'s
5-7 field range (line 374) has room for a sixth field; room existing is not
the same as warranted.

**Applied to the four windows named in QA's report and the project owner's
instruction**, verbatim text from
`corpus/mackexplains7/windows/{lkLwp9o7Djk,5unhHRFkC7I}.json` (worktree,
read-only):

- **`lkLwp9o7Djk:j0027`.** Closes: "Pointing at the right building, wrong
  floor." - a generalizing aside on Egypt's near-miss mood theory (`j0026`:
  "not quite right, but in the right neighborhood"). Opens: "Now we cross
  the Mediterranean, and we have to talk about ancient Greece..." - names a
  genuinely new subject, Greece, not discussed before this window. Rule:
  code the closing clause. It extends `j0026`'s established content to a
  broader generalization without being tied to one posed question -
  `implication`'s own definition. **New label: `implication`. Recorded
  today: `promise`. Changes.**
- **`lkLwp9o7Djk:j0064`.** Closes: "The people of a small Belgian town
  figured it out in the 1200s and just quietly kept doing it." - generalizes
  the Gilles/Belgium case just established. Opens: "Then comes the early
  modern period, and things in Europe get notably worse before they get
  better." - names a new era. Rule: code the closing clause ->
  `implication`. **New label: `implication`. Recorded today: `implication`.
  No change** - v2's word count happened to pick the closing clause here
  (19 vs. 17 words) too, coincidence rather than vindication, since the
  same rule misfires on the next two windows below.
- **`5unhHRFkC7I:j0054`.** "...they became... experts in being human. Now,
  dogs are an obvious case..." No genuine pivot: "dogs" is not a new
  subject, it is the established subject of the entire preceding act
  (`j0000`-`j0053`) - the engineer's own second-round finding, which holds
  under the rule above without needing the tie-breaker at all: the whole
  window reads directly as `implication`. **Label: `implication`. Recorded
  today: `implication`. No change.**
- **`5unhHRFkC7I:j0064`.** Closes: "Not, I know what humans look like when
  they're sad, but, I know what you look like when you're sad." -
  generalizes `j0061`-`j0063`'s established content about cats building an
  individualized model of their owner. Opens: "Horses operate on yet
  another level entirely." - names a new subject, horses, not discussed
  before this window. Rule: code the closing clause. It extends the cats
  content to a broader generalization - `implication`. **New label:
  `implication`. Recorded today: `promise`. Changes** - this is the row
  QA's mechanical check flagged.

A fifth window in the same worksheet, not in QA's table but flagged by the
same mechanical check: **`lkLwp9o7Djk:j0076`.** Closes: "Unevenly. With
enormous suffering in the gaps. But the direction was right." - qualifies
the prior claim of steady progress (`objection`). Opens: "And then the 19th
century arrived and built enormous asylums and overcrowded them to
catastrophic levels." - names a new era. Rule: code the closing clause ->
`objection`. **Recorded today: `objection`. No change** - this is the row
where v2's word count (opening's 16 beats closing's 12) disagreed with the
recorded label; the new rule predicts the recorded label correctly without
retconning it.

**Net effect on the 205-row worksheet.** Two rows change
(`lkLwp9o7Djk:j0027`, `5unhHRFkC7I:j0064`, both `promise -> implication`),
out of five confirmed boundary windows and 205 total; the two borderline
candidates above are flagged, not decided, for the next engineering round.
Neither changed row becomes `outro`/`dúvida` - both keep a concrete
`function` value - so the measured coverage-gate result (`corpus/mackexplains7/fase3_gate.json`,
**0/205, PASSOU, teto 20**) is unaffected and not reopened by this entry.

**Distributional consequence, stated rather than hidden.** Extrapolated at
the worksheet's own 2.4% boundary-window rate, the full `@MackExplains7`
corpus (3,103 windows, `#14`) has on the order of 60-90 boundary windows;
this rule moves each one's `function` to whichever value its closing clause
represents - a small, systematic, predictable shift in the `function`
distribution, not corpus-breaking. A systematic rule biases the
distribution predictably; the lookahead-dependent, word-count rule it
replaces injected exactly the kind of annotator-to-annotator noise Fase 5's
α gate exists to catch.

**What this does not reopen.** `transition`'s removal from `function`
(unaffected - the boundary tie-breaker exists because `transition` is gone,
not as a reason to bring it back), `cosmic`'s removal from `scale`, `scale`
staying in v1, the 20/205 gate ceiling, `SAMPLE_SEED = 42` and the sampled
video pair, or the codebook's verbatim-quote citation format. `schema/codebook.md`,
`schema/ontologia.v1.json`, and `corpus/mackexplains7/fase3_coverage.md`
are not edited by this entry - they stay worktree-only and unmerged
(`origin/main` confirmed at `78e277c` when this entry was written, unchanged
since `9d1182c`'s QA FAIL). The next engineering round applies the rule
above, corrects the two rows named, re-verifies the other three, resolves
the two borderline candidates, and re-measures the coverage gate.

**Correction, in place (round 4 resolution, Issue #11) - list composition,
not the rate.** This entry's "five confirmed cases" list above named
`5unhHRFkC7I:j0075` as one of the five genuine boundary windows. That is
false, found when the next engineering round finally applied the rule to
it (this entry flagged it as owed but never carried out the application -
see "What this does not reopen," which listed `5unhHRFkC7I:j0075` among
windows still needing verification). Read against its neighbors
(`5unhHRFkC7I:j0002`, `j0039`, `j0074`): its trailing sentence, "Let's come
back to that couch," is not a pivot under this entry's own test - "that
couch" is the video's own opening scenario, already established twice
before (`j0002`, revisited at `j0039`), not a new subject. The window has
no internal pivot and is coded as a whole, unchanged at `implication`.

The seat `5unhHRFkC7I:j0075` wrongly occupied belongs to
`5unhHRFkC7I:j0017`, one of the two windows this entry left as "borderline
candidates, flagged... not decided." Resolved: its opening ("Then came
neuroscience... brains of mammals... reframed the entire conversation")
names a specific subject - mammalian-brain neuroscience research - not
developed anywhere earlier in the video (only in the following window,
`j0018`, "the limbic system...") - a genuine pivot. Rule: code the closing
clause ("Machines don't make detours to visit the dead"), which continues
the same anti-"biological machine model" evidence chain as `j0014`-`j0016`
("Machines don't grieve") - `evidence`/`case`, not `promise`.

**Corrected five-window list:** `lkLwp9o7Djk:j0027`, `lkLwp9o7Djk:j0064`,
`lkLwp9o7Djk:j0076`, `5unhHRFkC7I:j0064`, `5unhHRFkC7I:j0017` - still five,
still 5/205 = 2.4%. The rate this entry used to reject Direction B is
unchanged and was never wrong; only the citation of which fifth window
earned the count was.

The other borderline candidate, `5unhHRFkC7I:j0039`, resolved the other
way: its trailing sentence ("Smell is only one piece of this") withholds
which piece, naming nothing specific - the same shape as this entry's own
negative example ("there's one more thing") - so it is not a pivot either,
and does not join the five. The whole window is coded directly, and the
codebook's pre-existing `hook`-vs-`promise` tie-breaker (subject withheld
-> `hook`, subject named -> `promise`) - not the boundary rule this entry
wrote - moves it from the `promise` recorded pre-Fase-3-rework to `hook`.

**Net effect on the 205-row worksheet, final count.** Four rows change
(all `promise` before this and the prior round's fixes): `lkLwp9o7Djk:j0027`
-> `implication`, `5unhHRFkC7I:j0064` -> `implication`, `5unhHRFkC7I:j0017`
-> `evidence`/`case` (three via this entry's boundary rule), and
`5unhHRFkC7I:j0039` -> `hook` (via the pre-existing `hook`/`promise`
tie-breaker, not this entry's rule). None becomes `outro`/`dúvida`; the
coverage gate remains **0/205, PASSOU, teto 20**
(`corpus/mackexplains7/fase3_gate.json`, regenerated) - unaffected and not
reopened by this correction, same as the original entry concluded.

`schema/codebook.md`'s worked examples for the boundary rule (previously
the three word-count arithmetic examples this entry's rule replaced) are
also rewritten in the same round to argue from the rule text above rather
than from word counts - no word-count arithmetic remains in the codebook.

Confirmed unaffected, same as the original entry: `transition`'s removal,
`cosmic`'s removal, `scale` staying in v1, the 20/205 gate ceiling, seeds,
the sampled video pair, and the codebook's citation format.

## 20. Issue #11 (`function` boundary tie-breaker, `#19`): anchored to the context an annotator actually receives in the call, not the whole video; "developed before" operationalized as semantic, never lexical - a near-miss on the same defect this project has now caught four times, this time in measurement before it reached a rule

`#19` fixed the wrong scope. It replaced "requires the next window"
(asymmetric - the real Fase 5 annotator never sees it) with "requires the
whole video read backward" - still more evidence than the annotator that
actually applies the rule receives. `_docs/plano_implementacao.md` line
478 (Fase 5A, step 2): the prompt's user turn is "as 3 janelas anteriores
(só texto, sem rótulos)" - three prior windows, text only, no labels -
then the window to classify. A rule requiring "not developed anywhere
earlier in the video" cannot be applied consistently by an annotator
holding three windows of context, independent of whether the missing
evidence is semantic or lexical.

**Principle.** A codebook rule may only require evidence its applier
actually receives in the call.

**Rule, re-anchored (supersedes `#19`'s "prior windows in the same
video").** The normative text does not name a window count - the codebook
feeds the Fase 5 prompt, and the context budget is a call-shape parameter
the plan leaves open to experimentation (`_docs/plano_implementacao.md`
line 479, "teste um campo por chamada vs. todos juntos"), not something
the codebook should freeze inside its own rule text:

> A trailing pivot exists when the window's final sentence(s) name or
> introduce a specific subject, claim, or event that is not otherwise
> developed in this window or in the context previously provided in this
> call - a bare transitional phrase with no new specific content ("Let's
> go further," "there's one more thing") is not a pivot.

Everything else in `#19`'s rule is unchanged: when a pivot exists, code
the closing content, never the opening/preview, regardless of word count,
sentence count, or salience.

**The budget itself: fixed at three windows, as a separate decision of
this entry, not folded into the rule's wording.** `_docs/plano_implementacao.md`
line 478 sets three prior windows for Fase 5's actual calls. This entry
adopts three as the budget the codebook's examples and the Fase 3
worksheet are audited against. Consequence, stated because it is a real
cost: changing the budget changes what the rule's "context previously
provided" means, so it changes which windows are pivots - a run measured
under a five-window budget is not comparable to one measured under three.
`_docs/plano_implementacao.md` line 495 already requires the Fase 5 run
record to persist model, ontology version, date, and α by field; this
entry adds the context budget to that record, same precaution family as
persisting `fase2_gate.json`'s constants (`#14`) and `fase3_gate.json`'s
`ontology_version` - so a future run measured under a different budget is
never silently compared against this one.

**"Developed before," operationalized - the change this entry actually
makes.** `#19` left this phrase undefined, and a competent reader (this
project's own orchestrator, verifying `#19`'s application against the real
corpus) fell into exactly the gap: flagged `lkLwp9o7Djk:j0076` as a false
pivot because the word "asylums" appears at `j0074`, two windows earlier,
and again at `j0071`. Read against the actual narrative (`j0070`-`j0078`):
`j0071` names a specific institution, the Bicetre Asylum, inside the
18th-century reform story; `j0074` uses "asylums" as a comparison baseline
("the York Retreat's outcomes were dramatically better than contemporary
asylums"); neither develops `j0076`'s actual claim - that the 19th century
built asylums at scale and overcrowded them to catastrophic levels - which
`j0077`-`j0078` go on to develop. `j0076` is a genuine pivot under any
context budget. The word recurring is not what "developed" means.

> "Developed before" means the context previously provided already
> supports the same claim, event, or subject - not that it shares a word
> with it. A passing mention, a use as a comparison baseline, or the same
> word applied to a different referent do not constitute development. The
> test is semantic, never lexical: term repetition decides neither for nor
> against.

**Worked negative example, built from exactly this pair** (more valuable
than a positive example, because it is the one case that teaches an
annotator not to make the mistake this project's own verification just
made): `lkLwp9o7Djk:j0074` says "asylums," and `lkLwp9o7Djk:j0071` names a
specific asylum by name - and `j0076` is still a pivot, because neither
window develops the claim `j0076` opens (mass-scale 19th-century
overcrowding to catastrophic conditions) - that claim first appears at
`j0076` and is developed at `j0077`-`j0078`.

**The named-vs-developed distinction dissolves.** It previously decided a
label without being written anywhere - the codebook justified `j0027` by
saying Greece was not discussed "anywhere before this window," when Greece
is literally named at `j0011`. Under the semantic test above, that
sentence is now precise: Greece is *named* at `j0011`, in an unrelated
list (trepanation across cultures); the specific claim `j0027` opens -
Greece as philosophically fascinating and occasionally horrifying - is not
developed until `j0027` itself. Naming is not developing.

**Evidence - measurement and recheck, both performed read-only before
this entry was written, and one self-correction made in the open.**
Reapplying `#19`'s pivot test with the three-window budget to the seven
windows previously examined (`lkLwp9o7Djk:j0027`, `j0064`, `j0076`;
`5unhHRFkC7I:j0064`, `j0017`, `j0075`, `j0039`), using verbatim text and
independently measured distances-to-prior-mention (matched exactly on the
four the project owner supplied for cross-check: Greece 16 windows before
`j0027`; horses 9 before `5unhHRFkC7I:j0064`; neuroscience 9 before
`j0017`; "that couch" 36/73 before `j0075`):

- `lkLwp9o7Djk:j0027`, `lkLwp9o7Djk:j0064`, `5unhHRFkC7I:j0064`,
  `5unhHRFkC7I:j0017` are pivots under both the full-video and the
  three-window budget - their pivot subject's nearest prior mention
  already exceeds three windows (16, never, 9, 9), or is never mentioned
  at all.
- `5unhHRFkC7I:j0039` is a pivot under neither budget - its trailing
  sentence ("Smell is only one piece of this") names nothing specific, so
  the test fails at the naming step regardless of context size.
- **`5unhHRFkC7I:j0075` is a pivot under the three-window budget.** The
  round-2 correction to `#19` (commit `66c54d6`) had argued it out of the
  confirmed list using `5unhHRFkC7I:j0002` and `:j0039` - 73 and 36
  windows before `j0075` - to show "that couch" was already established.
  That argument used exactly the kind of context this entry now forbids:
  evidence the real annotator never receives. Under the budget this entry
  fixes, `j0075` is a pivot, full stop; `66c54d6`'s reasoning for removing
  it is superseded by this entry, not confirmed by it. Its recorded label
  does not change (`implication`) - the closing clause the rule codes
  carries the same generalizing content whether or not the trailing
  sentence is read as a pivot - but its *classification* as a confirmed
  boundary window does.
- **`lkLwp9o7Djk:j0076`'s first read (this entry's own draft, before this
  correction) called it a false pivot on lexical grounds** - "asylums"
  recurs at `j0074`, two windows earlier, so a bare keyword check says
  "already developed." Re-read semantically (see "developed before," and
  the worked example, above), it is a genuine pivot under any budget. This
  is the fourth instance, on this project, of a countable or lexical
  surface trace standing in for semantic judgment - after the
  sentence-boundary punctuation heuristic and the SaT confidence threshold
  (`#15`), and `#19`'s own word-count rule. The first three reached code or
  a recorded label before being caught. This one was caught in a
  measurement, before it became a rule - which is the outcome this
  project's verification discipline exists to produce, and is worth more
  as precedent than the rule this entry writes.

**Corrected list: six windows, not five - `#19`'s rate was undercounted,
not wrong in kind.** `lkLwp9o7Djk:j0027`, `lkLwp9o7Djk:j0064`,
`lkLwp9o7Djk:j0076`, `5unhHRFkC7I:j0064`, `5unhHRFkC7I:j0017`,
`5unhHRFkC7I:j0075` - **6/205 = 2.9%**, not `#19`'s 5/205 = 2.4%. Direction
B's rejection does not need to be reargued at this rate: 2.9% remains far
short of justifying a new field with its own six-test defense, its own
worksheet column, its own `fase3_gate.json` thermometer, and its own line
in every one of the ~3,600-per-channel Fase 5 calls, for a signal
`function`'s own deterministic tie-breaker already resolves. `j0017`
entered the confirmed list on its own merits in the round-4 resolution and
is unaffected by this correction; `66c54d6` treated `j0075`'s exit and
`j0017`'s entry as one seat changing occupants, which this entry corrects:
they are two independent facts, and both windows are now confirmed.

**6/205 is a floor, not a final result, and this entry does not claim
otherwise.** The scan that found the original five (now six) read the
whole video for each window - a wider net than the three-window budget
this entry fixes. Narrowing the budget can only ever add pivots, never
remove them (less visible context cannot resolve an ambiguity the full
video could), so windows exist in the other 199 rows of
`corpus/mackexplains7/fase3_coverage.md` that were coded as a single unit
under full-video judgment and would show a pivot under the three-window
test - the same failure mode `5unhHRFkC7I:j0075` already demonstrates.
This does not threaten Direction B's rejection (the rate would have to
roughly triple before a new field's fixed overhead became proportionate),
it threatens individual labels: a window whose pivot went undetected was
coded as a whole unit when it should have been coded by its closing clause
alone, and the two readings only coincide when the closing clause already
dominates. The next engineering round re-sweeps all 205 rows under the
rule and budget this entry fixes, not just the seven already examined, and
reports the re-measured rate and gate - not the assumption that 6/205
holds.

**`schema/codebook.md`'s existing worked example for `5unhHRFkC7I:j0075`
inverts under this entry and cannot be left as written.** It currently
reads "not a pivot, because 'that couch' refers back to the video's
opening scene (`j0002`, revisited at `j0039`)" - the exact 36-/73-window
reach this entry's rule forbids. Left unedited, that paragraph teaches an
annotator to do what this entry's own evidence section just showed is
wrong. The next engineering round either rewrites it as a positive example
(pivot confirmed under the three-window budget, closing clause coded,
`implication` unchanged) or removes it - it does not survive as a negative
example under the rule this entry writes.

**Consequence for Fase 4, stated as a mechanism, not an intention.**
"Anotar sob o mesmo orçamento" fails silently if left as instruction: a
human with the full transcript in front of them reads past a three-window
boundary without noticing they crossed it. The gold-annotation material
must present, per window, exactly the context block the Fase 5 prompt
assembles (`_docs/plano_implementacao.md` line 478's three prior windows,
text only, no labels) and nothing more - not the full transcript, not the
doccano project's usual whole-video view. This is a requirement on the
Fase 4 tooling (`src/gold.py` or wherever `_docs/plano_implementacao.md`'s
Fase 4 issues land it), not a note in the codebook.

**Retroactive effect, declared rather than discovered later.** The 205
windows of Fase 3's coverage test (`corpus/mackexplains7/fase3_coverage.md`)
were classified with the whole transcript available - the budget this
entry now forbids for the rule that codebook enforces. This does **not**
invalidate the coverage gate: `0/205` in `outro`/`dúvida` holds under any
context budget, because a wider budget can only resolve more ambiguity,
never manufacture it, and the gate counts genuine ambiguity, not pivot
classification. It does **not** invalidate the ontology or the field/value
set. It **does** invalidate using the Fase 3 worksheet's `function`
distribution as a predictor of Fase 5's α (`_docs/plano_implementacao.md`
line 497, "α ≥ 0,667 por campo, no nível de janela," gate table at line
699): that distribution was produced under a more generous context budget
than the model receives, so agreement measured against it would overstate
what the codebook alone, at the budget Fase 5 actually uses, can achieve.

**What this does not reopen.** Direction A itself, `transition`'s removal
from `function`, `cosmic`'s removal from `scale`, the 20/205 gate ceiling,
`SAMPLE_SEED = 42` and the sampled video pair, or the codebook's
verbatim-quote citation format.

## 21. `scale` stays in v1 and Fase 6 (`M7`) aggregates it by narrative third, not as a marginal distribution - measured now, before Fase 6 is groomed

Project owner's decision, made during Fase 3: `scale` stays in
`schema/ontologia.v1.json`'s v1 field set. This entry is not that decision -
it is the aggregation consequence the decision requires, measured now so
Fase 6's grooming does not have to re-derive it, same posture as issue #6
(found during one phase's grooming, filed against the phase that actually
needs it, decided before that phase is touched).

**Why a marginal distribution would throw away the only thing `scale`
measures.** `perfis/<canal>.perfil.json`'s schema already carries
`style.scale_trajectory` as an ordered value
(`_docs/plano_implementacao.md` line 572, `["individual","human","planetary"]`),
not a `field: [p20, p80]` percentile-band shape like every other
`structure`/`pacing` metric in that schema - the plan's own example already
points at position-dependent structure, three elements, without ever
saying so in prose. Measured against the real evidence, `scale`'s
**by-third** distribution over the 205-window Fase 3 coverage worksheet
(`corpus/mackexplains7/fase3_coverage.md`, `_docs/decisions.md#16c`'s two
videos, windows ordered by index, each video split into thirds of
32/33/33 and 35/36/36, then combined by matching third position across
both videos):

| third | n | human | individual | planetary | abstract |
|---|---|---|---|---|---|
| 1st | 67 | 56.7% | 19.4% | 17.9% | 6.0% |
| 2nd | 69 | 81.2% | 14.5% | 0.0% | 4.3% |
| 3rd | 69 | 49.3% | 10.1% | 11.6% | 29.0% |

`planetary` appears only at the open and close of a video (17.9% and
11.6% of their thirds) and is **entirely absent from the middle third**
(0/69); `abstract` is rare everywhere except the final third, where it is
nearly a third of all windows (29.0%, against 4-6% elsewhere); `human`
peaks in the middle (81.2%) and dips at both ends. This is a real
narrative arc - open wide or personal, narrow to human-scale substance for
the body, widen again to implication at the close - not noise. **A flat
marginal distribution across all 205 windows (`human` 62.4%, `individual`
14.6%, `abstract` 13.2%, `planetary` 9.8%) erases this shape entirely** -
it would report the same three numbers for a video that opens planetary
and closes abstract as for one that stays human-scale throughout, which is
exactly the failure mode `position_pct`/`density_by_third`
(`_docs/plano_implementacao.md` lines 552/560) already avoid for `function`
and pacing, and the reason those two fields are stored positionally rather
than as a single marginal number.

**`scale` is not redundant with `function`, so this is not spending effort
on a field `function` already covers.** Mutual information between `scale`
and `function` over the same 205 rows: **0.29 bits**, against `scale`'s
own entropy of 1.54 bits (H(function) = 2.84 bits) - `scale` shares only
about 19% of its own information content with `function`
(0.29 / 1.54 ≈ 0.19), confirmed by the contingency table: `evidence` and
`implication` both occur at every `scale` value, `hook` skews individual
(10/15), `context`/`escalation` never occur at `abstract` or `planetary`
at all in this sample - real association, not independence, but nowhere
near collinearity. A field that mostly duplicated `function` would not
earn its ~3,600-per-channel annotation cost or its own line in Fase 5's
per-field α gate; this one carries information `function` does not.

**Decision: Fase 6's `structure.scale_trajectory` computes the dominant
(mode) `scale` value per narrative third of each video** (or the
distribution per third, if a single mode per third proves too lossy once
real per-channel corpora exist - that refinement is Fase 6's grooming to
make, not this entry's), never a single marginal `scale_distribution`
across the whole video. The percentile-band convention
(`_docs/plano_implementacao.md` line 587, 20-80 not min-max) still applies
per third, across the 30 videos of a profile, not instead of the by-third
split.

**What this does not reopen.** Whether `scale`'s value set is right
(`cosmic`'s removal, `#19`/`#20`) or should have more/fewer values -
separate question, Fase 5's confusion-matrix gate is what tests that, not
this entry. This entry only fixes how the field already frozen in v1 gets
aggregated, not what it contains.

## 22. Documentation gets four layers with declared shelf lives: gates and current state become data (`schema/portoes.json`, generated `_docs/estado.md`), narrative documents stop being read as live state - "one number, one place"

Audited the project owner's five named duplication blocks directly against
the real files, not against a summary of them. All five confirmed, two of
them actually divergent (not just duplicated); two content bugs found in
the same pass; one further staleness spot found beyond what was flagged.

**Measured, not assumed:**

| Block | Files | Divergent? | Evidence |
|---|---|---|---|
| Gates table | `README.md:231-247` vs `plano:689-703` | yes | `plano:696` still prints the flat pre-`#14` "0" for Fase 2 criterion 3; neither table carries `#16c`'s absolute `<=20/205` for Fase 3, both say only "`< 10%`" |
| Conventions | `README.md:282-289` vs `plano:169-176` | yes | `plano:175` says `versao_ontologia`/`gerado_em`; real artifacts (`corpus/mackexplains7/fase3_gate.json`) use `ontology_version`/`generated_at`, matching `README.md:288`, contradicting `plano:175` and its own `plano:182` |
| Phase state | `README.md:40-54`, `plano:84-92`, `plano:754-760` | yes, all three, plus `plano:280` and `plano:330` (not previously flagged) | Issue #11 merged into `main@4c3e165`; every one of these five spots still describes Fase 3 as blocked or upcoming |
| Language policy | `README.md:11-38` vs `plano:37-83` | no | concordant |
| `DECISOES.md` description | `AGENTS.md`, `_docs/process.md:16-20`, `DECISOES.md:3-8` | n/a (duplication, not divergence) | near-verbatim in three places |

Content bugs found in the same sweep, out of scope for this entry to fix
(narrative-document edits happen in the follow-up issue), recorded here so
they are not lost: `plano:336` ("Os cinco testes de cada campo") undercounts
- a sixth test follows at `plano:338-344` as an unlabeled paragraph, and
`_docs/decisions.md#16a` (line 835-836) already calls it "the six tests
(line 336-344 of the plan)" in settled prose. And `plano:572`'s
`scale_trajectory` contract shows a flat 3-element array, which `#21`
supersedes with a per-narrative-third aggregation.

**Diagnosis.** Three document types with different shelf lives share files.
A plan written before implementation ages by nature - expected. A table of
thresholds in force cannot age. A decision record is append-only and never
edited. The gates table went stale because it lives inside the plan and
inherited the plan's shelf life.

**Decision: four layers, each with a declared shelf life.**

| Layer | Ages? | Who edits | Artifact |
|---|---|---|---|
| current state | never - **generated** | script, verified by CI | `_docs/estado.md` |
| gates and constants | never | only with a new decision | `schema/portoes.json` |
| decisions | never - append-only | PM and owner | `_docs/decisions.md` |
| narrative | yes, and that's fine | rarely | `README.md`, `plano_implementacao.md`, `blueprint.md` |
| operational | yes, when process changes | when process changes | `AGENTS.md`, `_docs/process.md`, `_docs/team/*` |

**Rule: one number, one place.** No threshold, constant, key name, or count
appears in prose outside the layer that owns it. Explanatory prose may
repeat freely; a number may not. Number duplication is what produced the
stale "0" above and the Fase 3 threshold that never got its absolute form
outside `#16c`.

**`schema/portoes.json` shape.** `{"schema_version": 1, "created_at": "<full
ISO 8601>", "gates": [...]}`. Array under `gates`, one object per
independently-evaluated condition - a plan bullet stating two conditions
(e.g. Fase 6's "schema valida e o dono reconhece o canal") becomes two gate
rows, not one, each with its own `evaluation`. All keys English; the only
free-prose field is `note` (PT-BR, `#18`'s test), and `note` never carries a
measured value - only the threshold's rationale. A measured value lives in
`artifact`/`result_ref` (pointers to where it was measured/recorded) and is
reported by the generated `_docs/estado.md` - never copied into
`portoes.json`.

Fields:

- `id` - kebab-case, `fase<N><letter?>-<slug>`
- `phase` - integer, 0-10
- `metric` - what is counted, in English. When `threshold.kind` is
  `formula`, `metric` (or `note`) must also state what the formula's free
  variables are measured against (e.g. "`duration_min`/`n_windows`
  measured per video, from `corpus/{channel}/sentences|windows`, the same
  pair `fase2_gate.json` already reads") - undeclared free variables in a
  formula are the same "one number, two meanings" risk this entry exists
  to close, just one level up from a threshold value.
- `threshold` - polymorphic by `kind`:
  - `{"kind": "bound", "op": "<="|">="|"==", "value": number, "unit": string, "denominator"?: number}`
    - the simple case: one number, a fixed sample
  - `{"kind": "formula", "params": {<name>: number, ...}, "expression": string, "unit": string}`
    - parametric per-unit gate (video, minute): `params` are the named
      constants, `expression` is the literal formula against measured
      variables. Case: Fase 2 criterion 3d, which does not fit a single
      `op`/`value` (`_docs/decisions.md#14`). **`expression` is
      descriptive, never executable** - no parser is planned by this
      entry, and running `eval()` (or equivalent) over this string is
      prohibited. If a future phase needs to evaluate it programmatically,
      that parser is designed there, under review - not improvised over
      the string.
  - `{"kind": "qualitative", "statement": string}`
    - no number: pure human judgment. Implies `type: "judgment"` and
      `evaluation: "human_judgment"`.
- `type` - `invariant` | `tolerance` | `thermometer` (`#14`'s taxonomy,
  exclusive to `kind: "bound"`/`"formula"`) | `judgment` (exclusive to
  `kind: "qualitative"` - a deliberately subjective call by the project
  owner, e.g. `plano:595`; never reuses `invariant`, whose `#14` meaning is
  "the algorithm controls the outcome and failing it is a code defect" -
  the exact opposite of a deliberately subjective judgment).
- `blocking` - boolean (`3c`'s `false` comes from this field, never from
  prose - `#14`).
- `evaluation` - `automatic` | `human_judgment`, required.
- `scope` - `global` | `per_channel`, required. `global`: the gate fires
  once for the whole system and never re-blocks a new channel.
  `per_channel`: the gate runs again, blocking, every time a channel goes
  through that phase.
- `artifact` - path to the structured file the measured value is read
  from. Required when `evaluation: automatic`; `null` when
  `human_judgment` with no supporting worksheet. `{channel}` is the
  template placeholder when `scope: per_channel`. **A gate whose
  `artifact` file does not exist yet is "declared, not measured" - the
  `_docs/estado.md` generator must report it as such, never as failed.**
  This applies today to every not-yet-run automatic gate (Fase 4's α,
  Fase 5's α, 5C's smoothing rate): their rows exist in `portoes.json` with
  an `artifact` template pointing at a file that will only exist once that
  phase actually runs.
- `artifact_pointer` - optional, dotted path inside `artifact` when several
  sub-results share one file (e.g. `3d` inside `fase2_gate.json`, which
  already carries 3a/3b/3c/3d).
- `result_ref` - list of references to where a human-judgment verdict was
  recorded - never the verdict itself. Required (may be `[]` explicitly)
  when `evaluation: human_judgment`; absent when `automatic`. `[]` is the
  same "declared, not measured" state `artifact`-not-existing-yet
  represents on the automatic side - never read as a fail.
- `decision_ref` - **list**, one or more items, each in one of two forms:
  `_docs/decisions.md#N[letter]` or `_docs/plano_implementacao.md:LINE[-LINE2]`
  (for original thresholds that only the plan ever fixed - the follow-up
  issue does not write a retroactive decisions.md entry for those; the
  `plano:LINE` form is a legitimate, permanent citation, not a pending
  gap). List because a value can be fixed in one entry and
  revised/restructured in another without the first losing relevance -
  every item listed must remain authoritative for the value in force; a
  purely-superseded entry (e.g. `#12`, whose `5.6` was entirely replaced by
  `#14`'s `4.86`) does not join the list just because it is history -
  history is read inside the entry in force, which already cites the
  superseded one.
  **Test, two failure modes, not one:** rejects a `decision_ref` item whose
  target does not exist, **and** rejects one whose target's `Status` (in
  the generated `decisions.md` index this same wave adds) reads
  `superseded por #N` - a stale reference is exactly as wrong as a missing
  one, and the generated index is what makes "stale" mechanically
  checkable instead of requiring a human to read both entries. This ties
  `portoes.json`'s guard to the index, so the two deliverables of this wave
  validate each other instead of drifting independently.
  When populating: each `decision_ref` item is checked one by one against
  the source that actually fixes/revises that number - never deduced by
  temporal proximity. (`#14` vs. `#12` on `GATE_WINDOWS_PER_MINUTE` is the
  worked example: `#12`'s own "Decision:" block fixes `5.6` and never
  states `4.86` anywhere in its text, lines 348-427; `#14`'s own prose,
  lines 658-670, states it recalibrated and independently re-verified the
  value, rounding to `4.86` - confirmed a third way, independent of both
  entries' prose, against `src/janelas.py:41`'s live constant and
  `corpus/mackexplains7/fase2_gate.json`'s persisted `constants` block,
  both `4.86`. `decision_ref` for that gate is `["_docs/decisions.md#14"]`
  alone - `#14` is self-contained, so `#12` does not join the list.)
- `note` (optional) - PT-BR, the only free-prose field, never a measured
  value - only the threshold's rationale.

**Constants duplicated between `src/` and `portoes.json`.**
`GATE_WINDOWS_PER_MINUTE`/`GATE_WINDOWS_PER_MINUTE_BAND` already exist in
`src/janelas.py`, get persisted into `fase2_gate.json`'s `constants` block
at each measurement (legitimate - a record of what was in force at
measurement time, same role as `ontology_version`), and `portoes.json`
would be a third copy. `portoes.json` documents; it does not become the
execution source in this wave - that would require
`src/janelas.py`/`coleta.py` to read from it at runtime, a behavior change
to an already-tested, frozen module, and would duplicate the loader design
the F3-b issue (`src/schema_loader.py`) is going to build for the
ontology's `Enum`s. Building two divergent loaders for the same kind of
problem, one now and one in F3-b, is worse than one copy with a guard.
Instead: **a test, in the follow-up issue's acceptance criteria, fails if
any `kind: "formula"` gate's `params` diverge from the matching constants
in `src/*.py`** - same pattern as the JSON<->Enum test already planned for
F3-b. When a future phase builds the general loader that reads thresholds
from `schema/`, the duplication disappears by construction; until then the
test is the guard.

**Scope of this entry.** Authorizes, does not itself perform: creating
`schema/portoes.json` (full population, all phases, each `decision_ref`
checked one by one against its real source, not deduced by proximity),
`_docs/estado.md` (generated from `fase*_gate.json` files +
`portoes.json`'s declared-but-unmeasured rows + `git rev-parse HEAD` + open
issues by `fase-N` label, with a CI regenerate-and-compare step, same
posture as `TEST_COUNTS`/`alembic check`), the generated PT-BR index at the
top of `decisions.md` (one line per entry: number, phase, one sentence,
`Status: vigente` or `Status: superseded por #N`, itself tested for
dangling `Status` targets - the escape hatch `#18` already reserved), the
per-phase `Estado:` header in `plano_implementacao.md` (`executado` or
`intenção, não executado`), the dedup of the five blocks above (pointers,
not repeats), the two content-bug fixes, and the `AGENTS.md`/`process.md`
mandatory-reading change (`estado.md` + `portoes.json` + the decisions
index always; a full entry only when its subject is touched; the plan
drops out of mandatory reading for executed phases). All of that is the
follow-up issue's work, not this entry's.

**Related, filed separately.** Designing `scope` surfaced a real gap in
Fase 8's single "`>= 90%` dos criterios" line (`plano:625-654`) - it
conflates a once-only anticircular calibration against holdout with a
per-script, per-channel production report, the same kind of packed claim
`#14` already split for Fase 2 criterion 3. Filed as Issue #13
(`fase-8` label), not decided here - same posture as `#6`/`#12`, found
during another phase's grooming, archived against the phase that actually
needs it.

**Rejected, not reopened.** No gate threshold changes value in this wave.
Where a prose copy disagrees with a measured or decided value, the
measured/decided value wins and the divergence gets reported in
`portoes.json`'s population step, never silently written over - a value
that needs to actually change is a separate decision, not a side effect of
moving it into data. `schema/ontologia.v1.json`, `schema/codebook.md`, and
the frozen Fase 2/3 artifacts (`fase2_gate.json`, `fase2_sample.md`,
`fase3_gate.json`, `fase3_coverage.md`, `sentences/`, `windows/`) stay
read-only inputs to this entry, same as `#16` left them for Fase 3.

## 23. Two process corrections surfaced while grooming the documentation wave (`#22`): `fase-N` is a per-phase-issue rule, not a per-issue one; "main é para... os docs" only ever meant documentation *content*, not documentation *tooling*

Grooming the `#22` follow-up issue (four documentation layers:
`schema/portoes.json`, generated `_docs/estado.md`, the decisions.md
index, per-phase plan headers) hit two process gaps neither a product
decision nor `#22` itself resolves - technical/process calls, made here
per `_docs/team/pm.md`.

**(a) Labels.** `_docs/process.md`'s Labels section read "Toda issue
carrega exatamente uma [`fase-N`]", written before any issue existed that
belonged to no phase. This issue is documentation infrastructure across
every phase, and is the very issue that edits `process.md`. Decision: the
rule narrows to phase issues ("toda issue **de fase** carrega exatamente
uma `fase-N`"), not widened with an exception clause - a universal claim
that was only ever true of a subset is corrected at the subset, not
patched with a growing exclusion list. This issue itself carries the
existing default `documentation` label, no `fase-N`.

**(b) "Main é para... os docs."** The same section's integration rule
("Nada é implementado no checkout principal. Main é para grooming,
integração e os docs") conflated documentation *content* (prose, safely
edited on main) with documentation *tooling* (a generator script, its
tests, a CI step - code, same as any module in `src/`). This wave adds
exactly that tooling, and left unclarified, the sentence would license
skipping the worktree/branch/engineer/QA lifecycle for it, on the
reasoning "it's a documentation issue." Decision: reworded so "os docs"
names only the prose files enumerated in the reworded sentence; anything
else, regardless of subject matter, goes through a worktree like every
other issue. See `_docs/process.md` for the exact text in force.

Neither correction changes any gate threshold, corpus number, or ontology
content. Both are process-text edits, landed in the same commit as this
entry.

## 24. `_docs/decisions.md` index gets a third `Status`: `parcialmente superseded por #N (fragmento)`, not just vigente/superseded - found while grooming the `#22` follow-up, not assumed

`#22` specified the generated index's `Status:` field as binary -
`vigente` or `superseded por #N` - without considering an entry that is
only *partly* replaced. Grooming the `#22` follow-up issue hit a real
instance of exactly that case, so the convention is fixed here, before the
issue is implemented, per the same "decision before issue" discipline
`#22` itself was written under.

**Verified, not assumed: `#12`/`#14` is full supersession, `#19`/`#20` is
partial.** `#12`'s entire content is one thing - criterion 3's per-video
window-count band, `GATE_WINDOWS_PER_MINUTE = 5.6` (lines 382-392) - and
`#14` restructures that whole gate into 3a/3b/3c/3d, restating the same
formula with the recalibrated `4.86` (lines 658-677) and stating outright
it "supersedes item #12's `GATE_WINDOWS_PER_MINUTE=5.6` with `4.86`"
(lines 724-727). Nothing in `#12` survives outside what `#14` already
carries - full supersession, matching `#22`'s own worked example (lines
1783-1805) and `schema/portoes.json`'s existing `note` ("supera," not
"parcialmente supera," the `5.6` original).

`#19`/`#20` is different in kind, not degree. `#20` says so explicitly,
naming a clause, not the entry (line 1394): "**Rule, re-anchored
(supersedes `#19`'s "prior windows in the same video")**." Line 1407-1409:
"**Everything else in `#19`'s rule is unchanged**: when a pivot exists,
code the closing content, never the opening/preview, regardless of word
count, sentence count, or salience." `#19`'s core decision (Direction A,
no new structural-pivot field, the four applied window labels, its own
"what this does not reopen") remains authoritative today; `#20` replaces
only: the phrase "prior windows in the same video" (scope fix, 3-window
budget), `5unhHRFkC7I:j0075`'s status as a confirmed boundary window
(reversed - its `function` label is untouched), and the round-2
correction's stated reasoning for excluding `j0075` (line 1489). A weaker
secondary case with the same shape: `#4` supersedes only `#3`'s `>= 21`
floor (lines 143-145), leaving `#3`'s `collect()`-writes-incrementally
decision untouched and still in force in `src/coleta.py` today.

**Decision: `Status:` is three-way.**

- `Status: vigente` - nothing in the entry is superseded.
- `Status: superseded por #N` - **unqualified**, means the entry's entire
  decision content is replaced/restructured by `#N` (the `#12`/`#14`
  case). Purely historical; not a valid `decision_ref` target.
- `Status: parcialmente superseded por #N (fragmento)` - **the
  parenthetical is required, not optional**, and must name the specific
  clause, value, or classification `#N` replaces (the `#19`/`#20` case:
  `Status: parcialmente superseded por #20 (a frase "prior windows in the
  same video" da regra de pivo; classificacao de boundary de
  5unhHRFkC7I:j0075)`). A bare "parcialmente superseded por #N" with no
  fragment named is not a valid index entry - it states that something
  changed without saying what, which is indistinguishable from not having
  checked, and defeats the reason this index exists.

**Correction, in place** (same posture as item #11's median/mean fix and
item #16's `read_manifesto` fix - the convention is unchanged, the worked
example was incomplete). The `Status` line above for `#19` named two fragments
`#20` replaces and missed a third, equally real one: `#20` also replaced
the boundary-window **rate and confirmed-window list** itself, not just
the pivot rule's wording and one window's classification. `#20`'s own
text says so explicitly (line 1512): "**6/205 = 2.9%, not `#19`'s 5/205 =
2.4%**." The corrected, complete line is:

`Status: parcialmente superseded por #20 (a frase "prior windows in the
same video" da regra de pivo; classificacao de boundary de
5unhHRFkC7I:j0075; taxa e lista de janelas de fronteira confirmadas,
5/205 -> 6/205)`

This is not a cosmetic gap. The immediately following paragraph already
uses the 5/205 rate as its own illustration of a citation that would
slip past the mechanical test - which only works as an illustration if
that rate is in fact a dead fragment of `#19`, meaning it belongs in the
named parenthetical, not outside it. An incomplete fragment list is worse
than none: it lets a future `decision_ref` cite `#19` for the very number
`#20` killed while the `Status` line looks like it already accounted for
everything superseded. **Generalized rule for populating all 24 entries:**
when an entry supersedes more than one clause, value, or classification,
every one of them is named - not the first one found while checking.

**What the mechanical test does and does not catch - stated here so the
guard's real coverage is not overclaimed.** The `decision_ref`
dangling-target test (`#22`) rejects only the **unqualified**
`superseded por #N` string; both `vigente` and a properly-fragmented
`parcialmente superseded por #N (...)` pass it. This is a real, accepted
gap, not a solved problem: a `decision_ref` citing a partially-superseded
entry **for the exact dead fragment** passes the test, because the test
has no way to know which fragment inside the cited entry a given
`decision_ref` relies on - only a human reading the entry's text at
population time can tell that, say, `#19` cited for its old 5/205
boundary-window rate would be citing a number `#20` already killed, even
though `#19`'s `Status` correctly reads `parcialmente superseded` and
therefore passes. The test catches the case where an entire entry is dead
and something still points at it; it does not catch citing a dead part of
an entry that is still partly alive. The defense against that remaining
gap is the same one `#22` already names for every `decision_ref`: checked
one by one against the source that actually fixes the specific value,
never by matching on `Status` alone and never by temporal proximity.

This entry is itself an instance of what it describes: it partially
supersedes `#22`'s `Status:` convention (the binary vigente/superseded
wording) and nothing else in `#22` - `#22`'s four-layer model, its
`schema/portoes.json` field shapes, its scope authorization, and its
"Rejected, not reopened" clause all remain unchanged and in force. When
the generated index is built, `#22`'s own row reads `Status: parcialmente
superseded por #24 (a definicao binaria de Status no campo decision_ref)`.

## 25. `schema/portoes.json` gets a channel-role registry and a per-gate `applies_to_roles` filter; human-judgment `result_ref` becomes per-channel, never inherited; `_docs/estado.md`'s open-issues block stays, with an explicit staleness caveat; `_docs/decisions.md` gets a real in-place-correction boundary rule, not just five emergent examples

Four open technical calls left over by Issue #14 (`#22`/`#23`/`#24`), found
while `_docs/estado.md` was regenerated for real against a channel
(`@Zenn0009`) whose corpus predates any notion of "channel role." Made here
per `_docs/team/pm.md`, before the follow-up issue is groomed - the pattern
`#22`/`#23`/`#24` already used for this same wave.

**(a) `schema/portoes.json` needs a channel-role registry, and each
`scope: "per_channel"` gate needs to declare which roles it applies to.**

Root cause, read directly in `src/estado.py`: `render_portoes_table`
(lines 579-598) computes `channels = _iter_channels()` (every directory
under `corpus/`, line 584) and, for a `scope: "per_channel"` gate, expands
it over every one of those channels unconditionally (`targets = channels
if gate["scope"] == "per_channel" else [None]`, line 588) - there is no
concept, anywhere in `schema/portoes.json`'s field spec (`#22`), of which
channels a given per-channel gate is even meant to run against. This is
exactly why `fase1-holdout-row-floor` prints "falhou (0 linhas holdout)"
for `zenn0009`: the gate is correct (`#6`), the expansion is correct
(the gate is genuinely `per_channel`), and the channel is correct (it went
through Fase 1) - what is missing is that `@Zenn0009` was deliberately never
split into `profile`/`holdout` (`#6`, `#9`), so this gate was never
supposed to run against it at all.

*(1) New field, `applies_to_roles`, on the gate.* Added to every gate
object where `scope == "per_channel"`; absent/ignored where
`scope == "global"` (a global gate has no channel axis to filter). Value:
a non-empty array of role strings, e.g. `["profile_channel"]`. Required,
not defaulted - a `per_channel` gate with no `applies_to_roles` is exactly
the kind of silent gap `#22`'s "declared, not assumed" posture exists to
prevent, so the follow-up issue's acceptance criteria must assert every
`scope: "per_channel"` gate carries a non-empty `applies_to_roles`. Values
are English, snake_case - matching this file's existing convention for
enum-like string values (`type: "tolerance"`/`"invariant"`/`"thermometer"`/
`"judgment"`, `evaluation: "automatic"`/`"human_judgment"`), not the
kebab-case reserved for `id` (`#22`'s field spec). Two roles exist today:
`profile_channel` (a channel like `@MackExplains7` that gets a real
`profile`/`holdout` split and a real Fase 2 human-judgment sample) and
`fixture_channel` (a channel like `@Zenn0009` that, by design, never gets
either - `#6`/`#9` for the split, `#16` for its actual role: validating
collection code and, later, transfer-testing the ontology). These are a
different axis from the manifest's per-**video** `role` column
(`profile`/`holdout`, `#7`) - a `profile_channel` is made of rows with both
manifest roles; a `fixture_channel`'s rows are all manifest-`profile`
because it was never split, which is a fact about the channel, not a
per-row label.

Checked one by one against every existing gate, not assumed from
proximity, because this is exactly the discipline `#22`/`#24` require of
`decision_ref` and it applies equally here:

| Gate | `applies_to_roles` | Why |
|---|---|---|
| `fase1-profile-row-floor` | `["profile_channel", "fixture_channel"]` | Both channel kinds get 30 `profile` rows (`@Zenn0009`: `#4`; `@MackExplains7`: `#9`) |
| `fase1-holdout-row-floor` | `["profile_channel"]` | Only a channel that gets split has holdout rows by design (`#6`/`#9`); `@Zenn0009` never does (`#6`/`#9`) |
| `fase1-word-count-floor` | `["profile_channel", "fixture_channel"]` | Ratio check runs on `profile` rows, which both kinds have |
| `fase2-oversized-window-parity`, `fase2-nonlast-single-window-residual`, `fase2-nonlast-single-window-ratio`, `fase2-window-rate-band` | `["profile_channel", "fixture_channel"]` | Construction-algorithm properties of `sentences/`/`windows/`; `@Zenn0009` has its own (`#16b`), same pipeline |
| `fase2-two-narrative-functions`, `fase2-sentence-cut-midclause` | `["profile_channel"]` | The fixed-seed 50-window **human-judged** sample only ever ran, and is only scoped to run, against a `profile_channel` (`#10`'s `@MackExplains7`-only scope); `#16` never gave `@Zenn0009` an equivalent sample |
| `fase3-outro-duvida-coverage` | n/a | `scope: "global"`, no per-channel expansion to filter |
| `fase4-self-agreement-alpha`, `fase5-model-human-agreement-alpha`, `fase5c-smoothing-rate`, `fase6-owner-recognizes-channel`, `fase6-schema-valid` | `["profile_channel"]` | Fase 4-6 only ever run against a channel that completed a real Fase 1/2 `profile`/`holdout` split and Fase 2 human judgment; a `fixture_channel`'s role (`#16`) stops at Fase 3's transfer test |

*(2) Where the channel-to-role mapping itself lives.* A new top-level key
in `schema/portoes.json`, sibling to `gates`, not a new file and not a
hardcoded table in `src/estado.py`: `"channels": {"<slug>": {"role":
"profile_channel" | "fixture_channel"}, ...}`. `<slug>` matches
`_iter_channels()`'s output exactly - the `corpus/<slug>/` directory name
(`mackexplains7`, `zenn0009`), never the `@Handle` form. Weighed against
`#22`'s four/five-layer table: a channel's role does not age (fixed once,
in Fase 1 grooming, same shelf life as `#6`'s seed/floor) and only changes
with a new decision (e.g. a future entry promoting `@Zenn0009` to
`profile_channel` if it were ever split) - that is exactly the "gates and
constants, never ages, only with a new decision" layer, i.e.
`schema/portoes.json`, not narrative and not a fifth generated artifact. A
separate file would split one fact (which channels exist and what they
are) across two files for no reason; a hardcoded table in `src/estado.py`
would put decided data inside the generator, the exact anti-pattern `#22`
wrote `portoes.json` to stop happening. One map, in the file that already
owns every other gate constant - "one number, one place" applied to a new
kind of number.

*(3) `_docs/estado.md` rendering for a gate outside a channel's role.* Must
not print "passou (...)"/"falhou (...)" - the gate genuinely was not
evaluated - and must not silently omit the row either, or a reader
auditing the table cannot tell "this gate was never meant to run here"
from "this gate row went missing by accident." `measure_gate` already has
the right mechanism for a status that is neither pass nor fail:
`Measurement(passed=None, ...)` renders as bare text with no
`passou`/`falhou` wrapper (`_status_cell`, `src/estado.py:572-576` - this
is exactly how `"declarado, nao medido"` already renders today,
lines 425/451/462/512/537/541). The new case reuses that same mechanism
with **different text**, so it is never confused with "not yet measured":
`_status_cell` must print a row for every `(gate, channel)` pair as
today, and when `channels[channel]["role"] not in gate["applies_to_roles"]`,
`measure_gate` returns `Measurement(None, None, "nao aplicavel (papel do
canal: <role>; portao exige: <applies_to_roles>)")` before it ever reaches
the CSV/JSON-reading branches. `"declarado, nao medido"` keeps meaning
"this gate applies to this channel and has not run yet, run it"; `"nao
aplicavel"` means "this gate will never run against this channel unless a
new decision changes its role" - two different futures, two different
sentences, same non-blocking rendering family `#22` already established
for "declared, not measured is not a fail."

**(b) `result_ref` on a `human_judgment` gate must be keyed per channel -
distinct axis from (a), independently closed.**

(a) fixes *which* channels a gate runs against; it does nothing about
*whose* judgment gets reported once a channel passes the role filter. As
written today, `result_ref` is a flat `list[string]` on the gate object
(`schema/portoes.json:122`, `:137`; field spec, `#22` lines 1848-1852) and
`measure_gate`'s `human_judgment` branch (`src/estado.py:533-537`) returns
`f"registrado em {'; '.join(result_ref)}"` for **any** channel the gate
runs against - it has no channel parameter in that branch at all. A second
real `profile_channel` added after (a) ships passes the role filter
correctly and then inherits `_docs/decisions.md#17` verbatim, exactly as
`@Zenn0009` (whom (a) alone excludes) would have - `#17` only records a
judgment made on `@MackExplains7`'s sample, and it is undefined how a
second channel's own, never-yet-made judgment could already be "registrado
em #17."

**Decision: `result_ref` on every `evaluation: "human_judgment"` **and**
`scope: "per_channel"` gate becomes an object keyed by channel slug, not a
flat list:** `"result_ref": {"<slug>": ["_docs/decisions.md#N", ...], ...}`.
A channel absent from the keys - including one for which the gate's
`applies_to_roles` filter would otherwise let it through - renders
`"declarado, nao medido"` (the exact existing "not yet measured" phrase
from (a)3, deliberately reused rather than coined a third way: an unjudged
channel is the same kind of gap as an unmeasured automatic gate, not a new
kind). `measure_gate` **never** falls back to another channel's key,
never to the first key, never to a channel-less default - a missing key is
"not measured for this channel," full stop, even when every other
condition for running the gate is satisfied. Concretely, the two gates
`#17` already backs:

```json
"result_ref": {"mackexplains7": ["_docs/decisions.md#17"]}
```

for both `fase2-two-narrative-functions` and `fase2-sentence-cut-midclause`
(replacing today's `["_docs/decisions.md#17"]`), and
`fase6-owner-recognizes-channel`'s already-empty `result_ref: []`
(line 211, "`result_ref` vazio ate um veredito ser registrado") becomes
`result_ref: {}` - same meaning, correct shape. A `scope: "global"` gate
with `evaluation: "human_judgment"` (none exists today) keeps the flat
list unchanged: with no channel axis to key by, there is nothing to
mis-inherit across.

**(c) `_docs/estado.md`'s open-issues block: kept, with its own explicit
staleness sentence - not removed, not automated.**

`_open_phase_issues()` (`src/estado.py:627-667`) fetches live GitHub issue
state into a file whose only CI-enforced check, `check()`
(`src/estado.py:747-789`), diffs regenerated-vs-committed for exactly two
blocks - `PORTOES_TABLE` (line 755-763) and `DECISIONS_INDEX`
(line 765-775) - and nothing else, by the module's own stated design (the
`cddb2cb` commit message: the metadata block and the open-issues section
are excluded from that diff "de proposito... porque sao inerentemente
variaveis no tempo"). An issue closing produces no commit, so this block
can go stale for an arbitrarily long time with zero signal, unlike the
gates table (which only goes stale when a gate is actually re-measured,
a rare, committed event).

Weighed against `#22`'s layer table: GitHub already owns open-issue state
(that is why the block is fetched, not hand-maintained) - `_docs/estado.md`
republishing it is a **read-only mirror of a layer it does not own**, not
a duplicate value inside a layer that does (the "one number, one place"
violation `#22` targets is a value living in two owned places at once;
this is one authoritative place, GitHub, echoed into a snapshot). That
distinction is why removal (option 1) is rejected, not just deferred: the
block is genuinely useful - a reader gets the phase-open state without a
`gh` call - and nothing about it duplicates a number this file itself
owns.

A scheduled job that keeps the block fresh (option 3) is rejected too, and
explicitly, not silently: it would trade a stale-but-honestly-timestamped
snapshot for a **new moving part with its own failure modes** - `gh` auth
expiring, a cron silently failing, a job overwriting `main` outside this
project's entire worktree/branch/QA lifecycle (`_docs/process.md`). A
process that can fail invisibly is worse than a snapshot that is visibly,
honestly a snapshot.

**Decision: option 2, kept, with its own caveat sentence - the shared
`gerado em <timestamp>` under the metadata block is not sufficient on its
own**, because a reader has no reason to expect the gates table (real data
that only changes when a gate is remeasured) and the open-issues block
(state that can flip the instant this file finishes generating) carry
different, much shorter shelf lives, from one shared timestamp alone. The
"Fases abertas" section gains one line, directly under its heading:
`Instantaneo do GitHub em <mesmo timestamp do bloco de metadados> - uma
issue pode abrir ou fechar sem gerar nenhum commit aqui; para o estado
real, rode` `` `gh issue list --repo Lcjlle/roteiros-engine --label
fase-N` ``. This sentence is generated text (part of `render_estado_md`'s
output for that section), not hand-maintained prose, so it never drifts
from the timestamp it names.

**(d) In-place correction of an already-published `decisions.md` entry: a
real boundary rule, not five emergent examples with no stated line
between them.**

Read all five existing `**Correction, in place**` paragraphs against
`git blame`, not just their text, because the git history is what actually
shows whether each one edited settled, already-depended-on history or
merely fixed a draft before anything downstream existed:

| Line (this file) | Commit | What it fixed | Existed downstream at edit time? |
|---|---|---|---|
| ~888 (`#16b`) | `1f3a88b`, after `#16`'s own `d7968c6` | False claim about which function defaults `role` (`read_manifesto` vs. `sentencia.run()`) | No - narrative aside, cited nowhere |
| ~929 (`#16b`) | `78e277c`, after `d7968c6` and `1f3a88b` | Wrong window count for a named video ("56" vs. real "24") | No - descriptive fact from an admittedly scratch, uncommitted verification |
| ~950 (`#16b`) | `599b656`, after `d7968c6` | **Changed the actual decision** - `n_videos=1` reopened to a larger sample | No - the recipe itself was still "scratch directory, not committed" (`#16b`'s own words); no gate, entry, or artifact yet depended on `n_videos=1` |
| ~1320 (`#19`) | `66c54d6`, after `#19`'s own `99f72ad` | List-composition error: `5unhHRFkC7I:j0075` wrongly named a confirmed boundary window, real seat is `j0017` | No - `#20` did not exist yet (`06e7cd7` is later the same day); no `decision_ref` anywhere targets the boundary-pivot list (`schema/portoes.json`'s `fase3-outro-duvida-coverage` note says so explicitly: that block is "informativo, nao bloqueante, uma medicao separada") |
| ~1951 (`#24`) | part of `#24`'s own original commit, `40b32d8` - **not** a later edit | Completed `#24`'s own worked-example fragment list for `#19`/`#20` (added the `5/205 -> 6/205` fragment it had initially omitted) | n/a - corrected before the entry was ever published, in the same commit that first published it |

That last row is a real finding, not assumed from the task's framing: the
`5/205 -> 6/205` fragment addition is **not** a later in-place edit of
already-settled history at all - `git show 40b32d8:_docs/decisions.md`
already contains the complete, corrected paragraph. What actually happened
one day later, in `88243c2`, is narrower and different in kind: it
**reworded** that same paragraph's attribution clause - "item #16's
median/mean and `read_manifesto` fixes" became "item #11's median/mean fix
and item #16's `read_manifesto` fix" (`git show 88243c2` - a 3-line,
wording-only diff) - a pure citation-credit fix (which numbered entry set
the precedent for the "Correction, in place" convention itself: `#11`, not
`#16`, per direct check of `#11`'s own text). This one **left no visible
trail inside the entry** - no new `**Correction, in place**` paragraph, no
sentence anywhere in `#24`'s body - only `git log` shows it happened. It
is the one genuinely silent edit in this file's history.

**Testing the candidate rule ("in-place only when the correction does not
change what the entry decides or any fact the entry asserts that something
else could cite") against all five, honestly, including where it fails:**
the `read_manifesto` fix, the window-count fix, and the `j0075 -> j0017`
fix all pass cleanly - none changes a decision, none is cited by any
`decision_ref` or `result_ref` anywhere. The `88243c2` attribution reword
also passes cleanly - nothing cites "which entry gets credit," and no
number or decision changes. But the **`n_videos` amendment fails the
literal rule** - it plainly does change what `#16` decided (the sample
size) - and yet it is the one correction whose posture (`"round 2
amendment, Issue #11"`) this project's own subsequent practice never
revisited or flagged as wrong; `#22`/`#24` audited this file in detail
(`#22`'s whole opening section, `#24`'s `#19`/`#20` analysis) and neither
one names it as a problem. The literal rule is therefore too strict as
stated: it would forbid an amendment nobody has actually treated as
improper. What distinguishes it from the `#19` -> `#20` case (where a real
new entry, not an in-place edit, was required to re-anchor the pivot rule)
is not "did the ruling change" but **whether anything downstream had
already come to depend on the original ruling** - at the time of the
`n_videos` amendment, nothing had (no commit, no other entry, no
`portoes.json` field cited `n_videos=1`); by the time `#19`'s pivot rule
needed re-anchoring, it had already been implemented for real and measured
against the committed corpus (the very rounds 3-4 corrections inside `#19`
itself), so a further substantive change went to a new entry (`#20`)
instead.

**Final rule, precise enough to apply without re-deriving it:**

1. An in-place edit to an already-published entry's text is allowed only
   to fix a **factual or enumeration error in that entry's own prose**
   (a wrong code reference, a wrong count, a wrong item in a list) or to
   **amend a decision that nothing outside the entry has yet come to rely
   on** - checked, not assumed: no other `decisions.md` entry's `Status`
   or prose names this entry as a citation target for the specific value
   being changed, no `schema/portoes.json` field (`decision_ref`,
   `result_ref`, a `note`) cites it, and no committed artifact under
   `corpus/`/`gold/`/`perfis/`/`schema/` already embodies the original
   value as something that ran for real.
2. The moment any of those three things exists - another entry cites it,
   `portoes.json` cites it, or a real artifact was built against it - a
   further substantive change to what the entry decided is **not** an
   in-place edit. It is a new numbered entry, and the changed entry's
   `Status` becomes `superseded por #N` (nothing survives) or
   `parcialmente superseded por #N (fragmento)` (naming the exact
   fragment, per `#24`) - never a silent rewrite of the original text.
3. **Required, going forward, with no exception:** every in-place edit
   permitted by rule 1 must leave a visible, permanent trail *inside the
   entry itself* - a `**Correction, in place**` paragraph (or, for a
   wording-only fix too small to warrant a full paragraph, at minimum one
   sentence in the same place) stating what was wrong and what changed.
   `git log` is not that trail; a reader of the rendered file, not of its
   history, must be able to see that a correction happened. `88243c2` is
   the counter-example this rule closes: a substantively harmless edit
   that nonetheless left zero trace inside the file.

This entry does not reopen any gate threshold, any corpus number, or any
ontology content - `#3`/`#4`/`#6`/`#7`/`#9`/`#10`/`#14`/`#16`/`#17`/`#19`/
`#20`/`#22`/`#24` all stay exactly as they read. It authorizes, and does
not itself perform: adding `channels`/`applies_to_roles` to
`schema/portoes.json`, reshaping the affected `result_ref` fields, editing
`src/estado.py`'s `render_portoes_table`/`measure_gate`/`_open_phase_issues`
call site, and regenerating `_docs/estado.md` - all of that is the
follow-up issue's work, in a worktree, per `_docs/process.md`, same
posture `#22` set for its own follow-up.

## 26. `scripts/pin_worktree_database.py` pins each worktree's own `DATABASE_URL` via a generated `sitecustomize.py`, starting a `scripts/` directory convention

Issue #5. Closes, automatically, the gap `_docs/process.md`'s "Uma
pegadinha que vale saber" section previously guarded only by manual
discipline: a real `DATABASE_URL` exported by the shell that launched a
session wins over `load_dotenv()` by design (`src/db.py`'s own
documented behavior, unchanged), which silently puts every worktree back
on the same database unless someone remembers to prefix every command or
probe first.

**Where it lives, and why.** `scripts/pin_worktree_database.py` - this
repo has no `scripts/` directory yet, so this issue starts that
convention for one-off dev-infra tooling that is neither a pipeline
module (`src/`) nor a test.

**When it runs.** Once, as a step in `_docs/process.md`'s worktree-setup
sequence, placed right after `uv sync` (which can recreate `.venv` and
wipe out an earlier `sitecustomize.py`) and right after `.env` is copied
into the worktree, before `CREATE DATABASE`/`alembic upgrade head`. The
generated `sitecustomize.py` reads `.env` dynamically at every Python
startup rather than baking a `DATABASE_URL` value in when the script
runs, so ordering it right after the `.env` copy (rather than before)
costs nothing and removes any doubt about whether the pin is live before
`.env` exists.

No new dependency in `pyproject.toml` - the script and the
`sitecustomize.py` it writes both parse `.env` with the standard library
only. No database table added or changed; `src/db.py`'s documented
production/CI behavior (a real env var with no `.env` present keeps
winning) is unchanged.

## 27. `#25(a)(3)`'s inline code example is partially superseded by Issue #15's real `exists=False` - the first exercise of the `#25(d)` in-place-correction rule since it was written; `fase1-profile-row-floor` in `@Zenn0009` reconfirmed as `#25(a)`'s already-decided mechanism, not a new finding; `_open_phase_issues()`'s silent `gh` failure fallback named as a second, distinct gap from `#25(c)` - accepted, not implemented

Three items surfaced during a routine audit pass, before any new work was
groomed. Handled together here because all three touch `#25` directly and
none of them authorizes a worktree: one is a real supersession under the
rule `#25(d)` itself just wrote, one is a reconfirmation that must not be
mistaken for a new defect, and one is a named, accepted gap distinct from
one `#25(c)` already covers.

**(a) `#25(a)(3)`'s inline code example: `parcialmente superseded por #27`
- the first real exercise of the `#25(d)` boundary rule.**

The divergence, read directly: `#25(a)(3)`'s prose (`_docs/decisions.md`
line 2171) says `Measurement(passed=None, ...)`; the code block two lines
below it (lines 2178-2179) writes positionally,
`Measurement(None, None, "nao aplicavel (...)")`. `Measurement`
(`src/estado.py:448-451`) is a dataclass typed `exists: bool; passed: bool
| None; display: str` - a positional `None` in the first slot sets
`exists=None`, which is not a legal value for a field typed `bool`, only
for `bool | None`.

The real implementation, built for Issue #15, does not do that.
`measure_gate` (`src/estado.py:584-592`) returns
`Measurement(False, None, f"nao aplicavel (...)")` for exactly this case -
`exists=False`, never `exists=None`. Its own docstring
(`src/estado.py:574-576`) states the reasoning: the same convention
`_measure_manifesto_gate`/`_measure_json_pointer_gate` already use
elsewhere in this module, where `exists=False` means "no artifact read
was even attempted," not "the gate does not exist." QA on Issue #15
confirmed this reading against the real code, not against `#25`'s
example.

Applying `#25(d)`'s rule to this exact case, not assuming the answer:
rule 1's third condition - "no committed artifact already embodies the
original value as something that ran for real" - is false here. A
committed, tested artifact (`measure_gate`) embodies a *different* value
(`exists=False`) than the entry's own example implied (`exists=None`),
and it does so having read the entry and consciously departed from it,
not by accident or oversight. That is rule 2's trigger, read literally:
"another entry cites it... or a real artifact was built against it."
Silently editing `#25`'s code block now to read
`Measurement(False, None, ...)` would erase the fact that Issue #15 made
a considered call diverging from published guidance - exactly the
silent-rewrite failure mode rule 3 exists to prevent, the same one
`88243c2` was the counter-example for. So: not an in-place fix.
`#25`'s `Status` becomes `parcialmente superseded por #27 (fragmento: o
exemplo de codigo inline do (a)(3))`; nothing else in `#25` moves - the
`channels`/`applies_to_roles` registry, per-channel `result_ref`, the
`_docs/estado.md` staleness caveat, and the `#25(d)` rule's own text all
stand as written.

**Decision, for the record:** the corrected example, going forward, is
`Measurement(exists=False, passed=None, display="nao aplicavel (papel do
canal: <role>; portao exige: <applies_to_roles>)")` - matching the real
`measure_gate` code exactly, and written with keyword arguments this
time, precisely to remove the positional ambiguity that produced the
original error.

This is the first real invocation of the `#25(d)` rule since it was
written, in the same entry, the same day. What it decides here, as
precedent: a code example inside a `decisions.md` entry is not exempt
from the citation test just because it reads as illustrative rather than
declarative. An engineer who reads it and implements consciously against
it counts as "a real artifact was built against it" for rule 2's
purposes, exactly as a `schema/portoes.json` field citing the entry
would - the example does not get a lower bar than the prose around it
just because it is fenced as code.

**(b) `fase1-profile-row-floor` in `@Zenn0009`: a reconfirmation of
`#25(a)`'s mechanism, not a new finding.**

`corpus/zenn0009/manifesto.csv`'s header is `id,titulo,duracao_s,
contagem_palavras,fonte` - no `role` column, across all 30 rows. Both
`src/coleta.py::check_gate` (line 505) and `src/estado.py`'s
`_measure_manifesto_gate` (line 472) count a row with no `role` key as
`profile` (`row.get("role", ROLE_PROFILE)`), matching `check_gate`'s own
docstring ("Linhas sem coluna `role` (manifesto pre-holdout) contam como
`profile`, entao manifestos antigos continuam validados exatamente como
antes," lines 497-498) and `schema/portoes.json`'s `fase1-profile-row-floor`
`note` ("rows with no role column count as profile too, per
`src/coleta.py::check_gate`," line 8).

This is not an unnoticed mechanism. `#25(a)` already named it and decided
against it directly (`_docs/decisions.md:2126-2130`): "a fixture_channel's
rows are all manifest-profile because it was never split, which is a fact
about the channel, not a per-row label" - and `#25(a)`'s own gate table
already set `fase1-profile-row-floor`'s `applies_to_roles` to
`["profile_channel", "fixture_channel"]` with exactly this reasoning
named as the cause.

**Conclusion: correct, existing, deliberate behavior. No code change.**
This round's own audit re-confirmed `#25(a)`'s mechanism; it did not
discover it. Recorded here only so a future pass does not re-flag the
same fact as a new defect.

**Correction, in place** - the original fundamentation above only cited
`#25(a)`'s existing gate-table entry and its "a fact about the channel,
not a per-row label" phrase (line 2135 of this file); it never actually
examined the fallback mechanism's discriminating power or the render's
disclosure, which is exactly what a later QA advisory pass named as the
real risk worth checking - the same class of defect Issue #15 existed to
kill: a gate that renders "passed" without having verified anything
discriminating. Completing the reasoning here, in place, because the
conclusion below does not change - only what supports it does.

*Chronology, checked against this file's own line numbers, not assumed.*
`#3` (line 150) and `#4` (line 180), which fix `@Zenn0009`'s corpus
shape, predate `#6` (holdout draw, line 256) and `#7` (the manifest's
`role` column, line 273). The manifest's missing `role` column is
therefore not, at authoring time, evidence of an intentional "this
channel will never be split" call - the split concept did not exist yet.
`#25(a)`'s "a fact about the channel, not a per-row label" phrasing is
imprecise about that origin: read literally it suggests the manifest's
shape was chosen *because* the channel would never split, when the
causality runs the other way. That imprecision is real.

It does not change the conclusion, because `#16` - written after
`#6`/`#7`, before `#25`, and independently of it - already made the
deliberate call directly: "`role` defaulting makes every row `profile`,
which is correct here: `@Zenn0009` was never split into profile/holdout"
(lines 1010-1012). By the time `#25(a)` restated the same fact several
entries later, it was citing an already-decided position (`#16`'s own
explicit "correct here," on top of `#6`/`#9` deciding which channels
split at all), not inventing retroactive intent on the spot. The
chronological-accident point is correct about the manifest's *origin*; it
is not correct about whether the current behavior is *deliberate* - `#16`
settles that independently of `#25`.

*Discriminating power, checked against the real code, not assumed.*
`row.get("role", ROLE_PROFILE)` (`src/coleta.py:505`,
`src/estado.py:496`) does not make `fase1-profile-row-floor` check
nothing for `zenn0009`: it counts real rows in a real, committed
`manifesto.csv` against a real floor (`>= 30`), and that count fails if
rows are ever removed from the file. What it correctly does not do is
discriminate profile from holdout rows - because `zenn0009` legitimately
has zero holdout rows by design (`#6`/`#9`/`#16` exclude it from the
split), so there is no role distinction left to get wrong. The audit's
own observation that the check "can never fail" is accurate only as a
consequence of the corpus being frozen at exactly 30 rows (`#4`), a
property shared by *every* already-passing floor gate against a
committed, frozen corpus - `mackexplains7`'s own
`fase1-profile-row-floor`/`fase1-holdout-row-floor` are equally
frozen-passing at 30/5 rows (`#9`) - not something the role-fallback
mechanism introduces or is unique to.

*Disclosure, checked against the rendered file, not assumed.*
`_docs/estado.md` renders the gate's `note` ("rows with no role column
count as profile too, per `src/coleta.py::check_gate`") in the same
`Metrica` cell, on the same row, as the `Status` cell's `passou (30
linhas profile)` (`_docs/estado.md` line 24,
`fase1-profile-row-floor (zenn0009)`) - a reader who reads the row, not
only the `Status` column, sees the mechanism named right next to the
result. That is a real, if easy-to-skim, co-located disclosure -
categorically different from Issue #15's actual defect: a
`human_judgment` gate's `result_ref` inheriting another channel's
citation (`_docs/decisions.md#17`) with **no** caveat anywhere in the
render for the channel that was never actually judged. That is exactly
what `#25(b)`, implemented by Issue #15 (`fd3228c`), fixed - per-channel
`result_ref` keying so a missing key renders "declarado, nao medido"
instead of silently inheriting.

So the analogy the advisory raised fails on both axes it has to hold on
to land: `fase1-profile-row-floor`/`zenn0009` has a real, if narrow,
discriminating check (row count against a real file) and a visible
caveat (co-located in the render); Issue #15's actual defect had neither.
**Conclusion, unchanged: correct, existing, deliberate behavior, now with
the fundamentation the original text skipped over. No code change.**

**(c) `_open_phase_issues()`'s silent `gh` failure: a second, distinct
gap from `#25(c)` - named, accepted, not implemented.**

`check()` (`src/estado.py:825-854`) diffs exactly two regenerated-vs-
committed blocks, `PORTOES_TABLE` and `DECISIONS_INDEX` - never
`OPEN_ISSUES`/"Fases abertas," by the module's own documented design
(module docstring, `src/estado.py:17-25`). `#25(c)` already names and
accepts the consequence of that design: an issue can open or close with
no commit, so the block can go silently stale, and the staleness caveat
sentence `render_estado_md` writes into "Fases abertas"
(`src/estado.py:743-750`) is `#25(c)`'s answer to exactly that risk.

What `#25(c)` does not name is a second, different failure mode.
`_open_phase_issues()` (`src/estado.py:695-720`) wraps its `gh issue
list` call in a bare `except Exception` and, on failure - expired auth,
no network, `gh` not installed - returns the string "nao foi possivel
consultar issues abertas no GitHub agora (...)" instead of raising. That
string is ordinary rendered text, not an error signal: a `--write` run
during an outage commits it into `_docs/estado.md`'s `OPEN_ISSUES` block
for real, and `--check` never notices, for the same reason `#25(c)`
already gives - the block is never compared. This is not `#25(c)`'s
drift case restated: drift is the block being *stale but correct as of
its own last real fetch*; this is the block recording a *failed fetch*
as though it were data.

**Decision: accepted, not implemented - same posture `#24` gave the
`decision_ref`-fragment gap** (`_docs/decisions.md:2057-2074`, "a real,
accepted gap, not a solved problem"). Naming the risk here is the entire
action taken. A caveat sentence keyed to fetch success, or a retry, would
be a new moving part with its own failure modes - the exact reasoning
`#25(c)` already used to reject a scheduled refresh job for the whole
block. No code change follows from this item.

This entry does not reopen `#25`'s channel-role registry, per-channel
`result_ref`, or the `#25(d)` rule's own text - only the one inline code
example named in (a). It authorizes no follow-up issue and no worktree:
(a) is documentation-only (`measure_gate` has read `exists=False` since
Issue #15; only this entry's text changes), and (b)/(c) each close with a
named conclusion - reconfirmed-correct and accepted-risk, respectively -
that requires no code.

## 28. Fase 4↔Fase 5 context budget for gold annotation enforced by one bundle-generation function shared between the export and the prompt builder, by construction rather than instruction; `density`'s field-level alpha uses a project-implemented Krippendorff ordinal-distance closure with `nltk.metrics.agreement.AnnotationTask` (Apache-2.0), rejecting the GPL-3.0 `krippendorff` package

`#20` already named the problem for Fase 4 without settling the mechanism:
"'Anotar sob o mesmo orçamento' fails silently if left as instruction: a
human with the full transcript in front of them reads past a
three-window boundary without noticing they crossed it." This entry is
the mechanism `#20` deferred, corrected on one point this revision found
while writing the worked proof (which symmetry `#20` actually requires),
closed on a second leak the bundle format itself would otherwise
introduce, plus the same set of adjacent gaps in the two portões this
entry has always been about (`schema/portoes.json`'s
`fase4-self-agreement-alpha` and `fase5-model-human-agreement-alpha`):
does the person or process applying an alpha threshold actually receive
what the rule assumes they receive.

**(a) The budget is imposed by what the artifact contains, never by what
the UI hides - and the symmetry `#20` actually requires is between Fase 4
and Fase 5, not between this phase's own two annotation rounds.**

`_docs/plano_implementacao.md` names `doccano` as the Fase 4 tool (line
447) and Fase 5A's real context shape (line 483): "as 3 janelas
anteriores (só texto, sem rótulos)" before the target window. Feeding
doccano a project whose documents are the raw, in-order window list of a
gold video - the natural way to import "the windows of the 5 gold
videos" (plan line 454) - reproduces exactly the whole-video view `#20`
forbids: doccano's own document browser lets the annotator page forward
and back through every window of the video, which is the full transcript
in a different UI, not a restricted one. Hiding that browser with a UI
setting, or asking the annotator not to use it, is instruction - `#20`'s
own diagnosis is that instruction is what fails silently here.

**Decision: the Fase 4 export step does not import a video's window list
into doccano at all.** For each window `j` of a gold video, it builds one
self-contained bundle:

```
{
  window_id,     # real sequential id, e.g. "lkLwp9o7Djk:j0230" - persisted only, never rendered
  display_id,    # opaque per-window token shown wherever a document/prompt needs an id
  context,       # text of windows j-3..j-1, fewer if j<3, never padded from another video or from j+1 onward
  target,        # text of window j
}
```

and that bundle, not the video, is the unit imported as one doccano
document (or written to a lighter file-per-window worksheet, if the
eventual issue drops doccano for this pass). Every document in the
project is one window's already-budget-limited bundle, across all 5 gold
videos, so browsing to a different document in doccano's list only ever
surfaces a *different* window's own bounded context - never additional
context for the window currently being judged. The imposition is that
bytes beyond the budget are never assembled into the artifact in the
first place, not that they are present and suppressed. Annotating in
video order (plan's own trap, "Anote na ordem do vídeo") stays an
instruction, not a budget mechanism, because violating it does not leak
context - it only reintroduces the fatigue/ordering risk the plan already
names separately.

**`window_id` is a second positional leak the bundle format would
otherwise introduce - closed on both sides by the same field split.**
`_docs/plano_implementacao.md` line 157 already forbids exactly this
class of signal for Fase 5: "não passe a posição percentual da janela no
prompt - o modelo responderia pela posição e não pelo texto" (restated at
line 486 for the actual 5A prompt). Plan line 454 literally asks Fase 4's
doccano import to carry "`window_id` como metadado" - and a sequential
`window_id` like `j0230` is not a weaker version of that same leak, it is
the same leak measured coarser. Checked against this project's own
corpus, not assumed: the 30 real `@MackExplains7` `profile` videos this
gold sample is drawn from have windows/video mean 122.1, median 121.5,
range 106-141 (`_docs/decisions.md#12`'s measured stats, `WINDOW_MAX_WORDS=35`/
`WINDOW_MAX_SENTENCES=4`) - a coefficient of variation of ~9.6%. A
`window_id` in the `j0100`s is reliably late in *any* video in this
corpus without an annotator or a model ever being told the video's total
window count; four sequential ids shown together in one bundle's context
(e.g. `j0227`-`j0230`) make that inference free across repeated exposure
to many bundles, the exact same "responde pela posição e não pelo texto"
failure `pos_pct` is banned for - `pos_pct` is more precise, not more
disqualifying in kind. So the option of arguing `window_id` is an
acceptable, lesser leak does not survive contact with this corpus's own
measured window-count distribution - it is rejected, not adopted.

**Decision: the sequential `window_id` is never rendered to the
annotator or the model on either side.** `display_id` is a deterministic
function of `(video_id, window_id)` alone (e.g. `sha1(f"{video_id}:
{window_id}")[:8]`) - stable across re-runs, for the same reproducibility
QA already expects from a fixed seed (`#16`'s `n_videos`/window draws),
but carrying zero ordinal relationship to position: two windows' hashes
have no numeric relationship to which one comes first, unlike two
sequential ids. Fase 4's doccano metadata uses `display_id`, satisfying
plan line 454's "with `window_id` as metadata" literally - a stable
per-document key - without satisfying it with the leaking value. `window_id`
itself is written only into the persisted gold artifact (`gold/<canal>/...`),
which the annotator does not read during annotation. Fase 5's prompt
builder goes further: it interpolates neither `window_id` nor `display_id`
into the assembled prompt text at all - the bundle's `window_id` is used
purely as an in-code correlation key, to store the model's structured
output against the right row of the run record, never as text the model
reads. A stable `display_id` re-showing the same token 48h later, when
the same gold video is reannotated (b), does not reopen anything: the
annotator already recognizes the window's own *text* on reannotation by
design (the plan asks to reannotate the same video), and "sem consultar a
primeira anotação" governs access to recorded *answers*, not recognition
of a document's own already-familiar content.

**The symmetry `#20` requires is between phases, not between this
phase's two rounds - one function, two call sites, not two
implementations.** `#20`'s own text anchors the tie-breaker "to the
context an annotator actually receives in the call" and requires the
Fase 4 gold-annotation material to "present, per window, exactly the
context block the Fase 5 prompt assembles... and nothing more." That is
a Fase 4 ↔ Fase 5 requirement: the human doing Fase 4 and the model doing
Fase 5 must receive the same budget, because both are being held to the
same codebook rule under the same gate family. It is a different
requirement from (b) below, which is about Fase 4's own two annotation
rounds (round 1, round 2 48h later) never diverging on the *labels* a
prior pass produced - a within-phase concern this entry keeps separate so
the two do not get conflated the way `#19`'s asymmetric lookahead once
was. **Decision: the bundle-generation function this alínea defines is
consumed by exactly two call sites, not reimplemented at either one** -
the Fase 4 gold exporter (`src/gold.py`, `#20`'s placeholder), and the
Fase 5A prompt builder (`_docs/plano_implementacao.md` line 483's "as 3
janelas anteriores"). Neither module is a natural home for a function the
other also needs, so the follow-up issue places it in a small shared
module (e.g. `src/context_budget.py`), importable by both - the exact
name is the follow-up issue's call, not this entry's; what this entry
fixes is that there is exactly one function, and both callers invoke it
with the same `(video_id, window_index, windows_source)` signature. The
`j < 3` edge case (fewer context windows for the first two windows of a
video) is therefore handled identically on both sides by construction,
not asserted separately for each - a divergence here could only come from
maintaining two implementations, which this decision forecloses.

**Concrete proof, applied to the exact bundle format above, not just
asserted: the pivot rule produces `#20`'s already-decided labels for all
four of `#20`'s confirmed boundary windows, under the three-window
budget.** Verbatim text and reasoning below reused from `#19`/`#20`
directly (`_docs/decisions.md` lines 1331-1375, 1516-1541, 1570-1577,
1596-1599), not reinvented:

- **`lkLwp9o7Djk:j0027`.** Bundle context = text of `j0024`-`j0026`;
  target = `j0027`. Context contains only `j0026`'s "Pointing at the
  right building, wrong floor" (a generalizing aside on Egypt's near-miss
  mood theory) - Greece is not named or developed anywhere in this
  three-window context (its actual nearest prior mention is `j0011`, 16
  windows outside any three-window budget). `j0027`'s trailing sentence
  opens "Now we cross the Mediterranean, and we have to talk about
  ancient Greece..." - pivot confirmed under the bundle. Rule codes the
  closing clause, which generalizes `j0026`'s established content ->
  **`implication`**. Matches `#20`'s confirmed label exactly.
- **`lkLwp9o7Djk:j0064`.** Bundle context = `j0061`-`j0063` (the Belgian-
  town/Gilles case). Target opens "Then comes the early modern period,
  and things in Europe get notably worse before they get better." - this
  subject is never mentioned anywhere earlier in the video (`#20`:
  "never"), so a fortiori absent from the three-window context - pivot
  confirmed. Rule codes the closing clause, which generalizes the
  Belgian-town case -> **`implication`**. Matches.
- **`lkLwp9o7Djk:j0076`.** Bundle context = `j0073`-`j0075`. `j0074` is
  inside this budget and does contain the word "asylums" ("the York
  Retreat's outcomes were dramatically better than contemporary
  asylums") - the harder case, where the word recurs *inside* the
  budget, not outside it. Under `#20`'s semantic-not-lexical test, that
  mention is a comparison baseline, not a development of `j0076`'s
  actual claim (mass-scale 19th-century overcrowding to catastrophic
  levels) - pivot still confirmed. Rule codes the closing clause,
  "Unevenly. With enormous suffering in the gaps. But the direction was
  right," which qualifies the prior progress claim -> **`objection`**.
  Matches `#20`'s corrected label exactly, and demonstrates the semantic
  test survives the harder case (word present in-budget), not just the
  easy one.
- **`5unhHRFkC7I:j0075`.** Bundle context = `j0072`-`j0074`. Target's
  trailing sentence, "Let's come back to that couch," names "that
  couch" - not mentioned anywhere in this three-window context (its
  actual prior mentions, `j0002`/`j0039`, sit 73/36 windows outside any
  three-window budget). Pivot confirmed under the bundle, exactly as
  `#20` concludes ("under the budget this entry fixes, `j0075` is a
  pivot, full stop"). Recorded label unaffected either way, per `#20`:
  **`implication`** - only the window's classification as a confirmed
  boundary window changes, not its label.

All four match `#20`'s already-decided outcome under the bundle format
this alínea literally specifies - the same worked-example standard `#20`
itself used to close Fase 3, applied here to close Fase 4's mechanism.

**(b) The 48h self-agreement reannotation (`fase4-self-agreement-alpha`,
`schema/portoes.json` lines 164-178) runs under the identical bundles
from (a), because it is the identical shared function - and round 1's
answers are unreachable to round 2 by construction, not by discipline.**

The gate is Krippendorff's α, human×human, on the 1 gold video reannotated
48h later against the original annotation of the same video (`schema/portoes.json`'s
`fase4-self-agreement-alpha`; plan line 457: "Espere 48h e reanote 1
vídeo sem consultar a primeira anotação"). Two requirements have to hold
at once and are easy to conflate: not seeing the *content* beyond three
windows (a) already fixes, and not seeing the *first pass's labels* (the
plan's own "sem consultar" clause) - this alínea's own subject, and a
*within-phase* symmetry distinct from (a)'s *cross-phase* one, kept
separate per (a)'s own closing paragraph so the two are never treated as
one requirement solved by one fix. The bundle format from (a) already
never carries labels, first pass or second (it mirrors Fase 5A's own
rule, "não passe os rótulos das janelas anteriores" - the exclusion is
the same for a window's own neighbors as for its own annotator's prior
verdict). So the reannotation pass reuses the exact same
bundle-generation function against the same gold video; nothing about
the context budget is re-decided or re-coded for round 2.

**"Sem consultar" resolved as a mechanism, not an instruction to
remember.** The round-2 bundle-generation script's own signature takes
only `(video_id, windows_source_dir)` - it has no parameter, import, or
environment variable through which a path under `gold/<canal>/` (where
round 1's stored answers live) could ever reach it. This is stronger
than moving round 1's file out of reach before round 2 runs: it is not
that the file is inaccessible by policy, it is that the code path
generating round 2's bundles never has a way to open it, structurally.
If the two guarantees (content budget, prior labels) were implemented by
separate code paths instead, drift between them is exactly the failure
mode `#20` already caught once (the `j0075`/`j0017` seat-swap, `66c54d6`'s
reasoning built on evidence the real annotator never receives) - one
generator, invoked twice, with no read path to `gold/`, forecloses a
second instance of it here.

**Escalation when `fase4-self-agreement-alpha` fails.** The gate is
`blocking: true` (`schema/portoes.json` line 170) - a fail is not a soft
signal. `_docs/plano_implementacao.md` line 504 already writes a
three-step ladder for a failing field-level α - rewrite definition and
tie-breaker, reannotate (two attempts); merge the confused values; remove
the field - but writes it under Fase 5B, for `fase5-model-human-agreement-alpha`.
**Decision: the same ladder applies to a `fase4-self-agreement-alpha`
failure, in the same order.** A self-agreement fail means one person,
applying the codebook's own words to the same window twice, produces two
different labels - that is a direct, no-second-annotator-needed signal
that the field's definition is underspecified for *any* applier, human
or model, which is exactly what step 1 (rewrite definition, reannotate)
diagnoses and step 2/3 remedy if step 1 does not resolve it. Fase 4 as
scoped has no second independent human annotator to distinguish "this
one annotator is inconsistent" from "the definition is broken," so the
ladder's own bias toward fixing the definition first, rather than
assuming annotator noise, is the correct default here too. **Decision:
this blocks Fase 5** - not a new call, a consequence of the gate's own
`blocking: true` already read literally: `fase5-model-human-agreement-alpha`
measures model×human agreement against this same gold, and a passing
model×human α would be uninterpretable evidence if the human side of it
was never shown to be self-consistent (agreeing with a human who cannot
even agree with themself proves nothing about the model). No new field is
added to `schema/portoes.json` for this - the ladder is a documented
procedure for working the existing gate to a pass, same posture the plan
already gives `fase5-model-human-agreement-alpha`, not a second gate.

**(c) `cta`'s 0/205 sample gap gets a seeded, duration-blind
gold-selection procedure - and the heuristic scan only ever selects
candidates, it does not answer whether the zero rate is a channel
property or a segmentation artifact.**

`#16` fixed the gold/batch split but never fixed *which* profile videos
become gold - unlike Fase 2/3's window-level sampling
(`src/amostragem.py`, `SAMPLE_SEED = 42`), no seed or rule governs
gold-video selection yet, so nothing here reopens a settled draw. By the
time Fase 5's batch is annotated, the corpus is already fixed (`#4`/`#9`)
and the composition can no longer be biased toward a rare value without
re-touching frozen corpus decisions - Fase 4 is the last point this is
cheap.

**Concrete step, before the gold videos are picked - selects candidates
only, and does not itself resolve issue #12(a)'s open question.** Run a
text-heuristic scan (not annotation - no LLM calls, no human judgment)
across all 30 `@MackExplains7` profile-video transcripts for solicitation
language near each video's end ("subscribe", "link in the description",
"hit the bell", and channel-specific equivalents found by reading a
handful of real endings first). This raises the odds that the 5-video
gold sample actually exercises `cta` at all, using the full 30-video
corpus instead of the 2-video Fase 3 sample the issue itself flags as too
small to trust - it does **not** decide whether a zero `cta` rate is a
property of this channel or a signal of a segmentation cut too coarse to
ever produce a `cta`-shaped window; that question stays open exactly as
the closing paragraph of this entry already states, deferred until a
second channel's data can show whether the zero rate generalizes.

**Seed and procedure for the 5-video draw, registered before it is run
for real.** Same convention as `SAMPLE_SEED = 42` (`src/amostragem.py`,
`_docs/decisions.md#10c`/`#6`): candidate `video_id`s sorted, drawn with
`random.Random(42)`, without replacement, no duration weighting anywhere
in the draw.

- **If the scan finds candidate videos:** draw 1 anchor uniformly from
  the sorted list of candidates with `random.Random(42)`, then draw the
  remaining 4 from the sorted list of the other 29 profile videos, same
  seed, without replacement. This satisfies "the gold sample must
  include at least one candidate" deterministically and reproducibly -
  QA can re-derive the exact same 5 videos from the same seed, same
  posture as every other seeded draw this project has made.
- **If the scan finds none across all 30:** draw all 5 uniformly from
  the sorted list of all 30 profile videos, same seed, no constraint -
  the fallback issue #12(b) already asks for becomes mandatory
  regardless of which 5 are chosen, and `cta`'s absence does not change
  how `function`'s field-level α is computed (Krippendorff's formula
  does not break when one categorical value never occurs in the sample -
  it simply never gets tested); the persisted Fase 5 run record
  (`_docs/plano_implementacao.md` line 500, "Registre o run") must
  additionally log the observed per-value occurrence count for every
  field, so a passing `function` α (`fase5-model-human-agreement-alpha`)
  is never read as certifying all 10 `function` values, `cta` included,
  when `cta` was never exercised.

**This procedure is not yet run - what follows is the procedure, not a
result.** Once the scan and draw actually execute, the follow-up issue
must log the 5 drawn `video_id`s and their real `duracao_s`
(`corpus/mackexplains7/manifesto.csv`) here or in a superseding entry,
the same way `#16`'s Fase 3 draws logged their picks and durations
(`ZJai7C3tb1M`, 238s; `Dw2Pifv1JrM`, 547s).

**Gold selection does not pre-decide, and cannot accidentally bias, the
open duration question.** `@MackExplains7`'s real `profile` videos run
17.32-26.43 minutes (`_docs/decisions.md#12`), against `DECISOES.md`
item 2's 10-12 minute target duration for generated scripts - a real,
already-flagged mismatch (`_docs/decisions.md#11`/`#12`), and separately
still open as GitHub Issues #6 and #13 (both `fase-8` label, confirmed
live/open) about turning Fase 8's per-video profile metrics into
per-minute rates. That question is out of scope for this entry entirely.
The uniform random draw specified above (`random.Random(42)` over a
sorted candidate list, no duration term anywhere in the selection)
structurally forecloses the one way gold selection *could* bias it:
hand-picking the shortest videos. Nothing in this procedure ranks or
filters by `duracao_s`.

**(d) `density` (integer 0-2, `schema/ontologia.v1.json` lines 43-49)
uses Krippendorff's `ordinal` distance metric for its field-level α, not
the `nominal` default every other field in this ontology uses - computed
via `nltk.metrics.agreement.AnnotationTask` with a project-implemented
ordinal-distance closure, not the `krippendorff` PyPI package this
entry's prior revision adopted.** **Correction, in place**: this entry's
own title/index line previously read as if `AnnotationTask` supplied the
ordinal metric itself ("adopts `nltk.metrics.agreement.AnnotationTask`'s
ordinal metric") - false; the ordinal distance is this project's own
closure, merely consumed by `AnnotationTask` via its `distance=`
parameter. A second factual correction: the prior description counted all
valid `density` ratings in the closure's marginals. It now counts exactly
the ratings belonging to units with at least two valid ratings, the same
eligibility population used by `AnnotationTask.alpha()` for observed and
expected discordance. No architecture or metric changes.
`schema/codebook.md`'s own normative
definitions (lines 642-686) make this a censored count, not an
equal-interval scale: `0` = no new concept, `1` = exactly one new
concept, `2` = "two or more distinct new concepts" - an open-ended
ceiling bucket that absorbs 2, 3, 4, or more concepts identically. A
nominal metric would score a 0-vs-2 disagreement identically to a
0-vs-1 disagreement, discarding the ordering the codebook itself
asserts; an `interval` metric would instead treat the 1-to-2 gap as
numerically equal to the 0-to-1 gap, which the ceiling-bucket
definition of `2` makes false. Krippendorff's `ordinal` metric derives
inter-category distance from the observed marginal distribution's
cumulative frequencies rather than assuming a fixed numeric gap, which
is the correct fit for an ordered-but-unequally-spaced scale.

**Reversed from this entry's prior revision: the `krippendorff` PyPI
package (`pln-fing-udelar/fast-krippendorff`) is not adopted - the
owner's decision, not a new finding by this revision.** It is
**GPL-3.0** (confirmed against the package's own `LICENSE.txt` and PyPI
trove classifier, as the prior revision already established).
`_docs/blueprint.md` gets its own "NÃO ADOTADO — GPL-3.0" entry for it
(see that file's diff) - the copyleft risk the prior revision judged
tolerable for a non-commercial phase ("does not block adoption... must
be re-examined the day... is ever distributed") is, on reflection, a
door `DECISOES.md` item 3 explicitly leaves open ("ver
`_docs/decisions.md` se algum dia isso mudar"): a GPL-3.0 dependency is
not a mere footnote for that future revision, it is a real blocker that
would have to be excised. Not adopting it now, while `density`'s α is
not yet wired into any module, costs nothing; adopting it now and
un-adopting it later costs a rewrite. `nltk` (Apache-2.0) replaces it as
the concordance library for every field, `density` included.

**Runtime confirmed, not assumed: the code path this project actually
calls (`AnnotationTask(data, distance=...).alpha()`) never touches
`nltk`'s corpus-download machinery.** Checked directly against
`nltk/nltk` (branch `develop`, GitHub, read for this revision) at three
levels. First, `nltk/metrics/agreement.py` and its eight sibling
modules imported by `nltk/metrics/__init__.py` (`aline`, `association`,
`confusionmatrix`, `distance`, `paice`, `scores`, `segmentation`,
`spearman`) were grepped in full for `nltk.data`, `nltk.download`,
`LazyLoader`, `LazyCorpusLoader`, `.find(`, and `import nltk.corpus`/
`from nltk.corpus` - zero occurrences across all nine files. Second,
`import nltk` (an unavoidable side effect of `from
nltk.metrics.agreement import AnnotationTask`, since Python always runs
a package's `__init__.py` on import) does pull in many submodules at
top level in `nltk/__init__.py` (`nltk.chunk`, `nltk.classify`,
`nltk.metrics`, `nltk.tag`, `nltk.tokenize`, `nltk.translate`, and
others, ~215 lines total) - this is real and not free, but it is not
the same thing as "downloads a corpus." Third, and this is what makes
the two different: `nltk/__init__.py` line 175 assigns
`corpus = lazyimport.LazyModule("corpus", locals(), globals())` -
`nltk.corpus` itself is not eagerly imported, and the corpus objects it
eventually exposes are instances of `LazyCorpusLoader`
(`nltk/corpus/util.py`). `LazyCorpusLoader.__getattr__` (the only place
`self.__load()` - the method that calls `nltk.data.find(...)` and would
raise the "install this corpus" error - is invoked) explicitly skips
dunder attribute lookups and fires only on a real, named attribute
access such as `.words()`; nothing in the `AnnotationTask`/`alpha()`
call path this project uses ever accesses a `LazyCorpusLoader` attribute
at all, so no lazy loader is ever triggered by it, at import time or at
call time. **Decision-relevant conclusion: `import nltk` is not free,
but "not free" is not "downloads a corpus" - nothing on the path this
project's `density`/`evidence_type` α computation actually calls goes
near `nltk.download()` or a corpus lookup.**

**`nltk.metrics.agreement.AnnotationTask` accepts an arbitrary distance
function, but that function is a pure two-argument callable - it is
never given access to the dataset's frequency table, so the ordinal
distance cannot be a stateless formula and must be built as a
closure.** Confirmed directly against `nltk/metrics/agreement.py`
(branch `develop`, `nltk/nltk` on GitHub, read for this revision, not
inherited from a prior citation): `AnnotationTask.__init__(self,
data=None, distance=binary_distance, missing_values=None)` takes
`distance` as its second parameter, defaulting to `binary_distance`;
every call site - `agr()`, `Do_Kw_pairwise()`,
`weighted_kappa_pairwise()`, and `Disagreement(self, label_freqs)`
(called from `alpha()`) - invokes `self.distance(l, k)` with exactly
two label arguments inside a loop that itself already holds the
frequency table (`label_freqs`, a `FreqDist` built by `alpha()` per item
and accumulated across items into `all_valid_labels_freq`). `distance`
itself never receives `label_freqs`. The only way to give the ordinal
distance access to the marginals `n_g` it needs is to compute those
marginals independently - one pass over the same dataset, before
`AnnotationTask` is constructed - and close over them:

```
δ²(c, k) = ( Σ_{g=c}^{k} n_g − (n_c + n_k) / 2 )²        for c ≤ k
```

where `n_g` is the observed marginal frequency of category `g`: a count
over every valid `density` rating belonging exactly to a unit with at
least two valid ratings in the dataset being measured, not per-item.
That is the same eligibility filter `AnnotationTask.alpha()` uses for
its observed and expected discordance, so the closure, observed
discordance, and expected discordance share one population. **This
closure is a required implementation detail, not an option**:
`density_ordinal_distance = build_ordinal_distance(all_density_values)`
must run once against a `FreqDist` over those eligible ratings from the
dataset's own observed `density` labels (both round-1/round-2 or
model/human sides being compared) *before*
`AnnotationTask(data, distance=density_ordinal_distance)` is
constructed - never a bare `lambda c, k: abs(c - k)` or
`lambda c, k: (c - k) ** 2`. Both of those are interval distances
wearing an ordinal
name for exactly the reason this alínea's own codebook paragraph above
already rejects an `interval` metric for `density`: they assign a fixed
numeric gap to each adjacent pair of categories (1 for `|c−k|`, an even
more pronounced fixed gap for `(c−k)²`), which is precisely what the
`2`-or-more ceiling bucket makes indefensible. Krippendorff's ordinal
distance is the one construction that lets the *data itself*, not an
assumed scale, say how far apart `1` and `2` really are relative to `0`
and `1`.

**Test requirement: reproduce the nominal, ordinal, and interval α of
the worked example Krippendorff (2011) itself publishes, against
hard-coded data in the test - not just the nominal figure.** Source:
Klaus Krippendorff, "Computing Krippendorff's Alpha-Reliability"
(Annenberg School for Communication, University of Pennsylvania,
2011.1.25, literature updated 2013.9.13;
`https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff's%20Alpha-Reliability.pdf`,
identical text mirrored at
`https://www.infoamerica.org/documentos_pdf/kripen.pdf`; also
`repository.upenn.edu/asc_papers/242`) - read directly for this
revision, not taken from a secondary description. Section C/D's own
worked example, 4 coders × 12 units, values 1-5, missing data as `.`:

```
Coder A: 1 2 3 3 2 1 4 1 2 . . .
Coder B: 1 2 3 3 2 2 4 1 2 5 . 3
Coder C: . 3 3 3 2 3 4 2 2 5 1 .
Coder D: 1 2 3 3 2 4 4 1 2 5 1 .
```

The paper's own published results for this exact matrix: **α_nominal =
0.743** (Section C), **α_ordinal ≈ 0.815**, **α_interval = 0.849** (both
Section D; the paper also gives α_ratio = 0.797, not required here).
**Reproducing only the nominal figure does not validate anything about
this alínea's decision**: the nominal metric is the library default
(`binary_distance`-equivalent for exact match), exercises no custom
`distance` callable, and would pass identically whether or not the
ordinal closure is implemented correctly, or at all. Only the ordinal
figure exercises the marginals-dependent closure this alínea requires;
the interval figure (a much simpler, stateless `(c−k)²`) is included as
a second, independent check that the harness wiring itself - feeding a
custom `distance` into `AnnotationTask` and reading `alpha()` back out -
is correct, isolating closure-specific bugs from wiring-specific ones.

**The same matrix and the same three values appear, verbatim, as a
doctest inside the rejected package's own source file - which fixes
where the citation above has to point, and where it can never point.**
Checked directly for this revision, not assumed: `krippendorff/krippendorff.py`,
inside `pln-fing-udelar/fast-krippendorff` (branch `master` on GitHub,
read at lines ~330-349 in the commit checked for this revision - line
numbers shift between commits, the content does not), carries the same
4-coder × 12-unit matrix as a doctest in `alpha()`'s own docstring, with
`round(alpha(reliability_data, level_of_measurement="ordinal"), 3)` →
`0.815`, `level_of_measurement="ratio"` → `0.797`, and
`level_of_measurement="nominal"` → `0.743` - the same three numbers the
test requirement above must reproduce. The rejected package did not
invent this example: it reproduced the same published example this
alínea already cites. That is exactly the trap the follow-up issue's
test author must not fall into: if the test's hard-coded matrix/values
are ever copied out of a locally `pip install`ed `krippendorff` package
(even as a "just borrowing the numbers" shortcut, never importing the
library itself), the test's hard-coded data becomes traceable to the
rejected GPL-3.0 source file, not to the article - reopening, over
text/data rather than code, the exact same kind of workaround this
project has already refused once. **The test's data and its citation
must always trace to Krippendorff (2011) directly (URL already given
above), never to `krippendorff.py`.**

**Confirmed directly in the same source file, not assumed:
`AnnotationTask.alpha()` already excludes any unit with fewer than two
valid values natively - by omission of the triple, not by a filtering
step before the call - which is exactly what (e) below assumes for
`evidence_type`.** `alpha()`'s own body (`nltk/metrics/agreement.py`,
read for this revision):

```python
for i, itemdata in self._grouped_data("item"):
    label_freqs = FreqDist(x["labels"] for x in itemdata)
    labels_count = sum(label_freqs.values())
    if labels_count < 2:
        # Ignore the item.
        continue
```

and the constructor's own docstring states the same rule in prose:
"Missing data (a coder not annotating an item) is represented by simply
omitting that `(coder, item, label)` triple: Krippendorff's `alpha`
drops items annotated by fewer than two coders." No pre-filtering step
is required or should be written: a window where a given annotator did
not code a value for a conditional field (e.g. `evidence_type` when
`function != 'evidence'`) is handled correctly by never constructing
that `(coder, item, label)` triple in the first place - `alpha()`'s own
grouping-and-count logic above drops the resulting under-populated item
on its own.

**Alternative rejected: implement Krippendorff's alpha from scratch,
from the coincidence matrix, with no new dependency at all.** This was
considered because it would sidestep any dependency-license question
entirely. Rejected: the ordinal-distance closure over the dataset's
marginals (above) is required work either way - it is not optional
scaffolding that a from-scratch implementation would avoid. Once that
closure exists, what a from-scratch `alpha()` would still have to
reimplement - grouping ratings by item, computing observed and expected
disagreement from the resulting coincidence matrix, and dropping
under-populated items - is exactly what `AnnotationTask`/`alpha()`
already does, correctly, under a permissive license (Apache-2.0), with
no restriction this project's own use triggers. The test requirement
above (reproducing all three of Krippendorff (2011)'s own published α
values against hard-coded data) validates the *combination* of the
ordinal closure and whichever `alpha()` implementation computes the
coefficient - a from-scratch implementation would need to pass the
identical test to be trusted, buying no additional correctness
guarantee over reusing `nltk`'s. Writing and maintaining a second
implementation of coincidence-matrix bookkeeping this project does not
need to own is effort spent, not risk avoided.

**Decision: the Fase 5 validation module computes `density`'s
field-level α via `nltk.metrics.agreement.AnnotationTask(data,
distance=density_ordinal_distance)`, where `density_ordinal_distance`
is a closure built by the project over a `FreqDist` of the dataset's
own observed `density` values, implementing `δ²(c, k)` above - never a
bare function of two integers, and never the `krippendorff` PyPI
package.** Whichever library or bespoke code the other four nominal
fields' α uses is unaffected by this decision either way;
`nltk.metrics.agreement.AnnotationTask` is adopted as this project's one
concordance-computation entry point regardless, since its default
(`binary_distance`) already covers the nominal case those four fields
need.

**(e) `evidence_type` (categorical, `required: false`, `condition:
function == 'evidence'`, `schema/ontologia.v1.json` lines 30-36) treats
"not applicable" as missing data excluded from its own α, not as
automatic agreement and not as a sentinel `n/a` category - and its α is
conditional on `function` agreement in a way none of this ontology's
other four fields' α figures are.**

The two rejected options share the same failure: both a synthetic "n/a"
agreement and a sentinel `n/a` category let the overwhelming majority of
windows - every window where `function != 'evidence'` - inflate
`evidence_type`'s measured α, because that "agreement" is really
`function`'s agreement leaking into a different field's number: two
annotators who both correctly (or both incorrectly, in the same way)
call a window `hook` instead of `evidence` will *always* "agree" on
`evidence_type: n/a` for it, regardless of whether `study` vs.
`statistic` vs. `case` vs. `analogy` vs. `authority` are discriminable at
all on the much smaller subset of windows where the field actually
fires. `nltk.metrics.agreement.AnnotationTask.alpha()` already has a
native way to handle a value a coder does not provide - confirmed
directly in `nltk/metrics/agreement.py`, quoted in (d) above: a unit
with fewer than two valid values for a field contributes nothing to
that field's reliability estimate and is dropped. Exactly what happens
if the `(coder, item, label)` triple for `evidence_type` is simply
omitted from the data fed to `AnnotationTask` whenever `function !=
'evidence'` for that annotator/window, instead of coding a sentinel
`n/a` category.
**Decision: option (b), exclude.** `evidence_type`'s α is computed only
over windows where the annotators being compared both coded `function ==
'evidence'` and both filled the field.

**Named explicitly, not left as a side effect: `evidence_type`'s α is
conditional on `function` agreement, and is therefore not comparable to
the other four fields' α figures, which are each measured over the
entire sample.** `function`, `loop`, `scale`, and `density` are all
`required: true` and their α denominators are the full gold/batch window
count; `evidence_type`'s denominator is only the subset where two
annotators already agree `function == 'evidence'` - a fundamentally
different, much smaller and non-random population (conditioned on prior
agreement itself), which is why a marginal pass or fail on
`evidence_type`'s threshold (`fase5-model-human-agreement-alpha`,
`schema/portoes.json`) must be read against its own, much smaller,
occurrence-conditioned N - the same per-field occurrence-count logging
(c) already requires for `cta` - not assumed comparable to `function`'s
full-sample α.

**(f) The tool is `doccano`, not Potato - checked, not assumed - and no
`codebook: true` flag or named architectural conflict exists anywhere in
this repository to cite.** `_docs/plano_implementacao.md:447` names
`doccano` (MIT) as the Fase 4 tool; a full-repo grep for "Potato" returns
exactly one hit, `_docs/blueprint.md:118` (verified directly - not line
117 as an earlier pass of this text miscounted), inside a five-item
generic enumeration ("brat, doccano, INCEpTION, Label Studio, Potato")
that is never revisited, never selected, and never discussed again
anywhere in this project's docs. A full-repo grep for `codebook: true` /
`codebook:true` returns nothing. There is no line to cite and this entry
does not invent one. The real, actual architectural conflict Fase 4 has
to resolve is the one (a) already names and fixes: not a Potato flag, but
`doccano`'s own document-browser model, which by default exposes the
whole-video view `#20` forbids unless the import unit is a
pre-bundled, budget-limited window - (a)'s decision - not the raw
per-video window list.

**What this does not reopen.** `#16`'s gold/batch split, `#19`/`#20`'s
boundary-pivot rule and three-window budget figure itself, `scale`'s
value set or `#21`'s by-third aggregation, the ontology's five-field set
or any value already cut (`transition`, `cosmic`), or the open duration
question (`_docs/decisions.md#11`/`#12`, GitHub Issues #6/#13,
`fase-8`). This entry does not cut `cta` from v1 and does not claim the
heuristic CTA scan in (c) answers issue #12(a) - it is a cheap,
non-authoritative candidate-selection filter for gold-video choice only,
and the codebook's own definition of `cta` still governs any real
annotation.

**Follow-up work this entry authorizes but does not itself perform**
(same posture `#20`/`#25` set for their own follow-ups, per Regra #23 -
this is logic/tooling, not documentation content, so it needs an issue
and a worktree, not a direct commit): writing the shared bundle-generation
function (a) specifies, in a shared module the follow-up issue names
(not `src/gold.py` alone, since Fase 5 has no reason to import a module
named for Fase 4's own export step); wiring the project-implemented
ordinal-distance closure for `density` and the triple-omission-based
missing-data exclusion for `evidence_type` into
`nltk.metrics.agreement.AnnotationTask` calls inside the Fase 5
validation module (`src/valida.py`, not yet written); running
the 30-video CTA heuristic scan and the seeded gold-video draw from (c),
and recording the real result (video ids, durations) in a future
`decisions.md` entry once it is actually run; and updating
`schema/portoes.json`'s `fase4-self-agreement-alpha` and
`fase5-model-human-agreement-alpha` notes plus
`_docs/plano_implementacao.md`'s Fase 4/5A/5B text to point here once the
mechanism is real, per this file's own precedence rule over the plan.

## 29. Fase 4 gold-annotation mechanism made concrete: `doccano` dropped for a display-id/window-id split JSONL worksheet, `src/context_budget.py`/`src/valida.py` module names fixed, `#28(c)`'s cta-candidate scan and seeded gold/reannotation draw worked out as a checkable example against `@MackExplains7` for the follow-up issue's own acceptance criteria - not yet the frozen selection, which is that issue's deliverable - and `evidence_type` excluded from `fase4-self-agreement-alpha`'s binary pass/fail

`#28` fixed the Fase 4↔Fase 5 bundle mechanism and the α handling for
`density`/`evidence_type`, but left the annotation tool/file format, two
module names, and the `#28(c)` cta-candidate scan/seeded draw as "the
follow-up issue's call" (`#28`'s own closing paragraph). Grooming the Fase 4
backlog into five issues (F4-a through F4-e) closed all of these. Eight
decisions below, (a)-(h).

**Correction, in place**: an earlier revision of (f)/(g) below stated the
cta-candidate scan and the seeded gold/reannotation draw as already
"executed for real" and the resulting 5 videos as the decided "gold
set," logged the same way `#16`'s Fase 3 picks were. That overstated
what a grooming pass may settle: `#28(c)` itself assigns running this
procedure for real, and persisting `gold/mackexplains7/selection.json`,
to "the follow-up issue" - issue #18 - not to the entry that grooms it.
Nothing changes about the algorithm, the phrase list, or the
reannotation-draw rule (all still decided below); what changes is that
the specific video ids computed below are a verification example this
grooming pass ran to make issue #18's acceptance criteria checkable
against real data, not Fase 4's actual, settled selection - that
remains issue #18's own deliverable, produced by its own code, tests,
and QA.

**(a) `doccano` is dropped for this implementation pass; the Fase 4 gold
export uses a file-per-video JSONL worksheet instead.**

`_docs/plano_implementacao.md:447` names `doccano` as the Fase 4 tool, and
`#28(a)` explicitly leaves room to drop it ("ou escrita em um worksheet
mais leve, arquivo-por-janela, se a issue eventual abandonar doccano para
esta passada"). Reasons to exercise that option: the ontology has 5 fields
per window (`schema/ontologia.v1.json`), and doccano's text-classification
project model does not support multiple independent categorical fields per
document - the plan's own contingency for that case ("se a ferramenta não
suportar múltiplos campos por item, um projeto por campo", line 455) would
require 5 separate doccano projects, imports, and exports reconciled back
into one record per window, for ~610 windows across 5 gold videos. Nothing
else in this project runs a service; `schema/`, `codebook.md`, and
`perfis/<canal>.perfil.json` are already versioned files, diffed in review,
per `#1`. A file the project owner edits directly is the same pattern
applied to annotation, with no new infrastructure, no multi-project
reconciliation, and a diff-reviewable history.

**(b) Worksheet format: `display_id`, never `window_id`, is what the
annotator's file contains; the two are split into separate files.**

Embedding `window_id` in the same JSON record the annotator edits, in
video order, would reopen exactly the leak `#28(a)` closes for doccano's
own metadata field - a human editing 100+ records in a text editor sees
the monotonic `j0027`, `j0028`, ... sequence trivially, worse than
doccano's hidden document browser. Decision:
`gold/<canal>/round{1,2}/<video_id>.worksheet.jsonl` (the file the
annotator opens - `display_id`, `context`, `target`, and the 5 ontology
fields blank) is a separate file from
`gold/<canal>/round{1,2}/<video_id>.index.json` (`display_id ->
window_id`, consulted only by the merge step, never by the annotator).
`window_id` re-enters the record only in the persisted, merged gold
artifact (`round{1,2}.gold.json`) - which `#28(a)` already permits
("`window_id`... written only into the persisted gold artifact... which
the annotator does not read during annotation").

**(c) Shared bundle module named `src/context_budget.py`.**

`#28(a)` leaves the exact name open ("the exact name is the follow-up
issue's call") while floating `src/context_budget.py` as its own example.
Adopted literally - it is the name the decision itself already put
forward, avoids inventing a third candidate, and does not imply ownership
by either phase's own module (`src/gold.py` for Fase 4, a not-yet-written
Fase 5 prompt builder).

**(d) `src/valida.py` (the Fase 5 module name the plan already gives,
`_docs/plano_implementacao.md` F5-b) is built now, under Fase 4, and
reused later by Fase 5 without a second implementation.**

`#28`'s own follow-up paragraph places the ordinal-distance closure and
the `evidence_type` exclusion logic "into `nltk.metrics.agreement.AnnotationTask`
calls inside the Fase 5 validation module (`src/valida.py`, not yet
written)" - but Fase 4's own gate, `fase4-self-agreement-alpha`, needs a
working Krippendorff's α now, on the same two fields (`density`'s ordinal
closure, `evidence_type`'s exclusion), computed the same way. Building
the generic `compute_field_alpha()` machinery once, under a `fase-4`
issue, and letting a future Fase 5 issue call it for model×human data
(never reimplementing it) is the same "one function, two call sites"
posture `#28(a)` already established for `context_budget.build_bundle`.

**(e) The `#28(c)` cta-candidate scan reads each profile video's full
transcript text, not only its ending.**

`#28(c)` suggests "solicitation language near each video's end" as an
untested heuristic and explicitly defers the exact scan window to
whoever reads real endings first ("found by reading a handful of real
endings first"). Read for this grooming pass: the strongest real
solicitation pattern found in `@MackExplains7`'s 30 `profile`
transcripts - "Link in the description. See you inside." (an in-video
plug for an external PDF guide) - occurs at `pos_pct` 0.39-0.65,
mid-video, not near the end (first seen at
`corpus/mackexplains7/windows/pPm3vHUQCpo.json`'s `j0073`, and five more
videos listed in (f) below). A tail-only scan would have missed every one
of those. Decision: `scan_cta_candidates()` scans a video's entire
window-text sequence, not a suffix window.

**(f) cta-candidate phrase list fixed by evidence against the real
corpus: `["link in the description", "let me know in the comments", "let
us know in the comments"]`.**

Tested against all 30 `profile` transcripts before fixing the list:
`subscri` matched only `"no newsletter to unsubscribe from"` (negated,
not a solicitation); `follow`/`notification` matched only narrative uses
(`"the years that followed"`, `"a notification to check"`), zero real
hits; `"hit the bell"`/`"smash that like"`/`"comment below"` never
matched at all. The three phrases retained each matched a genuine
viewer-facing solicitation, and two of the resulting videos are not a new
finding - `Qgz_k2JQ3UY:j0113` and `yKqe_ey3QOs:j0101` are the exact two
windows `schema/codebook.md`'s own already-written positive examples for
`cta` already cite (lines 443-444) - the scan rediscovers the codebook
author's own known cases via a reproducible mechanism, rather than
replacing them with an unrelated heuristic. **Computed once during this
grooming pass, to make issue #18's acceptance criteria checkable against
real data - not an implementation of Fase 4 itself, and not the
persisted artifact `#28(c)` names**: sorted, the 8 candidates this
one-off computation found are `0neQIzWDXaM`, `7xgt_LQxedc`,
`kLYsABip8tI`, `MMycNJ05f8M`, `pPm3vHUQCpo`, `Qgz_k2JQ3UY`,
`Y_-aMBlHWgE`, `yKqe_ey3QOs`. `#28(c)`'s own closing sentence ("this
procedure is not yet run") stands: issue #18's own implementation is
what actually runs `scan_cta_candidates()` for real and persists
`gold/mackexplains7/selection.json`; the values above are a
verification target for that issue's tests, not a substitute for
running it.

**(g) New rule for which of the 5 gold videos gets the 48h
reannotation: drawn from the same `random.Random(42)` sequence,
immediately after the 5-video draw, never hand-picked.**

`#28(c)` fixes the 5-video draw's algorithm but never names which one
gets reannotated 48h later (`_docs/plano_implementacao.md:457` only
says "1 vídeo", no rule). New decision: the reannotation video is drawn
from the same `random.Random(42)` sequence used for the 5-video draw,
continued (`rng.choice(sorted(gold_videos))`) rather than hand-picked -
the same reproducibility every other seeded draw in this project already
has (`SAMPLE_SEED=42` in `src/amostragem.py`, `HOLDOUT_SEED=42` in
`#6`).

**Worked example, not the official selection.** Running `#28(c)`'s
procedure (candidates non-empty) against this grooming pass's one-off
computation of (f)'s candidate list and the real 30-video profile pool:
`rng = random.Random(42)`; `anchor = rng.choice(sorted(candidates))` ->
`7xgt_LQxedc`; `rest = rng.sample(sorted(v for v in all_30_profile if v
!= anchor), 4)` -> `['0neQIzWDXaM', 'rk7qIWcLJ40', 'Leol0DxxGe4',
'C27Dd23jZzA']`; reannotation video (same `rng`, continued) ->
`7xgt_LQxedc` - a coincidence of the draw order, not a selection
criterion; nothing in the procedure filters or ranks by cta-candidate
status past the first draw. Real `duracao_s` from
`corpus/mackexplains7/manifesto.csv`, for reference: `7xgt_LQxedc`
(1400s), `0neQIzWDXaM` (1395s), `rk7qIWcLJ40` (1281s), `Leol0DxxGe4`
(1196s), `C27Dd23jZzA` (1314s). **This is a verification computation
this grooming pass ran to make issue #18's acceptance criteria
checkable, not Fase 4's official gold-video selection.** Issue #18's own
implementation is what runs `select_gold_videos()`/
`select_reannotation_video()` for real and persists
`gold/mackexplains7/selection.json` - the artifact `#28(c)` names as the
actual decided output. Until that issue's code, tests, and QA pass, the
gold sample is not settled.

**(h) `evidence_type` does not count toward
`fase4-self-agreement-alpha`'s binary `passed`; only the four `required:
true` fields do.**

`_docs/plano_implementacao.md:465` states the gate by field without
naming an exception, and `evidence_type` is one of the five fields
`schema/ontologia.v1.json` defines. `#28(e)` already establishes that
`evidence_type`'s α is computed over a fundamentally different,
occurrence-conditioned population ("not comparable to the other four
fields' α figures") and must be read against its own N - but does not
itself say `evidence_type` is excluded from the gate's own pass/fail,
which is a distinct question from how its α is computed.

**Correction, in place**: the prior text repeated a numeric threshold,
including while quoting the plan. The source-owned configured per-field
threshold in `schema/portoes.json` applies instead; this is the
source-of-truth correction, not a threshold change.

Decision: `fase4-self-agreement-alpha`'s `passed` is `True` iff
`function`, `loop`, `scale`, and `density` (the four `required: true`
fields) each meet that configured per-field threshold; `evidence_type`'s
α is computed and persisted in the same
`gold/{channel}/fase4_gate.json` artifact but never folds into that
boolean. Reasoning: `evidence_type`'s `required: false`/`condition`
status in the ontology itself already marks it as structurally different
from the other four - `compute_field_alpha()` (`#22`'s own contract)
returns `None` for it whenever its eligible population - the windows in
the single reannotated gold video where both annotators code
`function == 'evidence'` - has zero eligible units, and also returns
`None` when at least one eligible unit exists but that eligible marginal
collapses to a single category; it calls `AnnotationTask.alpha()`
normally as soon as there is at least one eligible unit and the eligible
population contains at least two distinct categories, with no two-unit
minimum imposed anywhere. Treating a non-identifiable `evidence_type` α
(a degenerate eligible population) identically to a real failure on a
`required: true` field would block Fase 5 over a field the gate was
never in a position to measure meaningfully. `schema/portoes.json` is
aligned in the same grooming-correction round to encode this gate
definition and reference `#28`/`#29`; Issue `#22` consumes that
source-owned definition and does not modify it. Its note continues to
read "Fase 4 ainda não rodou para nenhum canal - declarado, não medido"
until real human data exists (`#23`).

**What this does not reopen.** `#28`'s bundle mechanism, the three-window
budget, the ordinal-distance formula for `density`, the
exclusion-based handling of `evidence_type`'s missing data, or the
rejection of the `krippendorff` PyPI package - all unchanged. Issue
`#12(a)`'s open question (whether `cta`'s rate is a channel property or a
segmentation artifact) is not resolved by (f)/(g)'s measured candidate
count - a non-zero candidate count from a cheap text heuristic is not an
annotated, agreed-upon `cta` rate. The duration question
(`_docs/decisions.md#11`/`#12`, GitHub Issues #6/#13, `fase-8`) is
untouched; the seeded draws in (g) rank and filter by nothing but the
cta-candidate scan and profile-video membership, never by `duracao_s`.

**Follow-up work this entry authorizes but does not itself perform**: the
five Fase 4 issues (F4-a through F4-e) implementing (a)-(h) above; a
future Fase 5 issue consuming `src/valida.py`'s `compute_field_alpha()`
for `fase5-model-human-agreement-alpha` without reimplementing it, per
(d); wiring `gold/mackexplains7/fase4_gate.json` for real once round 1
and round 2 are actually annotated, and updating
`schema/portoes.json`'s notes to point here, per (h).
