# Change Request CR-005 – Disaster Recovery Region

| Field | Value |
|---|---|
| CR ID | CR-005 |
| Requested by | Laura Bennett, CIO |
| Date raised | 2026-02-13 |
| Workstream | WS1 – Infrastructure & Landing Zone |
| Status | Approved by the Steering Committee at SC-02 on 2026-02-25 |

## Description
Add a secondary Azure region (Central US) for disaster recovery of the order management platform and its databases. The original design relied on zone redundancy within East US 2 only.

## Target recovery objectives
- **Recovery Point Objective (RPO):** 15 minutes.
- **Recovery Time Objective (RTO):** 4 hours.
- DR failover test to be completed before go-live.

## Justification
Northwind's internal audit flagged that a regional outage would stop order taking across all stores. The board risk committee requires a documented DR capability for tier-1 systems.

## Impact
- **Cost:** $140,000 (WS1 budget increases from $900,000 to $1,040,000), plus estimated Azure run cost of $9,500 per month for standby resources.
- **Schedule:** No milestone impact.

## Approval
Because the cost impact is $100,000 or more, the CR was escalated to and approved by the Steering Committee.
