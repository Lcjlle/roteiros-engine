# Estado do projeto

**Este arquivo e gerado. Nao edite a mao.** Regenere com
`uv run python -m src.estado --write` a partir de `schema/portoes.json`, dos
`fase*_gate.json`/`manifesto.csv` reais, do commit atual e das issues abertas
no GitHub - ver `_docs/decisions.md#22`. `uv run python -m src.estado --check`
e o que a CI roda para garantir que este arquivo nunca fica desatualizado
comparado ao dado real.

<!-- METADATA_START -->
- commit: `fc3a08f2603fe076d5c7ccc642aeab6936e977c8`
- gerado em: 2026-09-05T11:09:55.455058+00:00
<!-- METADATA_END -->

## Portoes

A fonte de cada numero abaixo e `schema/portoes.json` - nunca edite um limiar
aqui, edite la e regenere.

<!-- PORTOES_TABLE_START -->
| Fase | Gate | Metrica | Limite | Tipo | Escopo | Status |
|---|---|---|---|---|---|---|
| 1 | `fase1-profile-row-floor` (mackexplains7) | count of corpus/{channel}/manifesto.csv rows with role == profile (rows with no role column count as profile too, per src/coleta.py::check_gate) | >= 30 rows | tolerance | per_channel | passou (30 linhas profile) |
| 1 | `fase1-profile-row-floor` (zenn0009) | count of corpus/{channel}/manifesto.csv rows with role == profile (rows with no role column count as profile too, per src/coleta.py::check_gate) | >= 30 rows | tolerance | per_channel | passou (30 linhas profile) |
| 1 | `fase1-holdout-row-floor` (mackexplains7) | count of corpus/{channel}/manifesto.csv rows with role == holdout | >= 4 rows | tolerance | per_channel | passou (5 linhas holdout) |
| 1 | `fase1-holdout-row-floor` (zenn0009) | count of corpus/{channel}/manifesto.csv rows with role == holdout | >= 4 rows | tolerance | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 1 | `fase1-word-count-floor` (mackexplains7) | per-row ratio of contagem_palavras to expected_word_count(duracao_s) at WORDS_PER_MINUTE (src/coleta.py::expected_word_count), minimum across every profile row in corpus/{channel}/manifesto.csv | >= 0.6 ratio | tolerance | per_channel | passou (pior razao: 90.2%) |
| 1 | `fase1-word-count-floor` (zenn0009) | per-row ratio of contagem_palavras to expected_word_count(duracao_s) at WORDS_PER_MINUTE (src/coleta.py::expected_word_count), minimum across every profile row in corpus/{channel}/manifesto.csv | >= 0.6 ratio | tolerance | per_channel | passou (pior razao: 111.2%) |
| 2 | `fase2-oversized-window-parity` (mackexplains7) | count of windows with n_words > GATE_MAX_WINDOW_WORDS minus count of sentences with n_words > GATE_MAX_WINDOW_WORDS, across the whole corpus's sentences/*.json and windows/*.json (src/janelas.py::check_3a) | == 0 count_difference | invariant | per_channel | passou (19 janelas vs 19 sentencas) |
| 2 | `fase2-oversized-window-parity` (zenn0009) | count of windows with n_words > GATE_MAX_WINDOW_WORDS minus count of sentences with n_words > GATE_MAX_WINDOW_WORDS, across the whole corpus's sentences/*.json and windows/*.json (src/janelas.py::check_3a) | == 0 count_difference | invariant | per_channel | declarado, nao medido |
| 2 | `fase2-nonlast-single-window-residual` (mackexplains7) | count of non-last, single-sentence windows not explained by (i) their lone sentence already exceeding WINDOW_MAX_WORDS or (ii) a forced close to avoid exceeding GATE_MAX_WINDOW_WORDS (src/janelas.py::check_3b) | == 0 residual_count | invariant | per_channel | passou (residuo=0) |
| 2 | `fase2-nonlast-single-window-residual` (zenn0009) | count of non-last, single-sentence windows not explained by (i) their lone sentence already exceeding WINDOW_MAX_WORDS or (ii) a forced close to avoid exceeding GATE_MAX_WINDOW_WORDS (src/janelas.py::check_3b) | == 0 residual_count | invariant | per_channel | declarado, nao medido |
| 2 | `fase2-nonlast-single-window-ratio` (mackexplains7) | ratio of non-last, single-sentence windows to total windows in the corpus (src/janelas.py::check_3c) | <= 0.15 ratio | thermometer | per_channel | passou (11.9%) |
| 2 | `fase2-nonlast-single-window-ratio` (zenn0009) | ratio of non-last, single-sentence windows to total windows in the corpus (src/janelas.py::check_3c) | <= 0.15 ratio | thermometer | per_channel | declarado, nao medido |
| 2 | `fase2-window-rate-band` (mackexplains7) | windows per video vs. duration-derived expected rate; duration_min and n_windows measured per video from corpus/{channel}/sentences and corpus/{channel}/windows, the same pair fase2_gate.json already reads | ceil(duration_min * GATE_WINDOWS_PER_MINUTE * (1 - GATE_WINDOWS_PER_MINUTE_BAND)) <= n_windows <= floor(duration_min * GATE_WINDOWS_PER_MINUTE * (1 + GATE_WINDOWS_PER_MINUTE_BAND)) [GATE_WINDOWS_PER_MINUTE=4.86, GATE_WINDOWS_PER_MINUTE_BAND=0.4] | tolerance | per_channel | passou (todos os videos dentro da banda) |
| 2 | `fase2-window-rate-band` (zenn0009) | windows per video vs. duration-derived expected rate; duration_min and n_windows measured per video from corpus/{channel}/sentences and corpus/{channel}/windows, the same pair fase2_gate.json already reads | ceil(duration_min * GATE_WINDOWS_PER_MINUTE * (1 - GATE_WINDOWS_PER_MINUTE_BAND)) <= n_windows <= floor(duration_min * GATE_WINDOWS_PER_MINUTE * (1 + GATE_WINDOWS_PER_MINUTE_BAND)) [GATE_WINDOWS_PER_MINUTE=4.86, GATE_WINDOWS_PER_MINUTE_BAND=0.4] | tolerance | per_channel | declarado, nao medido |
| 2 | `fase2-two-narrative-functions` (mackexplains7) | windows judged to carry two distinct narrative functions, in the fixed-seed 50-window human-judged sample from 2 videos | <= 5/50 windows | tolerance | per_channel | registrado em _docs/decisions.md#17 |
| 2 | `fase2-two-narrative-functions` (zenn0009) | windows judged to carry two distinct narrative functions, in the fixed-seed 50-window human-judged sample from 2 videos | <= 5/50 windows | tolerance | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 2 | `fase2-sentence-cut-midclause` (mackexplains7) | sentences cut mid-clause, in the same fixed-seed 50-window human-judged sample | == 0/50 windows | tolerance | per_channel | registrado em _docs/decisions.md#17 |
| 2 | `fase2-sentence-cut-midclause` (zenn0009) | sentences cut mid-clause, in the same fixed-seed 50-window human-judged sample | == 0/50 windows | tolerance | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 3 | `fase3-outro-duvida-coverage` | windows classified 'outro' or genuine doubt, across the 205-window coverage sample (2 hand-classified videos, lkLwp9o7Djk + 5unhHRFkC7I) | <= 20/205 windows | tolerance | global | passou (0/205) |
| 4 | `fase4-self-agreement-alpha` (mackexplains7) | Krippendorff's alpha, human x human, by field, on the 1 gold video reannotated after 48h against the original annotation of the same video | >= 0.8 krippendorff_alpha | tolerance | per_channel | declarado, nao medido |
| 4 | `fase4-self-agreement-alpha` (zenn0009) | Krippendorff's alpha, human x human, by field, on the 1 gold video reannotated after 48h against the original annotation of the same video | >= 0.8 krippendorff_alpha | tolerance | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 5 | `fase5-model-human-agreement-alpha` (mackexplains7) | Krippendorff's alpha, model x human, by field, at window level, over the 5 gold videos | >= 0.667 krippendorff_alpha | tolerance | per_channel | declarado, nao medido |
| 5 | `fase5-model-human-agreement-alpha` (zenn0009) | Krippendorff's alpha, model x human, by field, at window level, over the 5 gold videos | >= 0.667 krippendorff_alpha | tolerance | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 5 | `fase5c-smoothing-rate` (mackexplains7) | fraction of length-1 window sequences absorbed by smoothing during block fusion (M6), across the channel's blocks | <= 0.15 ratio | tolerance | per_channel | declarado, nao medido |
| 5 | `fase5c-smoothing-rate` (zenn0009) | fraction of length-1 window sequences absorbed by smoothing during block fusion (M6), across the channel's blocks | <= 0.15 ratio | tolerance | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 6 | `fase6-owner-recognizes-channel` (mackexplains7) | project owner reads perfis/<channel>.perfil.json and recognizes the channel in it | the project owner reads the generated profile and recognizes the channel in it | judgment | per_channel | declarado, nao medido |
| 6 | `fase6-owner-recognizes-channel` (zenn0009) | project owner reads perfis/<channel>.perfil.json and recognizes the channel in it | the project owner reads the generated profile and recognizes the channel in it | judgment | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
| 6 | `fase6-schema-valid` (mackexplains7) | perfis/<channel>.perfil.json validates against schema/perfil.schema.json | == 1 schema_valid_boolean | invariant | per_channel | declarado, nao medido |
| 6 | `fase6-schema-valid` (zenn0009) | perfis/<channel>.perfil.json validates against schema/perfil.schema.json | == 1 schema_valid_boolean | invariant | per_channel | nao aplicavel (papel do canal: fixture_channel; portao exige: ['profile_channel']) |
<!-- PORTOES_TABLE_END -->

## Fases abertas (por label `fase-N`)

Instantaneo do GitHub em 2026-09-05T11:09:55.455058+00:00 - uma issue pode abrir ou fechar sem gerar nenhum commit aqui; para o estado real, rode `gh issue list --repo Lcjlle/roteiros-engine --label fase-N`.

<!-- OPEN_ISSUES_START -->
- **fase-5**: #12 Fase 5: cta com 0 ocorrências em 205 janelas indo para um portão de α por campo
- **fase-8**: #13 Fase 8: portão único (≥ 90% dos critérios) mistura calibração anticircular (uma vez) com relatório por roteiro gerado (por canal e por vídeo); #6 Fase 8: métricas de perfil por-vídeo (blocks_per_video, opened_per_video) devem virar taxa por minuto
<!-- OPEN_ISSUES_END -->
