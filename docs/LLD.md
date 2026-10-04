# LLD – askPMO (RAG)

Oct 3, 2026 · @Gopinath Dhayanandamurthy

## Purpose and prerequisites

This LLD is the build specification Claude Code works from: it fixes file layout, interfaces, schemas, algorithms, prompts and a phased plan with acceptance gates, so the build needs almost no decisions from you.

**How Claude Code should use it**

- Treat the PRD for *why*, the HLD for *what*, and this LLD for *how*. Where this LLD is silent, follow the HLD; where they conflict, this LLD wins and the conflict is logged in `docs/decisions-log.md`.
- Build phase by phase (last section). A phase is done only when its gate passes; Claude Code runs the gate commands itself.
- Ask the human only for the prerequisites below, or when a gate fails twice for reasons outside the code (quota, credentials).

**One refinement to the HLD.** Hybrid retrieval issues the dense and keyword legs as two store-native queries and fuses them with weighted RRF in the api. This keeps per-leg scores visible on every request, supports the item-ID weighting identically on Qdrant and Azure AI Search, and costs about 20 ms. ADR-007 is updated accordingly.

**Prerequisites you must supply** (in `.env`, never committed)

| Item | Example | Used by |
| --- | --- | --- |
| Foundry endpoint | `https://<resource>.openai.azure.com/` | api, worker, eval |
| Foundry API key | — | api, worker, eval (local only) |
| Chat deployment name | `gpt-5-mini` | api, eval (judge) |
| Embedding deployment name and dimensions | `text-embedding-3-small`, 1536 | api, worker |
| Arize space ID and API key | — | all services |
| Docker Desktop, Git, GitHub repo URL | — | Claude Code |

## Repository layout

One monorepo with a shared Python package (`pmo_core`) used by api, worker and eval, plus a separate `web` app; services stay thin and all logic lives in `pmo_core`.

```
askpmo/
├── CLAUDE.md                      # build instructions for Claude Code
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── pyproject.toml                 # uv workspace root
├── config/
│   ├── profiles/                  # baseline.yaml, hybrid.yaml, rerank.yaml, full.yaml
│   └── prompts/                   # rewrite.md, generate.md
├── corpus/                        # Project Atlas documents (seed data)
├── eval/
│   ├── golden_set.json
│   └── splits.json                # tune / test question IDs (generated once, committed)
├── packages/
│   └── pmo_core/
│       └── src/pmo_core/
│           ├── settings.py        # Pydantic settings + profile loader
│           ├── models.py          # domain dataclasses: Chunk, Candidate, StageTrace
│           ├── db/                # SQLAlchemy models, session, alembic/
│           ├── adapters/
│           │   ├── index_qdrant.py
│           │   ├── index_aisearch.py  # Azure phase
│           │   ├── storage_azure.py   # Blob + Queue (Azurite or Azure)
│           │   └── llm.py             # chat model + embeddings factory
│           ├── ingest/            # loaders.py, metadata.py, chunkers.py, pipeline.py
│           ├── query/             # filter.py, retrieve.py, fusion.py, rerank.py,
│           │                      # guardrail.py, context.py, generate.py, pipeline.py
│           ├── evaluation/        # metrics.py, normalize.py, ragas_eval.py, runner.py
│           └── telemetry.py       # OpenTelemetry + Arize setup
├── services/
│   ├── api/                       # FastAPI app: main.py, routers/, deps.py, Dockerfile
│   ├── worker/                    # main.py (queue loop), Dockerfile (also runs eval)
│   └── eval/                      # main.py (CLI entry point)
├── web/                           # React + Vite + TypeScript
│   ├── src/{pages,components,api,hooks}/
│   ├── nginx.conf
│   └── Dockerfile
├── tests/                         # unit/, contract/, integration/
├── infra/azure/                   # Bicep modules (Azure phase)
└── docs/
    ├── adr/                       # ADR-001 … ADR-014
    └── decisions-log.md
```

## Toolchain and dependencies

Claude Code resolves the latest stable release of each package at scaffold time and locks it (`uv.lock`, `package-lock.json`); the table gives the required major versions and the reason each package is there.

| Area | Package or tool | Version constraint | Purpose |
| --- | --- | --- | --- |
| Python | CPython, uv | 3.11.x; latest uv | Runtime; workspace and lockfile |
| API | fastapi, uvicorn, pydantic, pydantic-settings | Pydantic 2.x | HTTP layer and settings |
| Orchestration | langchain-core, langchain, langchain-classic | 1.x | LCEL, history-aware retriever, multi-query |
| Models | langchain-openai | 1.x | `AzureChatOpenAI`, `AzureOpenAIEmbeddings` against Foundry |
| Models (alternative) | langchain-azure-ai | latest | Only if a non-OpenAI Foundry model (e.g. Claude) is chosen |
| Index | qdrant-client, fastembed | qdrant-client 1.x | Dense and sparse (BM25) vectors, Query API |
| Rerank | sentence-transformers, torch (CPU wheel) | latest stable | `CrossEncoder` for bge-reranker-base |
| Loaders | pdfplumber, unstructured (markdown extra) | latest | PDF text and tables; Markdown |
| Storage | azure-storage-blob, azure-storage-queue, azure-identity | 12.x | Azurite and Azure via one client |
| Database | sqlalchemy, alembic, psycopg\[binary\] | SQLAlchemy 2.x, psycopg 3 | ORM, migrations, driver |
| Evaluation | ragas | latest stable | Faithfulness, relevance, correctness |
| Telemetry | arize-otel, openinference-instrumentation-langchain | latest | OTLP export to Arize AX |
| Tokens | tiktoken | latest | Context budget (o200k\_base encoding) |
| Quality | pytest, pytest-asyncio, ruff, mypy | latest | Tests, lint, types |
| Web | Node 20 LTS, React, Vite, TypeScript | React 18+, TS 5 | SPA |
| Web libraries | @tanstack/react-query, react-router, tailwindcss, openapi-typescript | latest | Server state, routing, styling, typed API client |
| Containers | postgres, qdrant/qdrant, mcr.microsoft.com/azure-storage/azurite, nginx | postgres 16; pinned tags | Local infrastructure |

The reranker model `BAAI/bge-reranker-base` is downloaded during the api image build, so containers start without network access to Hugging Face.

## Configuration

Environment variables describe *where* things are; YAML profiles describe *how* the pipeline behaves. Both load into one Pydantic `Settings` object, validated at startup so a bad value fails fast.

**Environment variables (`.env.example`)**

```bash
# Environment adapters
APP_ENV=local                      # local | azure
AUTH_MODE=none                     # none | platform
INDEX_BACKEND=qdrant               # qdrant | aisearch
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=pmo_chunks
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=<azurite-default>;BlobEndpoint=http://azurite:10000/devstoreaccount1;QueueEndpoint=http://azurite:10001/devstoreaccount1;
BLOB_CONTAINER=pmo
INGEST_QUEUE=ingest-jobs
DATABASE_URL=postgresql+psycopg://pmo:pmo@postgres:5432/pmo

# Azure AI Foundry
FOUNDRY_ENDPOINT=
FOUNDRY_API_KEY=
FOUNDRY_API_VERSION=2024-10-21
CHAT_PROVIDER=azure_openai         # azure_openai | azure_ai_inference
CHAT_DEPLOYMENT=gpt-5-mini
JUDGE_DEPLOYMENT=gpt-5-mini
EMBEDDING_DEPLOYMENT=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Arize AX
ARIZE_SPACE_ID=
ARIZE_API_KEY=
ARIZE_PROJECT_NAME=askpmo-local

# Runtime
DEFAULT_PROFILE=full
RERANKER_MODEL=BAAI/bge-reranker-base
LOG_LEVEL=INFO
```

**Profile schema (`config/profiles/full.yaml`)**

```yaml
name: full
rewrite:   { enabled: true,  history_turns: 6, expansion: none }   # none | multi_query | hyde
filter:    { enabled: true }
retrieve:
  hybrid: true                 # false = dense leg only
  k_candidates: 30
  rrf_k: 60
  weights: { dense: 0.5, keyword: 0.5 }
  id_keyword_weight: 0.7       # keyword weight when the query contains an item ID
rerank:    { enabled: true, top_n: 5, recency_boost: 0.05, batch_size: 32 }
guardrail: { enabled: true, threshold: 0.20 }
generate:  { max_context_tokens: 3000, temperature: 0.0, max_output_tokens: 800 }
```

The other three profiles override only what differs from this file: `baseline` (rewrite, filter, hybrid, rerank and guardrail off; final top 5 taken from the dense leg), `hybrid` (hybrid on, rerank off, final top 5 from fusion), `rerank` (hybrid and rerank on; rewrite, filter, guardrail and recency off). Per-request `overrides` can only flip the `enabled` and `hybrid` flags, never numeric parameters.

## Core interfaces and adapters

Three protocols isolate everything that differs between local and Azure; the pipeline code depends only on these and on the domain types.

```python
# pmo_core/models.py
@dataclass(frozen=True)
class Chunk:
    chunk_id: str            # "{document_id}:{chunk_no}"
    document_id: str
    text: str                # includes the contextual header line
    source: str              # original filename
    section: str             # header path, "page 3", or RAID row ID
    doc_type: str
    doc_date: date | None
    week: int | None
    ids: tuple[str, ...]     # item IDs found in the text

@dataclass
class Candidate:
    chunk: Chunk
    dense_score: float | None = None
    keyword_score: float | None = None
    dense_rank: int | None = None
    keyword_rank: int | None = None
    fused_score: float | None = None
    rerank_score: float | None = None    # sigmoid-normalized, 0..1
    final_score: float | None = None     # rerank + recency boost

@dataclass
class StageTrace:
    stage: str               # rewrite | filter | retrieve | rerank | guardrail | generate
    ms: int
    payload: dict[str, Any]  # serialized into turn_stages.payload and the API response

@dataclass(frozen=True)
class IndexFilter:
    weeks: tuple[int, ...] = ()
    dates: tuple[date, ...] = ()
    doc_types: tuple[str, ...] = ()

# pmo_core/adapters/base.py
class IndexBackend(Protocol):
    def ensure_schema(self) -> None: ...
    def upsert(self, chunks: Sequence[Chunk], dense: Sequence[list[float]]) -> None: ...
    def delete_document(self, document_id: str) -> None: ...
    def dense_search(self, vector: list[float], k: int, flt: IndexFilter) -> list[Candidate]: ...
    def keyword_search(self, query: str, k: int, flt: IndexFilter) -> list[Candidate]: ...
    def get_chunk(self, chunk_id: str) -> Chunk | None: ...
    def count(self) -> int: ...

class BlobStore(Protocol):
    def put(self, path: str, data: bytes, content_type: str) -> None: ...
    def get(self, path: str) -> bytes: ...

class JobQueue(Protocol):
    def send(self, job_id: str) -> None: ...
    def receive(self, visibility_timeout_s: int = 300) -> QueueMessage | None: ...
    def delete(self, msg: QueueMessage) -> None: ...
```

**Implementations.** `QdrantIndex` stores a named dense vector and a sparse `bm25` vector (fastembed `Qdrant/bm25`, IDF modifier on the collection) and computes the sparse query vector itself. `AISearchIndex` (Azure phase) maps `keyword_search` to a full-text query and `dense_search` to a vector query. `AzureStorage` implements both `BlobStore` and `JobQueue` and works against Azurite or Azure, depending on whether a connection string or an account URL with `DefaultAzureCredential` is configured.

**Model factory (`adapters/llm.py`).** `get_chat_model(deployment)` returns `AzureChatOpenAI` when `CHAT_PROVIDER=azure_openai`, otherwise the Azure AI Inference chat model. For reasoning models (gpt-5 family, o-series) it omits `temperature`, because those models reject it, and records that in the stage trace. `get_embeddings()` returns `AzureOpenAIEmbeddings` with the configured dimensions. Both use the API key locally and `DefaultAzureCredential` on Azure.

**Dependency wiring.** A single `Container` object built from `Settings` creates adapters once per process and is injected through FastAPI dependencies (api) or passed explicitly (worker, eval). Tests replace adapters with in-memory fakes.

## API models

These Pydantic models are the contract for the SPA and the eval runner; the OpenAPI schema generated from them feeds the TypeScript client, so they are written first and changed deliberately.

```python
# services/api/schemas.py
class Toggles(BaseModel):
    rewrite: bool | None = None
    filter: bool | None = None
    hybrid: bool | None = None
    rerank: bool | None = None
    guardrail: bool | None = None

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    history: list[HistoryMessage] | None = None   # eval only; ignored when conversation_id is set
    profile: Literal["baseline", "hybrid", "rerank", "full"] = "full"
    overrides: Toggles = Toggles()
    debug: bool = False

class Citation(BaseModel):
    marker: int
    chunk_id: str
    document_id: UUID
    source: str
    section: str
    quote: str

class CandidateOut(BaseModel):
    chunk_id: str
    source: str
    section: str
    preview: str                 # first 200 characters
    dense_score: float | None
    keyword_score: float | None
    fused_score: float | None
    rerank_score: float | None
    final_score: float | None
    rank: int

class StageOut(BaseModel):
    stage: str
    ms: int
    data: dict[str, Any]         # stage-specific, documented below

class ChatResponse(BaseModel):
    conversation_id: UUID
    turn_id: UUID
    trace_id: str
    answer: str
    abstained: bool
    conflict_note: str | None
    citations: list[Citation]
    stages: list[StageOut]
    latency_ms: int
```

**Stage `data` contents.** `rewrite`: `standalone_query`, `skipped`. `filter`: `weeks`, `dates`, `ids`, `applied`. `retrieve`: `candidates` (list of `CandidateOut`, top 30), `legs` (dense, keyword). `rerank`: `kept` (top N `CandidateOut`), `model`. `guardrail`: `top_score`, `threshold`, `passed`. `generate`: `deployment`, `input_tokens`, `output_tokens`, `invalid_citations`, `retried`.

**Other models:** `ProfileOut` (name and resolved toggles), `DocumentOut`, `IngestJobOut` (status and counters), `UploadResponse` (job\_id, document\_ids), `EvalRunOut` (headline aggregates), `EvalRunDetail` (aggregates by category), `EvalResultOut` (one row of `eval_results`), `FeedbackIn` (rating `up` or `down`, optional comment up to 1,000 characters). Errors follow RFC 7807 through one exception handler.

## Database DDL and index schemas

The first Alembic migration creates exactly this schema; later changes go through new migrations, never edits to this one.

```sql
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.documents (
  id            uuid PRIMARY KEY,
  filename      text NOT NULL,
  rel_path      text NOT NULL,            -- e.g. 02_status_reports/status_report_wk06_2026-02-20.md
  blob_path     text NOT NULL,
  doc_type      text,
  doc_date      date,
  week          int,
  content_hash  text NOT NULL,
  status        text NOT NULL CHECK (status IN ('uploaded','indexed','failed')),
  chunk_count   int  NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rel_path)                       -- re-upload replaces the same document
);

CREATE TABLE app.ingest_jobs (
  id               uuid PRIMARY KEY,
  status           text NOT NULL CHECK (status IN ('queued','running','succeeded','failed')),
  document_ids     uuid[] NOT NULL,
  documents_done   int NOT NULL DEFAULT 0,
  chunks_written   int NOT NULL DEFAULT 0,
  error            text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  started_at       timestamptz,
  finished_at      timestamptz
);

CREATE TABLE app.conversations (
  id          uuid PRIMARY KEY,
  profile     text NOT NULL,
  user_id     text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.turns (
  id                uuid PRIMARY KEY,
  conversation_id   uuid NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
  seq               int  NOT NULL,
  user_message      text NOT NULL,
  standalone_query  text,
  answer            text NOT NULL,
  abstained         boolean NOT NULL,
  conflict_note     text,
  citations         jsonb NOT NULL DEFAULT '[]',
  profile           text NOT NULL,
  toggles           jsonb NOT NULL,
  latency_ms        int NOT NULL,
  input_tokens      int,
  output_tokens     int,
  trace_id          text,
  error             text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, seq)
);

CREATE TABLE app.turn_stages (
  turn_id  uuid NOT NULL REFERENCES app.turns(id) ON DELETE CASCADE,
  stage    text NOT NULL,
  ms       int  NOT NULL,
  payload  jsonb NOT NULL,
  PRIMARY KEY (turn_id, stage)
);

CREATE TABLE app.feedback (
  turn_id     uuid PRIMARY KEY REFERENCES app.turns(id) ON DELETE CASCADE,
  rating      text NOT NULL CHECK (rating IN ('up','down')),
  comment     text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.eval_runs (
  id                 uuid PRIMARY KEY,
  profile            text NOT NULL,
  split              text NOT NULL CHECK (split IN ('tune','test','all')),
  git_sha            text NOT NULL,
  config_hash        text NOT NULL,
  golden_version     text NOT NULL,
  model_deployments  jsonb NOT NULL,
  status             text NOT NULL CHECK (status IN ('running','succeeded','failed')),
  aggregates         jsonb,              -- overall and per category
  started_at         timestamptz NOT NULL DEFAULT now(),
  finished_at        timestamptz
);

CREATE TABLE app.eval_results (
  run_id              uuid NOT NULL REFERENCES app.eval_runs(id) ON DELETE CASCADE,
  question_id         text NOT NULL,
  category            text NOT NULL,
  answer              text,
  abstained           boolean,
  retrieved_ranked    jsonb,             -- chunk IDs in final order
  hit_at_5            real, recall_at_5 real, mrr real, ndcg_at_5 real,
  key_facts_pass      boolean,
  abstention_correct  boolean,
  trap_avoided        boolean,
  faithfulness        real, answer_relevance real, answer_correctness real,
  latency_ms          int,
  cost_usd            real,
  error               text,
  PRIMARY KEY (run_id, question_id)
);
```

**Qdrant collection `pmo_chunks`.** Named vector `dense` (size `EMBEDDING_DIMENSIONS`, cosine distance); sparse vector `bm25` with the IDF modifier. Payload fields: `chunk_id`, `document_id`, `text`, `source`, `section`, `doc_type`, `doc_date` (ISO string), `week`, `ids` (list). Payload indexes on `document_id`, `doc_type`, `week` (integer), `doc_date` (datetime) and `ids` (keyword). Point ID is a UUIDv5 derived from `chunk_id`, so upserts are idempotent.

**Azure AI Search index `pmo-chunks` (Azure phase).** `chunk_id` (key), `text` (searchable, English analyzer), `dense` (vector, HNSW, cosine), `document_id`, `source`, `section`, `doc_type`, `week`, `doc_date` (filterable), `ids` (collection, filterable and searchable).

## Ingestion details

Metadata comes from the relative path, the filename and the first lines of the document, with no LLM involved, so ingestion is deterministic and cheap.

**Upload contract.** `POST /api/documents` takes multipart `files[]` plus a parallel `rel_paths[]` (for example `02_status_reports/status_report_wk06_2026-02-20.md`). `make seed` uploads the whole `corpus/` folder this way in one request. Re-uploading the same `rel_path` with the same content hash is skipped; with a different hash it replaces the document's chunks.

**Metadata rules**

| Field | Rule | Example |
| --- | --- | --- |
| `doc_type` | Top folder: 02 → `status_report`, 03 → `raid_log`, 05 → `meeting_minutes`, 07 → `reference`. Folders 01, 04 and 06 use the filename: `charter`, `sow`, `cutover_strategy`, `change_log`, `change_request`, `budget_report`, `resource_plan`. Otherwise `other` | `cutover_strategy_v2.0.md` → `cutover_strategy` |
| `doc_date` | First `YYYY-MM-DD` in the filename; else `YYYY-MM` in the filename as the last day of that month; else the first ISO date in the first 600 characters of extracted text; else null | Charter → 2026-01-14 (approval date in its header) |
| `week` | `_wk(\d{2})_` in the filename | `status_report_wk06_…` → 6 |
| `ids` | Per chunk, regex `\b(?:RSK\|ISS\|ACT\|DEC\|CR)-\d{3}\b`, deduplicated | `RSK-014`, `CR-007` |
| `section` | Markdown header path; `page N` for PDF; item ID for RAID rows | `Top risks and issues` |

**Chunking per format**

- **Markdown:** `MarkdownHeaderTextSplitter` on levels 1–3, then `RecursiveCharacterTextSplitter` (1,200 characters, 150 overlap, separators blank line, newline, space). A Markdown table under 2,400 characters stays in one chunk.
- **CSV (RAID log):** one chunk per row, rendered as labeled text: `RAID item RSK-014 (Risk) | Title: … | Workstream: … | Owner: … | Severity: … | Status: … | Raised: … | Description: … | Mitigation / Resolution: … | Linked: …`.
- **PDF:** pdfplumber per page. Tables become Markdown tables, each its own chunk (split by rows with the header repeated if over 2,400 characters). Remaining page text is chunked like Markdown.
- **Contextual header:** every chunk's text starts with one line, `[{document title} — {section}]`, where the title is the first H1 or, failing that, the filename. This lets both legs match on document identity (for example “week 6”).

**Worker loop.** Receive a message (5-minute visibility). Mark the job `running`. For each document: load, extract metadata, chunk, embed in batches of 64 with retries, call `delete_document` then `upsert`, update `documents` and job counters. Mark `succeeded` or `failed`, then delete the message. A message dequeued more than 3 times marks its job `failed` and is deleted, so poison messages cannot loop forever. The 31-document corpus produces roughly 250–400 chunks; the exact count is logged and asserted in the phase gate as a range, not a fixed number.

## Query pipeline algorithms

Each stage is a pure function of its inputs and the resolved profile, returning its result plus a `StageTrace`; `query/pipeline.py` runs them in order and skips disabled stages.

**1. Rewrite.** If there is no history, `standalone_query = message` and the stage records `skipped: true`. Otherwise the last `history_turns` turns (from the database, or from `request.history` for eval) go to the rewrite prompt. Expansion, when enabled, affects only the dense leg: `multi_query` generates 3 variants, runs a dense search for each and fuses them with plain RRF; `hyde` embeds a generated hypothetical answer instead of the query. The keyword leg always uses the standalone query.

**2. Filter.** Case-insensitive regexes on the standalone query: `\bweek\s*(\d{1,2})\b` gives weeks; `\b(20\d{2}-\d{2}-\d{2})\b` gives dates; the item-ID regex gives IDs. Weeks and dates become an `IndexFilter` (match if `week` is in weeks or `doc_date` is in dates) applied to both legs. If the filtered search returns fewer than 3 candidates, the stage retries without the filter and records `fallback: true`. IDs never filter; they only change fusion weights.

**3. Retrieve.** Embed the query, run `dense_search` and (if hybrid) `keyword_search`, each with `k = k_candidates`. Fuse with weighted Reciprocal Rank Fusion, where a candidate missing from a leg contributes nothing from that leg:

```latex
\mathrm{RRF}(c) = \frac{w_d}{k + r_d(c)} + \frac{w_k}{k + r_k(c)}
```

Defaults: k = 60, w\_d = w\_k = 0.5; when the query contains an item ID, w\_k = `id_keyword_weight` (0.7) and w\_d = 0.3. With hybrid off, candidates are the dense results in dense order. Keep the top `k_candidates` by fused score.

**4. Rerank.** Score (standalone query, chunk text) pairs with `CrossEncoder("BAAI/bge-reranker-base")` in batches of 32; convert logits with a sigmoid to 0–1. Apply the recency boost across dated candidates (undated candidates get no boost), then keep the top `top_n` by final score:

```latex
s_{\text{final}}(c) = s_{\text{rerank}}(c) + \beta \cdot \frac{d(c) - d_{\min}}{d_{\max} - d_{\min}}
```

β is `recency_boost` (0.05); d is the document date. With rerank off, the top `top_n` by fused (or dense) score are kept and rerank scores are null.

**5. Guardrail.** Compare the highest *pre-boost* rerank score among kept chunks with `threshold`. Below it: answer "I couldn't find this in the program documents.", set `abstained = true`, skip generation. The guardrail needs rerank scores, so when rerank is off it is skipped and the trace says so.

**6. Context and generate.** Drop near-duplicates (token Jaccard ≥ 0.9, keep the higher score). Order by final score. Format each chunk as `[n] {source} — {section} — {doc_date or "undated"}` followed by its text. Fit to `max_context_tokens` with tiktoken by dropping the lowest-ranked chunks, then assign markers 1..n in this order. Call the chat model with structured output (next section).

**Citation validation.** A citation is valid when its `chunk_id` is in the context and its marker matches that chunk's number. Every `[n]` in the answer must have a valid citation. On any failure, retry once with the validation errors appended to the prompt; if it still fails, drop invalid citations, strip their markers from the answer, and record `invalid_citations` in the trace. If the model sets `insufficient_evidence`, the turn is stored as abstained, with the model's short explanation as the answer.

## Prompts and structured output

Prompts live as Markdown files in `config/prompts/`, versioned with the code; their file hash is part of `config_hash`, so any prompt change shows up in eval run metadata.

**`rewrite.md`**

```markdown
You rewrite a follow-up question into a standalone search query for a program's document archive.

Rules:
- Resolve pronouns and references ("it", "he", "that risk") using the conversation.
- Keep exact identifiers verbatim: RSK-014, CR-007, ISS-009, week numbers, dates, section numbers.
- Do not answer the question. Do not add facts that are not in the conversation.
- If the question is already standalone, return it unchanged.

Conversation:
{history}

Follow-up question: {question}

Return only the standalone query.
```

**`generate.md` (system message)**

```markdown
You are askPMO, a PMO knowledge assistant. You answer questions about a program using only the numbered sources provided.

Rules:
1. Use only facts stated in the sources. If the sources do not answer the question, set insufficient_evidence to true and say briefly what is missing.
2. Cite every factual sentence with the source marker, like [2]. Cite only sources you actually used.
3. Each source shows its date. When sources disagree, prefer the most recent dated source, answer with the current fact, and explain the change in conflict_note (for example, the charter's date versus the later change request).
4. If a source is about a different project than the question, do not use it.
5. If the question asks about a specific point in time ("in week 3", "as of February"), answer for that time, not the latest value.
6. Be concise: answer first, in 1–4 sentences, then any needed detail. Use exact figures, dates and IDs from the sources.
```

The user message contains the formatted sources followed by `Question: {standalone_query}`.

**Structured output schema** (passed with `with_structured_output`, strict JSON schema)

```python
class CitationOut(BaseModel):
    marker: int
    chunk_id: str
    quote: str = Field(max_length=200, description="Short verbatim span from the source")

class GeneratedAnswer(BaseModel):
    answer: str = Field(description="Markdown answer with [n] markers")
    citations: list[CitationOut]
    conflict_note: str | None = None
    insufficient_evidence: bool = False
```

**Judge prompts** are Ragas defaults, run with `JUDGE_DEPLOYMENT`; they are not customized in version 1, so scores stay comparable with published Ragas behavior.

## Frontend design

The SPA has three pages; the chat page is the demo centerpiece, pairing the conversation with a live view of what every stage did.

| Page | Route | Contents |
| --- | --- | --- |
| Chat | `/` | Left (60%): conversation with Markdown answers, clickable `[n]` citation chips, a "not found" style for abstentions, a conflict-note callout, thumbs up/down per turn. Right (40%): the under-the-hood panel. Top bar: profile selector and five toggles (rewrite, filter, hybrid, rerank, guardrail) |
| Documents | `/documents` | Drag-and-drop upload that preserves folder paths, a documents table (type, date, week, chunks, status), and a progress bar for the active ingest job, polled every 3 seconds |
| Evaluation | `/eval` | Runs list with headline metrics; select two runs to compare overall and per-category metrics side by side, with deltas colored; drill into per-question results with answer, retrieved chunks and pass/fail flags |

**Under-the-hood panel (chat page).** One collapsible card per stage that ran, in order, each showing its milliseconds:

- Rewrite: original vs. standalone query.
- Filter: extracted weeks, dates and IDs; whether a fallback happened.
- Retrieve: a table of the top 30 candidates with dense rank, keyword rank and fused score; chunks later kept by rerank are highlighted.
- Rerank: the kept chunks with horizontal score bars, the recency boost shown as a separate segment.
- Guardrail: top score against the threshold on a small gauge, pass or fail.
- Generate: deployment, token counts, and a link to the trace in Arize AX.

Clicking a citation chip opens a side sheet with the full chunk text (from `GET /api/chunks/{id}`) and its source and section.

**Implementation.** React with TypeScript and Vite; TanStack Query for server state; React Router; Tailwind for styling; `react-markdown` for answers. `web/src/api/schema.d.ts` is generated from the api's OpenAPI document by `openapi-typescript` (`make web-types`), and a thin typed `fetch` wrapper uses it. Toggle state lives in the URL query string, so a configuration can be shared as a link. No authentication code exists in the SPA; on Azure the platform handles sign-in before the SPA loads.

## Evaluation runner

The eval CLI is how Claude Code proves each phase is done: `gate` exits non-zero when any target in `config/gates.yaml` is missed.

```bash
python -m eval split --seed 42                     # once: writes eval/splits.json (35 tune / 10 test, stratified)
python -m eval run --profiles baseline,full --split all --concurrency 4 [--no-ragas] [--resume RUN_ID]
python -m eval compare RUN_A RUN_B                 # prints overall and per-category deltas
python -m eval gate RUN_ID [--phase P4]            # checks thresholds; exit code 1 on failure
```

**Golden set addition.** Add a `forbidden` list to four trap questions, holding values that must not appear in the answer: Q23 `["2026-08-17"]`, Q37 `["2024-09-09"]`, Q38 `["2.9 million", "$2.9"]`, Q40 `["$185", "$175", "$150", "$48", "$40"]``  (Q41 relies on the abstention check) `. Recency questions (Q24–Q28) rely on `key_facts`, because a correct answer may mention the old value as history.

**Metric definitions**

- **Relevance:** a chunk is relevant to a question if its normalized text contains any normalized evidence snippet (strip `**` and `|`, convert en and em dashes to `-`, collapse whitespace, lowercase).
- **Ranking used:** the final order of all candidates (by rerank score when rerank ran, otherwise by fused or dense score), taken from the retrieve and rerank stage data.
- **Hit@5:** 1 if any of the top 5 is relevant. **Recall@5:** share of the question's evidence snippets matched by at least one top-5 chunk. **MRR:** 1 / rank of the first relevant chunk in the top 10, else 0.
- **nDCG@5**, with binary gains and the ideal ranking having min(E, 5) relevant chunks, where E is the number of evidence snippets:

```latex
\mathrm{nDCG@5} = \frac{\sum_{i=1}^{5} \mathrm{rel}_i / \log_2(i+1)}{\sum_{i=1}^{\min(E,5)} 1 / \log_2(i+1)}
```

- Retrieval metrics exclude the three unanswerable questions.
- **Key facts:** every `key_facts` string appears in the normalized answer; numbers also match with thousands separators removed.
- **Abstention correct:** unanswerable questions have `abstained = true`. **False abstention:** an answerable question has `abstained = true`.
- **Trap avoided:** key facts pass and no `forbidden` value appears.
- **Ragas:** faithfulness, response relevancy and answer correctness (use the current Ragas class names), with the judge and embedding deployments from Foundry.
- **Cost:** tokens multiplied by per-deployment prices in `config/prices.yaml`, which you keep current.

**Execution.** Conversational questions send `history` from the golden set. Each question is retried up to twice on `5xx` errors; a question that still fails is recorded with its error and counts as failed in the gates. Results stream to `eval_results` and `eval/runs/{run_id}/results.jsonl`; at the end the runner writes aggregates, a `summary.md` and an Arize AX experiment.

## Observability implementation

One `telemetry.setup(service_name)` call at process start configures tracing for api, worker and eval; every span name and attribute below is a constant in `telemetry.py`, so traces stay consistent across services.

```python
# pmo_core/telemetry.py (outline)
def setup(service_name: str) -> Tracer:
    tracer_provider = arize.otel.register(
        space_id=settings.arize_space_id,
        api_key=settings.arize_api_key,
        project_name=settings.arize_project_name,
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    return tracer_provider.get_tracer(service_name)

@contextmanager
def stage_span(name: str, kind: OpenInferenceSpanKindValues, **attrs): ...
```

**Rules**

- The chat endpoint opens the root `chat` span; each pipeline stage runs inside `stage_span(...)` so LangChain's auto-instrumented LLM, embedding and retriever spans nest under the right stage.
- Retrieve and rerank set OpenInference document attributes (`retrieval.documents.*`, `reranker.input_documents.*`, `reranker.output_documents.*`) with chunk ID, score and the first 500 characters of content.
- Root span attributes: `session.id` (conversation ID), `user.id`, `app.profile`, `app.toggles` (JSON), `app.turn_id`, `app.abstained`, `app.latency_ms`. The `trace_id` (hex) is returned in the response and stored on the turn.
- Feedback calls Arize's annotation API with the stored `trace_id` (label `user_feedback`, value up or down). If that call fails, feedback is still saved and the failure is logged.
- If `ARIZE_API_KEY` is empty, setup installs a no-op tracer and logs one warning, so the app and tests run offline.
- Logs are JSON lines (`structlog`) with `trace_id`, `span_id`, `service` and `level`; no prompt or answer text appears in logs, only in traces.

## Local runtime

`make up` builds and starts everything; `make seed` loads the corpus; `make eval` scores a profile. These three commands are the whole local workflow.

**`docker-compose.yml` (shape; image tags pinned at scaffold time)**

```yaml
services:
  postgres:
    image: postgres:16
    environment: { POSTGRES_USER: pmo, POSTGRES_PASSWORD: pmo, POSTGRES_DB: pmo }
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U pmo"], interval: 5s, retries: 10 }

  qdrant:
    image: qdrant/qdrant:<pinned>
    volumes: [qdrant:/qdrant/storage]

  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:<pinned>
    command: azurite --blobHost 0.0.0.0 --queueHost 0.0.0.0 --skipApiVersionCheck --loose
    volumes: [azurite:/data]

  api:
    build: { context: ., dockerfile: services/api/Dockerfile }
    env_file: .env
    depends_on: { postgres: { condition: service_healthy }, qdrant: { condition: service_started }, azurite: { condition: service_started } }
    healthcheck: { test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"], interval: 10s, retries: 12 }

  worker:
    build: { context: ., dockerfile: services/worker/Dockerfile }
    command: python -m worker
    env_file: .env
    depends_on: { api: { condition: service_healthy } }   # api runs migrations and creates the index

  eval:
    build: { context: ., dockerfile: services/worker/Dockerfile }
    entrypoint: ["python", "-m", "eval"]
    env_file: .env
    environment: { API_BASE_URL: "http://api:8000" }
    volumes: [./eval:/app/eval]
    profiles: [tools]                                      # not started by `up`

  web:
    build: { context: ., dockerfile: web/Dockerfile }
    ports: ["8080:80"]
    depends_on: { api: { condition: service_healthy } }

volumes: { pgdata: {}, qdrant: {}, azurite: {} }
```

On startup the api runs Alembic migrations, calls `ensure_schema()` on the index, and creates the Blob container and queue if missing, so a fresh clone needs no manual setup.

**Makefile targets**

| Target | Does |
| --- | --- |
| `make up` / `make down` / `make reset` | Build and start / stop / stop and delete volumes |
| `make logs` | Follow logs for all services |
| `make seed` | Upload `corpus/` with relative paths and wait for the ingest job to finish |
| `make split` | Generate `eval/splits.json` (run once, then commit) |
| `make eval PROFILES=full SPLIT=all` | `docker compose run --rm eval run …` |
| `make gate RUN=<id> PHASE=P4` | Check a run against the phase's gates |
| `make test` | Unit and contract tests (no network) |
| `make test-int` | Integration tests against the running stack |
| `make lint` | ruff, mypy, and the web linter |
| `make web-types` | Regenerate the TypeScript API types from OpenAPI |

## Testing strategy

Four test layers; the first two run in seconds with no network, so Claude Code runs them after every change, and the golden-set gate is the final word on quality.

| Layer | Scope | Examples | Runs |
| --- | --- | --- | --- |
| Unit | Pure functions with fixtures | Metadata rules (doc\_type, dates, weeks, IDs) for every corpus filename; chunkers (table kept whole, CSV row text); weighted RRF; recency boost; guardrail; context budget; citation validation; every eval metric against hand-computed cases | `make test`, every change, CI |
| Contract | Adapters against their protocol | One shared test suite run against `QdrantIndex` and an in-memory fake (later `AISearchIndex`): upsert idempotency, filters, keyword match on `RSK-014`, delete by document | `make test` (Qdrant via testcontainers), CI |
| Integration | Running Compose stack | Seed the corpus and assert job success with a chunk count between 250 and 400; `/api/ready` is 200; three smoke questions (ID lookup, recency, unanswerable) return the expected shape and citations | `make test-int`, end of each phase |
| Golden-set gate | Full quality bar | `make eval` then `make gate` with the phase's thresholds | Phase gates, before release |

**Test doubles.** `FakeChatModel` returns scripted structured outputs and `FakeEmbeddings` returns deterministic hashed vectors, so unit and contract tests never call Foundry. Integration tests and gates use the real Foundry deployments.

**CI (GitHub Actions).** On every push: ruff, mypy, web lint and type check, unit and contract tests. Integration and gates run manually (`workflow_dispatch`) because they need Foundry and Arize secrets.

## Phased build plan for Claude Code

Seven phases build version 1, each ending in a gate Claude Code runs itself; you are needed at three checkpoints only: supplying `.env` before P1, reviewing baseline numbers after P3, and signing off the release after P6.

| Phase | Builds | Gate (all must pass) |
| --- | --- | --- |
| P0 Scaffold | Repo layout, uv workspace, `pmo_core` skeleton, settings and profiles, Compose with postgres, qdrant, azurite, api `/health` and `/ready`, web shell, Makefile, CI, ADR files from the HLD | `make up` healthy; `make lint` and `make test` pass; CI green |
| P1 Ingestion | Upload endpoint, Blob and queue adapters, worker loop, loaders, metadata rules, chunkers, embeddings, Qdrant index, documents page (upload and progress) | Unit tests cover metadata for all 31 corpus files; `make seed` job `succeeded` with 250–400 chunks; contract suite passes on Qdrant |
| P2 Baseline chat | Pipeline with the dense leg only, context, generation with structured output and citation validation, persistence, Arize tracing, chat page with answers and citations | 3 smoke questions return cited answers; trace visible in Arize with root and stage spans; `make test-int` passes |
| P3 Evaluation | Splits, eval runner, all metrics including Ragas, `compare` and `gate`, evaluation page | Two `baseline` runs on `all` differ by under 2 points on every retrieval metric; baseline summary written to `docs/results.md` (**checkpoint: you review the baseline**) |
| P4 Retrieval | Keyword leg, weighted RRF, filter parser, reranker, `hybrid` and `rerank` profiles, retrieve and rerank cards in the panel | On `tune`, the `rerank` profile reaches Recall@5 ≥ 0.80 and MRR ≥ 0.75; every exact-ID question (Q08–Q13) has Hit@5 = 1 |
| P5 Query and answer | Rewrite with history, multi-query and HyDE options, guardrail with threshold tuned on `tune`, recency boost, conflict notes, `full` profile | All PRD release gates on `test` and on `all` with `full`, including 3 of 3 abstentions, false abstention ≤ 5%, 100% trap avoidance, p95 under 6 s |
| P6 Polish | Full under-the-hood panel, toggles, feedback with Arize annotations, eval comparison view, README with screenshots, results table across all four profiles in `docs/results.md` | UI checklist passes (each toggle changes the trace; feedback appears in Arize); release gates re-run green (**checkpoint: you sign off version 1**) |
| P7 Azure (after version 1) | `AISearchIndex`, Managed Identity paths, Bicep modules, GitHub Actions deploy, Container Apps jobs | Contract suite passes on AI Search; parity run within 0.03 of Qdrant on every retrieval metric; Azure smoke tests pass |

**Working rules for Claude Code**

- Finish and gate one phase before starting the next; commit at the end of each phase with the gate output in the commit message.
- When a gate fails, diagnose from the stage traces and per-question results before changing code; record what was tried in `docs/decisions-log.md`.
- Tune thresholds and weights only on the `tune` split; never edit the golden set's answers or evidence to pass a gate.
- Escalate to you only for credentials, quota, or a gate that still fails after two diagnosed attempts.
