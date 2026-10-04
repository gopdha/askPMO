# HLD – askPMO (RAG)

Oct 3, 2026 · @Gopinath Dhayanandamurthy

## Purpose and scope

This HLD fixes the component boundaries, contracts, data model and runtime behavior of askPMO, so the LLD and the build can proceed without reopening architecture decisions.

- **Inputs:** the PRD (goals, 22 functional requirements, NFR targets) and the architecture views deck (conceptual, logical, physical local and Azure, 13 proposed ADRs).
- **In scope:** version 1 running locally in Docker Compose, plus the Azure Container Apps target state, designed to the same contracts.
- **Left to the LLD:** module and class layout, exact schemas and DDL, prompts, config file contents, pinned package and model versions, test plan, and the phased task list for Claude Code.

**Design principles**

1. **One pipeline, many profiles.** Every feature is a stage toggled by a YAML profile; the baseline is the same code with stages switched off.
2. **Environment parity.** Local and Azure run the same containers; only adapters (index, storage, identity) differ, behind interfaces.
3. **Everything observable.** Every stage emits a span with its inputs, scores and latency; the UI and the eval runner read the same stage trace.
4. **Bounded answers.** The model only sees reranked evidence, must cite it, and is never called when evidence is too weak.

## Components and responsibilities

The system has four deployable services and four stores; each store has exactly one writer per data type, and only backend services touch stores.

| Component | Type | Owns | Never does |
| --- | --- | --- | --- |
| web | nginx container serving the React SPA build | Static assets; proxies `/api/*` to api; on Azure, sits behind Container Apps built-in auth | Holds tokens or keys; calls any store directly |
| api | FastAPI service (Python 3.11) | Chat endpoint and the query pipeline; document upload and ingest job creation; config profiles; feedback; read APIs for the UI | Runs ingestion work inline; writes to the retrieval index |
| worker | Python queue consumer | Loading, chunking, embedding and indexing documents; ingest job status | Serves HTTP; answers questions |
| eval | Python batch job | Replaying the golden set against api per profile; computing metrics; storing results | Calls the pipeline in-process (it uses the public API, so it measures what users get) |
| Retrieval index | Qdrant (local) / Azure AI Search (Azure) | Chunk text, vectors, keyword terms, chunk metadata | Stores chats or eval results |
| PostgreSQL | Container (local) / Flexible Server (Azure) | Documents registry, ingest jobs, conversations, turns, stage traces, feedback, eval runs and results | Stores vectors |
| Blob storage | Azurite (local) / Storage account (Azure) | Original uploaded files, golden set file, eval artifacts | — |
| Queue | Azurite queue (local) / Storage queue (Azure) | Ingest job messages (job ID only) | Carries document content |

**External dependencies:** Azure AI Foundry (chat and embedding deployments) and Arize AX (OTLP traces). The reranker model is packaged inside the api image, so reranking has no external dependency.

## Chat request flow

One question under the `full` profile makes one index query and up to three Foundry calls, and returns before anything is written to the database.

&#91;embedded content: Chat request sequence · 10 steps, full profile\]

Step 2 runs only when the conversation has history; on a first question the message is used as the query. Reranking and the guardrail run inside the api process, so they add no network hops. Persistence (step 9) and trace export (step 10) happen after the response is sent, keeping them off the user's critical path.

## Ingestion and evaluation flows

Both flows are asynchronous and never block chat; each records its progress in PostgreSQL so the UI can poll it.

**Ingestion (per batch of uploaded files)**

1. The SPA uploads one or more files to `POST /api/documents`. The api stores each file in Blob under `raw/{document_id}/{filename}`, creates a `documents` row (status `uploaded`) and one `ingest_jobs` row, then puts a message containing only the job ID on the queue. It returns `202` with the job ID.
2. The worker receives the message (KEDA wakes the Container Apps job on Azure). It sets the job to `running`.
3. For each document: load with the format-specific loader; derive metadata from the folder and file name (doc\_type, date, week, IDs such as RSK-014 and CR-007); chunk (Markdown by headers then recursive; CSV one row per chunk; PDF by page then recursive, tables kept whole when they fit).
4. Embed chunks in batches on the Foundry embedding deployment, then upsert into the retrieval index with deterministic chunk IDs (`{document_id}:{chunk_no}`), so re-ingesting a document replaces its chunks.
5. Update counters (`documents_done`, `chunks_written`) as it goes; on success set the job to `succeeded`, on error record the message and set `failed`. The queue message is deleted only after the status is written; a crash makes the message visible again after 5 minutes.
6. The SPA polls `GET /api/ingest-jobs/{id}` every 3 seconds.

**Evaluation (per run)**

1. Start with `docker compose run eval --profile full` locally, or by triggering the Container Apps job on Azure. A run takes one or more profiles and an optional split (`tune` or `test`).
2. The runner creates an `eval_runs` row, loads `golden_set.json`, and for each question calls `POST /api/chat` with the profile and any chat history. Calls run with a concurrency of 4.
3. Retrieval metrics are computed from the stage trace in the response (ranked chunk text vs. evidence snippets, with the normalization rule from the golden set README). Key-fact, abstention and trap checks run locally. Ragas metrics run against the Foundry chat deployment as judge.
4. Per-question results go to `eval_results`; aggregates per category and overall go to the `eval_runs` row. The run is also logged to Arize AX as an experiment.
5. The SPA's evaluation page compares runs side by side.

## API surface

The api exposes 13 JSON endpoints under `/api`; the SPA and the eval runner use the same contract, and the LLD defines the exact Pydantic models.

| Method and path | Purpose | Response |
| --- | --- | --- |
| `POST /api/chat` | Ask a question within a conversation, under a profile | `200` answer, citations and stage trace |
| `GET /api/conversations/{id}` | Reload a conversation with its turns | `200` |
| `POST /api/turns/{id}/feedback` | Thumbs up or down, optional comment | `204` |
| `GET /api/profiles` | List config profiles and their toggles for the UI | `200` |
| `GET /api/chunks/{chunk_id}` | Full chunk text and metadata, for a clicked citation | `200` |
| `POST /api/documents` | Upload files (multipart) and start an ingest job | `202` job ID and document IDs |
| `GET /api/documents` | List documents with status and chunk counts | `200` |
| `GET /api/ingest-jobs/{id}` | Ingest job progress | `200` |
| `GET /api/eval-runs` | List evaluation runs with headline metrics | `200` |
| `GET /api/eval-runs/{id}` | One run: aggregates per category and overall | `200` |
| `GET /api/eval-runs/{id}/results` | Per-question results | `200` |
| `GET /api/health` | Liveness | `200` |
| `GET /api/ready` | Readiness: index, database, queue and Foundry reachable | `200` or `503` |

**`POST /api/chat` request:** `conversation_id` (optional; new conversation if absent), `message`, `profile` (default `full`), optional `overrides` for individual toggles (`rewrite`, `hybrid`, `rerank`, `guardrail`), and `debug` (adds per-leg scores).

**`POST /api/chat` response:**

- `conversation_id`, `turn_id`, `trace_id` (links to Arize AX), `latency_ms`.
- `answer` (Markdown with inline markers like \[1\]), `abstained` (true when the guardrail blocked generation), optional `conflict_note` when sources disagree.
- `citations`: marker number, chunk ID, document ID, source file, section, and a short supporting quote.
- `stages`: one object per stage that ran, each with `ms` and its outputs. Rewrite returns the standalone query. Retrieve returns candidates with dense, keyword and fused scores and ranks. Rerank returns the kept chunks with rerank scores. Guardrail returns top score, threshold and pass or fail. Generate returns model, input tokens and output tokens.

**Conventions:** errors use RFC 7807 problem details; every response carries an `X-Trace-Id` header; chat requests time out at 30 seconds; no versioning prefix in version 1.

## Data model

PostgreSQL holds eight tables in one `app` schema; the retrieval index holds one chunk record per chunk; Blob holds the original files.

**PostgreSQL tables**

| Table | Key fields | Written by |
| --- | --- | --- |
| `documents` | id, filename, blob\_path, doc\_type, doc\_date, week, content\_hash, status, chunk\_count, created\_at | api (create), worker (status, counts) |
| `ingest_jobs` | id, status (queued, running, succeeded, failed), documents\_total, documents\_done, chunks\_written, error, started\_at, finished\_at | api (create), worker (progress) |
| `conversations` | id, profile, created\_at | api |
| `turns` | id, conversation\_id, user\_message, standalone\_query, answer, abstained, conflict\_note, latency\_ms, input\_tokens, output\_tokens, trace\_id, created\_at | api |
| `turn_stages` | turn\_id, stage, ms, payload (JSONB: candidates, scores, threshold) | api |
| `feedback` | turn\_id, rating, comment, created\_at | api |
| `eval_runs` | id, profile, split, git\_sha, config\_hash, model\_deployments, status, aggregates (JSONB), started\_at, finished\_at | eval |
| `eval_results` | run\_id, question\_id, category, answer, abstained, retrieved\_ranked (JSONB), hit\_at\_5, recall\_at\_5, mrr, ndcg\_at\_5, key\_facts\_pass, faithfulness, answer\_relevance, answer\_correctness, latency\_ms, cost\_usd | eval |

Schema migrations are managed with Alembic and run by the api on startup.

**Retrieval index record (one per chunk)**

| Field | Purpose |
| --- | --- |
| `chunk_id` | `{document_id}:{chunk_no}`, deterministic for idempotent re-ingest |
| `text` | Chunk text sent to the reranker and the model |
| `dense_vector` | Foundry embedding |
| keyword terms | Qdrant sparse vector (BM25-style) or AI Search full-text field |
| `document_id`, `source`, `section` | Citation display and grouping |
| `doc_type`, `doc_date`, `week` | Metadata filters and recency handling |
| `ids` | Item IDs found in the chunk (RSK-014, CR-007), for exact matching and boosting |

**Blob layout:** `raw/{document_id}/{filename}` for uploads, `eval/golden_set.json` for the golden set, `eval/runs/{run_id}/` for run artifacts.

## Retrieval and ranking design

The pipeline runs up to six stages in a fixed order; a profile decides which run, and every stage writes its outputs to the stage trace.

| Stage | Behavior | Key parameters (defaults) |
| --- | --- | --- |
| 1. Rewrite | With chat history, the chat model condenses the message into a standalone query; without history it passes through unchanged. Optional multi-query or HyDE expansion | `history_turns` 6, `expansion` none |
| 2. Filter | Rule-based parser (no LLM) extracts week numbers, ISO dates and item IDs from the query and turns them into index filters or boosts | on in `full` |
| 3. Retrieve | Embed the query on Foundry; run store-native dense and keyword queries and fuse them with weighted RRF in the api; queries containing an item ID give the keyword leg extra weight | `k_candidates` 30, `rrf_k` 60, weights 0.5 / 0.5, ID keyword weight 0.7 |
| 4. Rerank | bge-reranker-base scores each (query, chunk) pair; scores are normalized to 0–1 with a sigmoid; an optional recency boost favors newer documents; keep the top N | `top_n` 5, `recency_boost` 0.05 |
| 5. Guardrail | If the best rerank score is below the threshold, return a fixed "not found in the documents" answer and skip generation | `threshold` 0.20, tuned on the tune split |
| 6. Generate | Build context from the kept chunks (each labeled with source, section and date), within a token budget; call the chat model with structured output | `max_context_tokens` 3,000, temperature 0 |

**Generation contract.** The model returns `answer`, `citations` (marker, chunk ID, short quote), `conflict_note` and `insufficient_evidence`. The api checks that every cited chunk ID was in the context; if not, it retries once, then drops invalid citations. If the model sets `insufficient_evidence`, the turn is recorded as abstained. The system prompt requires citing every claim, preferring the most recent dated source when sources disagree, and saying so in `conflict_note`.

**Profiles**

| Profile | Rewrite | Filter | Hybrid | Rerank | Guardrail | Recency boost |
| --- | --- | --- | --- | --- | --- | --- |
| `baseline` | Off | Off | Off (dense only, top 5) | Off | Off | Off |
| `hybrid` | Off | Off | On | Off | Off | Off |
| `rerank` | Off | Off | On | On | Off | Off |
| `full` | On | On | On | On | On | On |

The UI toggles map to `overrides` on top of a profile, so any combination can be tried live; eval runs use named profiles only, so results stay reproducible.

## Security and identity

No secret or token ever reaches the browser in either environment; locally secrets live in one `.env` file, and on Azure Managed Identity replaces every secret except the Arize API key, held in Key Vault.

| Concern | Local (version 1) | Azure (target state) |
| --- | --- | --- |
| User sign-in | None; single user on localhost | Container Apps built-in auth with Entra ID on web; session cookie only |
| User identity in the api | Fixed `local-user` | Signed-in user from the `X-MS-CLIENT-PRINCIPAL` header, injected by the platform and trusted only on internal ingress |
| Service to Foundry | API key from `.env` | User-assigned Managed Identity, Cognitive Services OpenAI User role |
| Service to index, database, storage | Compose network; local passwords in `.env` | Managed Identity: Search Index Data Contributor (worker), Reader (api); Entra auth to PostgreSQL; Storage Blob and Queue data roles |
| Ingress | Only nginx published, on port 8080 | web external; api internal only; worker and eval have no ingress |
| Secrets | `.env`, excluded from git; `.env.example` committed | Key Vault for the Arize API key only, referenced as a Container Apps secret |
| Data in traces | Synthetic corpus, no masking | Span masking for chunk text before any real corpus |
| Upload safety | Allowed types .md, .pdf, .csv; 20 MB per file | Same, plus per-user rate limit |

The api never takes user identity or scope from request bodies; on Azure it reads identity only from the platform header.

## Observability

Every chat turn produces one OpenInference trace in Arize AX, with one span per pipeline stage, linked to the turn by `trace_id`.

| Span | OpenInference kind | Key attributes |
| --- | --- | --- |
| `chat` (root) | CHAIN | input and output value, `session.id` (conversation), `user.id`, `app.profile`, `app.turn_id`, `app.abstained`, total latency |
| `rewrite` | LLM | prompt, standalone query, model name, token counts |
| `filter` | CHAIN | extracted weeks, dates and IDs; filters applied |
| `retrieve` | RETRIEVER | query, candidate documents with dense, keyword and fused scores |
| `embed_query` (child of retrieve) | EMBEDDING | model name, token count |
| `rerank` | RERANKER | input and output documents with scores, `top_n`, model name |
| `guardrail` | CHAIN | `app.guardrail.top_score`, `app.guardrail.threshold`, passed |
| `generate` | LLM | messages, structured output, model name, token counts, citation validity |

**Instrumentation:** `openinference-instrumentation-langchain` auto-instruments LangChain calls; custom stages (filter, guardrail) use manual spans with the same tracer. Export is OTLP to Arize AX, with the project name per environment (`askpmo-local`, `askpmo-azure`).

**Other telemetry:** ingest jobs produce a trace per job with a span per document. Eval runs log to Arize AX as experiments, with per-question scores as evaluation labels. All services write structured JSON logs carrying `trace_id`; on Azure they go to Log Analytics. Thumbs-down feedback is attached to the trace as an annotation, so poor answers can be filtered in Arize.

## Deployment topology

Three images are built from one repository (web, api, worker; eval reuses the worker image with a different command) and run unchanged in both environments; only configuration and adapters differ.

| Component | Local: Docker Compose service | Azure: target resource |
| --- | --- | --- |
| web | `web`, nginx, port 8080 published | Container App, external ingress, built-in auth, min 0 / max 2 replicas |
| api | `api`, port 8000 on the Compose network | Container App, internal ingress, min 1 / max 3 replicas (min 1 avoids reranker cold start), 2 vCPU / 4 GiB |
| worker | `worker`, polls the Azurite queue | Container Apps job, event-driven, KEDA Azure Queue scaler |
| eval | `eval`, run on demand with `docker compose run` | Container Apps job, manual trigger or schedule |
| Retrieval index | `qdrant` with a named volume | Azure AI Search, Basic tier (SKU to confirm) |
| Database | `postgres` 16 with a named volume | Azure Database for PostgreSQL Flexible Server, Burstable tier |
| Blob and queue | `azurite` with a named volume | Storage account (Blob + Queue) |
| Images | Built locally | Azure Container Registry, pulled by Managed Identity |
| Logs | `docker compose logs` | Log Analytics workspace |
| Secrets | `.env` | Key Vault (Arize key) |

**Environment adapters.** The code selects implementations by setting: `INDEX_BACKEND` (qdrant or aisearch), `STORAGE_BACKEND` (azurite connection string or account URL with Managed Identity), `AUTH_MODE` (none or platform). Everything else, including the pipeline and prompts, is identical.

**Infrastructure as code.** Local uses `docker-compose.yml` with a `make up` wrapper. Azure uses Bicep modules (environment, apps, jobs, data services, identity and role assignments) deployed by a GitHub Actions workflow; the Azure phase comes after version 1.

## Non-functional design

The full pipeline is budgeted at about 5 seconds against the 6-second p95 target, with generation taking most of it.

| Stage | Budget (p95) | Notes |
| --- | --- | --- |
| Rewrite | 800 ms | Skipped on first turns (no history), so most single questions spend 0 ms here |
| Filter, embed and hybrid search | 300 ms | One embedding call plus one index query |
| Rerank (30 pairs) | 600 ms | CPU, batch of 30; falls back to a smaller cross-encoder if over budget |
| Generate | 3,000 ms | About 3,500 input and 400 output tokens |
| API, persistence and network | 300 ms | Stage trace written after the response is sent |
| **Total** | **about 5,000 ms** | Retrieval plus rerank about 900 ms, inside the 1.5-second target |

**Cost per query.** About 4,300 input and 450 output tokens across rewrite and generate. With gpt-5-mini at list price this is roughly $0.002 per query (approximate, from public pricing; confirm when the model is chosen). Any model up to about 10 times that price still meets the $0.02 target. A 45-question eval run with Ragas judging is estimated at well under $1.

**Failure handling**

- Foundry rate limits or timeouts: 3 retries with exponential backoff and jitter, then a `503` with a problem detail; the turn is still recorded with the error.
- Index or database unavailable: `/api/ready` reports `503`, the SPA shows a banner, and chat returns `503` rather than an ungrounded answer.
- Invalid citations from the model: one retry, then invalid citations are dropped and the turn is flagged in the trace.
- Worker crash mid-job: the queue message reappears after 5 minutes; deterministic chunk IDs make re-processing idempotent.
- Eval interruption: runs are resumable and skip questions that already have results.

**Scaling.** Version 1 serves one user. On Azure, web scales 0–2 replicas on HTTP concurrency, api 1–3, and the ingest job scales on queue length; the index and database are single instances.

## Evaluation design

Evaluation is a first-class component: every profile is scored on the same 45 questions, and a release or cutover is blocked until the targets hold on the held-out test split.

**Splits.** The golden set is split once, with a fixed seed and stratified by category, into 35 `tune` questions and 10 `test` questions. Thresholds and weights are tuned only on `tune`; release gates are checked on `test` and on all 45.

**Metrics computed per question**

- Retrieval, from the reranked list in the stage trace (or the retrieved list when rerank is off): Hit@5, Recall@5, MRR, nDCG@5. A chunk is relevant if it contains any evidence snippet after normalization.
- Answer checks, without an LLM: all `key_facts` present; abstained correctly on unanswerable questions; trap avoided (the answer does not contain the trap value for recency and distractor questions).
- Ragas, with the Foundry chat deployment as judge: faithfulness, answer relevance, answer correctness against `reference_answer`.
- Operations: latency and estimated cost from token counts.

**Release gates** (from the PRD): Hit@5 ≥ 0.90, Recall@5 ≥ 0.80, MRR ≥ 0.75, nDCG@5 ≥ 0.75, key facts on 85% of answerable questions, faithfulness ≥ 0.90, answer relevance ≥ 0.85, correctness ≥ 0.80, 3 of 3 correct abstentions, false abstention ≤ 5%, 100% trap avoidance, p95 latency under 6 seconds.

**Backend parity check (before Azure cutover).** Run the `full` profile against Qdrant and against Azure AI Search on the same corpus. Cutover requires every retrieval metric within 0.03 of the Qdrant baseline and no new failures on recency or exact-ID questions.

**Reproducibility.** Each run stores the git SHA, a hash of the resolved config, model deployment names and versions, and the golden set version. Temperature is 0 for generation and judging.

## Architecture decision records

Fourteen decisions shape the design; five are accepted from your direction, one remains open, and the rest are proposed for your review before the LLD.

| ADR | Topic | Decision | Status |
| --- | --- | --- | --- |
| ADR-001 | Front end | React SPA over a FastAPI API | Accepted |
| ADR-002 | API shape | One FastAPI service on internal ingress, no separate BFF | Proposed |
| ADR-003 | Session model | Container Apps built-in auth with Entra ID; no sign-in locally | Proposed |
| ADR-004 | Chat path | Synchronous request; queue reserved for ingestion | Proposed |
| ADR-005 | Orchestration | LangChain (LCEL), versions pinned | Accepted |
| ADR-006 | Retrieval index | One retriever interface: Qdrant locally, Azure AI Search on Azure | Proposed |
| ADR-007 | Hybrid fusion | Store-native dense and keyword legs, fused by weighted RRF in the api | Proposed |
| ADR-008 | Reranking | bge-reranker-base in the api process | Proposed |
| ADR-009 | Embeddings | Foundry embedding deployment in both environments | Proposed |
| ADR-009a | Chat model | Foundry deployment named per profile; model (gpt-5-mini vs. a Claude model on Foundry) not chosen | Open |
| ADR-010 | App database | PostgreSQL (container locally, Flexible Server on Azure) | Proposed |
| ADR-011 | Ingestion trigger | Queue worker: Azurite locally, Storage Queue with KEDA on Azure | Accepted |
| ADR-012 | Tracing | Arize AX via OpenTelemetry (OpenInference) | Accepted |
| ADR-013 | Configuration | YAML profiles (baseline, hybrid, rerank, full) with per-request overrides | Proposed |
| ADR-014 | Deployment | Docker Compose locally for version 1; Azure Container Apps as target state | Accepted |

Each ADR is written up in full in the repository (`docs/adr/`) during the LLD, using the context, decision, consequences format.

## Open items and handoff to the LLD

The LLD can start now; none of the open items below blocks version 1, because each sits behind a config value or an adapter.

**Open items**

- [ ] Confirm or change the proposed ADRs (002–004, 006–010, 013).
- [ ] Choose the Foundry chat model (ADR-009a) and confirm quota in the chosen region.
- [ ] Pick the PDF table parser after comparing pypdf, pdfplumber and docling on the two finance PDFs.
- [ ] Confirm Azure region, AI Search tier and PostgreSQL tier before the Azure phase.

**What the LLD will define**

1. Repository layout and module boundaries for web, api, worker and eval.
2. Pydantic models for every endpoint, SQL DDL and Alembic migrations, and index schemas for Qdrant and AI Search.
3. Prompts (rewrite, generate, judge) and the structured-output schema.
4. YAML profile files and the settings model, with all defaults from this HLD.
5. Interfaces for the environment adapters (index, storage, auth) and their two implementations.
6. Test plan: unit, contract (retriever parity), integration with Docker Compose, and golden-set gates.
7. Pinned versions of packages, models and container images.
8. The phased build plan for Claude Code, with acceptance criteria per phase taken from the release gates.
