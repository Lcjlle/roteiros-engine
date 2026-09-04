# Codebook - Authorial ontology (`schema/ontologia.v1.json`)

Bilingual codebook for the annotation ontology derived from `@MackExplains7`
(`DECISOES.md#4`), applied at the `window` unit
(`corpus/<canal>/windows/<video_id>.json`).

**Precedence.** This codebook is bilingual by convention, not by authority.
Every Definition, example, and tie-breaker below is stated in **English**,
which is the normative text a human annotator or an LLM annotator prompt must
follow. Each value also carries a PT-BR gloss marked `<!-- não normativo -->`,
included only so the project owner can think in their working language.
**Where the PT-BR gloss and the English definition disagree, the English
definition governs.** Stored identifiers (field names, enum values) are
always the English tokens in `schema/ontologia.v1.json` - the PT-BR gloss is
never a stored value.

**Example citation format.** Every positive and negative example below is a
verbatim quote of a real window's `text` field plus its `window_id`, never a
paraphrase (`_docs/decisions.md#16d`) - open
`corpus/mackexplains7/windows/<video_id>.json` (or, for the two `function=cta`
examples, the named video's own window file elsewhere in the same corpus) to
verify any citation against the real corpus. No negative example needed a
constructed near-miss; a real corpus window served every case.

## Fields

| field | type | required | values / range |
|---|---|---|---|
| `function` | categorical | yes | `hook`, `promise`, `context`, `escalation`, `mechanism`, `evidence`, `objection`, `resolution`, `implication`, `cta` |
| `loop` | categorical | yes | `opens`, `closes`, `holds`, `none` |
| `evidence_type` | categorical | only when `function == 'evidence'` | `study`, `statistic`, `case`, `analogy`, `authority` |
| `scale` | categorical | yes | `individual`, `human`, `planetary`, `abstract` |
| `density` | integer | yes | `0`-`2` |

## Field evaluation (six tests)

Each of the five candidate fields (`function`, `loop`, `evidence_type`, `scale`,
`density`) is evaluated in writing against the plan's six tests
(`_docs/plano_implementacao.md` lines 336-344): observable, closed, mutually
exclusive, aggregable, decidable in window, transferable between channels.
Evidence is drawn from hand-classifying all 205 coverage-test windows
(`corpus/mackexplains7/fase3_coverage.md`, `lkLwp9o7Djk` + `5unhHRFkC7I`,
`_docs/decisions.md#16c`) and from the 20-window transfer test against
`@Zenn0009` (`corpus/zenn0009/fase3_transfer_notes.md`, `_docs/decisions.md#16b`).

### `function`

1. **Observable** - yes. A window's narrative role can be read off its 2-4
   sentences plus limited prior context, without outside knowledge of the
   video's subject matter.
2. **Closed** - yes, a fixed enumerated list.
3. **Mutually exclusive** - the starting 11-value proposal included
   `transition` ("apenas move de um tópico a outro"), which the Fase 2 human
   sample already flagged as co-occurring with a substantive function in 4 of
   5 "two functions" windows (`_docs/decisions.md#17`: `lkLwp9o7Djk:j0027`,
   `j0054`, `j0064`, `5unhHRFkC7I:j0054`, `j0075`). **This is the mandated
   `transition` question, answered here with corpus evidence.** Full
   hand-classification of all 205 coverage-test windows found **zero**
   windows whose best-fit function was a bare topic pivot with no other
   payload: every boundary window (content and topic-shift sharing space) was
   better captured by an existing value - `hook` when it poses a new open
   question (`5unhHRFkC7I:j0055`, "But what about other animals? ... Let's
   start with cats. They deserve the floor."), `promise` when it names the
   upcoming subject (`lkLwp9o7Djk:j0021`, "Egypt is where things take a
   slightly more interesting turn, and I say interesting like someone who
   has just found out that ancient Egyptians were arguably more progressive
   about mental health than a large portion of the modern world."), or by
   the boundary tie-breaker below when a closer and an opener genuinely
   share a window (confirmed cases audited in
   `corpus/mackexplains7/fase3_coverage.md`, `_docs/decisions.md#20`;
   `5unhHRFkC7I:j0054`, on inspection below, turns out not to need it at
   all). **Decision: `transition` is removed from `function`'s
   value set (11 -> 10 values, option 3 of the three the task named).** This is
   the outcome backed by direct evidence rather than an a priori preference for
   simplicity: keeping `transition` bought no coverage `hook`/`promise` did not
   already provide, while creating the exact test-3 collisions the Fase 2 gate
   measured.
   A window may contain content that concludes an established topic and a
   trailing pivot that opens a new one. Detecting the pivot never requires
   the next window, and it never requires more context than the annotator
   actually receives when applying this rule (`_docs/decisions.md#20`,
   superseding `#19`'s "prior windows in the same video" - a full-video read
   no real Fase 5 annotator gets): a trailing pivot exists when the window's
   final sentence(s) name or introduce a specific subject, claim, or event
   that is not otherwise developed in this window or in the context
   previously provided in this call - a bare transitional phrase with no new
   specific content ("Let's go further," "there's one more thing") is not a
   pivot. When a window contains such a pivot, code `function` for the
   content the window concludes, never for the content it only opens or
   previews - regardless of relative word count, sentence count, or which
   half reads as more salient. A window with no internal pivot is coded
   normally, from its own content as a whole. **Context budget: three prior
   windows, same video, text only, no labels** - the same shape
   `_docs/plano_implementacao.md` line 478 (Fase 5A) hands the real
   annotator, so "the context previously provided in this call" above is
   audited, in this codebook and in `corpus/mackexplains7/fase3_coverage.md`,
   against those three prior windows, never the whole video; changing the
   budget changes which windows are pivots (`_docs/decisions.md#20`).
   **"Developed before" is semantic, never lexical:** the context previously
   provided has to already support the same claim, event, or subject, not
   merely share a word with it - a passing mention, a use as a comparison
   baseline, or the same word applied to a different referent do not
   constitute development; term repetition decides neither for nor against.
   Worked negative example, the case that teaches the trap rather than just
   the rule: `lkLwp9o7Djk:j0076` closes "Unevenly. With enormous suffering in
   the gaps. But the direction was right." - qualifying the Enlightenment-era
   reform account just established (`j0070`-`j0075`) - and opens "And then
   the 19th century arrived and built enormous asylums and overcrowded them
   to catastrophic levels." A bare lexical check finds "asylums" already
   said twice in the three prior windows (`j0074`, "the York Retreat's
   outcomes were dramatically better than contemporary asylums"; `j0071`,
   "...ordered the chains removed from patients at the Bicetre Asylum in
   Paris in 1793") and could wrongly call this "already developed, not a
   pivot." Read semantically instead: `j0074` uses "asylums" only as a
   comparison baseline for the York Retreat's outcomes; `j0071` names one
   specific asylum inside the reform story. Neither develops `j0076`'s
   actual claim - mass-scale 19th-century overcrowding to catastrophic
   conditions - which first appears at `j0076` itself and is developed only
   afterward, at `j0077`-`j0078`. `j0076` is a genuine pivot under the
   three-window budget; the word recurring is not what "developed" means.
   Code the closing clause, which qualifies the prior claim of steady
   progress -> `objection`. Two more positive examples, closing coded:
   `lkLwp9o7Djk:j0027`'s opening pivot ("Now we cross the Mediterranean, and
   we have to talk about ancient Greece...suffering.") names a specific new
   subject - ancient Greece - not developed in this window or in
   `j0024`-`j0026`, so the window is coded for what it concludes: the
   closing clause ("Pointing at the right building, wrong floor.")
   generalizes `j0026`'s near-miss theory about Egypt into a broader
   consequence, without being tied to one posed question -> `implication`.
   `lkLwp9o7Djk:j0064`'s opening pivot ("Then comes the early modern
   period...better.") names a new era not developed in `j0061`-`j0063`, so
   the window is coded for its closing clause ("The people of a small
   Belgian town...doing it."), which generalizes the Gilles/Belgium case
   just established -> `implication`. **`5unhHRFkC7I:j0075` is a pivot under
   the three-window budget, and stays `implication` either way.** Its
   trailing sentence, "Let's come back to that couch," names "that couch" -
   the video's own opening scenario - but the only prior windows that
   develop it are `5unhHRFkC7I:j0002` and `j0039`, 73 and 36 windows
   earlier, both far outside the three-window budget this codebook is
   audited against; nothing in `j0072`-`j0074` develops it, so it is a
   genuine pivot. The window is still coded for what it concludes: the
   closing clause generalizes `j0073`-`j0074`'s claim about empathy crossing
   species boundaries into a broader statement about which animals read
   human emotion -> `implication` - the same label a non-pivot reading would
   have given, because the closing content already dominates the window
   either way; a wider, whole-video budget can resolve a pivot the
   three-window budget cannot, never the reverse. Not every candidate is a
   pivot: `5unhHRFkC7I:j0054` was cited alongside these in earlier drafts
   but does not actually qualify - its trailing sentences ("Now, dogs are an
   obvious case. They've been shaped by thousands of years of selective
   pressure specifically around human interaction.") do not name or
   introduce anything new; `5unhHRFkC7I:j0055` opens on "other animals"
   (cats/horses/elephants), which neither sentence names or previews, so the
   whole window stays on one topic (dogs) with no pivot to detect. Read as a
   single unit against `implication`'s own definition, it is a direct match
   without any tie-break -> `implication`, unchanged, but for the correct
   reason, not the boundary tie-breaker earlier drafts cited. The full,
   audited list of confirmed boundary windows for the 205-window coverage
   worksheet, measured under this budget, lives in
   `corpus/mackexplains7/fase3_coverage.md` and `fase3_gate.json`, not
   hardcoded here - narrowing the context budget can only ever add pivots,
   never remove them, so that list is a floor, not a ceiling, re-audited
   whenever the budget or the corpus changes.
4. **Aggregable** - yes; counting/averaging the `function` distribution per
   video is exactly the profile signal the project wants (hook/resolution
   ratio, evidence density, etc.).
5. **Decidable in window** - yes, with the boundary tie-breaker above for the
   handful of straddling cases.
6. **Transferable** - confirmed. The `@Zenn0009` transfer test (20 windows,
   two videos in a different subject domain - social-psychology and
   medical-history explainers, vs. `@MackExplains7`'s mental-illness history
   and dog cognition) found zero windows requiring a function value outside
   the 10-value set, including real instances of `objection` (correcting the
   "cowardice" assumption, `Dw2Pifv1JrM:j0014`) and `resolution` (closing the
   anesthesia-pain loop, `Dw2Pifv1JrM:j0038`) matching patterns first observed
   in `@MackExplains7`.

**Outcome: accept with adjustment - cut `transition`.**

### `loop`

1. **Observable** - yes, generally, though it requires holding in mind
   whether an earlier window in the same video left something open; the
   plan's own "decidable in window + previous context" allowance covers this.
2. **Closed** - yes, 4 values.
3. **Mutually exclusive** - a real collision exists when a single window both
   poses and answers a question (`5unhHRFkC7I:j0024`). Resolved by an explicit
   tie-breaker (code by the state at the window's end - `closes`, since
   nothing is left dangling for the audience), not by adding a field or
   cutting a value, because it does not recur nearly as pervasively as
   `transition` did for `function`, and a single rule fully resolves it.
4. **Aggregable** - yes; counting opens/closes/holds/none per video profiles a
   channel's pacing (front-loaded hooks vs. slow-burn holds).
5. **Decidable in window** - yes, with the tie-breaker above.
6. **Transferable** - confirmed by the transfer test: `Dw2Pifv1JrM:j0002`
   opens ("So, what did that actually feel like?") and `j0038` closes it - the
   same opens/closes pattern already seen in `@MackExplains7`.

**Outcome: accept, with the opens/closes tie-breaker recorded.**

### `evidence_type`

1. **Observable** - yes.
2. **Closed** - yes, 5 values, conditional on `function == 'evidence'`.
3. **Mutually exclusive** - two real collisions found and resolved: `study`
   vs. `statistic` (a window can both name a study and state its result
   number - resolved by "whichever is the window's point: the study's
   existence/design, or the quantified finding"); `case` vs. `authority` (a
   named person's documented act vs. their cited argument - resolved by "who
   said it" vs. "what was done"). Both resolved by tie-breakers, no value cut.
4. **Aggregable** - yes; the evidence-type mix per video/channel is a real
   style signal (a channel leaning on `authority` reads differently from one
   leaning on `statistic`).
5. **Decidable in window** - yes.
6. **Transferable** - confirmed: the transfer sample independently exercised
   `study`/`statistic` (`Dw2Pifv1JrM:j0035`, Semmelweis) and `case`
   (`Dw2Pifv1JrM:j0027`, Liston) without needing a new sub-type.

**Outcome: accept as-is** (no cuts; two tie-breakers recorded).

### `scale`

1. **Observable** - mostly yes, with one genuine friction documented below.
2. **Closed** - yes.
3. **Mutually exclusive** - a real collision between `human` and `abstract`
   on windows that generalize about "societies"/"humanity" in an abstract
   voice, resolved by a grammatical-subject test: a concrete group/institution
   is `human` even in a generalizing sentence; a bare concept/question is
   `abstract`.
4. **Aggregable** - yes.
5. **Decidable in window** - yes, with the test above.
6. **Transferable - two real findings, not idiosyncratic to one video.**
   - The original value set (`individual, human, planetary, cosmic,
     abstract`) reads `human` narrowly ("people/humanity") in the plan's
     gloss, but `5unhHRFkC7I` (dog/cat/horse/elephant cognition - still
     `@MackExplains7`) is full of claims about an animal *population* as a
     group (`5unhHRFkC7I:j0026`, "a dog's nose contains roughly 300 million
     receptors") that are neither about one individual animal, nor about
     humans, nor about a claim spanning multiple species/the whole biosphere
     (which is what `planetary` already covers, e.g. `5unhHRFkC7I:j0019`,
     "across virtually all mammals... birds... fish"). **Decision: `human`'s
     definition is broadened (token unchanged) to "a social or
     population-level collective - human or animal, a society, era,
     institution, or species treated as a group" rather than literally
     "human beings only".** This is a genuine adjustment driven by the
     coverage test, not a cosmetic rename: without it, every population-level
     claim about a single animal species in this corpus (dogs, cats, horses,
     elephants, each covered individually) would have no home among the other
     values.
   - **`cosmic` is cut.** Two lines of evidence. First, all 205 windows
     hand-classified across the two coverage-test videos
     (`_docs/decisions.md#16c`) never once needed `cosmic` for `scale`.
     Second, a full-corpus lexical scan
     (`corpus/mackexplains7/windows/*.json`, all 30 videos, **3,103**
     windows) for the four terms `universe`/`cosmos`/`galaxy`(`galaxies`)/
     `space` found **32 hits total** - `universe` **7**, `cosmos` 0, `galaxy`/
     `galaxies` 0, `space` 25 - every one of them read individually, none of
     literal cosmic scope. The 7 `universe` hits are all figurative/idiomatic
     (`5unhHRFkC7I:j0086` "the hardest thing in the universe to verify",
     `pJYm-8WQbEE:j0000` "the most important being in the universe")
     describing individual- or human-scale content. The 25 `space` hits are
     unambiguously non-astronomical ("personal space", "space for
     correction", "private space", "how space is used in communication"),
     with one exception - `z1StpnRL4k4:j0031`, "the earliest ancestors of
     modern military and space rocketry" - whose claim is scoped to
     technological history, not cosmic scale. Outside this four-term scan,
     the word `cosmic` itself occurs once in the corpus (`th-0rmRYBSg:j0002`,
     "It wasn't some cosmic roll of the dice") - also idiomatic/negated, and
     consistent with the same conclusion. Per the codebook's own rule (two
     real positive examples required for every value that survives into v1,
     with no constructed-example escape hatch for positive examples - only
     for negatives), `cosmic` cannot be honestly retained: it never fires
     once in this channel's real output, and the idiomatic "universe" hits
     are a live annotator trap that would tempt a false-positive `cosmic`
     code on ordinary individual-scale hyperbole, degrading exactly the
     inter-annotator agreement Fase 5's gate measures. **Decision: `cosmic`
     is cut from `scale`** (5 -> 4 values), left available to be reintroduced
     in a future `v2` if a channel that actually covers astronomy/physics
     enters the corpus, with real examples to anchor it.

**Outcome: accept with adjustment - redefine `human`, cut `cosmic`.**

### `density`

1. **Observable** - mostly yes; requires tracking what the video has already
   introduced (the same "decidable in window + previous context" latitude the
   plan allows).
2. **Closed** - yes, a bounded integer 0-2.
3. **Mutually exclusive** - trivially yes: it is a count, not a category, so
   no two values can both be true of the same window by construction.
4. **Aggregable** - yes; sum/average density per video is a direct measure of
   information pacing, exactly the kind of channel-level metric the project
   wants.
5. **Decidable in window** - yes, with the same prior-context allowance as
   observability above.
6. **Transferable** - not exercised by the transfer test (the transfer AC's
   structural-gap check covers `function`/`scale`/`loop`, not `density`), but
   counting new concepts is not `@MackExplains7`-specific.

**Outcome: accept as-is.**

### Field count

Five fields survive: `function`, `loop`, `evidence_type`, `scale`, `density` -
within the plan's stated 5-7 range (`_docs/plano_implementacao.md` line 374).
No field was cut entirely; two values were cut (`function`'s `transition`,
`scale`'s `cosmic`) and one value's definition was broadened (`scale`'s
`human`), all logged above with the evidence that drove each change.

## `function`

#### `hook`

**Definition (EN, normative).** Opens an information gap or poses an unresolved question/scenario without yet delivering an answer, a topic name, or a payoff.

**Positive examples.**
- `lkLwp9o7Djk:j0000`: "Imagine waking up one morning hearing voices, voices that tell you things, important things, maybe warnings, maybe prophecies, maybe just pure chaos at 3 a.m. while everyone else is asleep. Now imagine this is happening to you in ancient Egypt 3,000 years ago."
- `5unhHRFkC7I:j0083`: "It is genuinely, profoundly limited when it comes to answering the question underneath all of this. What does it feel like from the inside?"

**Negative example.** `5unhHRFkC7I:j0024`: "Can they detect those same signals in others? Can they read the emotional state of a being that isn't them? The answer, it turns out, is yes. Conclusively, measurably, scientifically, yes." - not `hook`: the question is answered inside the same window, so nothing is left open for the audience - see `resolution`.

**Tie-breaker.** Against `promise`: if the sentence withholds the subject and only creates curiosity/tension, code `hook`; if it names or previews the specific subject matter that follows, code `promise`.

<!-- não normativo --> **Glosa PT-BR.** Abre uma lacuna de informação sem entregar nada ainda - o gancho clássico de vídeo de YouTube.

#### `promise`

**Definition (EN, normative).** Declares or previews what the video/segment will cover next, naming the upcoming subject or claim rather than only creating suspense.

**Positive examples.**
- `lkLwp9o7Djk:j0004`: "Everything. Let's start with prehistoric humans because yes, we actually have evidence of how they dealt with mental illness, and it is immediately insane."
- `5unhHRFkC7I:j0008`: "It touches evolutionary biology, neuroscience, animal cognition, and the 15,000-year-old experiment that changed both humans and dogs forever. So let's actually answer it. Properly. With science."

**Negative example.** `lkLwp9o7Djk:j0000`: "Imagine waking up one morning hearing voices, voices that tell you things, important things, maybe warnings, maybe prophecies, maybe just pure chaos at 3 a.m. while everyone else is asleep. Now imagine this is happening to you in ancient Egypt 3,000 years ago." - not `promise`: it withholds the subject entirely - no topic or claim is named, only a scenario to imagine. See `hook`.

**Tie-breaker.** Against `hook` (mirrored above): naming the subject -> `promise`; withholding it -> `hook`.

<!-- não normativo --> **Glosa PT-BR.** Declara o que o vídeo vai entregar a seguir, nomeando o assunto - não apenas cria expectativa.

#### `context`

**Definition (EN, normative).** Supplies background or framework information needed to understand what follows, without yet explaining a causal "how/why" or making an evaluative claim.

**Positive examples.**
- `lkLwp9o7Djk:j0028`: "The Greeks had two competing frameworks for mental illness, and they were at war with each other for centuries. Framework one, the divine explanation."
- `5unhHRFkC7I:j0011`: "But science, bless its cautious little heart, needed roughly a century of careful observation, controlled studies, and a lot of heated conference debates before it was willing to commit that to paper. For most of the 20th century, the dominant view in biology was something called behaviorism."

**Negative example.** `lkLwp9o7Djk:j0029`: "Mental illness was sent by the gods, specifically as punishment or as a form of divine communication. This was actually considered by some Greeks to be almost a privilege." - not `context`: it explains the causal logic behind the belief (why madness could be a privilege), which crosses into `mechanism`.

**Tie-breaker.** Against `mechanism`: does the window answer how/why X happens or worked? If yes, `mechanism`. If it only states background facts/frameworks without causal explanation, `context`.

<!-- não normativo --> **Glosa PT-BR.** Traz a informação de fundo necessária antes do argumento, sem ainda explicar o porquê.

#### `escalation`

**Definition (EN, normative).** Raises the stakes, strangeness, or urgency of the already-established topic, without correcting a prior claim or introducing a new one.

**Positive examples.**
- `lkLwp9o7Djk:j0010`: "Done. Next patient. And here's the thing that really messes with you when you sit with it. Trepanation actually survived for thousands of years across completely unconnected civilizations."
- `5unhHRFkC7I:j0041`: "This is the part where you should probably sit down, because it gets genuinely strange. For somewhere between 15,000 and 40,000 years, depending on which archaeological evidence you trust, dogs have lived alongside humans."

**Negative example.** `lkLwp9o7Djk:j0042`: "However, Rome also gives us some of the darker chapters in ancient mental health history, because wealthy Romans who had inconvenient relatives, relatives whose madness might embarrass the family, endanger the inheritance, or just make dinner parties awkward, could have those relatives legally declared incapable and confined." - not `escalation`: the "however" signals a correction/complication of the preceding positive claim about Roman medicine (Galen), not just an intensification of the same thread - see `objection`.

**Tie-breaker.** Against `objection`: does the sentence correct or complicate a claim already made (signaled by "but/however/actually")? -> `objection`. Does it just intensify the same established thread without contradicting anything? -> `escalation`.

<!-- não normativo --> **Glosa PT-BR.** Aumenta a aposta, a estranheza ou a urgência do que já está estabelecido, sem corrigir nada.

#### `mechanism`

**Definition (EN, normative).** Explains how or why something works or worked - a causal or procedural chain, stated as a general claim rather than a single dated instance.

**Positive examples.**
- `lkLwp9o7Djk:j0007`: "This is called trepanation, and it is exactly as metal as it sounds. The working theory? They were letting the evil spirits out, literally drilling an exit door for the demon living in someone's skull."
- `5unhHRFkC7I:j0021`: "It is an ancient biological tool, hundreds of millions of years old, that evolution kept because it works. Fear keeps you away from predators."

**Negative example.** `lkLwp9o7Djk:j0028`: "The Greeks had two competing frameworks for mental illness, and they were at war with each other for centuries. Framework one, the divine explanation." - not `mechanism`: it only names the two competing frameworks without yet explaining how either is believed to work - see `context`.

**Tie-breaker.** Against `evidence`: is this a specific named/dated/quantified instance? -> `evidence`. Is it a general causal claim/principle without a specific named instance? -> `mechanism`.

<!-- não normativo --> **Glosa PT-BR.** Explica como ou por que algo funcionava - uma cadeia causal ou procedimental.

#### `evidence`

**Definition (EN, normative).** Presents a specific supporting instance for a claim already on the table - a named study, a statistic, a concrete case, an illustrative comparison, or a cited authority.

**Positive examples.**
- `5unhHRFkC7I:j0035`: "A 2022 study published in the journal PLOS One was specifically designed to test this. Researchers trained dogs to discriminate between breath and sweat samples collected from humans in high-stress states versus calm, relaxed states."
- `lkLwp9o7Djk:j0053`: "The first psychiatric hospitals in history were built in the Islamic world. Baghdad had one in the 8th century. Cairo had one in the 9th century. These were not prisons."

**Negative example.** `lkLwp9o7Djk:j0009`: "Acting erratic and strange? Demon. Obviously. Demon, drill the hole, boom." - not `evidence`: it restates the already-established causal belief rhythmically, without adding a new named instance or data point - see `mechanism`.

**Tie-breaker.** Against `mechanism` (mirrored above): a specific named/dated/quantified instance -> `evidence`; a general causal claim without one -> `mechanism`. Required companion field when this value is used: `evidence_type`.

<!-- não normativo --> **Glosa PT-BR.** Apresenta dado, estudo ou caso concreto que sustenta uma afirmação já feita.

#### `objection`

**Definition (EN, normative).** Pushes back against a claim, assumption, or framing already established in the video - including the video's own prior framing - as a correction or a stated limitation.

**Positive examples.**
- `lkLwp9o7Djk:j0019`: "They weren't monsters. They were working with the best explanatory framework available to them, and their diagnostic tablets incredibly detailed. They described symptoms we would today recognize as schizophrenia, epilepsy, depression, mania."
- `5unhHRFkC7I:j0013`: "It was executing a hardwired behavioral response pattern associated with social bonding scenarios. Very clinical. Very tidy. Very much how someone who has never owned a dog would describe a dog."

**Negative example.** `lkLwp9o7Djk:j0010`: "Done. Next patient. And here's the thing that really messes with you when you sit with it. Trepanation actually survived for thousands of years across completely unconnected civilizations." - not `objection`: nothing here contradicts or limits a prior claim; it only raises the strangeness of an idea already accepted - see `escalation`.

**Tie-breaker.** Against `escalation` (mirrored above): corrects/complicates a prior claim -> `objection`; merely intensifies the same thread -> `escalation`. Against `evidence` on the same window: when a window both supplies a supporting fact and immediately complicates/contrasts it (e.g. `lkLwp9o7Djk:j0054`), code by whichever occupies the majority of the window's sentences; a tie resolves to `objection`, since the objection is what changes the reader's evaluation of the preceding claim.

<!-- não normativo --> **Glosa PT-BR.** Levanta contra-argumento ou limitação contra algo já afirmado no vídeo.

#### `resolution`

**Definition (EN, normative).** Directly answers a question or closes an information gap the video explicitly posed earlier (including earlier in the same window).

**Positive examples.**
- `lkLwp9o7Djk:j0096`: "It is found in whether or not you are willing to look at a person who is suffering in a way that makes you uncomfortable and still say, This is a person. This person belongs here."
- `5unhHRFkC7I:j0024`: "Can they detect those same signals in others? Can they read the emotional state of a being that isn't them? The answer, it turns out, is yes. Conclusively, measurably, scientifically, yes."

**Negative example.** `lkLwp9o7Djk:j0037`: "But the principle that mental illness has a physical, biological basis rather than a supernatural one, was so far ahead of its time that most of the Western world wouldn't consistently operate on that assumption again for roughly another 2,000 years." - not `resolution`: there is no specific earlier posed question this answers - it draws a general consequence instead - see `implication`.

**Tie-breaker.** Against `implication`: can you point to the specific earlier hook/question this window answers? -> `resolution`. Is it a general "so what this means is..." without a specific antecedent question? -> `implication`.

<!-- não normativo --> **Glosa PT-BR.** Fecha uma lacuna de informação aberta antes no vídeo.

#### `implication`

**Definition (EN, normative).** Extends established content to a broader consequence, generalization, or meaning, without being tied to one specific earlier posed question.

**Positive examples.**
- `lkLwp9o7Djk:j0084`: "The most humane responses to mental illness throughout history almost never came from the most sophisticated societies."
- `5unhHRFkC7I:j0103`: "We share this planet with creatures who have spent millions of years developing the capacity to feel, and thousands of years developing the capacity to feel for us, specifically. That is not a small thing."

**Negative example.** `lkLwp9o7Djk:j0095`: "It is found in the same place it was found in Gill in the 13th century, and in Avicenna's writing in 1025, and in William Tewkes' retreat in 1796." - not `implication`: it answers the specific question the video posed two windows earlier ("what do we believe the mentally ill deserve?", `lkLwp9o7Djk:j0093`), not a free-standing generalization - see `resolution`.

**Tie-breaker.** Against `resolution` (mirrored above): tied to a specific antecedent question -> `resolution`; a free-standing generalization -> `implication`.

<!-- não normativo --> **Glosa PT-BR.** Estende para consequências ou significados maiores, sem responder uma pergunta específica.

#### `cta`

**Definition (EN, normative).** Directly addresses the viewer with an imperative to engage with the channel or video itself (comment, subscribe, watch another video) - not a narrative imperative addressed to an imagined scenario.

**Positive examples.**
- `Qgz_k2JQ3UY:j0113`: "Let me know in the comments. Until then, take care of yourselves, and I'll see you soon."
- `yKqe_ey3QOs:j0101`: "Some things, genuinely, never change. And what about you? Would you go back in time and live completely naked? Let me know in the comments."

**Negative example.** `lkLwp9o7Djk:j0000`: "Imagine waking up one morning hearing voices, voices that tell you things, important things, maybe warnings, maybe prophecies, maybe just pure chaos at 3 a.m. while everyone else is asleep. Now imagine this is happening to you in ancient Egypt 3,000 years ago." - not `cta`: "imagine" is a narrative device building the hook's hypothetical scenario, not a request to engage with the video or channel.

**Tie-breaker.** Against `hook`: does the imperative ask the viewer to do something with the platform (comment/subscribe/watch next)? -> `cta`. Does it ask the viewer to imagine/consider something inside the story? -> `hook`.

<!-- não normativo --> **Glosa PT-BR.** Pede uma ação ao espectador em relação ao próprio vídeo/canal (comentar, se inscrever) - não uma instrução narrativa.

## `loop`

#### `opens`

**Definition (EN, normative).** Poses a genuine question or unresolved anticipation that is not yet answered by the end of this window.

**Positive examples.**
- `lkLwp9o7Djk:j0093`: "The question that every generation has faced, and that we face right now, is not only, what do we know about mental illness? It is, what do we believe the mentally ill deserve?"
- `5unhHRFkC7I:j0083`: "It is genuinely, profoundly limited when it comes to answering the question underneath all of this. What does it feel like from the inside?"

**Negative example.** `5unhHRFkC7I:j0024`: "Can they detect those same signals in others? Can they read the emotional state of a being that isn't them? The answer, it turns out, is yes. Conclusively, measurably, scientifically, yes." - not `opens`: the question is answered inside the very same window, so nothing is left dangling for the audience - see `closes`.

**Tie-breaker.** Against `closes`: if a window poses and answers a question within itself, code by the net state at the window's end - `closes`, since no gap survives the window, even though it was posed mid-window.

<!-- não normativo --> **Glosa PT-BR.** Abre uma lacuna que o vídeo ainda não respondeu.

#### `closes`

**Definition (EN, normative).** Answers a question or resolves an anticipation that was left open by an earlier window (or by the same window, per the `opens` tie-breaker).

**Positive examples.**
- `lkLwp9o7Djk:j0096`: "It is found in whether or not you are willing to look at a person who is suffering in a way that makes you uncomfortable and still say, This is a person. This person belongs here."
- `5unhHRFkC7I:j0024`: "Can they detect those same signals in others? Can they read the emotional state of a being that isn't them? The answer, it turns out, is yes. Conclusively, measurably, scientifically, yes."

**Negative example.** `lkLwp9o7Djk:j0006`: "Some of these skulls even show signs of bone regrowth around the edges, which means the patient survived the procedure. They lived with a hole in their head, intentionally put there." - not `closes`: it does not resolve why they did this - that answer only arrives in `j0007` - see `holds`.

**Tie-breaker.** Against `holds`: does the window supply the actual answer to the open question? -> `closes`. Does it add detail/tension to the same still-open question without answering it? -> `holds`.

<!-- não normativo --> **Glosa PT-BR.** Responde uma pergunta ou fecha uma expectativa aberta antes.

#### `holds`

**Definition (EN, normative).** Maintains an already-open loop's tension by adding development, without closing it or opening an unrelated new one.

**Positive examples.**
- `lkLwp9o7Djk:j0006`: "Some of these skulls even show signs of bone regrowth around the edges, which means the patient survived the procedure. They lived with a hole in their head, intentionally put there."
- `5unhHRFkC7I:j0085`: "Or is it a very sophisticated pattern-matching system? Stress signals detected, approach behavior executed, reinforcement received, with nothing we'd call genuine experience behind it. Honestly? We don't know."

**Negative example.** `lkLwp9o7Djk:j0043`: "the Romans had a legal category called Furiosus, basically madman, and a person declared Furiosus lost all legal rights. They could be locked up. Their property was managed by a guardian." - not `holds`: there is no open loop this connects to - it is plain exposition - see `none`.

**Tie-breaker.** Against `none`: is there an identifiable open question this window is deepening without answering? -> `holds`. Is the window free-standing exposition with no active loop? -> `none`.

<!-- não normativo --> **Glosa PT-BR.** Mantém a tensão de uma lacuna já aberta, sem fechá-la nem abrir outra.

#### `none`

**Definition (EN, normative).** Neither opens, closes, nor holds any loop-relevant tension - plain informational content.

**Positive examples.**
- `lkLwp9o7Djk:j0043`: "the Romans had a legal category called Furiosus, basically madman, and a person declared Furiosus lost all legal rights. They could be locked up. Their property was managed by a guardian."
- `5unhHRFkC7I:j0032`: "It is chemically different. Your cortisol levels rise. Your adrenaline shifts. Your heart rate changes."

**Negative example.** `lkLwp9o7Djk:j0007`: "This is called trepanation, and it is exactly as metal as it sounds. The working theory? They were letting the evil spirits out, literally drilling an exit door for the demon living in someone's skull." - not `none`: it looks like plain exposition, but it actually closes the loop opened by the earlier skull-mystery windows (`j0004`-`j0006`) by naming and explaining the practice - see `closes`.

**Tie-breaker.** Before coding `none`, check whether an earlier window left a question open that this window's content actually answers or develops - if so, code `closes`/`holds`, not `none`.

<!-- não normativo --> **Glosa PT-BR.** Não abre, não fecha e não mantém nenhuma tensão narrativa - conteúdo puramente informativo.

## `evidence_type`

Applicable only on windows where `function == 'evidence'` (`schema/ontologia.v1.json`'s `condition`).

#### `study`

**Definition (EN, normative).** Cites a specific named research study or research team's methodology as the support for a claim.

**Positive examples.**
- `5unhHRFkC7I:j0035`: "A 2022 study published in the journal PLOS One was specifically designed to test this. Researchers trained dogs to discriminate between breath and sweat samples collected from humans in high-stress states versus calm, relaxed states."
- `5unhHRFkC7I:j0059`: "A study from Oakland University found that cats behave measurably differently around owners who are smiling versus owners who are frowning. Around smiling owners, they were significantly more likely to approach, to purr, to engage in affiliative behaviors like rubbing."

**Negative example.** `5unhHRFkC7I:j0036`: "No visual cues. No behavioral information. Just the chemical signal on a cotton swab. The dogs identified the stressed samples correctly, with an accuracy of over 93%—93%—from a cotton swab." - not `study`: the study itself was already introduced in the previous window - this window's point is the number, so `statistic`.

**Tie-breaker.** Against `statistic`: is the window's point the study's existence/design (who ran it, how)? -> `study`. Is the window's point a specific quantified finding, even if a study was named as its source? -> `statistic`.

<!-- não normativo --> **Glosa PT-BR.** Cita um estudo de pesquisa nomeado como sustentação da afirmação.

#### `statistic`

**Definition (EN, normative).** Presents a specific quantified number or percentage as the core evidentiary content.

**Positive examples.**
- `5unhHRFkC7I:j0036`: "No visual cues. No behavioral information. Just the chemical signal on a cotton swab. The dogs identified the stressed samples correctly, with an accuracy of over 93%—93%—from a cotton swab."
- `lkLwp9o7Djk:j0062`: "It still runs today. Gilles, Belgium, has an unbroken tradition of community-based mental health care that is over 700 years old, predating professional psychiatry by half a millennium. Seven. Hundred."

**Negative example.** `lkLwp9o7Djk:j0053`: "The first psychiatric hospitals in history were built in the Islamic world. Baghdad had one in the 8th century. Cairo had one in the 9th century. These were not prisons." - not `statistic`: the dates identify specific historical instances, not a quantified magnitude the claim rests on - see `case`.

**Tie-breaker.** Against `study` (mirrored above).

<!-- não normativo --> **Glosa PT-BR.** Apresenta um número ou percentual específico como o núcleo da evidência.

#### `case`

**Definition (EN, normative).** Presents a specific concrete historical or real example, incident, or artifact as the supporting instance - not a formal contemporary research study and not a hypothetical comparison.

**Positive examples.**
- `lkLwp9o7Djk:j0053`: "The first psychiatric hospitals in history were built in the Islamic world. Baghdad had one in the 8th century. Cairo had one in the 9th century. These were not prisons."
- `lkLwp9o7Djk:j0060`: "The town of Giel in Belgium is perhaps the most remarkable example. A town that, from at least the 13th century onward, operated a community foster care system for mentally ill individuals who came as pilgrims and stayed."

**Negative example.** `lkLwp9o7Djk:j0079`: "The conditions in many 19th century asylums would be recognizable to anyone who has read accounts of prisons or concentration camps, not in the deliberate evil sense, but in the sense of what happens when you put large numbers of vulnerable people in total institutions with minimal oversight and insufficient resources." - not `case`: it compares 19th-century asylums to a different category of thing (prisons/camps) to convey severity, rather than citing a literal instance of the same phenomenon - see `analogy`.

**Tie-breaker.** Against `analogy`: is this a literal real instance of the exact phenomenon under discussion? -> `case`. Is it a comparison to something else, in a different category, used to convey magnitude or quality? -> `analogy`.

<!-- não normativo --> **Glosa PT-BR.** Apresenta um exemplo histórico ou real concreto como sustentação.

#### `analogy`

**Definition (EN, normative).** Compares the claim to something else, often in a different category, to convey magnitude or quality - not a literal instance of the phenomenon itself.

**Positive examples.**
- `lkLwp9o7Djk:j0079`: "The conditions in many 19th century asylums would be recognizable to anyone who has read accounts of prisons or concentration camps, not in the deliberate evil sense, but in the sense of what happens when you put large numbers of vulnerable people in total institutions with minimal oversight and insufficient resources."
- `5unhHRFkC7I:j0028`: "But the gap here isn't like comparing a good swimmer to an excellent swimmer. It's like comparing someone who can see a candle to someone who can detect a single candle flame from 80 kilometers away on a clear night."

**Negative example.** `lkLwp9o7Djk:j0060`: "The town of Giel in Belgium is perhaps the most remarkable example. A town that, from at least the 13th century onward, operated a community foster care system for mentally ill individuals who came as pilgrims and stayed." - not `analogy`: Giel is a literal real instance of community-based mental health care, not a comparison to something else - see `case`.

**Tie-breaker.** Against `case` (mirrored above).

<!-- não normativo --> **Glosa PT-BR.** Compara a afirmação com outra coisa para transmitir magnitude ou qualidade.

#### `authority`

**Definition (EN, normative).** Justifies a claim by citing a specific named expert or historical figure's argument or theory - their idea, not their action/event or a data point.

**Positive examples.**
- `lkLwp9o7Djk:j0031`: "Plato himself wrote about four types of divine madness. prophetic madness, ritual madness, poetic madness, and erotic madness, all of which were considered superior states to ordinary rational thought."
- `lkLwp9o7Djk:j0034`: "In his text, On the Sacred Disease, written about epilepsy but with implications across all mental conditions, Hippocrates argued that mental disturbances were diseases of the brain caused by physical imbalances, specifically an imbalance of the four humors."

**Negative example.** `lkLwp9o7Djk:j0071`: "A few key reformers began arguing that the mentally ill were not subhuman, not demonic, not entertainment, but sick people who deserved humane care. Philippe Pinel in France famously, perhaps apocryphally, but the story stuck, ordered the chains removed from patients at the Bicetre Asylum in Paris in 1793." - not `authority`: Pinel's specific documented act (ordering chains removed) is an event, not a cited argument or theory - see `case`.

**Tie-breaker.** Against `case`: is the claim justified by who said/believed it (their argument/expertise is the point)? -> `authority`. Is it justified by what specifically, concretely happened or was done, regardless of who? -> `case`.

<!-- não normativo --> **Glosa PT-BR.** Justifica a afirmação citando o argumento ou a teoria de um especialista/figura histórica nomeada.

## `scale`

#### `individual`

**Definition (EN, normative).** The clause's core subject is one specific person or animal experiencing or doing something as themselves - the claim's meaning would not survive swapping the subject for "many people/several examples".

**Positive examples.**
- `5unhHRFkC7I:j0002`: "And your dog, who, let's be honest, has spent the last eight hours aggressively napping on your couch in positions that would send a chiropractor into cardiac arrest, immediately walks over, puts his head in your lap, and stares at you with those enormous, ridiculous, impossibly warm eyes."
- `lkLwp9o7Djk:j0044`: "And the decision about who qualified as Furiosus was made by the family and local magistrate, not a physician. So if your uncle was genuinely suffering from severe psychosis, he might be confined."

**Negative example.** `lkLwp9o7Djk:j0028`: "The Greeks had two competing frameworks for mental illness, and they were at war with each other for centuries. Framework one, the divine explanation." - not `individual`: the claim is about a whole people/society ("the Greeks"), not one bounded person or animal - see `human`.

**Tie-breaker.** Against `human`: replace the subject with "many people/several examples" - does the claim's meaning survive equivalently? If yes, `human`; if the claim is fundamentally about what this one entity, uniquely, did or experienced, `individual`, even when used to illustrate a broader point.

<!-- não normativo --> **Glosa PT-BR.** O sujeito da oração é uma única pessoa ou animal específico, vivendo ou fazendo algo por si.

#### `human`

**Definition (EN, normative).** The clause's subject is a social or population-level collective - a society, era, institution, profession, or "we/humanity" - or an animal population/species treated as a group. Broadened from a literal "human beings" reading (see the six-tests note below) to cover animal-population claims: not a single individual, and not a claim spanning multiple species or the whole biosphere.

**Positive examples.**
- `lkLwp9o7Djk:j0053`: "The first psychiatric hospitals in history were built in the Islamic world. Baghdad had one in the 8th century. Cairo had one in the 9th century. These were not prisons."
- `5unhHRFkC7I:j0026`: "Specifically, let's talk about your dog's nose, because this is where dogs go from adorable and loyal companions to walking biological supercomputers that are casually doing things we barely understand. A dog's nose contains roughly 300 million olfactory receptors."

**Negative example.** `5unhHRFkC7I:j0019`: "It is present in varying forms and degrees of complexity across virtually all mammals. Traces of it appear in birds. Elements of it show up even in fish." - not `human`: the claim explicitly spans multiple species (mammals, birds, fish), not one bounded population - see `planetary`.

**Tie-breaker.** Against `planetary`: does the claim concern one species/society/institution as a bounded group? -> `human`. Does it explicitly span multiple species or the whole biosphere/evolutionary timescale? -> `planetary`.

<!-- não normativo --> **Glosa PT-BR.** O sujeito é um coletivo social ou populacional - humano ou animal - não um indivíduo, nem várias espécies ao mesmo tempo.

#### `planetary`

**Definition (EN, normative).** Spans multiple species or the whole biosphere/Earth-scale evolutionary process, not a single population.

**Positive examples.**
- `5unhHRFkC7I:j0005`: "That moment right there, it's not just heartwarming, it's not just, aw, what a good boy. It is one of the most scientifically fascinating things happening on this planet every single day, and almost nobody takes it seriously enough to actually investigate it."
- `5unhHRFkC7I:j0103`: "We share this planet with creatures who have spent millions of years developing the capacity to feel, and thousands of years developing the capacity to feel for us, specifically. That is not a small thing."

**Negative example.** `5unhHRFkC7I:j0026`: "Specifically, let's talk about your dog's nose, because this is where dogs go from adorable and loyal companions to walking biological supercomputers that are casually doing things we barely understand. A dog's nose contains roughly 300 million olfactory receptors." - not `planetary`: the claim is about one species (dogs) as a population, not multiple species or the whole biosphere - see `human`.

**Tie-breaker.** Against `human` (mirrored above).

<!-- não normativo --> **Glosa PT-BR.** Abrange várias espécies ou a biosfera/escala evolutiva inteira - não uma única população.

#### `abstract`

**Definition (EN, normative).** The clause's core subject is a concept, question, or proposition with no concrete embodied actor - a "gap", a definition, or a meta-claim about knowledge or method.

**Positive examples.**
- `lkLwp9o7Djk:j0093`: "The question that every generation has faced, and that we face right now, is not only, what do we know about mental illness? It is, what do we believe the mentally ill deserve?"
- `5unhHRFkC7I:j0073`: "This is important. Because it means that empathy, the capacity to detect and respond to the emotional state of another being, is not inherently species-locked."

**Negative example.** `lkLwp9o7Djk:j0084`: "The most humane responses to mental illness throughout history almost never came from the most sophisticated societies." - not `abstract`: despite the generalizing tone, the grammatical subject is a concrete collective ("societies"), not a free-standing concept - see `human`.

**Tie-breaker.** Against `human`: is the clause's grammatical subject a concept/question/proposition (empathy, the gap, the question) rather than a group of people or animals? -> `abstract`. Is the subject a society/group/institution, even in a generalizing sentence? -> `human`.

<!-- não normativo --> **Glosa PT-BR.** O sujeito é um conceito, pergunta ou proposição sem ator concreto - não uma pessoa, animal ou grupo.

## `density`

Integer, `min: 0`, `max: 2` - count of new concepts, terms, or facts the window introduces that the video has not already named.

#### `0`

**Definition (EN, normative).** Introduces no new named concept, term, or entity beyond what the video has already established - restates or stylizes existing information.

**Positive examples.**
- `lkLwp9o7Djk:j0009`: "Acting erratic and strange? Demon. Obviously. Demon, drill the hole, boom."
- `lkLwp9o7Djk:j0020`: "They were observing carefully and systematically. They just had the causal mechanism completely wrong, which in the grand tradition of medicine is a completely normal phase to go through."

**Negative example.** `lkLwp9o7Djk:j0015`: "This was called the hand of a god doctrine. Your madness was literally the hand of a specific god pressing down on you." - not `0`: it introduces one new named concept (the "hand of a god" doctrine) - see `1`.

**Tie-breaker.** Against `1`: count only genuinely new named ideas/terms/facts not previously mentioned in the video up to this window; a stylistic restatement of an idea already named counts as `0`.

<!-- não normativo --> **Glosa PT-BR.** Não introduz nenhum conceito novo - repete ou estiliza o que já foi dito.

#### `1`

**Definition (EN, normative).** Introduces exactly one new named concept, term, or fact not previously mentioned in the video.

**Positive examples.**
- `lkLwp9o7Djk:j0015`: "This was called the hand of a god doctrine. Your madness was literally the hand of a specific god pressing down on you."
- `lkLwp9o7Djk:j0007`: "This is called trepanation, and it is exactly as metal as it sounds. The working theory? They were letting the evil spirits out, literally drilling an exit door for the demon living in someone's skull."

**Negative example.** `lkLwp9o7Djk:j0034`: "In his text, On the Sacred Disease, written about epilepsy but with implications across all mental conditions, Hippocrates argued that mental disturbances were diseases of the brain caused by physical imbalances, specifically an imbalance of the four humors." - not `1`: it introduces two independent new concepts (the text's title and the four-humors theory) - see `2`.

**Tie-breaker.** Against `2`: if a second, independent new concept/term appears in the same window (not just an elaboration of the first), count it - `2`, not `1`.

<!-- não normativo --> **Glosa PT-BR.** Introduz exatamente um conceito novo, termo ou fato ainda não mencionado no vídeo.

#### `2`

**Definition (EN, normative).** Introduces two or more distinct new concepts, terms, or facts in the same window.

**Positive examples.**
- `lkLwp9o7Djk:j0034`: "In his text, On the Sacred Disease, written about epilepsy but with implications across all mental conditions, Hippocrates argued that mental disturbances were diseases of the brain caused by physical imbalances, specifically an imbalance of the four humors."
- `lkLwp9o7Djk:j0035`: "blood, phlegm, yellow bile, and black bile. This is where we get melancholy, from the Greek melas, meaning black, and kole, meaning bile."

**Negative example.** `lkLwp9o7Djk:j0007`: "This is called trepanation, and it is exactly as metal as it sounds. The working theory? They were letting the evil spirits out, literally drilling an exit door for the demon living in someone's skull." - not `2`: it introduces only one new concept (trepanation) - see `1`.

**Tie-breaker.** Against `1` (mirrored above).

<!-- não normativo --> **Glosa PT-BR.** Introduz dois ou mais conceitos novos distintos na mesma janela.
