# Build status

Update this file at the start and end of every phase. Gate definitions: `docs/LLD.md`
("Phased build plan") and `config/gates.yaml`.

| Phase | Status | Gate evidence (summary) | Commit |
| --- | --- | --- | --- |
| P0 Scaffold | Done (CI pending first push) | `make up` 6/6 healthy, `/api/ready` 200; lint clean; 23 unit + 2 integration tests pass | see git log |
| P1 Ingestion | Not started | | |
| P2 Baseline chat | Not started | | |
| P3 Evaluation | Not started | | |
| P4 Retrieval | Not started | | |
| P5 Query and answer | Not started | | |
| P6 Polish | Not started | | |
| P7 Azure (on request only) | Not started | | |

## Human checkpoints
- [x] Before P1: `.env` complete (`make check-env` all green, 19/19 set — 2026-10-03)
- [ ] After P3: baseline results reviewed (`docs/results.md`)
- [ ] After P6: version 1 signed off

## Phase notes
<!-- Claude Code: add a section per phase with the plan, decisions and gate output. -->

### P0 Scaffold — plan
- Root: `pyproject.toml` (uv workspace, Python 3.11), `uv.lock`, `Makefile`, `docker-compose.yml`, `.github/workflows/ci.yml`, `tools/check_env.py`.
- `packages/pmo_core`: `settings.py` (env + profile loader with overrides), `models.py`, `adapters/base.py` (protocols),
  `adapters/index_qdrant.py` (`ensure_schema`, `count`), `adapters/storage_azure.py` (container/queue bootstrap),
  `db/` (SQLAlchemy models, first Alembic migration = LLD DDL), `telemetry.py` (no-op when Arize key empty), `logging.py`.
- `config/profiles/{full,baseline,hybrid,rerank}.yaml`, `config/prompts/{rewrite,generate}.md`.
- `services/api` (FastAPI, `/api/health`, `/api/ready`, `/api/profiles`, API schemas), `services/worker` (queue loop skeleton),
  `services/eval` (CLI skeleton), Dockerfiles.
- `web/`: Vite + React + TS + Tailwind shell with three routes, nginx proxy, Dockerfile, ESLint.
- Tests: settings/profile resolution, models, check-env, api health/ready/profiles with fakes.

### P0 Scaffold — gate evidence (2026-10-03)
| Gate item | Command | Result |
| --- | --- | --- |
| Stack healthy | `make up` | postgres, qdrant, azurite, api, worker, web all healthy; only `0.0.0.0:8080->80` published |
| Readiness | `curl localhost:8080/api/ready` | 200, index/queue/database/foundry all ok |
| Bootstrap | `psql \dt app.*` / Qdrant | 8 LLD tables + alembic_version; collection `pmo_chunks` exists (0 points) |
| Lint | `make lint` | ruff check + format clean; mypy --strict: 0 issues in 30 files; eslint + tsc clean |
| Tests | `make test` | 23 passed |
| Integration | `make test-int` | 2 passed (health via nginx, SPA served) |
| Env | `make check-env` | 19/19 required variables set |
| CI green | `.github/workflows/ci.yml` | **Pending**: runs on first push to `origin` (needs human OK to push) |
