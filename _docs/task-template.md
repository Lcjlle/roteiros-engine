## Goal

One or two sentences on what should be true when this is done.

## Acceptance criteria

- [ ] A statement you can check by looking at the result
- [ ] One line per case, including the awkward ones
- [ ] If this issue closes a phase from `_docs/plano_implementacao.md`, the
      phase's gate is one of these lines, with its exact numeric threshold
      (e.g. "<= 5 de 50 janelas com duas funções, semente 42" or
      "Krippendorff's alpha >= 0.667 model x human, per field")

## Out of scope

- Something that does not belong in this task, moved to #12

## Constraints

- Files this should stay inside
- Libraries it may not add, patterns it must follow
- Shared files this touches (`schema/`, `src/db.py`, `AGENTS.md`,
  `.env.example`, `_docs/decisions.md`) - name them so the orchestrator can
  keep the wave from colliding on them
- Tables this adds or changes, if any - so the orchestrator can keep two
  issues in the same wave from migrating the same table
