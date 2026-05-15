import sys, re
sys.path.insert(0, r'C:\Claude')
# Import builder from v6
exec(open(r'C:\Claude\generate_resumes_v6.py', encoding='utf-8').read().split('CONTACT')[0])

CONTACT   = ("+33 7 45 37 54 09  .  gkmurali37@gmail.com  .  "
             "linkedin.com/in/krishnakrish77  .  Saint-Germain-en-Laye, France")
EDU_BLOCK = [
    {"t": "MSc Data Science & Business Analytics",           "b": True},
    {"t": "EDC Paris Business School  . Mar 2025 - Feb 2026"},
    {"t": "BTech Electronics & Instrumentation",             "b": True},
    {"t": "SVET, Tirupati  . Apr 2020 - Jun 2024"},
]

make_resume(
    path     = r"C:\Claude\Resume_AE_tmp.pdf",
    subtitle = "Analytics Engineer  |  dbt . Databricks . SQL . Python . Snowflake . Airflow",
    contact  = CONTACT,
    summary  = (
        "Analytics Engineer with 3+ years building trusted data models, dbt pipelines, and "
        "Databricks analytics layers on Snowflake, Azure, and BigQuery. Skilled at designing "
        "governed, well-tested datasets that serve as a single source of truth for Power BI and "
        "Tableau at scale. Reduced reporting effort by 40% and improved forecast accuracy by 20-25% "
        "through automated pipelines. "
        "Open to full-time, remote, and freelance opportunities across Europe."
    ),
    skills   = [
        ("Analytics Engineering", "dbt, SQL, Python, Pandas, Apache Spark, Airflow, Databricks, scikit-learn, R"),
        ("BI & Visualisation",    "Power BI, Tableau, DAX, Advanced Excel, Power Query, KPI Frameworks"),
        ("Cloud & Data",          "Azure, Databricks, Snowflake, Google BigQuery, Microsoft Fabric, AWS, SharePoint"),
        ("Data Management",       "ETL/ELT, Data Modeling, Warehousing, Data Validation, Testing, Power Automate"),
    ],
    exps     = [
        {"t": "Analytics Engineer - BI & Power Platform",
         "c": "Sodexo", "l": "Paris, France", "d": "Mar 2025 - Sep 2025",
         "b": [
             "Designed Power BI semantic models and pipelines tracking KPIs, accelerating decisions by 30%.",
             "Built Power Platform automation (Power Apps & Power Automate), cutting manual effort by 40%.",
             "Integrated Microsoft Fabric and SharePoint into governed, centralised analytics pipelines.",
             "Delivered trusted analytics layers via advanced DAX modelling as a single source of truth.",
         ]},
        {"t": "Analytics Engineer",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2024 - Mar 2025",
         "b": [
             "Built SQL and Python analytical workflows powering business intelligence reporting.",
             "Designed Power BI semantic models with real-time KPI dashboards for cross-functional teams.",
             "Applied Power Query and SQL transformations on large datasets; improved forecast accuracy 20-25%.",
             "Developed modular transformation pipelines to cleanse and enrich datasets for downstream analytics.",
         ]},
        {"t": "Junior Analytics Engineer",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2023 - Aug 2024",
         "b": [
             "Built Power BI dashboards and analytics pipelines translating data into stakeholder insights.",
             "Applied Python ML models to detect patterns and generate predictive insights for operations.",
             "Used SQL and advanced Excel to analyse large datasets and automate reporting processes.",
         ]},
        {"t": "ML & Analytics Engineer Intern",
         "c": "Airbus India Operations", "l": "Bengaluru, India", "d": "Jan 2023 - Sep 2023",
         "b": [
             "Built ML models with Python and scikit-learn; improved predictive accuracy by 20-25%.",
             "Preprocessed large aviation datasets and built pipelines supporting model training.",
             "Delivered Power BI dashboards surfacing aviation insights to engineering and strategy teams.",
         ]},
    ],
    edu_block = EDU_BLOCK)

make_resume(
    path     = r"C:\Claude\Resume_DE_tmp.pdf",
    subtitle = "Data Engineer  |  Databricks . Azure . Snowflake . Spark . Airflow . dbt . Python",
    contact  = CONTACT,
    summary  = (
        "Data Engineer with 3+ years architecting scalable pipelines, ETL/ELT workflows, and cloud "
        "data platforms using Databricks, Azure, AWS, Snowflake, Spark, Airflow, and dbt. Strong at "
        "building reliable, high-throughput data systems that power analytics at scale. Delivered "
        "40% reduction in manual reporting effort and 30% faster decisions through production-grade "
        "data infrastructure. "
        "Open to full-time, remote, and freelance opportunities across Europe."
    ),
    skills   = [
        ("Data Engineering",       "Apache Spark, Airflow, dbt, Databricks, ETL/ELT, Pipelines, Data Modeling, Warehousing"),
        ("Languages & Frameworks", "Python, SQL, R, Pandas, scikit-learn, Power Query"),
        ("Cloud & Data Platforms", "Azure, AWS, Databricks, Google BigQuery, Snowflake, Microsoft Fabric, SharePoint"),
        ("Automation & AI",        "Power Automate, Power Apps, Machine Learning, Generative AI, Agentic AI, RPA"),
    ],
    exps     = [
        {"t": "Data Engineer - BI Pipelines & Automation",
         "c": "Sodexo", "l": "Paris, France", "d": "Mar 2025 - Sep 2025",
         "b": [
             "Automated data pipelines with Power Automate and Microsoft Fabric, boosting efficiency by 40%.",
             "Built Power BI data models integrating SharePoint and Microsoft 365, accelerating decisions by 30%.",
             "Designed scalable ingestion and transformation workflows for centralised analytics access.",
             "Delivered analytics-ready data layers using advanced DAX modelling as a single source of truth.",
         ]},
        {"t": "Data Engineer & Analyst",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2024 - Mar 2025",
         "b": [
             "Designed end-to-end SQL and Python data workflows, improving pipeline reliability across functions.",
             "Built automated ETL pipelines and Power BI data models for real-time stakeholder reporting.",
             "Applied SQL transformations and Power Query to large datasets; improved forecast accuracy 20-25%.",
             "Implemented data validation logic ensuring integrity and schema consistency across pipelines.",
         ]},
        {"t": "Junior Data Engineer",
         "c": "InsightMetrics Consulting", "l": "Bengaluru, India", "d": "Sep 2023 - Aug 2024",
         "b": [
             "Built data pipelines in Python and SQL supporting analytics and executive-level dashboards.",
             "Automated reporting workflows and applied ML techniques to detect patterns in large datasets.",
             "Conducted data analysis to surface business trends supporting strategic decision-making.",
         ]},
        {"t": "Data Engineering & ML Intern",
         "c": "Airbus India Operations", "l": "Bengaluru, India", "d": "Jan 2023 - Sep 2023",
         "b": [
             "Developed ML models with Python and scikit-learn for predictive analytics and classification.",
             "Built ingestion pipelines to clean, validate, and structure large aviation operational datasets.",
             "Delivered Power BI dashboards surfacing operational insights to engineering and strategy teams.",
         ]},
    ],
    edu_block = EDU_BLOCK)

print("Done - temp files written.")
