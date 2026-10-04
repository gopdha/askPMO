# Project Atlas – Cutover Strategy

| Field | Value |
|---|---|
| Document ID | ATL-WS5-004 |
| Version | 2.0 |
| Date | 2026-03-16 |
| Owner | Sarah Lindqvist, WS5 Testing & Cutover Lead |
| Supersedes | Version 1.0 (2026-02-02, "big bang" cutover) |

## 1. Why this version exists

Version 1.0 assumed a "big bang" cutover in which the full 2.3 TB order history would be migrated during the 48-hour cutover window. The performance test on 2026-02-17 (issue ISS-009) showed DataBridge Migrate sustaining only 18 GB per hour against the 50 GB per hour required, which would have stretched the migration to well over 100 hours.

At the special Steering Committee session on 2026-03-04, the program adopted a **hybrid cutover approach** (decision DEC-006) and approved CR-007, which moved go-live to 2026-08-17.

## 2. Hybrid cutover approach

1. **Pre-migration (T-6 weeks to T-1 week):** Historical orders older than 90 days (approximately 2.0 TB) are migrated in advance, in weekly batches, while Meridian remains the system of record.
2. **Delta sync (T-1 week to T-0):** Changes to historical data are captured and replayed daily.
3. **Cutover weekend:** Only open orders, orders from the last 90 days and the final delta (approximately 300 GB) are migrated inside the 48-hour window.
4. **Reconciliation:** Record counts and order value totals are reconciled per store before the go/no-go call.

## 3. Cutover timeline (revised)

| Step | Date / time |
|---|---|
| Final go/no-go decision | Friday 2026-08-14, 16:00 CT |
| Cutover window opens (Meridian frozen) | Saturday 2026-08-15, 00:00 CT |
| Cutover window closes | Monday 2026-08-17, 00:00 CT |
| Production go-live (stores open on new OMS) | Monday 2026-08-17 |
| Hypercare | 2026-08-17 to 2026-09-18 |

## 4. Rollback plan

If reconciliation fails or a Severity 1 defect is found before 2026-08-16 18:00 CT, the cutover lead may invoke rollback. Rollback re-enables Meridian as the system of record; orders taken on the new platform during the window are replayed into Meridian using the reverse sync job. The rollback decision authority is Tom Harris (Client Program Director), with Arjun Mehta as delegate.

## 5. Dependencies

- DataBridge connector v3.2 delivered and performance-certified (see RSK-014).
- At least two successful mock runs (mock run 1 now planned for 2026-05-08).
- Store operations communication sent at least 10 days before cutover.
