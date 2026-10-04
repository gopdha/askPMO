# Data Migration Deep-Dive – Meeting Notes

**Date:** Wednesday 2026-02-18, 10:00–11:30 CT
**Facilitator:** Marcus Chen, WS2 Data Migration Lead
**Attendees:** Arjun Mehta, Sarah Lindqvist, Ravi Shankar (Lead Data Architect), Kevin Walsh (Account Executive, DataBridge Solutions), Lena Fischer (Solutions Engineer, DataBridge Solutions)

## 1. Performance test results
Ravi Shankar presented results from the performance test run on 2026-02-17 against a 200 GB representative extract of order history:
- Sustained throughput: **18 GB per hour** with connector v3.1.
- Required throughput: **50 GB per hour** to move 2.3 TB within the 48-hour cutover window.
- Bottleneck: order line tables are extracted single-threaded; CPU on the migration servers stayed below 30%.

Logged as issue ISS-009 (Critical).

## 2. Vendor response
Lena Fischer confirmed that connector v3.2 introduces parallel extraction and that internal benchmarks show 60 to 70 GB per hour. However, Kevin Walsh warned that the v3.2 general availability date of 2026-03-13 is "at risk" because of a regression found in their QA cycle.

## 3. Options discussed
1. Wait for v3.2 and keep the big bang cutover (high risk).
2. Pre-migrate historical data before cutover (hybrid approach) to shrink the cutover payload.
3. Evaluate Azure Data Factory as an alternative tool.

Sarah Lindqvist noted that option 2 needs a reverse sync for rollback and an extra performance test cycle.

## 4. Actions
- Arjun Mehta: prepare recovery options and a change request for the Steering Committee.
- Marcus Chen: size the pre-migration volume for orders older than 90 days.
- Kevin Walsh: provide a written v3.2 delivery commitment by 2026-02-25.
