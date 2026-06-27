"""Agent 5 — Dashboard / BI Export Agent. Prepares Tableau-ready exports."""
from pathlib import Path
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
AGENT4_DIR = PROCESSED_DIR / "agent4_business"
TABLEAU_SOURCE_DIR = PROCESSED_DIR / "tableau"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
TABLEAU_EXPORT_DIR = DASHBOARD_DIR / "tableau_exports"
TABLEAU_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

BUSINESS_RECOMMENDATIONS_CSV = AGENT4_DIR / "business_recommendations.csv"
SEGMENT_RECOMMENDATIONS_CSV = AGENT4_DIR / "segment_recommendations.csv"
REGION_NEEDS_CSV = AGENT4_DIR / "region_needs.csv"
CUSTOMER_TARGETING_CSV = AGENT4_DIR / "customer_targeting_summary.csv"
TABLEAU_READY_EXPORT_CSV = TABLEAU_SOURCE_DIR / "tableau_ready_export.csv"

MAIN_TABLEAU_EXPORT = TABLEAU_EXPORT_DIR / "main_tableau_export.csv"
KPI_CARDS_CSV = TABLEAU_EXPORT_DIR / "kpi_cards.csv"
OPPORTUNITY_SCORES_CSV = TABLEAU_EXPORT_DIR / "opportunity_scores.csv"
TOP_SEGMENTS_CSV = TABLEAU_EXPORT_DIR / "top_customer_segments.csv"
REGIONAL_NEEDS_EXPORT_CSV = TABLEAU_EXPORT_DIR / "regional_needs.csv"
TARGETING_SUMMARY_EXPORT_CSV = TABLEAU_EXPORT_DIR / "targeting_summary.csv"
DASHBOARD_LAYOUT_GUIDE = TABLEAU_EXPORT_DIR / "dashboard_layout_guide.md"
DASHBOARD_REPORT_JSON = TABLEAU_EXPORT_DIR / "dashboard_report.json"

def read_required_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path}. Run Agent 4 first.")
    return pd.read_csv(path)

def safe_first_value(df, column, default=""):
    if df.empty or column not in df.columns:
        return default
    value = df.iloc[0][column]
    return default if pd.isna(value) else value

def safe_numeric_mean(df, column):
    if df.empty or column not in df.columns:
        return 0
    return round(pd.to_numeric(df[column], errors="coerce").fillna(0).mean(), 2)

def build_kpi_cards(main_df, recommendations, segments, region_needs):
    rows = [
        {"kpi_name": "Total responses", "kpi_value": len(main_df), "kpi_type": "count", "description": "Number of collected community responses."},
        {"kpi_name": "Service categories", "kpi_value": main_df["service_category"].nunique() if "service_category" in main_df.columns else 0, "kpi_type": "count", "description": "Number of service categories analyzed."},
        {"kpi_name": "Regions covered", "kpi_value": main_df["region"].nunique() if "region" in main_df.columns else 0, "kpi_type": "count", "description": "Number of regions represented."},
        {"kpi_name": "Occupations covered", "kpi_value": main_df["occupation"].nunique() if "occupation" in main_df.columns else 0, "kpi_type": "count", "description": "Number of occupation groups represented."},
        {"kpi_name": "Top opportunity", "kpi_value": safe_first_value(recommendations, "service_category", "No opportunity found"), "kpi_type": "text", "description": "Highest-ranked service category."},
        {"kpi_name": "Top opportunity score", "kpi_value": safe_first_value(recommendations, "business_opportunity_score", 0), "kpi_type": "score", "description": "Highest business opportunity score."},
        {"kpi_name": "Recommendation", "kpi_value": safe_first_value(recommendations, "recommendation", ""), "kpi_type": "text", "description": "Recommendation label for top opportunity."},
        {"kpi_name": "Top region", "kpi_value": safe_first_value(region_needs, "region", "No region found"), "kpi_type": "text", "description": "Region with strongest local need."},
        {"kpi_name": "Top pilot segment", "kpi_value": safe_first_value(segments, "pilot_segment", "No segment found"), "kpi_type": "text", "description": "Best customer group to test with first."},
        {"kpi_name": "Average feasibility", "kpi_value": safe_numeric_mean(recommendations, "feasibility_score"), "kpi_type": "score", "description": "Average feasibility score."},
        {"kpi_name": "Average scalability", "kpi_value": safe_numeric_mean(recommendations, "scalability_score"), "kpi_type": "score", "description": "Average scalability score."},
        {"kpi_name": "Average testability", "kpi_value": safe_numeric_mean(recommendations, "testability_score"), "kpi_type": "score", "description": "Average testability score."},
    ]
    return pd.DataFrame(rows)

def build_opportunity_scores(recommendations):
    wanted = ["service_category", "business_opportunity_score", "feasibility_score", "scalability_score", "testability_score", "recommendation", "priority_level", "suggested_business_idea", "recommendation_source", "first_pilot_segment", "why_this_opportunity"]
    available = [c for c in wanted if c in recommendations.columns]
    out = recommendations[available].copy()
    if "business_opportunity_score" in out.columns:
        out = out.sort_values("business_opportunity_score", ascending=False)
    return out

def build_dashboard_layout_guide():
    return """
# Tableau Dashboard Layout Guide

Use files in `dashboard/tableau_exports/`.

## Dashboard 1: Executive Overview
KPI cards, top opportunity, opportunity score, and suggested business idea.

## Dashboard 2: What Should I Build?
Top opportunity card with feasibility, scalability, testability, pilot segment, and AI-generated idea.

## Dashboard 3: Regional Needs
Region/category heatmap and local_need_score bars.

## Dashboard 4: Customer Segments
Top customer segments by pilot_readiness_score.

## Dashboard 5: Raw Community Insights
Text table with region, occupation, service category, opinion_text, and sentiment_label.
""".strip()

def main():
    main_df = read_required_csv(TABLEAU_READY_EXPORT_CSV)
    recommendations = read_required_csv(BUSINESS_RECOMMENDATIONS_CSV)
    segments = read_required_csv(SEGMENT_RECOMMENDATIONS_CSV)
    region_needs = read_required_csv(REGION_NEEDS_CSV)
    targeting = read_required_csv(CUSTOMER_TARGETING_CSV)
    kpis = build_kpi_cards(main_df, recommendations, segments, region_needs)
    opportunities = build_opportunity_scores(recommendations)
    top_segments = segments.sort_values("pilot_readiness_score", ascending=False).head(25) if "pilot_readiness_score" in segments.columns else segments.head(25)
    main_df.to_csv(MAIN_TABLEAU_EXPORT, index=False, encoding="utf-8")
    kpis.to_csv(KPI_CARDS_CSV, index=False, encoding="utf-8")
    opportunities.to_csv(OPPORTUNITY_SCORES_CSV, index=False, encoding="utf-8")
    top_segments.to_csv(TOP_SEGMENTS_CSV, index=False, encoding="utf-8")
    region_needs.to_csv(REGIONAL_NEEDS_EXPORT_CSV, index=False, encoding="utf-8")
    targeting.to_csv(TARGETING_SUMMARY_EXPORT_CSV, index=False, encoding="utf-8")
    DASHBOARD_LAYOUT_GUIDE.write_text(build_dashboard_layout_guide(), encoding="utf-8")
    report = {"agent": "Agent 5 - Dashboard / BI Export Agent", "outputs_dir": str(TABLEAU_EXPORT_DIR)}
    DASHBOARD_REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Agent 5 completed successfully.")
    print(f"Saved Tableau exports to: {TABLEAU_EXPORT_DIR}")

if __name__ == "__main__":
    main()
