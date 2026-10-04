---
description: Continue the build from docs/build-status.md (optionally a specific phase)
argument-hint: [phase, e.g. P2]
---
Continue building askPMO.

1. Read `CLAUDE.md`, then `docs/build-status.md`. Target phase: $ARGUMENTS (if empty, the first phase not marked done).
2. Re-read the target phase's row in the "Phased build plan" section of `docs/LLD.md`, plus every LLD section it depends on.
3. Write a short plan (files to create or change, tests to add) into `docs/build-status.md` under the phase.
4. Implement it. Run `make lint` and `make test` as you go.
5. Run the phase gate exactly as defined in the LLD and `config/gates.yaml`. Fix and re-run until it passes, following the diagnosis rules in `CLAUDE.md`.
6. Record gate evidence in `docs/build-status.md`, mark the phase done, and commit.
7. If the next step is a human checkpoint (see `CLAUDE.md`), stop and summarize what the human needs to review. Otherwise continue with the next phase.
