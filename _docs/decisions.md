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
