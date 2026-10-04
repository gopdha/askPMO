# Build status

Update this file at the start and end of every phase. Gate definitions: `docs/LLD.md`
("Phased build plan") and `config/gates.yaml`.

Timestamps are local time (CDT). "Updated" changes on every status change.

| Phase | Status | Started | Finished | Updated | Gate evidence (summary) | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| P0 Scaffold | Done | 2026-10-03 23:12 | 2026-10-03 23:31 | 2026-10-03 23:34 | `make up` 6/6 healthy, `/api/ready` 200; lint clean; 23 unit + 2 integration tests pass; CI run 37177350337 green | f61073f, 7ebb3bc |
| P1 Ingestion | Blocked (needs human: embedding deployment 404; chunk-count range) | 2026-10-03 23:34 | | 2026-10-03 23:54 | 134 unit+contract tests pass (metadata for all 31 files; contract on Qdrant + fake); seed job failed: DeploymentNotFound | WIP |
| P2 Baseline chat | Not started | | | | | |
| P3 Evaluation | Not started | | | | | |
| P4 Retrieval | Not started | | | | | |
| P5 Query and answer | Not started | | | | | |
| P6 Polish | Not started | | | | | |
| P7 Azure (on request only) | Not started | | | | | |

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
| CI green | `.github/workflows/ci.yml` | GitHub Actions run 37177350337 on 7ebb3bc: python ✅, web ✅ |

### P1 Ingestion — plan
- `ingest/metadata.py` (doc_type, doc_date, week, title, IDs), `ingest/loaders.py` (md, csv, pdf via pdfplumber),
  `ingest/chunkers.py` (header split + 1,200/150 packing, tables whole, RAID rows, PDF tables), `ingest/pipeline.py`
  (chunk → embed in batches of 64 with retries → delete + upsert), `ingest/jobs.py` (upload registration, job processing).
- `adapters/bm25.py` (offline sparse encoder), `adapters/index_qdrant.py` (full IndexBackend), `adapters/llm.py` (embeddings),
  `db/tables.py` (SQLAlchemy Core tables).
- api: `POST/GET /api/documents`, `GET /api/ingest-jobs/{id}`, `GET /api/chunks/{id}`; worker: queue loop with poison handling;
  `tools/seed.py` (`make seed`); web Documents page (folder drag-and-drop, table, 3 s progress polling).
- Tests: metadata for all 31 files, chunkers, BM25, worker loop; contract suite (fake + Qdrant testcontainer); ingest jobs on
  Postgres testcontainer.

### P1 Ingestion — gate status (2026-10-03 23:54)
| Gate item | Result |
| --- | --- |
| Unit tests cover metadata for all 31 corpus files | ✅ `tests/unit/test_metadata.py` — 31 parametrized cases + coverage check; `make test` 134 passed |
| Contract suite passes on Qdrant | ✅ `tests/contract/test_index_contract.py` — 9 tests × (fake, Qdrant v1.19.1) all pass |
| `make seed` job `succeeded` with 250–400 chunks | ❌ job failed: Foundry `DeploymentNotFound` (404) on embeddings. Offline chunk count is 203 (< 250) — see decisions log |
| Lint | ✅ ruff, mypy --strict (40 files), eslint, tsc clean |
