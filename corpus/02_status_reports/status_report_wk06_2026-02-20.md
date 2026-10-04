# Project Atlas – Weekly Status Report

| Field | Value |
|---|---|
| Report | Week 6 |
| Week ending | 2026-02-20 |
| Prepared by | Neha Kapoor, PMO Analyst |
| Reviewed by | Arjun Mehta, Program Manager |
| Overall status | **Red** |
| Forecast go-live | 2026-06-15 (under review) |

## Executive summary
Overall status is Red. The data migration performance test on 2026-02-17 achieved only 18 GB per hour against the 50 GB per hour needed to move the 2.3 TB order history within the 48-hour cutover window (ISS-009). The June 15 go-live is at serious risk and options are being assessed.

## Workstream status

| Workstream | Lead | Status |
|---|---|---|
| WS1 – Infrastructure & Landing Zone | Priya Raman | Amber |
| WS2 – Data Migration | Marcus Chen | Red |
| WS3 – Application Modernization | Elena Rossi | Green |
| WS4 – Integration & APIs | David Okafor | Green |
| WS5 – Testing & Cutover | Sarah Lindqvist | Amber |

## Key accomplishments this week
- Performance test executed on 2026-02-17; results logged as ISS-009.
- Data migration deep-dive held on 2026-02-18 with DataBridge.
- Order management core services scaffolding complete (WS3).

## Planned for next week
- Prepare recovery options for the Steering Committee.
- Obtain DataBridge commitment on connector v3.2 performance fixes.

## Top risks and issues
- ISS-009 – Data migration throughput below requirement (Critical).
- RSK-014 – DataBridge connector v3.2 delivery slipping (High).
- ISS-004 – ExpressRoute circuit provisioning delayed (High).

## Milestones

| ID | Milestone | Baseline | Forecast | Status |
|---|---|---|---|---|
| M1 | Azure landing zone ready | 2026-02-27 | 2026-02-27 | At risk |
| M2 | Data migration mock run 1 complete | 2026-03-20 | Under review | At risk |
| M3 | Order management application build complete | 2026-04-30 | 2026-04-30 | On track |
| M4 | SIT complete | 2026-05-22 | Under review | At risk |
| M5 | UAT complete | 2026-06-05 | Under review | At risk |
| M6 | Production go-live | 2026-06-15 | Under review | At risk |
| M7 | Hypercare end | 2026-07-17 | Under review | At risk |
