# WS4 Integration & APIs – Weekly Sync Notes

**Date:** Wednesday 2026-03-18, 11:00–11:45 CT
**Facilitator:** David Okafor, WS4 Integration Lead
**Attendees:** Elena Rossi, Sarah Lindqvist, Priyanka Iyer (Integration Developer), Omar Haddad (Northwind Information Security)

## 1. Interface build status
- 9 of 14 interfaces built and unit tested.
- Store inventory availability API (CR-003): first version deployed to SIT, p95 response time 240 ms against the 300 ms target.
- Payment gateway integration: tokenization design complete.

## 2. PCI DSS
Omar Haddad confirmed the PCI DSS review with Northwind's Qualified Security Assessor (QSA) is booked for **2026-04-14** (RSK-016). Card data must remain tokenized and never be stored in the order management database. Live payment flows cannot enter SIT until the QSA signs off.

## 3. SIT environment outage
TLS certificates expired in the SIT environment on 2026-03-16, breaking integration tests for two days (ISS-012). Certificates were renewed and automated renewal has been enabled through Azure Key Vault. Issue closed today.

## 4. Actions
- David Okafor: send the tokenization design pack to the QSA by 2026-04-03.
- Priyanka Iyer: performance test the inventory API at 3x peak load.
