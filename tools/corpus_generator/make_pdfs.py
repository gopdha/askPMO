from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
OUT="/home/claude/project-atlas/corpus/06_finance_resourcing/"
GOV="/home/claude/project-atlas/corpus/01_governance/"
ss=getSampleStyleSheet()
H1=ss['Title']; H2=ss['Heading2']; B=ss['BodyText']
cell=ParagraphStyle('cell',parent=B,fontSize=8.5,leading=10.5)
def P(t): return Paragraph(t,B)
def tbl(data, widths=None, bold_last=False):
    data=[[Paragraph(str(c),cell) for c in r] for r in data]
    t=Table(data,colWidths=widths,repeatRows=1)
    st=[('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCE6F1')),('VALIGN',(0,0),(-1,-1),'TOP')]
    if bold_last: st.append(('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#F2F2F2')))
    t.setStyle(TableStyle(st)); return t
def doc(path,title,author):
    return SimpleDocTemplate(path,pagesize=letter,title=title,author=author,leftMargin=0.8*inch,rightMargin=0.8*inch,topMargin=0.8*inch,bottomMargin=0.8*inch)

# ---------------- SOW ----------------
s=[]
s+= [Paragraph("Statement of Work – Project Atlas",H1),
 P("<b>SOW number:</b> NRG-COB-2026-01 &nbsp;&nbsp; <b>Effective date:</b> 2026-01-09"),
 P("<b>Between:</b> Northwind Retail Group, Inc. (\"Client\") and Cobalt Systems LLC (\"Supplier\"), under the Master Services Agreement dated 2023-05-01."),Spacer(1,8),
 Paragraph("1. Purpose",H2),
 P("This Statement of Work describes the services Supplier will provide to migrate Client's Meridian order management system and enterprise data warehouse from the Client's Dallas data center to Microsoft Azure, modernize the order management application, and support the production cutover and hypercare. The program is known as Project Atlas."),
 Paragraph("2. Scope of Services",H2),
 P("2.1 Supplier will design and build the Azure landing zone, including networking, identity and security controls."),
 P("2.2 Supplier will migrate order history (approximately 2.3 TB), customer master, product master and open orders, and will reconcile record counts and order value totals."),
 P("2.3 Supplier will re-platform and modernize the order management application and build integrations with POS, e-commerce, payment gateway, warehouse management and ERP systems."),
 P("2.4 Supplier will execute system integration testing, support user acceptance testing, plan and execute cutover, and provide 5 weeks of hypercare after go-live."),
 P("2.5 Out of scope: loyalty program platform changes, mobile POS devices and replacement of the warehouse management system."),
 Paragraph("3. Fees",H2),
 P("3.1 The services are provided on a fixed-price basis of <b>$4,800,000</b> (four million eight hundred thousand US dollars), excluding Azure consumption costs, which are paid directly by Client."),
 P("3.2 Approved change requests are priced at the rate card in Appendix A and added to the fixed price by written amendment."),
 Paragraph("4. Payment Milestones",H2),
 tbl([["Payment milestone","Program milestone","% of fixed price","Amount"],
      ["PM-1","M1 – Azure landing zone ready","20%","$960,000"],
      ["PM-2","M3 – Order management application build complete","25%","$1,200,000"],
      ["PM-3","M5 – UAT complete","25%","$1,200,000"],
      ["PM-4","M7 – Hypercare end","30%","$1,440,000"]],[1.0*inch,3.0*inch,1.1*inch,1.1*inch]),Spacer(1,6),
 P("Invoices are payable within 45 days of receipt. Each payment milestone requires written acceptance by the Client Program Director."),
 Paragraph("5. Key Personnel",H2),
 P("Supplier's Program Manager (Arjun Mehta) and the five workstream leads are designated Key Personnel. Supplier will not replace Key Personnel without 30 days' notice and Client's consent, except in cases of resignation, illness or termination of employment."),
 Paragraph("6. Service Levels During Hypercare",H2),
 tbl([["Priority","Definition","Response time","Resolution target"],
      ["P1","Order taking stopped in multiple stores or on e-commerce","30 minutes","4 hours"],
      ["P2","Major function degraded, workaround available","2 hours","1 business day"],
      ["P3","Minor defect or cosmetic issue","1 business day","10 business days"]],[0.8*inch,3.0*inch,1.2*inch,1.3*inch]),Spacer(1,6),
 P("6.2 The modernized order management service shall achieve 99.9% monthly availability, measured from go-live, excluding agreed maintenance windows."),
 P("6.3 If Supplier misses the P1 resolution target more than twice in a calendar month during hypercare, Client may withhold 5% of payment milestone PM-4 until a remediation plan is accepted."),
 Paragraph("7. Acceptance",H2),
 P("Each deliverable will be reviewed by Client within 10 business days of submission. Deliverables not rejected in writing within that period are deemed accepted."),
 Paragraph("8. Client Responsibilities",H2),
 P("Client will provide business subject matter experts at 50% allocation during design and UAT, timely access to source systems, and decisions within 5 business days of a request."),
 Paragraph("9. Subcontractors",H2),
 P("9.1 Supplier will engage DataBridge Solutions, Inc. as a subcontractor to supply the DataBridge Migrate tool, including Oracle connector v3.2, and associated migration engineering support."),
 P("9.2 Supplier remains fully responsible for the performance of its subcontractors under this SOW."),
 P("9.3 <b>Subcontractor delay service credits.</b> The subcontract between Supplier and DataBridge Solutions shall provide service credits of 2% of DataBridge's monthly fees for each full week of delay beyond a committed delivery date, capped at 10% of monthly fees. Supplier shall pass 100% of any service credits received through to Client as a reduction of its next invoice."),
 Paragraph("10. Term and Termination",H2),
 P("This SOW runs from the effective date until the end of hypercare or 2026-12-31, whichever comes first. Either party may terminate for material breach not cured within 30 days of written notice."),
 Paragraph("11. Signatures",H2),
 P("Signed for Northwind Retail Group: Laura Bennett, Chief Information Officer, 2026-01-09."),
 P("Signed for Cobalt Systems: Victor Alvarez, Managing Director, 2026-01-09."),
 PageBreak(), Paragraph("Appendix A – Rate Card for Change Requests",H2),
 tbl([["Role","Location","Hourly rate"],["Program / Project Manager","Onshore (US)","$185"],["Solution Architect","Onshore (US)","$175"],["Senior Engineer","Onshore (US)","$150"],["Engineer","Offshore (Chennai, India)","$48"],["Test Analyst","Offshore (Chennai, India)","$40"]],[2.4*inch,2.4*inch,1.2*inch]),
]
doc(GOV+"SOW_NRG-COB-2026-01_project_atlas.pdf","Statement of Work - Project Atlas","Cobalt Systems").build(s)

# ---------------- Budget burn ----------------
s=[Paragraph("Project Atlas – Monthly Budget Burn Report",H1),
 P("<b>Reporting period:</b> March 2026 &nbsp;&nbsp; <b>Data as of:</b> 2026-03-31 &nbsp;&nbsp; <b>Published:</b> 2026-04-02"),
 P("<b>Prepared by:</b> Rachel Moore (Finance Controller, Northwind) and Neha Kapoor (PMO Analyst, Cobalt)"),Spacer(1,8),
 Paragraph("1. Summary",H2),
 P("Total actual spend to date is $1,955,000 against planned spend to date of $1,870,000, or 104.5% of plan. The revised approved budget, including CR-003, CR-005 and CR-007, is $5,345,000. One workstream, WS2 Data Migration, breaches the 10% over-budget tolerance."),
 Paragraph("2. Spend by workstream (USD thousands)",H2),
 tbl([["Workstream","Baseline budget","Approved CRs","Revised budget","Planned to date","Actual to date","% of plan","Status"],
  ["WS1 Infrastructure &amp; Landing Zone","900","+140 (CR-005)","1,040","610","595","97.5%","Within tolerance"],
  ["WS2 Data Migration","1,100","+240 (CR-007)","1,340","420","560","133.3%","Over budget"],
  ["WS3 Application Modernization","1,400","0","1,400","520","470","90.4%","Within tolerance"],
  ["WS4 Integration &amp; APIs","800","+85 (CR-003)","885","230","245","106.5%","Within tolerance"],
  ["WS5 Testing &amp; Cutover","600","+80 (CR-007)","680","90","85","94.4%","Within tolerance"],
  ["Total","4,800","+545","5,345","1,870","1,955","104.5%","Watch"]],
  [1.45*inch,0.65*inch,0.85*inch,0.65*inch,0.65*inch,0.65*inch,0.65*inch,0.85*inch],bold_last=True),
 Paragraph("3. Variance commentary",H2),
 P("<b>WS2 Data Migration (133.3% of plan, +$140,000):</b> Overspend is driven by extended DataBridge performance testing after ISS-009 and two additional data engineering contractors engaged for the customer master cleansing sprint (RSK-011). Part of the CR-007 funding covers this from April onward."),
 P("<b>WS4 Integration &amp; APIs (106.5% of plan):</b> Slightly ahead of plan because the store inventory availability API (CR-003) started earlier than scheduled. Within tolerance."),
 P("<b>WS3 Application Modernization (90.4% of plan):</b> Under plan due to two open developer positions filled late in February."),
 Paragraph("4. Forecast at completion",H2),
 tbl([["Workstream","Revised budget","Estimate at completion (EAC)","Forecast variance"],
  ["WS1","1,040","1,040","0"],["WS2","1,340","1,515","+175"],["WS3","1,400","1,400","0"],["WS4","885","885","0"],["WS5","680","680","0"],["Total","5,345","5,520","+175"]],
  [1.4*inch,1.4*inch,2.0*inch,1.4*inch],bold_last=True),Spacer(1,6),
 P("The program is forecast to finish $175,000 (3.3%) over the revised budget, entirely in WS2. Expected DataBridge service credits under SOW section 9.3 could offset up to $48,000 of this. A recovery plan for WS2 will be presented at the April Steering Committee."),
]
doc(OUT+"budget_burn_report_2026-03.pdf","Project Atlas Budget Burn Report March 2026","Northwind Finance / Cobalt PMO").build(s)

# ---------------- Resource plan ----------------
rows=[["Name","Role","Workstream","Organization","Location","Allocation","Period"],
 ["Arjun Mehta","Program Manager","PMO","Cobalt Systems","Dallas, US","100%","Jan–Sep 2026"],
 ["Neha Kapoor","PMO Analyst","PMO","Cobalt Systems","Dallas, US","100%","Jan–Sep 2026"],
 ["Priya Raman","Workstream Lead","WS1","Cobalt Systems","Dallas, US","100%","Jan–Jun 2026"],
 ["Marcus Chen","Workstream Lead","WS2","Cobalt Systems","Dallas, US","100%","Jan–Sep 2026"],
 ["Ravi Shankar","Lead Data Architect","WS2","Cobalt Systems","Dallas, US","100%","Jan 2026 – 2026-04-17"],
 ["Ana Gomez","Lead Data Architect (backfill)","WS2","Cobalt Systems","Dallas, US","100%","From 2026-04-13"],
 ["Elena Rossi","Workstream Lead","WS3","Cobalt Systems","Austin, US","100%","Jan–Sep 2026"],
 ["David Okafor","Workstream Lead","WS4","Cobalt Systems","Dallas, US","100%","Jan–Sep 2026"],
 ["Priyanka Iyer","Integration Developer","WS4","Cobalt Systems","Chennai, India","100%","Feb–Aug 2026"],
 ["Sarah Lindqvist","Workstream Lead","WS5","Cobalt Systems","Dallas, US","100%","Feb–Sep 2026"],
 ["Lena Fischer","Solutions Engineer","WS2","DataBridge Solutions","Remote","50%","Feb–Aug 2026"],
 ["Omar Haddad","Information Security Advisor","WS4","Northwind Retail Group","Dallas, US","25%","Feb–Aug 2026"]]
teams=[["Team","Workstream","Location","Headcount (FTE)","Notes"],
 ["Cloud engineers","WS1","Chennai, India","4","Ramps down after June 2026"],
 ["Data engineers","WS2","Chennai, India","6","Plus 2 contractors for cleansing sprint, Feb–Apr 2026"],
 ["Application developers","WS3","Chennai, India / Austin, US","12","8 offshore, 4 onshore"],
 ["Integration developers","WS4","Chennai, India","5","Includes 1 added for CR-003"],
 ["Test analysts","WS5","Chennai, India","6","Scales to 9 during SIT and UAT"]]
s=[Paragraph("Project Atlas – Resource Plan",H1),
 P("<b>Version:</b> 3.0 &nbsp;&nbsp; <b>Date:</b> 2026-04-01 &nbsp;&nbsp; <b>Owner:</b> Arjun Mehta, Program Manager"),Spacer(1,8),
 Paragraph("1. Named key roles",H2), tbl(rows,[1.0*inch,1.4*inch,0.7*inch,1.1*inch,0.9*inch,0.6*inch,1.1*inch]),
 Paragraph("2. Delivery teams",H2), tbl(teams,[1.4*inch,0.8*inch,1.6*inch,1.0*inch,2.0*inch]),
 Paragraph("3. Headcount profile",H2),
 P("Total program headcount is 39 in April 2026 and peaks at 42 between May and July 2026 during SIT, UAT and mock runs. About 75% of the delivery team is based offshore in Chennai, India, with a time-zone gap of 10.5 to 11.5 hours managed through a daily 08:00 CT stand-up."),
 Paragraph("4. Changes in this version",H2),
 P("Version 3.0 adds Ana Gomez as backfill for lead data architect Ravi Shankar (RSK-019), with a one-week overlap from 2026-04-13 to 2026-04-17, and extends WS2 and WS5 resources to September 2026 in line with CR-007."),
]
doc(OUT+"resource_plan_v3.0.pdf","Project Atlas Resource Plan v3.0","Cobalt Systems").build(s)
print("pdfs ok")
