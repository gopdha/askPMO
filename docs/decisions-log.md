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
| 2026-10-04 | P1 | Keyword leg uses an in-repo BM25 sparse encoder (`adapters/bm25.py`) instead of fastembed `Qdrant/bm25`; Qdrant applies IDF (`Modifier.IDF`) | fastembed splits `RSK-014` into `rsk`/`014` (weaker exact-ID matching) and downloads a model at runtime; ours is offline, deterministic and keeps IDs whole | LLD toolchain (fastembed dropped) |
| 2026-10-04 | P1 | Markdown is read as raw text; `unstructured` not used | MarkdownHeaderTextSplitter works on raw text; unstructured is a very heavy dependency with no benefit here | LLD toolchain |
| 2026-10-04 | P1 | Weekly reports' title gets the suffix `– Week N` (e.g. `[Project Atlas – Weekly Status Report – Week 6 — Executive summary]`) | All 12 reports share one H1, so the LLD's goal of matching 'week 6' through the header was impossible otherwise | LLD contextual header |
| 2026-10-04 | P1 | `doc_date` month rule only matches a `YYYY-MM` not embedded in an identifier | Literal rule would date the SOW by its contract number `NRG-COB-2026-01` (2026-01-31) instead of its effective date 2026-01-09 | LLD metadata rules |
| 2026-10-04 | P1 | PDF U+FFFD glyphs (unmapped en dashes) become `–`; P3 normalizer will treat U+FFFD as a dash | Golden evidence for Q07 contains U+FFFD (`M5 � UAT complete`); golden set is not edited | LLD metric normalization (P3) |
| 2026-10-04 | P1 | RAID row text adds `Closed: <date>` when present (between Raised and Description) | Closure dates are useful facts; LLD field list omitted Date Closed | LLD CSV chunking |
| 2026-10-04 | P1 | Content before the first H2 gets section `Overview`; section = `H2 > H3` path (H1 is already the title) | LLD did not name the section for pre-H2 content | — |
| 2026-10-04 | P1 | GATE DIAGNOSIS — chunk count. Spec chunking (header split L1–3, 1,200/150, tables ≤2,400 whole) yields **203** chunks for the 31-file corpus (status 84, minutes 38, CRs 22, RAID 18, charter 12, SOW 8, cutover 6, reference 5, budget 4, change log 3, resource plan 3). Attempt 2: every Markdown table as its own chunk → 207. Corpus is ~52 KB of Markdown + 6 PDF pages; most sections are < 1,200 chars, so one chunk per section. Reaching 250 would need ~600-char chunks, i.e. changing LLD parameters only to hit an estimate | LLD calls 250–400 'roughly'; its own parameters contradict it. Not gaming the gate: escalated to the human with a proposal to set the range to 180–260 (offline count ±~25%) | LLD P1 gate, ingestion section |
| 2026-10-04 | P1 | GATE BLOCKER — Foundry embeddings return 404 `DeploymentNotFound` for the configured `EMBEDDING_DEPLOYMENT` (29 chars) and for `text-embedding-3-small`; endpoint is a valid `*.openai.azure.com` resource URL, API version 2025-04-01-preview | Configuration/credentials: needs the human | — |
