# Decisions log

Record every deviation from, or conflict between, the PRD/HLD/LLD, and every notable
implementation choice (library versions, threshold tuning, gate-failure diagnoses).

| Date | Phase | Decision / finding | Why | Docs affected |
| --- | --- | --- | --- | --- |
| 2026-10-03 | Design | Hybrid legs are store-native; fusion is weighted RRF in the api | Per-leg scores on every request; same ID weighting on Qdrant and AI Search | ADR-007, HLD, LLD |
| 2026-10-03 | Design | Golden set v1.1 adds `forbidden` lists to Q23, Q37, Q38, Q40 | Machine-checkable trap avoidance | LLD evaluation section |
| 2026-10-03 | P0 | Installed missing host tools: uv 0.12.23 (`pip --user`), GNU make (winget `ezwinports.make`); started Docker Desktop | KICKOFF prerequisites; no admin rights needed | — |
| 2026-10-03 | P0 | Host Node is 20.13.1 (Vite 8 / ESLint 10 need ≥20.19; the elevated Node upgrade was cancelled). `make lint`, `make web-types`, `make web-build` run web tooling in a pinned `node:20.20.2-alpine` container | Host Node version no longer matters; CI and the web image use 20.20.2 | Makefile |
| 2026-10-03 | P0 | Node 20 reached end of life in 2026-04; kept Node 20.20.2 because the LLD requires Node 20 LTS | Follow LLD; revisit when the LLD is updated | — |
| 2026-10-03 | P0 | Pinned: Python 3.11.17, postgres 16.15-bookworm, qdrant v1.19.1, azurite 3.37.0, nginx 1.30.5-alpine, node 20.20.2-alpine; React 19, react-router 8, Vite 8, Tailwind 4, ESLint 10, TypeScript 5.9 (TS 6 rejected: typescript-eslint peer range <6.1 and LLD says TS 5) | Latest stable within LLD major-version constraints | uv.lock, web/package-lock.json |
| 2026-10-03 | P0 | Heavy dependencies (langchain*, fastembed, sentence-transformers/torch, pdfplumber, unstructured, tiktoken, ragas, arize-otel) are added in the phase that first uses them | Keeps P0 images small; versions locked when added | — |
| 2026-10-03 | P0 | Derived profiles: `hybrid` and `rerank` also turn rewrite, filter and guardrail off; `baseline`/`hybrid`/`rerank` set recency_boost 0 | LLD lists only partial overrides; this isolates each retrieval upgrade for measurement | config/profiles |
| 2026-10-03 | P0 | Added `ping()` to `IndexBackend`; `QueueMessage` lives in `models.py`; dependency wiring in `pmo_core/container.py` | `/api/ready` needs a reachability check per adapter | LLD interfaces (additive) |
| 2026-10-03 | P0 | Services are packages `services/<svc>/src/<svc>/` (e.g. `api/schemas.py`) rather than flat files | Installable uv workspace members; `python -m api|worker|eval` entry points | LLD layout |
| 2026-10-03 | P0 | `/api/ready` Foundry check = endpoint configured and answers HTTP within 5 s (any status) | Reachability without spending tokens | — |
| 2026-10-03 | P0 | ruff excludes `docs/` and `*.md` | ruff format rewrote Python blocks inside LLD.md (reverted) | pyproject.toml |
| 2026-10-03 | P0 | Alembic version table lives in schema `app`; migration 0001 is the LLD DDL verbatim | Keep all app objects in one schema | — |
