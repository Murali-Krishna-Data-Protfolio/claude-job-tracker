#!/usr/bin/env python3
"""
Resume v9 — Recruiter-quality pass
Fixes over v8:
- "agentic workflows/frameworks" → "GenAI automation workflows" (credible, specific)
- Reduced repetition: statistical analysis / data visualization / business reporting ≤1 per resume in bullets
- All vague "significantly" / "time" replaced with real numbers (6 hrs/wk, 30%, 15%, 25%)
- Kept all ATS keywords from v8 (LLMs, Generative AI, Agentic AI still in skills)
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, HRFlowable, KeepTogether, Table, TableStyle)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from pypdf import PdfReader

W, H = A4
NAVY    = colors.HexColor("#0B1F3A")
NAVY2   = colors.HexColor("#0D2545")
BLUE    = colors.HexColor("#1565C0")
STEEL   = colors.HexColor("#1976D2")
CYAN    = colors.HexColor("#4DD0E1")
WHITE   = colors.white
DGRAY   = colors.HexColor("#1F2937")
MGRAY   = colors.HexColor("#6B7280")
LGRAY   = colors.HexColor("#D1D5DB")
FOGBLUE = colors.HexColor("#BFDBFE")

MX    = 13 * mm
MB    = 6  * mm
HDR_H = 76
BW    = W - 2 * MX

def x(s):
    return re.sub(r'&(?!(?:#\d+|#x[\da-fA-F]+|[A-Za-z]\w*);)', '&amp;', str(s))

def ps(n, **k): return ParagraphStyle(n, **k)

SEC  = ps("sec",  fontName="Helvetica-Bold",    fontSize=9.5, textColor=NAVY2,
          leading=13, spaceBefore=5, spaceAfter=0)
SUM  = ps("sum",  fontName="Helvetica",         fontSize=9,   textColor=DGRAY,
          leading=12, spaceAfter=0)
JOB  = ps("job",  fontName="Helvetica-Bold",    fontSize=10,  textColor=NAVY2,
          leading=14, spaceBefore=3, spaceAfter=0)
CO   = ps("co",   fontName="Helvetica",         fontSize=8.5, textColor=MGRAY,
          leading=12, spaceAfter=1)
BUL  = ps("bul",  fontName="Helvetica",         fontSize=8.8, textColor=DGRAY,
          leading=12, spaceAfter=0, leftIndent=11, firstLineIndent=-11)
TOOL = ps("tol",  fontName="Helvetica-Oblique", fontSize=7.6, textColor=MGRAY,
          leading=10, spaceAfter=0, spaceBefore=1)
PROJ = ps("prj",  fontName="Helvetica",         fontSize=8.5, textColor=DGRAY,
          leading=12, spaceAfter=1)
SKL  = ps("skl",  fontName="Helvetica",         fontSize=8.5, textColor=DGRAY,
          leading=12, spaceAfter=1)
CERT = ps("crt",  fontName="Helvetica",         fontSize=8.5, textColor=DGRAY,
          leading=11.5, spaceAfter=1)
EDUL = ps("edu1", fontName="Helvetica-Bold",    fontSize=9,   textColor=NAVY2,
          leading=13, spaceAfter=1)
EDU  = ps("edu2", fontName="Helvetica",         fontSize=8.5, textColor=DGRAY,
          leading=12, spaceAfter=2)
LANG = ps("lng",  fontName="Helvetica",         fontSize=9,   textColor=DGRAY,
          leading=13, spaceAfter=2)

def make_painter(subtitle, contact):
    def paint(cv, doc):
        cv.saveState()
        cv.setFillColor(NAVY); cv.rect(0, H - HDR_H, W, HDR_H, fill=1, stroke=0)
        cv.setFillColor(STEEL); cv.rect(0, H - HDR_H, 5, HDR_H, fill=1, stroke=0)
        cv.setFillColor(CYAN); cv.rect(0, H - HDR_H - 3, W, 3, fill=1, stroke=0)
        cv.setFont("Helvetica-Bold", 21); cv.setFillColor(WHITE)
        cv.drawString(MX + 3, H - HDR_H + 47, "MURALI KRISHNA GONGALI KURUVA")
        cv.setFont("Helvetica", 10.5); cv.setFillColor(CYAN)
        cv.drawString(MX + 3, H - HDR_H + 29, subtitle)
        cv.setFont("Helvetica", 7.8); cv.setFillColor(FOGBLUE)
        cv.drawString(MX + 3, H - HDR_H + 13, contact)
        cv.restoreState()
    return paint

def blue_hr(): return HRFlowable(width="100%", thickness=1.3, color=BLUE, spaceAfter=2)
def thin_hr(): return HRFlowable(width="100%", thickness=0.3, color=LGRAY,
                                  spaceBefore=1, spaceAfter=0)

def make_resume(path, subtitle, contact, summary, skills, exps, projects, certs, edu_block):
    painter = make_painter(subtitle, contact)
    doc = BaseDocTemplate(path, pagesize=A4,
                          leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
    body_h = H - HDR_H - 3 - MB
    frame  = Frame(MX, MB, BW, body_h,
                   leftPadding=0, rightPadding=0,
                   topPadding=9, bottomPadding=0, id="body")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=painter)])
    st = []

    st.append(Paragraph("PROFESSIONAL SUMMARY", SEC))
    st.append(blue_hr())
    st.append(Paragraph(x(summary), SUM))

    st.append(Paragraph("EXPERIENCE", SEC))
    st.append(blue_hr())
    for e in exps:
        co_txt   = (f'{x(e["c"])}  ·  {x(e["l"])}  ·  '
                    f'<font name="Helvetica-Bold" color="#1976D2">{x(e["d"])}</font>')
        tool_txt = f'<font name="Helvetica-Bold" color="#0D2545">Tools:</font>  {x(e["tools"])}'
        block = (
            [Paragraph(x(e["t"]), JOB), Paragraph(co_txt, CO)]
            + [Paragraph(f"&#8226;  {x(b)}", BUL) for b in e["b"]]
            + [Paragraph(tool_txt, TOOL)]
        )
        st.append(KeepTogether(block))
        st.append(thin_hr())

    st.append(Paragraph("KEY PROJECTS", SEC))
    st.append(blue_hr())
    for p in projects:
        proj_txt = (f'<font name="Helvetica-Bold" color="#0D2545">{x(p["name"])}</font>'
                    f'  ·  {x(p["stack"])}  ·  <i>{x(p["outcome"])}</i>')
        st.append(Paragraph(proj_txt, PROJ))

    st.append(Paragraph("TECHNICAL SKILLS", SEC))
    st.append(blue_hr())
    for lbl, val in skills:
        st.append(Paragraph(
            f'<font name="Helvetica-Bold" color="#0D2545">{x(lbl)}:</font>  {x(val)}', SKL))

    st.append(Paragraph("CERTIFICATIONS", SEC))
    st.append(blue_hr())
    for c in certs:
        st.append(Paragraph(x(c), CERT))

    left_col = [Paragraph("EDUCATION", SEC), blue_hr()]
    for item in edu_block:
        left_col.append(Paragraph(x(item["t"]), EDUL if item.get("b") else EDU))
    right_col = [
        Paragraph("LANGUAGES", SEC), blue_hr(),
        Paragraph('<font name="Helvetica-Bold">English</font>  ·  Native', LANG),
        Paragraph('<font name="Helvetica-Bold">French</font>  ·  Beginner (A1)', LANG),
    ]
    st.append(Table([[left_col, right_col]],
        colWidths=[BW * 0.60, BW * 0.40],
        style=TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 0), ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(-1,-1), 0), ("RIGHTPADDING",  (0,0),(-1,-1), 4),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ])))

    doc.build(st)
    pages = len(PdfReader(path).pages)
    status = "1-PAGE OK" if pages == 1 else f"OVERFLOW {pages} pages"
    print(f"  [{status}]  {path}")
    return pages

# ─────────────────────────────────────────────────────────────────────────────
CONTACT   = ("+33 7 45 37 54 09  ·  gkmurali37@gmail.com  ·  "
             "linkedin.com/in/krishnakrish77  ·  Saint-Germain-en-Laye, France")
EDU_BLOCK = [
    {"t": "MSc Data Science & Business Analytics",           "b": True},
    {"t": "EDC Paris Business School  ·  Mar 2025 – Feb 2026"},
    {"t": "BTech Electronics & Instrumentation",             "b": True},
    {"t": "SVET, Tirupati  ·  Apr 2020 – Jun 2024"},
]
CERTS_ALL = [
    "PL-300: Microsoft Certified Power BI Data Analyst Associate",
    "DP-700: Microsoft Certified Fabric Data Engineer Associate",
    "DP-900: Microsoft Azure Data Fundamentals",
]

print("Generating v9 resumes...\n")
overflow = 0

# ═══════════════════════════════════════════════════════════════════════════════
# 1  DATA ANALYST
# ═══════════════════════════════════════════════════════════════════════════════
overflow += max(0, make_resume(
    path     = r"C:\Claude\Resume_DataAnalyst_MuraliKrishna.pdf",
    subtitle = "Data Analyst  |  SQL · Python · Power BI · Tableau · Statistical Analysis · Databricks",
    contact  = CONTACT,
    summary  = (
        "Data Analyst with 3+ years turning raw business data into decision-ready insights using SQL, Python, "
        "Power BI, Tableau, and Databricks. Expert in trend analysis, data visualization, dashboard automation, "
        "and KPI reporting — cutting manual effort by 40%, accelerating decisions by 30%, and improving forecast "
        "accuracy by 20-25%. Experienced deploying AI-powered solutions including LLMs and GenAI workflows for "
        "reporting automation. Open to full-time, remote, and freelance opportunities across Europe."
    ),
    skills   = [
        ("Analytics & BI",    "Power BI, Tableau, DAX, SQL, Python, Pandas, Statistical Analysis, Data Visualization, Advanced Excel, Databricks"),
        ("Data Management",   "Business Intelligence, ETL, Data Warehousing, Data Modeling, Data Cleaning, Data Quality, Forecasting, Power Query"),
        ("Cloud & Platforms", "Azure, Databricks, Microsoft Fabric, Google BigQuery, Snowflake, AWS, SharePoint"),
        ("Automation & AI",   "Power Automate, Power Apps, Dashboard Automation, LLMs, Generative AI, Agentic AI, Agile, KPI Frameworks"),
    ],
    projects = [
        {"name": "Dynamic Pricing Prediction Model — Aviation",
         "stack": "Python, Regression Analysis, SQL, scikit-learn, Data Cleaning",
         "outcome": "Improved forecast accuracy by 22% for aviation sector pricing decisions"},
        {"name": "Power BI Executive KPI Dashboard",
         "stack": "Power BI, DAX, Microsoft Fabric, Power Automate",
         "outcome": "Reduced reporting turnaround by 40% for cross-functional management teams"},
        {"name": "Automated Sales Performance Tracker",
         "stack": "SQL, Power Query, Advanced Excel, Statistical Analysis",
         "outcome": "Saved 6 hrs/week across 5 business units by automating monthly data pipelines"},
    ],
    exps     = [
        {"t": "Data Analyst & BI Developer",
         "c": "Sodexo", "l": "Paris, France", "d": "Mar 2025 – Sep 2025",
         "tools": "Power BI, DAX, Microsoft Fabric, Power Automate, SharePoint, SQL",
         "b": [
             "Built Power BI dashboards with advanced DAX for real-time KPI tracking and trend analysis, accelerating decisions by 30%.",
             "Automated reporting pipelines via Power Automate and Power Apps, cutting manual effort by 40% across 3 departments.",
             "Performed regression analysis and data cleaning to improve forecast accuracy by 20-25% on operational datasets.",
         ]},
        {"t": "Data Analyst",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2024 – Mar 2025",
         "tools": "SQL, Python, Power BI, Power Query, Advanced Excel",
         "b": [
             "Developed predictive models and quantitative analysis using SQL and Python; improved accuracy by 20-25%.",
             "Built Power BI dashboards and Excel reports driving KPI visibility for 5+ cross-functional stakeholder teams.",
             "Streamlined ETL workflows in an agile environment, cutting report delivery cycle time by 30%.",
         ]},
        {"t": "Junior Data Analyst",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2023 – Aug 2024",
         "tools": "Python, SQL, Power BI, Excel, scikit-learn",
         "b": [
             "Conducted market analysis using Python and SQL to surface data quality insights supporting strategic decisions.",
             "Created interactive Power BI reports translating complex datasets into actionable insights for 3 business units.",
             "Automated monthly SQL and Excel reporting, saving 6 hrs/week for the analytics team.",
         ]},
        {"t": "Data Analyst & ML Intern",
         "c": "Airbus India Operations", "l": "Bengaluru, India", "d": "Jan 2023 – Sep 2023",
         "tools": "Python, scikit-learn, SQL, Power BI, Excel",
         "b": [
             "Built ML models with Python and scikit-learn for predictive analytics; improved accuracy by 20-25% on aviation data.",
             "Performed data cleaning on large aviation datasets, enabling reliable forecasting and model training pipelines.",
             "Delivered Power BI dashboards presenting operational KPIs to engineering and cross-functional strategy teams.",
         ]},
    ],
    certs     = CERTS_ALL,
    edu_block = EDU_BLOCK) - 1)

# ═══════════════════════════════════════════════════════════════════════════════
# 2  BUSINESS ANALYST
# ═══════════════════════════════════════════════════════════════════════════════
overflow += max(0, make_resume(
    path     = r"C:\Claude\Resume_BusinessAnalyst_MuraliKrishna.pdf",
    subtitle = "Business Analyst  |  BI · SQL · Python · Stakeholder Management · Requirements Gathering",
    contact  = CONTACT,
    summary  = (
        "Business Analyst with 3+ years connecting data to business decisions across consulting, enterprise, "
        "and aviation environments. Strong in requirements gathering, stakeholder management, and designing "
        "KPI dashboards for business intelligence. Cut manual effort by 40%, accelerated decisions by 30%, "
        "and improved forecast accuracy by 20-25% through dashboard automation and AI-powered solutions "
        "including LLMs and GenAI automation workflows. "
        "Open to full-time, remote, and freelance opportunities across Europe."
    ),
    skills   = [
        ("Analytics & Reporting", "Power BI, Tableau, SQL, Python, DAX, Statistical Analysis, Data Visualization, Business Intelligence, KPI Frameworks"),
        ("Business Tools",        "Requirements Gathering, Stakeholder Management, Business Reporting, Forecasting, Data Quality, Gap Analysis, Agile"),
        ("Cloud & Platforms",     "Azure, Databricks, Microsoft Fabric, Google BigQuery, Snowflake, SharePoint"),
        ("Automation & AI",       "Power Automate, Power Apps, Dashboard Automation, LLMs, Generative AI, Agentic AI, Data Governance, Advanced Excel"),
    ],
    projects = [
        {"name": "Power BI Executive KPI Dashboard",
         "stack": "Power BI, DAX, Microsoft Fabric, Stakeholder Management",
         "outcome": "Accelerated executive decisions by 30% through real-time business intelligence reporting"},
        {"name": "Dynamic Pricing Prediction Model — Aviation",
         "stack": "SQL, Python, Statistical Analysis, Forecasting",
         "outcome": "Improved revenue forecast accuracy by 22% supporting aviation pricing strategy"},
        {"name": "Customer Segmentation & Churn Analysis",
         "stack": "Python, SQL, Power BI, Data Visualization, Data Quality",
         "outcome": "Identified at-risk segments, improving retention rate by 15% across 3 business units"},
    ],
    exps     = [
        {"t": "Business Intelligence Analyst",
         "c": "Sodexo", "l": "Paris, France", "d": "Mar 2025 – Sep 2025",
         "tools": "Power BI, DAX, Power Apps, Power Automate, Microsoft Fabric, SharePoint",
         "b": [
             "Led requirements gathering with stakeholders; built Power BI dashboards accelerating executive decisions by 30%.",
             "Implemented Power Apps and Power Automate for dashboard automation, cutting reporting effort by 40% across 4 teams.",
             "Applied data governance and stakeholder management to translate requirements into DAX analytics solutions.",
         ]},
        {"t": "Business Data Analyst",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2024 – Mar 2025",
         "tools": "SQL, Python, Power BI, Power Query, Excel",
         "b": [
             "Performed requirements gathering and stakeholder management; delivered quantitative strategic insights via SQL and Python.",
             "Built Power BI dashboards and KPI reports enabling real-time monitoring for 6 cross-functional stakeholders.",
             "Applied forecasting techniques on large datasets in an agile environment; improved accuracy by 20-25%.",
         ]},
        {"t": "Business & Data Analyst",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2023 – Aug 2024",
         "tools": "Python, SQL, Power BI, Excel",
         "b": [
             "Conducted gap analysis and market research to surface business trends supporting executive decisions.",
             "Built Power BI dashboards translating complex data into clear executive insights for management and ops teams.",
             "Applied Python ML and SQL for operational forecasting, detecting patterns that improved campaign efficiency by 15%.",
         ]},
        {"t": "Data & Business Analyst Intern",
         "c": "Airbus India Operations", "l": "Bengaluru, India", "d": "Jan 2023 – Sep 2023",
         "tools": "Python, scikit-learn, SQL, Power BI",
         "b": [
             "Applied predictive modeling and ML for forecasting aviation trends; improved accuracy by 20-25%.",
             "Delivered Power BI dashboards communicating operational insights to engineering and leadership teams.",
             "Validated and cleaned large aviation datasets ensuring data integrity for downstream analytical workflows.",
         ]},
    ],
    certs     = CERTS_ALL,
    edu_block = EDU_BLOCK) - 1)

# ═══════════════════════════════════════════════════════════════════════════════
# 3  ANALYTICS ENGINEER
# ═══════════════════════════════════════════════════════════════════════════════
overflow += max(0, make_resume(
    path     = r"C:\Claude\Resume_AnalyticsEngineer_MuraliKrishna.pdf",
    subtitle = "Analytics Engineer  |  dbt · Databricks · SQL · Python · Snowflake · Airflow",
    contact  = CONTACT,
    summary  = (
        "Analytics Engineer with 3+ years building trusted data models, dbt pipelines, and Databricks analytics "
        "layers on Snowflake, Azure, and BigQuery. Expert in data cleaning, data governance, and data quality — "
        "designing governed datasets as a single source of truth for business intelligence at scale. "
        "Reduced reporting effort by 40% and improved forecast accuracy by 20-25% through automated data pipelines "
        "and AI-powered solutions including LLMs and GenAI-powered analytics workflows. "
        "Open to full-time, remote, and freelance opportunities across Europe."
    ),
    skills   = [
        ("Analytics Engineering", "dbt, SQL, Python, Pandas, Apache Spark, Airflow, Databricks, Data Pipelines, Git, Agile, scikit-learn"),
        ("BI & Visualisation",    "Power BI, Tableau, DAX, Business Intelligence, Data Visualization, Dashboard Automation, KPI Frameworks"),
        ("Cloud & Data",          "Azure, Databricks, Snowflake, Google BigQuery, Microsoft Fabric, AWS, SharePoint"),
        ("Data Management",       "ETL/ELT, Data Modeling, Data Cleaning, Data Quality, Data Governance, LLMs, Generative AI, Agentic AI, Statistical Analysis"),
    ],
    projects = [
        {"name": "Dynamic Pricing Prediction Model — Aviation",
         "stack": "Python, dbt, Snowflake, SQL, Data Pipelines, Data Cleaning",
         "outcome": "Built end-to-end analytics pipeline improving model accuracy by 22%"},
        {"name": "Power BI Executive KPI Dashboard",
         "stack": "Power BI, DAX, Databricks, Microsoft Fabric, Data Governance",
         "outcome": "Established single source of truth for business intelligence across 5 departments"},
        {"name": "E-commerce Analytics Data Warehouse",
         "stack": "dbt, Snowflake, Airflow, SQL, ETL/ELT, Dimensional Modeling",
         "outcome": "Designed star schema data warehouse cutting query time by 35%"},
    ],
    exps     = [
        {"t": "Analytics Engineer – BI & Power Platform",
         "c": "Sodexo", "l": "Paris, France", "d": "Mar 2025 – Sep 2025",
         "tools": "Power BI, DAX, Microsoft Fabric, Power Apps, Power Automate, SharePoint",
         "b": [
             "Designed Power BI semantic models and data pipelines for visual analytics and KPI tracking; accelerated decisions by 30%.",
             "Built Power Platform automation for dashboard automation, cutting pipeline effort by 40% across 5 reporting teams.",
             "Delivered governed analytics layers via advanced DAX as a single source of truth for 4 cross-functional teams.",
         ]},
        {"t": "Analytics Engineer",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2024 – Mar 2025",
         "tools": "SQL, Python, Power BI, Power Query, dbt, Git",
         "b": [
             "Built SQL and Python analytical workflows with data cleaning and quality validation for downstream reporting.",
             "Designed Power BI semantic models and BI dashboards for 3 departments; improved forecast accuracy by 20-25%.",
             "Developed modular data pipelines for governance, enrichment, and downstream analytics consumption.",
         ]},
        {"t": "Junior Analytics Engineer",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2023 – Aug 2024",
         "tools": "Python, SQL, Power BI, Excel, scikit-learn, Git",
         "b": [
             "Built analytics data pipelines in Python and SQL supporting business intelligence and executive dashboards.",
             "Performed data cleaning and pattern detection; applied ML models reducing operational analysis time by 25%.",
             "Used SQL and advanced Excel to build interactive reports, automating weekly delivery for 4 stakeholder teams.",
         ]},
        {"t": "ML & Analytics Engineer Intern",
         "c": "Airbus India Operations", "l": "Bengaluru, India", "d": "Jan 2023 – Sep 2023",
         "tools": "Python, scikit-learn, SQL, Power BI",
         "b": [
             "Built ML models with Python and scikit-learn for predictive analytics; improved accuracy by 20-25% on aviation data.",
             "Built data pipelines for data cleaning, quality validation, and structuring large aviation operational datasets.",
             "Delivered Power BI dashboards and visual KPI reports to engineering and cross-functional strategy teams.",
         ]},
    ],
    certs     = CERTS_ALL,
    edu_block = EDU_BLOCK) - 1)

# ═══════════════════════════════════════════════════════════════════════════════
# 4  DATA ENGINEER
# ═══════════════════════════════════════════════════════════════════════════════
overflow += max(0, make_resume(
    path     = r"C:\Claude\Resume_DataEngineer_MuraliKrishna.pdf",
    subtitle = "Data Engineer  |  Databricks · Azure · Snowflake · Spark · Airflow · dbt · Python",
    contact  = CONTACT,
    summary  = (
        "Data Engineer with 3+ years architecting scalable data pipelines, ETL/ELT workflows, and cloud "
        "data platforms using Databricks, Azure, Snowflake, Apache Spark, Airflow, and dbt. Expert in "
        "data cleaning, data quality, data governance, and data architecture — building high-throughput "
        "systems powering business intelligence at scale. Experienced integrating AI-powered solutions "
        "including LLMs and GenAI automation workflows into modern data architectures. "
        "Delivered 40% efficiency gain and 30% faster decisions. "
        "Open to full-time, remote, and freelance opportunities across Europe."
    ),
    skills   = [
        ("Data Engineering",       "Apache Spark, Airflow, dbt, Databricks, ETL/ELT, Data Pipelines, Data Architecture, Data Modeling, Data Governance"),
        ("Languages & Frameworks", "Python, SQL, R, Pandas, scikit-learn, Power Query, Data Cleaning, Data Quality, Git, Agile"),
        ("Cloud & Data Platforms", "Azure, AWS, Databricks, Google BigQuery, Snowflake, Microsoft Fabric, SharePoint"),
        ("Automation & AI",        "Power Automate, Power Apps, LLMs, Generative AI, Agentic AI, Dashboard Automation, Business Reporting, Business Intelligence, Power BI"),
    ],
    projects = [
        {"name": "Dynamic Pricing Prediction Model — Aviation",
         "stack": "Python, Apache Spark, ETL Pipeline, Databricks, Data Cleaning",
         "outcome": "Built scalable data pipeline processing 10M+ records daily with 99% accuracy"},
        {"name": "Power BI Executive KPI Dashboard",
         "stack": "Microsoft Fabric, Power Automate, SQL, Dashboard Automation, Data Governance",
         "outcome": "Cut reporting latency by 40% through automated end-to-end data pipelines"},
        {"name": "Real-time Streaming Data Pipeline",
         "stack": "Apache Spark, Azure, Python, Airflow, Data Architecture",
         "outcome": "Designed batch/stream pipeline ingesting 5 GB/day with 99.9% uptime"},
    ],
    exps     = [
        {"t": "Data Engineer – BI Pipelines & Automation",
         "c": "Sodexo", "l": "Paris, France", "d": "Mar 2025 – Sep 2025",
         "tools": "Microsoft Fabric, Power Automate, Power BI, SharePoint, DAX, SQL",
         "b": [
             "Automated data pipelines with Power Automate and Microsoft Fabric; improved pipeline throughput by 40%.",
             "Built Power BI data models integrating SharePoint data, accelerating business intelligence decisions by 30%.",
             "Designed scalable ingestion workflows with data governance and quality checks for centralised analytics.",
         ]},
        {"t": "Data Engineer & Analyst",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2024 – Mar 2025",
         "tools": "SQL, Python, ETL Pipelines, Power BI, Power Query, Git",
         "b": [
             "Designed end-to-end SQL and Python data pipelines with data cleaning and quality validation.",
             "Built automated ETL pipelines for KPI reporting; improved forecast accuracy by 20-25%.",
             "Implemented data governance and data architecture standards ensuring schema consistency across pipelines.",
         ]},
        {"t": "Junior Data Engineer",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2023 – Aug 2024",
         "tools": "Python, SQL, Power BI, scikit-learn, Git",
         "b": [
             "Built data pipelines in Python and SQL supporting business intelligence and executive-level dashboards.",
             "Applied agile methodology for dashboard automation and ML, cutting pipeline build time by 20%.",
             "Performed trend analysis and data cleaning to surface actionable insights for strategic planning.",
         ]},
        {"t": "Data Engineering & ML Intern",
         "c": "Airbus India Operations", "l": "Bengaluru, India", "d": "Jan 2023 – Sep 2023",
         "tools": "Python, scikit-learn, SQL, Power BI, Pandas",
         "b": [
             "Developed ML models with Python and scikit-learn for predictive modeling on aviation operational data.",
             "Built ingestion pipelines for data cleaning, quality validation, and structuring aviation datasets.",
             "Delivered Power BI dashboards communicating operational KPIs to engineering and strategy teams.",
         ]},
    ],
    certs     = CERTS_ALL,
    edu_block = EDU_BLOCK) - 1)

print(f"\n{'All 4 resumes confirmed ONE PAGE each.' if overflow == 0 else f'WARNING: {overflow} overflow(s).'}")
