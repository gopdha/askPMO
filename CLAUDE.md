# CLAUDE.md — askPMO

You are building askPMO, a RAG assistant that answers questions about a program (the synthetic
"Project Atlas") from its documents, with citations, an honest "not found", and a visible,
measured retrieval pipeline. The human (Gopi) wants to give as little input as possible:
work autonomously, phase by phase, and prove each phase with its gate.

## Sources of truth (read before writing code)

| Order | File | Use it for |
|---|---|---|
| 1 | `docs/LLD.md` | HOW: layout, interfaces, schemas, algorithms, prompts, phases, gates |
| 2 | `docs/HLD.md` | WHAT: components, contracts, flows, security, deployment |
| 3 | `docs/PRD.md` | WHY: goals, requirements, release targets |
| 4 | `docs/adr/` | Decisions and their rationale |
| — | `docs/architecture/*.pptx` | Diagrams (conceptual, logical, physical local + Azure) |

- If the LLD and HLD conflict, the LLD wins. If the PRD conflicts with either, the LLD wins.
  Log every conflict or deviation you resolve in `docs/decisions-log.md` (date, what, why).
- If `docs/PRD.md`, `docs/HLD.md` or `docs/LLD.md` is missing, STOP and ask the human to
  export them (see `KICKOFF.md`). Do not reconstruct them from memory.
- `eval/golden_set.json` (v1.1) already contains the `forbidden` lists described in the LLD.

## How to work

1. Track progress in `docs/build-status.md`. Read it at the start of every session.
2. Work on exactly one phase at a time (P0 → P6). Phase P7 (Azure) only when the human asks.
3. For a phase: plan briefly → implement → write tests → run the phase gate → fix → repeat.
4. A phase is done only when every gate item in the LLD build-plan table passes. Record the
   gate evidence (commands + key numbers) in `docs/build-status.md`, then commit:
   `git commit -m "P<n>: <summary>" -m "<gate evidence>"`.
5. Stop and hand back to the human at the three checkpoints:
   - before P1, if `make check-env` reports missing variables;
   - after P3, with the baseline results (`docs/results.md`);
   - after P6, for version-1 sign-off.
   Otherwise continue to the next phase without asking.
6. Escalate only for credentials, quota/rate limits you cannot work around, or a gate that
   still fails after two diagnosed attempts (write the diagnosis first).

## Quality bar and evaluation rules

- Never edit `eval/golden_set.json` answers, key facts or evidence to pass a gate.
- Tune thresholds and weights only on the `tune` split (`eval/splits.json`); report on `test`
  and `all`. Generate the split once with seed 42 and commit it.
- When a gate fails, diagnose from stage traces and per-question results first; write what you
  tried in `docs/decisions-log.md` before changing code.
- Gate thresholds live in `config/gates.yaml`; `python -m eval gate RUN_ID --phase P<n>` must use it.

## Engineering conventions

- Python 3.11, uv workspace. All logic in `packages/pmo_core`; services stay thin.
- Type hints everywhere; `mypy --strict` on `pmo_core`; `ruff` for lint and format.
- Pure functions for pipeline stages; adapters behind the protocols in the LLD.
- Tests: unit and contract tests must run offline (fakes for chat model and embeddings).
  Run `make lint` and `make test` after every meaningful change.
- Web: React + TypeScript + Vite; types generated from OpenAPI (`make web-types`); no auth code.
- Keep prompts in `config/prompts/`, profiles in `config/profiles/`; never hard-code them.
- Pin dependency versions in lockfiles; record notable version choices in the decisions log.

## Security rules (non-negotiable)

- Never read, print, copy or commit `.env`. To check configuration, run `make check-env`
  (P0 creates it: prints which required variables are set, never their values).
- No secrets, prompts or answer text in logs; traces go to Arize AX only.
- Only nginx is published (port 8080). Do not expose other ports to the host except where the
  LLD says so for local debugging (none by default).

## Commands (created in P0; keep this list current)

```
make up | down | reset | logs      # stack lifecycle
make check-env                     # which required env vars are set (no values)
make seed                          # upload corpus/ and wait for the ingest job
make split                         # once: eval/splits.json
make eval PROFILES=full SPLIT=all  # golden-set run
make gate RUN=<id> PHASE=P4        # gate check
make test | test-int | lint | web-types
```

## Custom slash commands

- `/next-phase` — continue the build from `docs/build-status.md`.
- `/gate <phase>` — run and report a phase gate.
- `/status` — summarize progress, latest metrics and open issues.
