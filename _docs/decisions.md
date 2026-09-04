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
