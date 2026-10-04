# Project Helios – Lessons Learned Report

| Field | Value |
|---|---|
| Program | Project Helios – Store POS Platform Upgrade |
| Client | Northwind Retail Group |
| Program Manager | Grace Liu |
| Report date | 2024-12-12 |

## 1. Summary
Project Helios upgraded the point-of-sale (POS) software in all Northwind stores between March and November 2024. Go-live was originally planned for 2024-09-09 but moved to **2024-10-07** after the store data migration vendor missed two delivery dates. Hypercare ended on 2024-11-08, one week before the retail freeze.

## 2. What went well
- Pilot rollout in 12 Dallas stores caught 40% of the defects before the wider rollout.
- Daily stand-ups between store operations and the technology team kept issue resolution under 24 hours.

## 3. What did not go well
- **Vendor dependency:** The data migration vendor's tool could not meet the throughput needed for price and promotion data. The program waited too long, about six weeks, before escalating and had no fallback tool evaluated.
- **Budget:** The program finished at $2.9 million against a $2.5 million budget, mostly due to the go-live delay.
- **Test environments:** A single shared test environment caused repeated scheduling conflicts.

## 4. Recommendations for future programs
1. Run a performance test of migration tooling in the first 6 weeks, using production-like data volumes.
2. Evaluate a fallback migration tool early whenever a single vendor is on the critical path.
3. Include service credit clauses for vendor delays in contracts.
4. Fund at least two pre-production environments.
