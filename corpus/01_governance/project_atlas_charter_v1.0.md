# Project Atlas – Program Charter

| Field | Value |
|---|---|
| Document ID | ATL-GOV-001 |
| Version | 1.0 (Baseline) |
| Status | Approved |
| Approval date | 2026-01-14 |
| Approved by | Laura Bennett, CIO, Northwind Retail Group |
| Prepared by | Arjun Mehta, Program Manager, Cobalt Systems |

## 1. Background

Northwind Retail Group operates 340 stores across the United States and runs its order management on "Meridian", a legacy Oracle-based Order Management System (OMS) hosted in the company's Dallas data center, together with an on-premises enterprise data warehouse. The Dallas data center lease expires in December 2026, and Meridian's current hardware reaches end of support in the same quarter.

Project Atlas is the program to migrate Meridian and the data warehouse to Microsoft Azure, modernize the order management application, and decommission the on-premises footprint before the lease expires. Northwind has engaged Cobalt Systems as the systems integrator. DataBridge Solutions supplies the data migration tooling (DataBridge Migrate) under a sub-contract to Cobalt Systems.

## 2. Objectives

1. Migrate the order management platform and the enterprise data warehouse to Azure (primary region: East US 2).
2. Migrate the full order history, approximately 2.3 TB, with zero data loss and reconciled record counts.
3. Complete production cutover within a 48-hour cutover window to limit store and e-commerce downtime.
4. Achieve 99.9% monthly availability for the new order management service after go-live.
5. Decommission the Dallas data center footprint for Meridian by December 2026.

## 3. Scope

### In scope
- Azure landing zone, networking (including ExpressRoute connectivity to stores and the Dallas data center) and security baseline.
- Data migration of order history, customer master, product master and open orders.
- Re-platforming and modernization of the order management application.
- Integrations with POS, e-commerce storefront, payment gateway, warehouse management and finance (ERP).
- System integration testing (SIT), user acceptance testing (UAT), cutover and 5 weeks of hypercare.

### Out of scope
- Loyalty program platform changes.
- Mobile POS devices.
- Replacement of the warehouse management system itself.

## 4. Workstreams and Leads

| Workstream | Lead | Organization |
|---|---|---|
| WS1 – Infrastructure & Landing Zone | Priya Raman | Cobalt Systems |
| WS2 – Data Migration | Marcus Chen | Cobalt Systems (with DataBridge Solutions) |
| WS3 – Application Modernization (Order Management) | Elena Rossi | Cobalt Systems |
| WS4 – Integration & APIs | David Okafor | Cobalt Systems |
| WS5 – Testing & Cutover | Sarah Lindqvist | Cobalt Systems |

## 5. Key Milestones (Baseline)

| ID | Milestone | Baseline date |
|---|---|---|
| M1 | Azure landing zone ready | 2026-02-27 |
| M2 | Data migration mock run 1 complete | 2026-03-20 |
| M3 | Order management application build complete | 2026-04-30 |
| M4 | System integration testing (SIT) complete | 2026-05-22 |
| M5 | User acceptance testing (UAT) complete | 2026-06-05 |
| M6 | Production go-live | 2026-06-15 |
| M7 | Hypercare end | 2026-07-17 |

## 6. Budget

The approved baseline budget is **$4,800,000**, allocated as follows:

| Workstream | Baseline budget |
|---|---|
| WS1 – Infrastructure & Landing Zone | $900,000 |
| WS2 – Data Migration | $1,100,000 |
| WS3 – Application Modernization | $1,400,000 |
| WS4 – Integration & APIs | $800,000 |
| WS5 – Testing & Cutover | $600,000 |
| **Total** | **$4,800,000** |

A workstream is considered over budget when actual spend to date exceeds planned spend to date by more than 10%.

## 7. Governance

- **Executive Sponsor:** Laura Bennett, CIO, Northwind Retail Group.
- **Client Program Director:** Tom Harris, Northwind Retail Group.
- **Program Manager:** Arjun Mehta, Cobalt Systems.
- **PMO Analyst:** Neha Kapoor, Cobalt Systems.
- **Finance Controller:** Rachel Moore, Northwind Retail Group.

The Steering Committee (SteerCo) meets monthly, on the last Wednesday of the month, and may hold special sessions when a decision cannot wait. Weekly status reports are published every Friday by the PMO.

### Change control
All scope, schedule or budget changes require a Change Request (CR) logged in the change log.
- CRs with a cost impact **below $100,000** and no milestone impact may be approved by the Client Program Director.
- CRs with a cost impact of **$100,000 or more**, or any change to the go-live date, require Steering Committee approval.

### Escalation path
Workstream Lead → Program Manager → Client Program Director → Steering Committee.

## 8. Assumptions and Constraints

- DataBridge Migrate, with its Oracle connector v3.2, will sustain the throughput required to move the order history within the cutover window.
- Northwind business SMEs will be available at 50% allocation during design and UAT.
- No production changes are allowed during the retail freeze window from November 15 to January 5.
