# PRD – askPMO (RAG)

Oct 3, 2026 · @Gopinath Dhayanandamurthy

## Overview

askPMO is a PMO knowledge assistant that answers natural-language questions about a program from its own documents, with cited sources and an honest "not found" when the answer isn't there. Version 1 is a React SPA over a FastAPI and LangChain backend, using Azure AI Foundry models and Arize AX tracing. It runs locally in Docker Compose, with Azure Container Apps as the target state, over the Project Atlas corpus (31 documents), measured against a 45-question golden set.

**Problem.** Program facts are scattered across charters, status reports, RAID logs, change requests, minutes and finance PDFs. Answering "what's the current go-live date?" or "which open risks hit the over-budget workstream?" takes a PM 10–30 minutes of searching. Facts also go stale: the charter still says June 15 after a change request moved go-live to August 17.

**Product.** A chat assistant with an "under the hood" panel showing every retrieval stage: dense and keyword scores, fused rank, reranker score, and the chunks that reached the model. Each pipeline feature (hybrid search, reranking, query rewriting, guardrails) can be toggled and its effect measured.

**Why build it.** It complements OnePulse: OnePulse pushes scheduled executive reports, while this assistant answers ad hoc questions on demand. It is also a hands-on vehicle for mastering production RAG patterns and evaluation.

## Goals and non-goals

Version 1 succeeds when the full pipeline beats the naive baseline on the golden set by a measurable margin, and every gain is attributed to a specific feature.

**Goals**

1. Answer program questions accurately, with a citation to document and section for every claim.
2. Implement the core RAG feature set: metadata-aware ingestion, hybrid retrieval, reranking, query rewriting, chat history, citations and a no-answer guardrail.
3. Measure everything: retrieval metrics (Hit Rate, Recall, MRR, nDCG) and generation metrics (faithfulness, answer relevance, correctness) for every configuration.
4. Make each feature toggleable by config so experiments are a config change, not a code change.
5. Trace every query end to end for debugging and demos.

**Non-goals for version 1**

- Multi-tenant access control or document-level permissions.
- Live connectors to Azure DevOps, SharePoint or Jira (static corpus only).
- Agentic workflows such as writing back to the RAID log.
- Deploying to Azure in version 1 (Container Apps is the designed target state), and scale beyond a single user.
- Fine-tuning embedding or generation models.

## Users and user stories

The primary user is the program manager; the builder evaluating the pipeline is a first-class secondary user.

| Persona | Need | Example question |
| --- | --- | --- |
| Program manager (Arjun) | Fast, current, cited answers across all program documents | "Which open risks affect the workstream that's over budget?" |
| Executive sponsor (Laura) | Plain-language status and the reason behind decisions | "Why was the go-live moved?" |
| Workstream lead (Marcus) | Precise lookups by ID and owner | "What is the mitigation for RSK-014?" |
| PMO analyst (Neha) | Point-in-time facts for reporting | "What was overall status in week 6?" |
| RAG engineer (builder) | See and compare what each pipeline stage contributes | Toggle reranking and compare MRR |

**Key user stories**

1. As a PM, I ask a question and get an answer with citations I can click to verify.
2. As a PM, when the documents disagree, I get the most recent approved fact and a note on what changed.
3. As a PM, I can ask a follow-up ("who owns it?") without restating context.
4. As a sponsor, when the answer isn't in the documents, the assistant says so instead of guessing.
5. As a builder, I see dense, keyword, fused and reranker scores for every retrieved chunk.
6. As a builder, I run the golden set against any config and get a metrics report in one command.

## Corpus and data

Version 1 runs on the synthetic Project Atlas corpus: 31 documents in three formats covering 2026-01-09 to 2026-04-03, with facts that reconcile across every document.

| Folder | Contents | Format | Metadata to extract |
| --- | --- | --- | --- |
| 01\_governance | Charter v1.0, SOW, cutover strategy v2.0 | Markdown, PDF | doc\_type, version, date |
| 02\_status\_reports | 12 weekly status reports | Markdown | doc\_type, week, week\_ending |
| 03\_raid | RAID log (risks, issues, actions, decisions) | CSV, one row per item | item\_id, type, workstream, owner, status |
| 04\_change\_requests | Change log and 4 CR documents | Markdown | cr\_id, status, decision\_date |
| 05\_meeting\_minutes | SteerCo and working-session minutes | Markdown | meeting\_type, date |
| 06\_finance\_resourcing | Budget burn report, resource plan | PDF with tables | doc\_type, as\_of\_date |
| 07\_reference | Lessons learned from a different project | Markdown | doc\_type, project |

**Built-in challenges the pipeline must handle**

- **Stale facts:** the charter and weeks 1–7 say go-live 2026-06-15 and budget $4.8M; current values are 2026-08-17 and $5,345,000.
- **Superseded documents:** cutover v2.0 replaces v1.0; CR-006 was superseded by CR-007.
- **Exact identifiers:** RSK-014, ISS-009, DEC-006 and "section 9.3" are weak signals for embeddings.
- **Distractor:** Project Helios also had a vendor delay, a moved go-live and an overrun.
- **PDF tables:** budget and payment figures exist only inside PDF tables.
- **Unanswerable questions:** e.g., DataBridge's hourly rate is not in any document.

## Functional requirements

Requirements are grouped by stage; each one names the golden-set categories that test it.

| ID | Stage | Requirement | Priority | Tested by |
| --- | --- | --- | --- | --- |
| FR-01 | Ingestion | Upload Markdown, PDF (including tables) and CSV through the API; a queue-driven worker loads them with format-specific loaders and records status | Must | table\_pdf |
| FR-02 | Ingestion | Attach metadata per chunk: source, doc\_type, date, week, workstream, item IDs | Must | temporal, recency |
| FR-03 | Ingestion | Support configurable chunking: recursive, Markdown-header-aware, semantic | Must | all retrieval metrics |
| FR-04 | Ingestion | Keep each RAID row and each CR as its own chunk | Must | exact\_id |
| FR-05 | Retrieval | Dense retrieval through one retriever interface (Qdrant locally, Azure AI Search on Azure) with similarity scores returned | Must | paraphrase |
| FR-06 | Retrieval | Keyword (sparse / BM25) retrieval from the same index | Must | exact\_id |
| FR-07 | Retrieval | Store-native hybrid query fused with Reciprocal Rank Fusion; debug mode returns per-leg scores | Must | exact\_id, multi\_hop |
| FR-08 | Retrieval | Metadata filters extracted from the query (week, date, doc type) | Should | temporal |
| FR-09 | Reranking | In-process cross-encoder reranking (bge-reranker-base): retrieve top 30, keep top 5 (configurable) | Must | why\_rerank, distractor |
| FR-10 | Reranking | Recency boost or latest-version preference when facts conflict | Should | recency |
| FR-11 | Query | Condense follow-up questions using chat history into a standalone query | Must | conversational |
| FR-12 | Query | Multi-query expansion and HyDE as optional rewriting strategies | Could | paraphrase |
| FR-13 | Context | Deduplicate near-identical chunks and fit context to a token budget | Should | all |
| FR-14 | Generation | Answer only from retrieved context using an Azure AI Foundry chat model via LangChain | Must | faithfulness |
| FR-15 | Generation | Return structured output: answer, cited chunk IDs, confidence | Must | all |
| FR-16 | Generation | Inline citations to document and section for every claim | Must | all |
| FR-17 | Guardrails | Abstain with "not found in the documents" when the top rerank score is below threshold | Must | no\_answer |
| FR-18 | Guardrails | Flag when sources conflict and state which is newer | Should | recency |
| FR-19 | UI | React SPA chat with an "under the hood" panel of scores per stage | Must | demo |
| FR-20 | UI | Live toggles for hybrid, reranking and query rewriting, mapped to YAML config profiles | Should | demo |
| FR-21 | UI | Thumbs up/down feedback logged with the trace | Could | — |
| FR-22 | Evaluation | One-command golden-set run producing a metrics report per config | Must | all |

## Non-functional requirements

Targets are for a single-user local deployment and are measured by the eval runner on every config.

| Area | Requirement | Target |
| --- | --- | --- |
| Latency | End-to-end response, full pipeline (hybrid + rerank) | p95 under 6 s |
| Latency | Retrieval and reranking only | p95 under 1.5 s |
| Cost | LLM cost per query, full pipeline | Under $0.02 |
| Cost | Full golden-set run (45 questions, including Ragas judging) | Under $3 |
| Observability | Every stage traced: query, rewrites, retrieved IDs and scores, reranked order, prompt, answer, latency, tokens | 100% of queries |
| Configurability | Chunking, k, top\_n, weights, toggles and thresholds set in YAML; no code change per experiment | All FR-03 to FR-17 parameters |
| Reproducibility | Fixed model versions, temperature 0, config and git hash stored with every eval run | Re-run variance under 2 points on retrieval metrics |
| Portability | The same containers run in Docker Compose locally and on Azure Container Apps (target state) | One command: docker compose up |
| Data handling | Keys in .env locally, never in the browser; Managed Identity and Key Vault on Azure; corpus data leaves only to Azure AI Foundry and, in traces, Arize AX | Enforced |

## Architecture and tech stack

The system is a LangChain pipeline in three layers: offline ingestion, a five-stage query pipeline, and an evaluation and tracing layer around it.

&#91;embedded content: RAG architecture · ingestion, 5-stage query pipeline, evaluation\]

Every query stage can be switched off in config, so the baseline is the same pipeline with stages 1, 3 and 4 disabled and dense-only retrieval.

| Layer | Local (version 1) | Azure (target state) | LangChain component / package |
| --- | --- | --- | --- |
| UI | React SPA (Vite) served by nginx, which proxies /api | Same container on external ingress, Entra ID built-in auth | — |
| API | FastAPI, Python 3.11 | Same container, internal ingress only | LCEL chains |
| Loaders | Markdown, PDF, CSV | Same | `UnstructuredMarkdownLoader`, `PyPDFLoader`, `CSVLoader` (langchain-community) |
| Chunking | Header-aware + recursive | Same | `MarkdownHeaderTextSplitter`, `RecursiveCharacterTextSplitter` |
| Embeddings | Azure AI Foundry embedding deployment (API key) | Same deployment (Managed Identity) | `AzureOpenAIEmbeddings` (langchain-openai) |
| Retrieval index | Qdrant container (dense + sparse) | Azure AI Search (vector + keyword) | `QdrantVectorStore` / `AzureSearch`, behind one retriever interface |
| Hybrid fusion | Qdrant native hybrid, RRF | AI Search native hybrid, RRF | Custom retriever wrapper |
| Reranking | bge-reranker-base, in the API process | Same | `CrossEncoderReranker` + `HuggingFaceCrossEncoder` |
| Query rewriting | History-aware, multi-query, HyDE | Same | `create_history_aware_retriever`, `MultiQueryRetriever` (langchain-classic) |
| Chat model | Azure AI Foundry chat deployment, temperature 0 | Same (Managed Identity) | `AzureChatOpenAI` with structured output (or the Foundry client for non-OpenAI models) |
| App database | PostgreSQL container | Azure Database for PostgreSQL Flexible Server | SQLAlchemy |
| Documents and jobs | Azurite (Blob + Queue emulator) | Storage account (Blob + Queue) | azure-storage SDK |
| Ingestion | Worker container polling the queue | Container Apps job, KEDA queue trigger | — |
| Evaluation | `docker compose run eval` | Container Apps job, manual or scheduled | `ragas` + custom retrieval metrics |
| Tracing | Arize AX over OTLP | Same | `openinference-instrumentation-langchain` |
| Secrets | .env file | Managed Identity, Key Vault | — |
| Config | YAML profiles: baseline, hybrid, full | Same | Pydantic settings |

Package and model names are pinned in the LLD; the Foundry chat model choice is still open.

## Evaluation and success metrics

Version 1 ships when the full pipeline meets every target below on the 45-question golden set, reported overall and per category.

**How relevance is judged.** A retrieved chunk counts as relevant if it contains any evidence snippet for that question, after normalization (strip Markdown bold and table pipes, unify dashes, collapse whitespace, lowercase). This keeps labels valid across chunking strategies, so experiments compare fairly.

| Metric | What it measures | Source | Target (full pipeline) |
| --- | --- | --- | --- |
| Hit Rate@5 | Any relevant chunk in the final top 5 | Custom code | 0.90 or higher |
| Recall@5 | Share of evidence snippets found in the top 5 | Custom code | 0.80 or higher |
| MRR | How high the first relevant chunk ranks | Custom code | 0.75 or higher |
| nDCG@5 | Rank-weighted relevance of the top 5 | Custom code | 0.75 or higher |
| Key-fact accuracy | Answer contains every `key_facts` string | Custom code | 85% of answerable questions |
| Faithfulness | Claims supported by retrieved context | Ragas | 0.90 or higher |
| Answer relevance | Answer addresses the question | Ragas | 0.85 or higher |
| Answer correctness | Agreement with `reference_answer` | Ragas / LLM judge | 0.80 or higher |
| Correct abstention | Unanswerable questions answered "not found" | Custom code | 3 of 3 |
| False abstention | Answerable questions wrongly refused | Custom code | 5% or lower |
| Trap avoidance | Recency and distractor questions answered with the current, correct-project fact | Custom code | 100% |

**Experiment protocol.** Run the baseline first, then add one feature at a time and re-run the full set. Each run stores config, git hash, per-question results and latency/cost. The final deliverable is a comparison table (baseline → +hybrid → +rerank → +query rewriting → +guardrails) with metric deltas, so every gain is attributable to a feature.

## Release plan

Version 1 takes about four weeks of part-time work, and each phase ends at a gate measured on the golden set.

&#91;embedded content: Release plan · 5 phases over 4 weeks, gate at each phase end\]

A phase starts only when the previous gate passes. The baseline gate fixes the reference scores that every later improvement is measured against; the release gate requires every target in the evaluation section. Azure deployment follows as a separate phase, gated on a golden-set parity run between Qdrant and Azure AI Search.

## Risks, assumptions and open questions

The biggest risk is overfitting the pipeline to a 45-question synthetic set; the mitigation is to hold questions back and add a second corpus later.

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Overfitting to the golden set | Metrics look strong but don't generalize | Hold out 10 questions as a test split; tune only on the other 35 |
| Synthetic corpus is cleaner than real program documents | Ingestion issues hidden until real data | Phase 2 test on a sanitized real document set |
| PDF table extraction loses row and column structure | Wrong figures on budget questions | Compare pypdf, pdfplumber and docling; keep the best per document |
| LLM-as-judge scores drift or are biased | Unreliable generation metrics | Fix judge model and prompt; spot-check 10 answers by hand per run |
| Qdrant and AI Search behave differently | Azure results diverge from local benchmarks | Golden-set parity run on both backends before cutover; retriever contract tests |
| Foundry quota or regional model availability | Blocked runs or a forced model change | Confirm quota and region early; keep the deployment name in config so models swap without code changes |
| LangChain API changes (v1 moved retrievers to langchain-classic) | Broken imports, wasted time | Pin package versions; contract tests on each pipeline stage |
| Reranker adds too much latency on CPU | Misses the 6 s p95 target | Measure; fall back to a smaller cross-encoder |
| Corpus text in Arize AX traces | Sensitive data leaves the environment with real documents | Synthetic data in version 1; enable span masking before any real corpus |

**Assumptions**

- A single user runs the app locally in version 1 with no sign-in; Entra ID sign-in applies only to the Azure target.
- An Azure AI Foundry project with a chat deployment and an embedding deployment is available for generation, embeddings and judging.
- The corpus is static during version 1; re-ingestion is a manual command.

**Open questions**

- [ ] Which Foundry chat model: gpt-5-mini or a Claude model on Foundry?
- [ ] Recency handling: metadata boost at rerank time, or prompt the model to prefer the newest source?
- [ ] Should version 2 connect to live Azure DevOps data, reusing OnePulse's integration?
