import datetime as dt
from pathlib import Path
OUT=Path("/home/claude/project-atlas/corpus/02_status_reports")
start=dt.date(2026,1,16)
WS=["WS1 – Infrastructure & Landing Zone","WS2 – Data Migration","WS3 – Application Modernization","WS4 – Integration & APIs","WS5 – Testing & Cutover"]
LEADS=["Priya Raman","Marcus Chen","Elena Rossi","David Okafor","Sarah Lindqvist"]

W = {
1: dict(overall="Green", ws=["Green"]*5,
  summary="Project Atlas kicked off on 2026-01-12. The program charter was approved by Laura Bennett on 2026-01-14. All workstreams are mobilized and on track.",
  done=["Program kickoff held on 2026-01-12 with Northwind and Cobalt leadership.","Program charter v1.0 approved on 2026-01-14.","Azure subscriptions and access provisioned for the core team.","Data migration tooling licenses for DataBridge Migrate activated."],
  next=["Landing zone design workshops (WS1).","Start data profiling of the Meridian database (WS2).","Order management design workshops with Northwind SMEs (WS3)."],
  risks=["RSK-003 – Business SME availability over holidays (Low)."]),
2: dict(overall="Green", ws=["Green"]*5,
  summary="Design activities progressing well. CR-001 approved to move to 2-week sprints.",
  done=["Landing zone high-level design approved.","CR-001 approved on 2026-01-21: delivery sprints move from 3-week to 2-week cadence.","Integration inventory completed: 14 interfaces identified across POS, e-commerce, payments, WMS and ERP."],
  next=["Raise Azure quota increase request for East US 2 (RSK-007).","Begin data profiling on customer and order tables."],
  risks=["RSK-003 – Business SME availability over holidays (Low).","RSK-007 – Azure subscription quota limits in East US 2 (Medium)."]),
3: dict(overall="Green", ws=["Green","Amber","Green","Green","Green"],
  summary="First Steering Committee (SC-01) held on 2026-01-28; East US 2 confirmed as primary region. Data profiling surfaced customer master quality concerns, so WS2 is Amber.",
  done=["SC-01 held on 2026-01-28; DEC-003 confirmed East US 2 as primary Azure region.","Data profiling found a 12% duplicate rate in the Meridian customer master; raised as RSK-011.","RSK-003 closed after design workshops were rescheduled."],
  next=["Agree deduplication rules with Northwind data owners.","Submit landing zone build plan."],
  risks=["RSK-011 – Data quality in legacy customer master (High).","RSK-007 – Azure quota limits (Medium)."]),
4: dict(overall="Amber", ws=["Amber","Amber","Green","Green","Green"],
  summary="Overall status moved to Amber. The ExpressRoute circuit provisioning is delayed by the carrier (ISS-004), threatening milestone M1. DataBridge has signalled a slip in the beta of connector v3.2 (RSK-014).",
  done=["CR-002 (mobile POS) withdrawn by Northwind Store Operations on 2026-02-02.","CR-003 (store inventory availability API) submitted, estimate $85,000.","Cutover strategy v1.0 (big bang approach) published on 2026-02-02."],
  next=["Escalate ExpressRoute delay through the Microsoft account team.","Weekly checkpoint with DataBridge on connector v3.2 delivery."],
  risks=["ISS-004 – ExpressRoute circuit provisioning delayed (High).","RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-011 – Data quality in legacy customer master (High)."]),
5: dict(overall="Amber", ws=["Amber","Amber","Green","Green","Green"],
  summary="Status remains Amber. CR-003 approved. Azure quota increase granted, closing RSK-007. ExpressRoute still pending.",
  done=["CR-003 approved on 2026-02-11 by Tom Harris; WS4 budget increases to $885,000.","CR-004 approved on 2026-02-12: UAT pilot stores moved from the Houston to the Austin region.","Azure quota increase approved by Microsoft on 2026-02-10; RSK-007 closed.","CR-005 (disaster recovery region) raised by Laura Bennett."],
  next=["Run data migration performance test on representative order history (WS2).","Present CR-005 to the February SteerCo."],
  risks=["ISS-004 – ExpressRoute circuit provisioning delayed (High).","RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-016 – PCI DSS compliance sign-off for payment integration (Medium)."]),
6: dict(overall="Red", ws=["Amber","Red","Green","Green","Amber"],
  summary="Overall status is Red. The data migration performance test on 2026-02-17 achieved only 18 GB per hour against the 50 GB per hour needed to move the 2.3 TB order history within the 48-hour cutover window (ISS-009). The June 15 go-live is at serious risk and options are being assessed.",
  done=["Performance test executed on 2026-02-17; results logged as ISS-009.","Data migration deep-dive held on 2026-02-18 with DataBridge.","Order management core services scaffolding complete (WS3)."],
  next=["Prepare recovery options for the Steering Committee.","Obtain DataBridge commitment on connector v3.2 performance fixes."],
  risks=["ISS-009 – Data migration throughput below requirement (Critical).","RSK-014 – DataBridge connector v3.2 delivery slipping (High).","ISS-004 – ExpressRoute circuit provisioning delayed (High)."]),
7: dict(overall="Red", ws=["Amber","Red","Green","Green","Amber"],
  summary="Overall status remains Red. Milestone M1 (landing zone ready) missed its 2026-02-27 date because of ISS-004; new forecast is 2026-03-06. CR-005 approved at SC-02. CR-007 raised to re-plan go-live; a special SteerCo is scheduled for 2026-03-04.",
  done=["SC-02 held on 2026-02-25; CR-005 (disaster recovery region, $140,000) approved.","CR-006 (extra performance test cycle) raised by Marcus Chen.","CR-007 (go-live re-plan) raised by Arjun Mehta on 2026-02-27."],
  next=["Special Steering Committee (SC-03) on 2026-03-04 to decide on CR-007.","Complete ExpressRoute cutover and landing zone validation."],
  risks=["ISS-009 – Data migration throughput below requirement (Critical).","RSK-014 – DataBridge connector v3.2 delivery slipping (High).","ISS-004 – ExpressRoute circuit provisioning delayed (High)."]),
8: dict(overall="Amber", ws=["Green","Amber","Green","Green","Amber"],
  summary="Overall status improved to Amber. At the special SteerCo (SC-03) on 2026-03-04, CR-007 was approved and go-live moved from 2026-06-15 to 2026-08-17. A hybrid cutover approach was adopted (DEC-006). Milestone M1 achieved on 2026-03-06.",
  done=["CR-007 approved on 2026-03-04; new go-live date 2026-08-17; cost impact $320,000.","DEC-006: hybrid cutover approach adopted.","CR-006 closed as superseded by CR-007.","ExpressRoute circuit live on 2026-03-05; ISS-004 closed.","M1 Azure landing zone ready – achieved 2026-03-06 (one week late).","Formal notice of delay sent to DataBridge on 2026-03-06 (ACT-021)."],
  next=["Publish re-baselined integrated plan.","Vendor review meeting with DataBridge on 2026-03-11."],
  risks=["ISS-009 – Data migration throughput below requirement (Critical).","RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-021 – Go-live slipping into retail freeze (Low)."]),
9: dict(overall="Amber", ws=["Green","Amber","Green","Green","Green"],
  summary="Status Amber. The re-baselined plan has been published. In the vendor review on 2026-03-11, DataBridge committed to deliver connector v3.2 by 2026-04-30. An Azure Data Factory fallback proof of concept has started.",
  done=["Re-baselined plan v2 published on 2026-03-10.","DataBridge vendor review held on 2026-03-11; v3.2 committed for 2026-04-30.","ACT-024 opened: Azure Data Factory fallback proof of concept, due 2026-04-24."],
  next=["Publish cutover strategy v2.0 reflecting the hybrid approach.","Start MDM cleansing sprint for customer master (RSK-011)."],
  risks=["RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-011 – Data quality in legacy customer master (High).","RSK-016 – PCI DSS compliance sign-off (Medium)."]),
10: dict(overall="Amber", ws=["Green","Amber","Green","Amber","Green"],
  summary="Status Amber. Cutover strategy v2.0 published. WS4 moved to Amber after the SIT certificate outage (ISS-012) and pending PCI review. Order management application build is 55% complete.",
  done=["Cutover strategy v2.0 published on 2026-03-16.","Integration sync held on 2026-03-18; PCI QSA review booked for 2026-04-14.","ISS-012 (SIT certificate expiry) resolved on 2026-03-18.","Order management application build 55% complete (WS3).","CR-008 (loyalty module integration) raised by Jessica Park on 2026-03-16."],
  next=["Present CR-008 and March budget position at SC-04 on 2026-03-25.","Continue MDM cleansing sprint."],
  risks=["RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-016 – PCI DSS compliance sign-off (Medium).","RSK-018 – Test environment contention (Medium)."]),
11: dict(overall="Amber", ws=["Green","Amber","Green","Green","Green"],
  summary="Status Amber. At SC-04 on 2026-03-25, CR-008 was rejected and deferred to Phase 2. The budget review flagged WS2 Data Migration as over budget. The lead data architect has resigned (RSK-019).",
  done=["SC-04 held on 2026-03-25; CR-008 rejected and deferred to Phase 2 (DEC-008).","Budget review: WS2 spend running about one third above plan.","RSK-019 raised: lead data architect Ravi Shankar resigned, last day 2026-04-17.","Customer master duplicate rate reduced from 12% to 4.5% (RSK-011)."],
  next=["Close March financials and publish budget burn report.","Confirm backfill for lead data architect."],
  risks=["RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-011 – Data quality in legacy customer master (High).","RSK-019 – Lead data architect attrition (Medium)."]),
12: dict(overall="Amber", ws=["Green","Amber","Green","Green","Green"],
  summary="Status Amber. March budget burn report published: overall spend is 4.5% above plan, driven by WS2 Data Migration at 133% of planned spend to date. Backfill for the lead data architect confirmed. Go-live remains on track for 2026-08-17.",
  done=["March budget burn report (as of 2026-03-31) published.","Backfill confirmed: Ana Gomez joins on 2026-04-13 as lead data architect.","Azure Data Factory fallback proof of concept 40% complete (ACT-024).","Order management application build 68% complete (WS3)."],
  next=["Azure Data Factory fallback go/no-go decision by 2026-04-24.","DataBridge connector v3.2 delivery due 2026-04-30.","PCI QSA review on 2026-04-14."],
  risks=["RSK-014 – DataBridge connector v3.2 delivery slipping (High).","RSK-011 – Data quality in legacy customer master (High).","RSK-019 – Lead data architect attrition (Medium)."]),
}

def milestones(wk, date):
    base=[("M1","Azure landing zone ready","2026-02-27"),("M2","Data migration mock run 1 complete","2026-03-20"),("M3","Order management application build complete","2026-04-30"),("M4","SIT complete","2026-05-22"),("M5","UAT complete","2026-06-05"),("M6","Production go-live","2026-06-15"),("M7","Hypercare end","2026-07-17")]
    rows=[]
    for mid,name,b in base:
        if wk>=8:
            fc={"M1":"2026-03-06","M2":"2026-05-08","M3":"2026-04-30","M4":"2026-07-10","M5":"2026-07-31","M6":"2026-08-17","M7":"2026-09-18"}[mid]
        elif wk>=6:
            fc={"M1":"2026-03-06" if wk==7 else "2026-02-27"}.get(mid, "Under review" if mid in("M2","M4","M5","M6","M7") else b)
        else:
            fc=b
        if mid=="M1":
            st="Achieved" if wk>=8 else ("Missed – re-forecast" if wk==7 else ("At risk" if wk>=4 else "On track"))
        elif wk>=8: st="Re-baselined (CR-007)" if mid not in ("M3",) else "On track"
        elif wk>=6: st="At risk" if mid!="M3" else "On track"
        else: st="On track"
        rows.append(f"| {mid} | {name} | {b} | {fc} | {st} |")
    return "\n".join(rows)

for wk,d in W.items():
    date=start+dt.timedelta(7*(wk-1))
    golive="2026-08-17" if wk>=8 else ("2026-06-15 (under review)" if wk>=6 else "2026-06-15")
    md=f"""# Project Atlas – Weekly Status Report

| Field | Value |
|---|---|
| Report | Week {wk} |
| Week ending | {date.isoformat()} |
| Prepared by | Neha Kapoor, PMO Analyst |
| Reviewed by | Arjun Mehta, Program Manager |
| Overall status | **{d['overall']}** |
| Forecast go-live | {golive} |

## Executive summary
{d['summary']}

## Workstream status

| Workstream | Lead | Status |
|---|---|---|
""" + "\n".join(f"| {w} | {l} | {s} |" for w,l,s in zip(WS,LEADS,d['ws'])) + f"""

## Key accomplishments this week
""" + "\n".join(f"- {x}" for x in d['done']) + """

## Planned for next week
""" + "\n".join(f"- {x}" for x in d['next']) + """

## Top risks and issues
""" + "\n".join(f"- {x}" for x in d['risks']) + f"""

## Milestones

| ID | Milestone | Baseline | Forecast | Status |
|---|---|---|---|---|
{milestones(wk,date)}
"""
    (OUT/f"status_report_wk{wk:02d}_{date.isoformat()}.md").write_text(md)
print("done")
