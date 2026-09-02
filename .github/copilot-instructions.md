# Copilot and coding-agent instructions for `gitminer-dash`

Use these instructions for all edits in this repository.

## Mandatory workflow

- Discover before changing: search standard library/framework/repo before creating new code.
- Make the smallest conservative change that solves the requested problem.
- Keep changes aligned with existing architecture, patterns, and domain vocabulary.
- After each change, run `./run_tests`.
- Before proposing merge readiness, run `./check` and `./run_tests`.

## Eleven virtues (operational)

### Product virtues

- Working: prove correctness with tests/checks.
- Unique: preserve a single point of truth; avoid duplication.
- Simple: reduce local operands, operations, and paths.
- Clear: use intention-revealing code and names.
- Easy: optimize for safe future changes.
- Developed: prefer domain abstractions over primitive manipulation.
- Brief: remove noise and unnecessary ceremony.

### Stewardship virtues

- Aligned: follow existing architecture/conventions.
- Discovered: understand surrounding code before modifying.
- Traceable: keep rationale explainable through requirement/defect/domain need.
- Conservative: prefer focused incremental changes.

## Naming operational checklist

- Name for team/domain audience, not individual style.
- Prefer familiar ecosystem idioms already used in the codebase.
- Prefer domain language used in tests/tickets/docs.
- Let surrounding context carry meaning; remove repeated prefixes.
- Name for purpose, not composition.
- Match name length to scope/lifespan.
- Avoid low-information noise words unless they add distinction.
- Ensure neighboring names are distinguishable and front-load the meaningful part.
- If naming is hard, improve cohesion/extraction before inventing clever names.
