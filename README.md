# askPMO (RAG)

askPMO is a retrieval-augmented assistant that answers questions about a program from its own documents,
with citations, an honest "not found", and every retrieval stage visible and measured.

**Status:** design complete; build in progress with Claude Code. See `docs/build-status.md`.

- Start here: `KICKOFF.md`
- Build instructions for Claude Code: `CLAUDE.md`
- Design: `docs/PRD.md`, `docs/HLD.md`, `docs/LLD.md`, `docs/architecture/`, `docs/adr/`
- Seed corpus (synthetic "Project Atlas", 31 documents): `corpus/`
- Golden evaluation set (45 questions): `eval/golden_set.json` — see `eval/README.md`

Stack: React + FastAPI + LangChain, Qdrant (local) / Azure AI Search (target), Azure AI Foundry,
bge-reranker-base, PostgreSQL, Azurite / Azure Storage, Arize AX. Runs locally with Docker
Compose; Azure Container Apps is the target state.
