"""
Role:
1. Read Agent 4 business intelligence outputs.
2. Prepare Tableau-ready dashboard files.
3. Create KPI cards, opportunity charts, segment charts, and regional need files.
4. Generate a dashboard layout guide for building the Tableau dashboard.

Important:
This agent does not build Tableau dashboards directly.
It prepares clean BI-ready files that Tableau can connect to.
"""

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


# Input files from Agent 4
BUSINESS_RECOMMENDATIONS_CSV = AGENT4_DIR / "business_recommendations.csv"
SEGMENT_RECOMMENDATIONS_CSV = AGENT4_DIR / "segment_recommendations.csv"
REGION_NEEDS_CSV = AGENT4_DIR / "region_needs.csv"
CUSTOMER_TARGETING_CSV = AGENT4_DIR / "customer_targeting_summary.csv"
TABLEAU_READY_EXPORT_CSV = TABLEAU_SOURCE_DIR / "tableau_ready_export.csv"
TREND_REPORT_JSON = AGENT4_DIR / "trend_report.json"


# Output files for Tableau
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
        raise FileNotFoundError(
            f"Cannot find {path}. Run Agent 4 first."
        )

    return pd.read_csv(path)


def safe_first_value(df, column, default=""):

    if df.empty:
        return default

    if column not in df.columns:
        return default

    value = df.iloc[0][column]

    if pd.isna(value):
        return default

    return value


def safe_numeric_mean(df, column):

    if column not in df.columns or df.empty:
        return 0

    return round(pd.to_numeric(df[column], errors="coerce").fillna(0).mean(), 2)


def safe_numeric_max(df, column):

    if column not in df.columns or df.empty:
        return 0

    return round(pd.to_numeric(df[column], errors="coerce").fillna(0).max(), 2)


def build_kpi_cards(main_df, recommendations, segments, region_needs):

    total_responses = len(main_df)

    total_categories = (
        main_df["service_category"].nunique()
        if "service_category" in main_df.columns
        else 0
    )

    total_regions = (
        main_df["region"].nunique()
        if "region" in main_df.columns
        else 0
    )

    total_occupations = (
        main_df["occupation"].nunique()
        if "occupation" in main_df.columns
        else 0
    )

    top_opportunity = safe_first_value(
        recommendations,
        "service_category",
        "No opportunity found"
    )

    top_business_score = safe_first_value(
        recommendations,
        "business_opportunity_score",
        0
    )

    top_recommendation = safe_first_value(
        recommendations,
        "recommendation",
        ""
    )

    top_region = safe_first_value(
        region_needs,
        "region",
        "No region found"
    )

    top_segment = safe_first_value(
        segments,
        "pilot_segment",
        "No segment found"
    )

    avg_feasibility = safe_numeric_mean(
        recommendations,
        "feasibility_score"
    )

    avg_scalability = safe_numeric_mean(
        recommendations,
        "scalability_score"
    )

    avg_testability = safe_numeric_mean(
        recommendations,
        "testability_score"
    )

    rows = [
        {
            "kpi_name": "Total responses",
            "kpi_value": total_responses,
            "kpi_type": "count",
            "description": "Number of collected community responses."
        },
        {
            "kpi_name": "Service categories",
            "kpi_value": total_categories,
            "kpi_type": "count",
            "description": "Number of different service categories analyzed."
        },
        {
            "kpi_name": "Regions covered",
            "kpi_value": total_regions,
            "kpi_type": "count",
            "description": "Number of regions represented in the responses."
        },
        {
            "kpi_name": "Occupations covered",
            "kpi_value": total_occupations,
            "kpi_type": "count",
            "description": "Number of occupation groups represented."
        },
        {
            "kpi_name": "Top opportunity",
            "kpi_value": top_opportunity,
            "kpi_type": "text",
            "description": "Highest-ranked service category."
        },
        {
            "kpi_name": "Top opportunity score",
            "kpi_value": top_business_score,
            "kpi_type": "score",
            "description": "Highest business opportunity score."
        },
        {
            "kpi_name": "Recommendation",
            "kpi_value": top_recommendation,
            "kpi_type": "text",
            "description": "Recommendation label for the top opportunity."
        },
        {
            "kpi_name": "Top region",
            "kpi_value": top_region,
            "kpi_type": "text",
            "description": "Region with strongest local need signal."
        },
        {
            "kpi_name": "Top pilot segment",
            "kpi_value": top_segment,
            "kpi_type": "text",
            "description": "Best customer group to test with first."
        },
        {
            "kpi_name": "Average feasibility",
            "kpi_value": avg_feasibility,
            "kpi_type": "score",
            "description": "Average feasibility score across opportunities."
        },
        {
            "kpi_name": "Average scalability",
            "kpi_value": avg_scalability,
            "kpi_type": "score",
            "description": "Average scalability score across opportunities."
        },
        {
            "kpi_name": "Average testability",
            "kpi_value": avg_testability,
            "kpi_type": "score",
            "description": "Average testability score across opportunities."
        },
    ]

    return pd.DataFrame(rows)

def build_opportunity_scores(recommendations):

    wanted_columns = [
        "service_category",
        "business_opportunity_score",
        "feasibility_score",
        "scalability_score",
        "testability_score",
        "recommendation",
        "priority_level",
        "suggested_business_idea",
        "first_pilot_segment",
        "why_this_opportunity",
    ]

    available_columns = [
        col for col in wanted_columns
        if col in recommendations.columns
    ]

    output = recommendations[available_columns].copy()

    if "business_opportunity_score" in output.columns:
        output = output.sort_values(
            by="business_opportunity_score",
            ascending=False
        )

    return output

def build_top_segments(segments, top_n=25):

    output = segments.copy()

    if "pilot_readiness_score" in output.columns:
        output = output.sort_values(
            by="pilot_readiness_score",
            ascending=False
        )

    return output.head(top_n)


def build_dashboard_layout_guide():

    guide = """
# Tableau Dashboard Layout Guide

## Data files to connect

Use the CSV files in:

`dashboard/tableau_exports/`

Recommended files:

1. `main_tableau_export.csv`
2. `kpi_cards.csv`
3. `opportunity_scores.csv`
4. `top_customer_segments.csv`
5. `regional_needs.csv`
6. `targeting_summary.csv`

---

## Dashboard 1: Executive Overview

Purpose:
Show the big picture for judges and entrepreneurs.

Suggested visuals:
- KPI cards:
  - Total responses
  - Regions covered
  - Top opportunity
  - Top opportunity score
  - Average feasibility
  - Average scalability
  - Average testability
- Bar chart:
  - Service category vs business opportunity score
- Table:
  - Suggested business ideas

Recommended file:
`opportunity_scores.csv`

---

## Dashboard 2: Opportunity Ranking

Purpose:
Compare business opportunities.

Suggested visuals:
- Bar chart:
  - service_category on rows
  - business_opportunity_score on columns
- Side-by-side scores:
  - feasibility_score
  - scalability_score
  - testability_score
- Filter:
  - recommendation
  - priority_level

Recommended file:
`opportunity_scores.csv`

---

## Dashboard 3: Regional Needs

Purpose:
Show what each region needs most.

Suggested visuals:
- Region vs service category heatmap
- Bar chart:
  - region
  - local_need_score
- Filters:
  - region
  - service_category

Recommended file:
`regional_needs.csv`

---

## Dashboard 4: Customer Segments

Purpose:
Show who the entrepreneur should test with first.

Suggested visuals:
- Table:
  - pilot_segment
  - pilot_readiness_score
  - suggested_business_idea
- Bar chart:
  - pilot_segment vs pilot_readiness_score
- Filters:
  - service_category
  - region
  - occupation
  - age_group

Recommended file:
`top_customer_segments.csv`

---

## Dashboard 5: Raw Community Insights

Purpose:
Allow deeper exploration of the original responses.

Suggested visuals:
- Text table:
  - region
  - occupation
  - age_group
  - service_category
  - opinion_text
  - sentiment_label
- Filters:
  - region
  - occupation
  - age_group
  - gender
  - monthly_budget
  - service_category

Recommended file:
`main_tableau_export.csv`

---

## Best dashboard filters

Use these as interactive filters:

- service_category
- region
- occupation
- age_group
- gender
- monthly_budget
- recommendation
- priority_level

---

## Final presentation story

The dashboard should answer:

1. What do rural communities need?
2. Where is demand strongest?
3. Who is most likely to pay?
4. Which business idea is most feasible?
5. Which customer segment should be tested first?
"""
    return guide.strip()


# ============================================================
# 7. Main function
# ============================================================

def main():
    main_df = read_required_csv(TABLEAU_READY_EXPORT_CSV)
    recommendations = read_required_csv(BUSINESS_RECOMMENDATIONS_CSV)
    segments = read_required_csv(SEGMENT_RECOMMENDATIONS_CSV)
    region_needs = read_required_csv(REGION_NEEDS_CSV)
    targeting_summary = read_required_csv(CUSTOMER_TARGETING_CSV)

    kpi_cards = build_kpi_cards(
        main_df=main_df,
        recommendations=recommendations,
        segments=segments,
        region_needs=region_needs
    )

    opportunity_scores = build_opportunity_scores(
        recommendations=recommendations
    )

    top_segments = build_top_segments(
        segments=segments,
        top_n=25
    )

    dashboard_guide = build_dashboard_layout_guide()

    main_df.to_csv(
        MAIN_TABLEAU_EXPORT,
        index=False,
        encoding="utf-8"
    )

    kpi_cards.to_csv(
        KPI_CARDS_CSV,
        index=False,
        encoding="utf-8"
    )

    opportunity_scores.to_csv(
        OPPORTUNITY_SCORES_CSV,
        index=False,
        encoding="utf-8"
    )

    top_segments.to_csv(
        TOP_SEGMENTS_CSV,
        index=False,
        encoding="utf-8"
    )

    region_needs.to_csv(
        REGIONAL_NEEDS_EXPORT_CSV,
        index=False,
        encoding="utf-8"
    )

    targeting_summary.to_csv(
        TARGETING_SUMMARY_EXPORT_CSV,
        index=False,
        encoding="utf-8"
    )

    DASHBOARD_LAYOUT_GUIDE.write_text(
        dashboard_guide,
        encoding="utf-8"
    )

    report = {
        "agent": "Agent 5 - Dashboard / BI Export Agent",
        "outputs": {
            "main_tableau_export": str(MAIN_TABLEAU_EXPORT),
            "kpi_cards": str(KPI_CARDS_CSV),
            "opportunity_scores": str(OPPORTUNITY_SCORES_CSV),
            "top_customer_segments": str(TOP_SEGMENTS_CSV),
            "regional_needs": str(REGIONAL_NEEDS_EXPORT_CSV),
            "targeting_summary": str(TARGETING_SUMMARY_EXPORT_CSV),
            "dashboard_layout_guide": str(DASHBOARD_LAYOUT_GUIDE),
        },
        "note": (
            "Connect Tableau to these CSV files to build interactive dashboards. "
            "Use filters for region, service_category, occupation, age_group, gender, and monthly_budget."
        )
    }

    DASHBOARD_REPORT_JSON.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print("Agent 5 completed successfully.")
    print()
    print(f"Saved main Tableau export to: {MAIN_TABLEAU_EXPORT}")
    print(f"Saved KPI cards to: {KPI_CARDS_CSV}")
    print(f"Saved opportunity scores to: {OPPORTUNITY_SCORES_CSV}")
    print(f"Saved top customer segments to: {TOP_SEGMENTS_CSV}")
    print(f"Saved regional needs to: {REGIONAL_NEEDS_EXPORT_CSV}")
    print(f"Saved targeting summary to: {TARGETING_SUMMARY_EXPORT_CSV}")
    print(f"Saved dashboard guide to: {DASHBOARD_LAYOUT_GUIDE}")
    print(f"Saved dashboard report to: {DASHBOARD_REPORT_JSON}")


if __name__ == "__main__":
    main()