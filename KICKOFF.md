# Kickoff — handing the build to Claude Code (CLI)

About 15 minutes of setup; after that Claude Code builds phase by phase and stops only at the
three checkpoints in `CLAUDE.md`.

## 1. Prerequisites on your machine
- Docker Desktop (running), Git, Node.js 20 LTS, and `uv` (Python package manager).
- Claude Code CLI installed and signed in (`claude` starts a session in the current folder).
- An Azure AI Foundry resource with a chat deployment and an embedding deployment.
- An Arize AX space (space ID and API key).

## 2. Put the repo in place
```bash
unzip askpmo.zip && cd askpmo
git init && git add . && git commit -m "Seed: design docs, corpus, golden set, Claude Code config"
# optional: create an empty GitHub repo and push
```

## 3. Add the three design documents
Open each doc in Claude, click the doc's name → **Export** → **Markdown**, and save it into
`docs/` with exactly these names:

| Doc in Claude | Save as |
| --- | --- |
| PRD – askPMO (RAG) | `docs/PRD.md` |
| HLD – askPMO (RAG) | `docs/HLD.md` |
| LLD – askPMO (RAG) | `docs/LLD.md` |

Commit them: `git add docs && git commit -m "Add PRD, HLD, LLD"`.

## 4. Fill in credentials
```bash
cp .env.example .env
```
Edit `.env` and set `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, the deployment names if yours differ,
`EMBEDDING_DIMENSIONS` to match your embedding model, `ARIZE_SPACE_ID` and `ARIZE_API_KEY`.
Claude Code is configured never to read `.env`.

## 5. Start Claude Code and paste the kickoff prompt
```bash
claude
```
Then paste:

> Read CLAUDE.md, docs/build-status.md and docs/LLD.md. Build askPMO phase by
> phase starting at P0, using /next-phase. Work autonomously; run each phase gate yourself, record
> the evidence, commit, and continue. Stop only at the human checkpoints defined in CLAUDE.md or
> when you need credentials or quota. At each stop, give me a short summary and exactly what you
> need from me.

Useful during the build: `/status` for a progress summary, `/gate P4` to re-run a gate.

## 6. Your three checkpoints
1. **Before P1:** if `make check-env` shows a missing variable, fix `.env` and say "continue".
2. **After P3:** review `docs/results.md` (baseline numbers) and say "continue".
3. **After P6:** open http://localhost:8080, try the chat and toggles, review `docs/results.md`,
   and sign off version 1.

The Azure phase (P7) starts only when you ask for it.
