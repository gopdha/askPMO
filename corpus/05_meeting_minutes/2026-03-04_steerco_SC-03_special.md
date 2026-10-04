# Steering Committee Minutes – SC-03 (Special Session)

**Date:** Wednesday 2026-03-04, 09:00–10:30 CT
**Chair:** Laura Bennett, CIO
**Attendees:** Tom Harris, Rachel Moore, Arjun Mehta, Neha Kapoor (minutes), Marcus Chen, Sarah Lindqvist, Ravi Shankar

## 1. Purpose
Special session called at SC-02 to decide on the re-plan of the program following the data migration throughput issue (ISS-009).

## 2. Options presented by Arjun Mehta
| Option | Description | Go-live | Cost | Risk |
|---|---|---|---|---|
| A | Keep 2026-06-15 go-live, wait for connector v3.2 | 2026-06-15 | $60,000 (CR-006 only) | Very high – v3.2 already slipping |
| B | Hybrid cutover, re-plan go-live | 2026-08-17 | $320,000 | Medium |
| C | Switch to Azure Data Factory now | 2026-09-28 | $510,000 | Medium – rework of mappings |

## 3. Discussion
Rachel Moore questioned the cost of option B. Arjun Mehta explained that $240,000 covers the extended WS2 team and two additional mock runs, and $80,000 covers extended test environments and cutover rehearsals in WS5. Tom Harris confirmed store operations can support an August go-live, which is well clear of the November 15 retail freeze.

Laura Bennett asked that Azure Data Factory still be evaluated as a fallback in case DataBridge slips again.

## 4. Decisions
- **DEC-006:** Adopt the hybrid cutover approach – historical orders older than 90 days are pre-migrated before cutover.
- **DEC-007:** Approve **CR-007** (option B). Go-live moves from **2026-06-15 to 2026-08-17**. Cost impact $320,000, funded through additional budget approved by Laura Bennett.
- CR-006 is closed as superseded by CR-007.

## 5. Actions
- Arjun Mehta: send formal notice of delay to DataBridge to trigger service credits under SOW section 9.3 (ACT-021).
- Neha Kapoor: publish the re-baselined plan by 2026-03-10.
- Sarah Lindqvist: issue cutover strategy v2.0 by 2026-03-16.
