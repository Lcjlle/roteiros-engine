# Rascunho — decisão Fase 4 (orçamento de contexto do gold humano)

Status: **rascunho, revisão 2 aplicada** (ajustes que o dono pediu depois de
ler a revisão 1) - ainda não commitado em `_docs/decisions.md`.

Este arquivo existe para o rascunho parar de viver só na conversa do
orquestrador. Revisões acontecem neste mesmo arquivo, nesta mesma branch
(`draft-fase4-decisao`), preservando histórico via commits - a versão
original entregue pelo PM (`PM-Fase4-Draft`), antes de qualquer revisão, é
o commit `d767d84`; esse commit é o histórico, não uma seção duplicada
dentro deste arquivo. A partir daqui o arquivo contém a revisão 2: aplica
os bloqueantes e ajustes pedidos pelo dono, substituindo a prosa da
revisão 1 em vez de acumulá-la ao lado.

Numeração: confirmada contra o índice vigente de `_docs/decisions.md` no
momento desta revisão - a última entrada publicada é `#27`
(`_docs/decisions.md` linhas 2413/2620), então `#28` é o próximo número
livre. Fixado abaixo como `## 28.` diretamente, não mais como "quando for
aprovado será #28" - quando esta entrada de fato migrar para
`_docs/decisions.md`, reconfirmar que `#28` continua livre no índice
vigente naquele momento (uma entrada nova pode ter sido publicada entre
esta revisão e a aprovação final).

---

## 28. Fase 4↔Fase 5 context-budget symmetry - not round-1↔round-2 within Fase 4 - enforced by one bundle-generation function shared by the Fase 4 export and the Fase 5 prompt builder; the bundle's own `window_id` ordinality closed as a positional leak on both sides; the 48h self-agreement reannotation resolved by construction, not instruction; `cta`'s 0/205 sample gap gets a seeded, duration-blind gold-selection procedure instead of a silent pass; `density` moves to Krippendorff's ordinal metric instead of nominal; `evidence_type`'s not-applicable case excluded from its own alpha, conditional on `function` agreement, rather than counted as agreement

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
the `nominal` default every other field in this ontology uses.**
`schema/codebook.md`'s own normative definitions (lines 642-686) make
this a censored count, not an equal-interval scale: `0` = no new
concept, `1` = exactly one new concept, `2` = "two or more distinct new
concepts" - an open-ended ceiling bucket that absorbs 2, 3, 4, or more
concepts identically. A nominal metric would score a 0-vs-2 disagreement
identically to a 0-vs-1 disagreement, discarding the ordering the
codebook itself asserts; an `interval` metric would instead treat the
1-to-2 gap as numerically equal to the 0-to-1 gap, which the
ceiling-bucket definition of `2` makes false. Krippendorff's `ordinal`
metric derives inter-category distance from the observed marginal
distribution's cumulative frequencies rather than assuming a fixed
numeric gap, which is the correct fit for an ordered-but-unequally-spaced
scale. Implementation consequence: the `krippendorff` PyPI package
exposes `level_of_measurement='ordinal'` directly; `simpledorff` (the
plan's other named option, line 475) exposes no such parameter.

**License checked before adoption, not assumed - and it is not the same
class of license every other dependency this project has adopted
carries.** `krippendorff` (PyPI, `pln-fing-udelar/fast-krippendorff`) is
**GPL-3.0** - confirmed against the package's own `LICENSE.txt` (full GPLv3
text) and its PyPI trove classifier ("License :: OSI Approved :: GNU
General Public License v3 (GPLv3)"), not against a secondary source.
`_docs/blueprint.md` line 68 named `simpledorff`/`krippendorff`/
`nltk.metrics.agreement` in one enumeration with no license attributed to
any of the three - the same gap the Pydantic entry closed for `pydantic`
this same revision round (`_docs/blueprint.md` line 59). Own line added
to `_docs/blueprint.md`'s Peça 5 section for `krippendorff` specifically
(the one this alínea actually decides to use), naming GPL-3.0 - see that
file's diff. **This does not block adoption**: `DECISOES.md` item 3 fixes
the project's current scope as non-commercial, and `krippendorff` is only
ever an internal measurement dependency during Fase 5B - never conveyed
or distributed as part of a product, the condition under which GPL-3.0's
copyleft terms actually engage. It **is** a real, load-bearing difference
from every other dependency this project has adopted so far (all
MIT/BSD-2-Clause/Apache-2.0/Unlicense per `_docs/blueprint.md`), and must
be re-examined the day `roteiros-engine`'s own pipeline code - not the
generated video scripts, which are not a derivative work of
`krippendorff` under any reading - is ever distributed or open-sourced,
not only the day the project's commercial-use decision changes.
**Decision: the Fase 5 validation module uses the `krippendorff` package
specifically for `density`'s α**, whichever library it uses (or doesn't)
for the other four nominal fields.

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
fires. Krippendorff's alpha already has a native way to handle a value a
coder does not provide: a unit with fewer than two valid values for a
field contributes nothing to that field's reliability estimate and is
dropped - exactly what happens if `evidence_type` is passed to
`krippendorff.alpha()` as `None`/missing whenever `function != 'evidence'`
for that annotator, instead of coding it as its own category.
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
named for Fase 4's own export step); wiring `krippendorff`'s `ordinal`
level for `density` and missing-data exclusion for `evidence_type` into
the Fase 5 validation module (`src/valida.py`, not yet written); running
the 30-video CTA heuristic scan and the seeded gold-video draw from (c),
and recording the real result (video ids, durations) in a future
`decisions.md` entry once it is actually run; and updating
`schema/portoes.json`'s `fase4-self-agreement-alpha` and
`fase5-model-human-agreement-alpha` notes plus
`_docs/plano_implementacao.md`'s Fase 4/5A/5B text to point here once the
mechanism is real, per this file's own precedence rule over the plan.
