# Project Atlas – RAG Practice Corpus

A synthetic but internally consistent document set for a fictional cloud migration program, built to test a RAG pipeline (hybrid search, reranking, metadata filtering, recency handling, guardrails) and score it with a golden evaluation set.

**Program in one paragraph:** Northwind Retail Group (340 stores) is migrating its legacy "Meridian" order management system and data warehouse to Azure, with Cobalt Systems as the integrator and DataBridge Solutions supplying the migration tool. A throughput problem (18 GB/hr vs 50 GB/hr needed) forced CR-007, moving go-live from 2026-06-15 to 2026-08-17. Documents cover 2026-01-09 to 2026-04-03.

## Corpus (31 documents, 3 formats)

| Folder | Contents | Format |
|---|---|---|
| 01_governance | Charter v1.0 (baseline), SOW, cutover strategy v2.0 | .md, .pdf |
| 02_status_reports | 12 weekly status reports (weeks 1–12) | .md |
| 03_raid | RAID log snapshot: risks, issues, actions, decisions | .csv |
| 04_change_requests | Change log + CR-003, CR-005, CR-007, CR-008 | .md |
| 05_meeting_minutes | 4 SteerCo meetings, data migration deep-dive, vendor review, integration sync | .md |
| 06_finance_resourcing | March budget burn report, resource plan v3.0 (table-heavy) | .pdf |
| 07_reference | Project Helios lessons learned (a DIFFERENT, older project – distractor) | .md |

Useful metadata to attach at ingestion: `doc_type` (from folder), `date` (from file name), `week` (status reports), `workstream`.

## Deliberate traps

- **Stale facts:** the charter and weeks 1–7 say go-live 2026-06-15 and budget $4.8M; the current values are 2026-08-17 and $5,345,000.
- **Superseded documents:** cutover v2.0 replaces the "big bang" v1.0 referenced in week 4; CR-006 was superseded by CR-007.
- **Exact IDs:** RSK-014, ISS-009, CR-006, DEC-006, "section 9.3" – embeddings alone often miss these.
- **Distractor:** Helios also had a vendor delay, a moved go-live and a cost overrun.
- **PDF tables:** budget and payment figures live only in PDF tables.
- **No-answer questions:** e.g., DataBridge's hourly rate (the rate card covers Cobalt roles only).

## Golden set – `eval/golden_set.json`

45 questions across 12 categories: factual, table_pdf, exact_id, paraphrase, why_rerank, temporal, recency, multi_hop, aggregation, distractor, no_answer, conversational.

Each question has:
- `reference_answer` – the ground truth (for Ragas answer correctness / LLM-as-judge).
- `key_facts` – strings the answer must contain (cheap exact-match check).
- `evidence` – source file + a verbatim snippet. **A retrieved chunk is relevant if it contains any evidence snippet for that question**, after normalizing both texts (`scripts/validate_golden.py` → `norm()`: remove `**` and `|`, convert en/em dashes to `-`, collapse whitespace, lowercase). This keeps relevance labels valid no matter how you chunk, so you can compare chunking strategies fairly.
- `chat_history` – prior turns for conversational questions.
- `answerable: false` – the system should abstain.
- `trap` – what a wrong answer looks like.

Run `python scripts/validate_golden.py` after editing any document to confirm all evidence snippets still exist.

## Scripts

`scripts/` contains the generators for the status reports, RAID log, PDFs and golden set, so you can extend the corpus (e.g., add weeks 13+) and keep facts consistent.
