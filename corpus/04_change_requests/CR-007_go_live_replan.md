# Change Request CR-007 – Re-plan Go-Live Due to Data Migration Throughput

| Field | Value |
|---|---|
| CR ID | CR-007 |
| Requested by | Arjun Mehta, Program Manager |
| Date raised | 2026-02-27 |
| Workstreams | WS2 – Data Migration, WS5 – Testing & Cutover |
| Status | Approved by the Steering Committee at special session SC-03 on 2026-03-04 |
| Supersedes | CR-006 (extra performance test cycle) |

## Problem statement
During the performance test on 2026-02-17, DataBridge Migrate with the current Oracle connector (v3.1) sustained only **18 GB per hour**. Migrating the 2.3 TB order history inside the 48-hour cutover window requires at least **50 GB per hour**. At the observed rate the migration would take over 120 hours. This was logged as issue ISS-009.

DataBridge Solutions has confirmed that the performance fixes are in connector v3.2, but delivery of v3.2 has slipped from 2026-03-13 to 2026-04-30 (see risk RSK-014).

## Root cause
1. The v3.1 connector processes order line tables single-threaded.
2. The original plan assumed a "big bang" migration of all history during cutover.
3. The vendor's v3.2 release, which adds parallel extraction, is late.

## Proposed change
- Move production go-live from **2026-06-15** to **2026-08-17**.
- Adopt a hybrid cutover: pre-migrate history older than 90 days before cutover (decision DEC-006).
- Fold the extra performance test cycle requested in CR-006 into the re-plan.

## Revised milestones

| ID | Milestone | Previous date | New date |
|---|---|---|---|
| M2 | Data migration mock run 1 complete | 2026-03-20 | 2026-05-08 |
| M3 | Order management application build complete | 2026-04-30 | 2026-04-30 (unchanged) |
| M4 | SIT complete | 2026-05-22 | 2026-07-10 |
| M5 | UAT complete | 2026-06-05 | 2026-07-31 |
| M6 | Production go-live | 2026-06-15 | 2026-08-17 |
| M7 | Hypercare end | 2026-07-17 | 2026-09-18 |

The new go-live still falls well before the November 15 retail freeze and leaves time to decommission the Dallas data center before the lease expires in December 2026.

## Impact
- **Cost:** $320,000, of which $240,000 is allocated to WS2 (extended team and additional mock runs) and $80,000 to WS5 (extended test environments and re-planned cutover rehearsals). Funded through additional budget approved by Laura Bennett.
- **Schedule:** Go-live moves 9 weeks.
- **Commercial:** Cobalt Systems will pursue service credits from DataBridge under SOW section 9.3.

## Approval
Approved by the Steering Committee because it changes the go-live date and exceeds $100,000. See minutes of SC-03.
