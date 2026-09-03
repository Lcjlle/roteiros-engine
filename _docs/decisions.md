# Decisions

Calls made while grooming the backlog - technical and scope decisions, not
the three product decisions in `DECISOES.md`. Settled here so issues stop
re-litigating them.

Where this file and `_docs/plano_implementacao.md` or `_docs/blueprint.md`
disagree, this file wins.

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
bounds were sized against. Median sentence length here is 14 words
(`sat-3l-sm`, verified against the real output, not assumed); at
`WINDOW_MAX_SENTENCES = 4` that is a natural window size around 55-60
words, right at the gate's own per-window ceiling - there is no room left
to also shrink window *count* into `[25, 60]` for a video this long without
either raising `GATE_MAX_WINDOWS_PER_VIDEO` or raising
`WINDOW_MAX_SENTENCES`, neither of which this issue's acceptance criteria
authorize an engineer to change unilaterally.

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
has an engineer decide alone.
