# Decisions log

Record every deviation from, or conflict between, the PRD/HLD/LLD, and every notable
implementation choice (library versions, threshold tuning, gate-failure diagnoses).

| Date | Phase | Decision / finding | Why | Docs affected |
| --- | --- | --- | --- | --- |
| 2026-10-03 | Design | Hybrid legs are store-native; fusion is weighted RRF in the api | Per-leg scores on every request; same ID weighting on Qdrant and AI Search | ADR-007, HLD, LLD |
| 2026-10-03 | Design | Golden set v1.1 adds `forbidden` lists to Q23, Q37, Q38, Q40 | Machine-checkable trap avoidance | LLD evaluation section |
