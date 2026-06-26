from pathlib import Path
import json
import pandas as pd
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

AGENT3_DIR = PROCESSED_DIR / "agent3_nlp"
AGENT4_DIR = PROCESSED_DIR / "agent4_business"
TABLEAU_DIR = PROCESSED_DIR / "tableau"

AGENT4_DIR.mkdir(parents=True, exist_ok=True)
TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

NLP_CSV = AGENT3_DIR / "nlp_insights.csv"
CATEGORY_METRICS_CSV = AGENT3_DIR / "category_metrics.csv"
REGION_METRICS_CSV = AGENT3_DIR / "region_metrics.csv"
OCCUPATION_METRICS_CSV = AGENT3_DIR / "occupation_metrics.csv"
AGE_GROUP_METRICS_CSV = AGENT3_DIR / "age_group_metrics.csv"
GENDER_METRICS_CSV = AGENT3_DIR / "gender_metrics.csv"
BUDGET_METRICS_CSV = AGENT3_DIR / "budget_metrics.csv"
CUSTOMER_SEGMENTS_CSV = AGENT3_DIR / "customer_segments.csv"
MARKET_SIGNALS_CSV = AGENT3_DIR / "market_signals.csv"

RECOMMENDATIONS_CSV = AGENT4_DIR / "business_recommendations.csv"
REGION_NEEDS_CSV = AGENT4_DIR / "region_needs.csv"
SEGMENT_RECOMMENDATIONS_CSV = AGENT4_DIR / "segment_recommendations.csv"
CUSTOMER_TARGETING_CSV = AGENT4_DIR / "customer_targeting_summary.csv"
TREND_REPORT_JSON = AGENT4_DIR / "trend_report.json"

TABLEAU_EXPORT_CSV = TABLEAU_DIR / "tableau_ready_export.csv"


def read_required_csv(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Cannot find {path}. Run Agent 3 first."
        )

    return pd.read_csv(path)


def normalize(series):

    series = pd.to_numeric(series, errors="coerce").fillna(0)

    max_value = series.max()
    min_value = series.min()

    if max_value == min_value:
        return pd.Series([0.5] * len(series), index=series.index)

    return (series - min_value) / (max_value - min_value)


def safe_top_value(series):

    series = series.dropna()

    if series.empty:
        return ""

    value_counts = series.value_counts()

    if value_counts.empty:
        return ""

    return value_counts.index[0]


def recommendation_label(score):

    if score >= 80:
        return "Strong opportunity"

    if score >= 65:
        return "Promising, test with pilot"

    if score >= 50:
        return "Needs validation"

    return "Low priority for now"


def priority_label(score):

    if score >= 75:
        return "High priority"

    if score >= 55:
        return "Medium priority"

    return "Low priority"


def get_business_idea(category):

    business_ideas = {
        "Delivery": "Rural essentials delivery hub for groceries, pharmacy items, and parcels",
        "Education": "Hybrid tutoring and digital skills workshops for rural students",
        "Transport": "Scheduled rural shuttle and shared transport coordination service",
        "Agriculture": "Farm support marketplace for equipment repair, advisory visits, and produce pickup",
        "Repair": "Verified mobile repair booking service for homes, farms, and small businesses",
        "Tourism": "Local rural experience and stargazing booking platform with community guides",

        # Extra labels in case your categories change later
        "Veterinary & Camel Care": "Mobile camel-vet booking and livestock medicine delivery",
        "Farm Operations": "Farm maintenance and equipment repair coordination",
        "Rural Transport": "Scheduled rural shuttle and shared delivery network",
        "Mobile Healthcare": "Mobile health checkup and medicine pickup service",
        "Education & Tutoring": "Hybrid tutoring and digital skills workshops",
        "Tourism & Stargazing": "Guided stargazing packages with local products",
        "Market Access": "Marketplace for dates, camel products, crafts, and home food",
        "Utilities & Maintenance": "Verified local maintenance directory and issue tracker",
    }

    return business_ideas.get(
        category,
        "Run more community research before choosing a business idea"
    )


def calculate_growth(df):
    df = df.copy()

    if "date_collected" not in df.columns:
        categories = sorted(df["service_category"].dropna().unique())

        return pd.DataFrame({
            "service_category": categories,
            "recent_30_day_count": 0,
            "previous_30_day_count": 0,
            "growth_rate_percent": 0,
        })

    df["date_collected"] = pd.to_datetime(
        df["date_collected"],
        errors="coerce"
    )

    df = df.dropna(subset=["date_collected"])

    if df.empty:
        return pd.DataFrame({
            "service_category": [],
            "recent_30_day_count": [],
            "previous_30_day_count": [],
            "growth_rate_percent": [],
        })

    latest_date = df["date_collected"].max()

    recent_start = latest_date - pd.Timedelta(days=30)
    previous_start = latest_date - pd.Timedelta(days=60)

    recent = df[df["date_collected"] > recent_start]

    previous = df[
        (df["date_collected"] > previous_start) &
        (df["date_collected"] <= recent_start)
    ]

    recent_counts = recent.groupby("service_category").size()
    previous_counts = previous.groupby("service_category").size()

    all_categories = sorted(df["service_category"].dropna().unique())

    rows = []

    for category in all_categories:
        recent_count = int(recent_counts.get(category, 0))
        previous_count = int(previous_counts.get(category, 0))

        if previous_count == 0 and recent_count > 0:
            growth_rate = 100
        elif previous_count == 0 and recent_count == 0:
            growth_rate = 0
        else:
            growth_rate = ((recent_count - previous_count) / previous_count) * 100

        rows.append({
            "service_category": category,
            "recent_30_day_count": recent_count,
            "previous_30_day_count": previous_count,
            "growth_rate_percent": round(growth_rate, 2),
        })

    return pd.DataFrame(rows)

def build_segment_summary(customer_segments):

    segments = customer_segments.copy()

    if "segment_market_strength_score" not in segments.columns:
        if "market_strength_score" in segments.columns:
            segments["segment_market_strength_score"] = segments["market_strength_score"]
        else:
            segments["segment_market_strength_score"] = 0

    required_columns = [
        "service_category",
        "region",
        "occupation",
        "age_group",
        "response_count",
        "avg_budget_aed",
        "avg_would_pay",
        "need_score",
        "payment_readiness_score",
        "testability_score",
        "segment_market_strength_score",
    ]

    for column in required_columns:
        if column not in segments.columns:
            segments[column] = ""

    numeric_columns = [
        "response_count",
        "avg_budget_aed",
        "avg_would_pay",
        "need_score",
        "payment_readiness_score",
        "testability_score",
        "segment_market_strength_score",
    ]

    for column in numeric_columns:
        segments[column] = pd.to_numeric(segments[column], errors="coerce").fillna(0)

    best_segments = (
        segments
        .sort_values(
            by=[
                "segment_market_strength_score",
                "response_count",
                "avg_would_pay",
                "avg_budget_aed",
            ],
            ascending=False
        )
        .groupby("service_category")
        .head(1)
        .copy()
    )

    best_segments = best_segments[
        [
            "service_category",
            "region",
            "occupation",
            "age_group",
            "response_count",
            "avg_budget_aed",
            "avg_would_pay",
            "need_score",
            "payment_readiness_score",
            "testability_score",
            "segment_market_strength_score",
        ]
    ]

    best_segments = best_segments.rename(columns={
        "region": "best_test_region",
        "occupation": "best_test_occupation",
        "age_group": "best_test_age_group",
        "response_count": "best_segment_response_count",
        "avg_budget_aed": "best_segment_avg_budget_aed",
        "avg_would_pay": "best_segment_would_pay_score",
        "need_score": "best_segment_need_score",
        "payment_readiness_score": "best_segment_payment_readiness_score",
        "testability_score": "best_segment_testability_score",
        "segment_market_strength_score": "best_segment_market_strength_score",
    })

    segment_counts = (
        segments
        .groupby("service_category")
        .agg(
            total_customer_segments=("service_category", "count"),
            testable_segments=("response_count", lambda x: int((x >= 2).sum())),
            avg_segment_market_strength=("segment_market_strength_score", "mean"),
            max_segment_market_strength=("segment_market_strength_score", "max"),
        )
        .reset_index()
    )

    summary = best_segments.merge(
        segment_counts,
        on="service_category",
        how="left"
    )

    return summary

def build_source_confidence(df):

    source_summary = (
        df.groupby("service_category")
        .agg(
            source_count=("source", "nunique"),
            top_source=("source", safe_top_value),
            gender_groups=("gender", "nunique"),
            sample_regions=("region", "nunique"),
            sample_occupations=("occupation", "nunique"),
        )
        .reset_index()
    )

    source_summary["source_diversity_score"] = (
        normalize(source_summary["source_count"]) * 50 +
        normalize(source_summary["sample_regions"]) * 30 +
        normalize(source_summary["sample_occupations"]) * 20
    ).round(2)

    return source_summary

def build_recommendations(df, category_metrics, customer_segments):

    category = category_metrics.copy()

    if "category_market_strength_score" not in category.columns:
        if "demand_score" in category.columns:
            category["category_market_strength_score"] = category["demand_score"]
        else:
            category["category_market_strength_score"] = 0

    if "testability_score" in category.columns:
        category = category.rename(columns={
            "testability_score": "agent3_category_testability_score"
        })

    expected_numeric_columns = [
        "response_count",
        "avg_importance",
        "avg_frequency",
        "avg_urgency",
        "avg_pain",
        "avg_budget_aed",
        "avg_would_pay",
        "avg_satisfaction",
        "avg_sentiment",
        "unique_regions",
        "unique_occupations",
        "category_market_strength_score",
        "need_score",
        "payment_readiness_score",
        "agent3_category_testability_score",
    ]

    for column in expected_numeric_columns:
        if column not in category.columns:
            category[column] = 0

        category[column] = pd.to_numeric(
            category[column],
            errors="coerce"
        ).fillna(0)

    growth_df = calculate_growth(df)
    segment_summary = build_segment_summary(customer_segments)
    source_confidence = build_source_confidence(df)

    merged = category.merge(
        growth_df,
        on="service_category",
        how="left"
    )

    merged = merged.merge(
        segment_summary,
        on="service_category",
        how="left"
    )

    merged = merged.merge(
        source_confidence,
        on="service_category",
        how="left"
    )

    fill_numeric = [
        "recent_30_day_count",
        "previous_30_day_count",
        "growth_rate_percent",
        "best_segment_response_count",
        "best_segment_avg_budget_aed",
        "best_segment_would_pay_score",
        "best_segment_need_score",
        "best_segment_payment_readiness_score",
        "best_segment_testability_score",
        "best_segment_market_strength_score",
        "total_customer_segments",
        "testable_segments",
        "avg_segment_market_strength",
        "max_segment_market_strength",
        "source_count",
        "gender_groups",
        "sample_regions",
        "sample_occupations",
        "source_diversity_score",
    ]

    for column in fill_numeric:
        if column not in merged.columns:
            merged[column] = 0

        merged[column] = pd.to_numeric(
            merged[column],
            errors="coerce"
        ).fillna(0)

    fill_text = [
        "best_test_region",
        "best_test_occupation",
        "best_test_age_group",
        "top_source",
        "top_solution_type",
        "top_current_solution",
    ]

    for column in fill_text:
        if column not in merged.columns:
            merged[column] = ""

        merged[column] = merged[column].fillna("")

    merged["category_strength_norm"] = normalize(
        merged["category_market_strength_score"]
    )

    merged["budget_norm"] = normalize(
        merged["avg_budget_aed"]
    )

    merged["region_norm"] = normalize(
        merged["unique_regions"]
    )

    merged["occupation_norm"] = normalize(
        merged["unique_occupations"]
    )

    merged["growth_norm"] = normalize(
        merged["growth_rate_percent"]
    )

    merged["segment_strength_norm"] = normalize(
        merged["best_segment_market_strength_score"]
    )

    merged["source_confidence_norm"] = normalize(
        merged["source_diversity_score"]
    )

    merged["opportunity_gap_score"] = (
        ((5 - merged["avg_satisfaction"]) / 4).clip(0, 1) * 50 +
        (merged["avg_pain"] / 5).clip(0, 1) * 50
    ).round(2)

    merged["feasibility_score"] = (
        normalize(merged["need_score"]) * 30 +
        normalize(merged["payment_readiness_score"]) * 25 +
        merged["budget_norm"] * 15 +
        merged["source_confidence_norm"] * 10 +
        normalize(merged["opportunity_gap_score"]) * 20
    ).round(2)

    merged["scalability_score"] = (
        merged["region_norm"] * 30 +
        merged["occupation_norm"] * 20 +
        merged["growth_norm"] * 25 +
        normalize(merged["response_count"]) * 15 +
        merged["source_confidence_norm"] * 10
    ).round(2)

    merged["testability_score"] = (
        merged["segment_strength_norm"] * 30 +
        normalize(merged["best_segment_response_count"]) * 20 +
        (merged["avg_urgency"] / 5).clip(0, 1) * 20 +
        merged["avg_would_pay"].clip(0, 1) * 20 +
        normalize(merged["testable_segments"]) * 10
    ).round(2)

    # Overall final business score
    merged["business_opportunity_score"] = (
        merged["feasibility_score"] * 0.40 +
        merged["scalability_score"] * 0.30 +
        merged["testability_score"] * 0.30
    ).round(2)

    merged["recommendation"] = merged["business_opportunity_score"].apply(
        recommendation_label
    )

    merged["priority_level"] = merged["business_opportunity_score"].apply(
        priority_label
    )

    merged["suggested_business_idea"] = merged["service_category"].apply(
        get_business_idea
    )

    merged["first_pilot_segment"] = (
        merged["best_test_region"].astype(str)
        + " | "
        + merged["best_test_occupation"].astype(str)
        + " | "
        + merged["best_test_age_group"].astype(str)
    )

    merged["why_this_opportunity"] = (
        "Need score: "
        + merged["need_score"].round(1).astype(str)
        + ", payment readiness: "
        + merged["payment_readiness_score"].round(1).astype(str)
        + ", best pilot segment: "
        + merged["first_pilot_segment"].astype(str)
    )

    merged = merged.sort_values(
        by="business_opportunity_score",
        ascending=False
    )

    return merged

def build_region_needs(df):

    region_needs = (
        df.groupby(["region", "service_category"])
        .agg(
            response_count=("response_id", "count"),
            avg_importance=("importance_score", "mean"),
            avg_frequency=("frequency_score", "mean"),
            avg_urgency=("urgency_score", "mean"),
            avg_pain=("pain_score", "mean"),
            avg_budget_aed=("budget_midpoint_aed", "mean"),
            avg_would_pay=("would_pay_score", "mean"),
            avg_sentiment=("sentiment_score", "mean"),
            top_occupation=("occupation", safe_top_value),
            top_age_group=("age_group", safe_top_value),
            common_solution_type=("preferred_solution_type", safe_top_value),
            common_current_solution=("current_solution", safe_top_value),
        )
        .reset_index()
    )

    region_needs["local_need_score"] = (
        normalize(region_needs["response_count"]) * 25 +
        (region_needs["avg_importance"] / 5).clip(0, 1) * 20 +
        (region_needs["avg_frequency"] / 4).clip(0, 1) * 20 +
        (region_needs["avg_urgency"] / 5).clip(0, 1) * 20 +
        normalize(region_needs["avg_budget_aed"]) * 15
    ).round(2)

    region_needs["local_priority"] = region_needs["local_need_score"].apply(
        priority_label
    )

    return region_needs.sort_values(
        ["region", "local_need_score"],
        ascending=[True, False]
    )

def build_segment_recommendations(customer_segments):

    segments = customer_segments.copy()

    if "segment_market_strength_score" not in segments.columns:
        if "market_strength_score" in segments.columns:
            segments["segment_market_strength_score"] = segments["market_strength_score"]
        else:
            segments["segment_market_strength_score"] = 0

    numeric_columns = [
        "response_count",
        "avg_budget_aed",
        "avg_would_pay",
        "avg_urgency",
        "avg_frequency",
        "avg_pain",
        "need_score",
        "payment_readiness_score",
        "testability_score",
        "segment_market_strength_score",
    ]

    for column in numeric_columns:
        if column not in segments.columns:
            segments[column] = 0

        segments[column] = pd.to_numeric(
            segments[column],
            errors="coerce"
        ).fillna(0)

    segments["pilot_readiness_score"] = (
        normalize(segments["segment_market_strength_score"]) * 35 +
        normalize(segments["response_count"]) * 20 +
        segments["avg_would_pay"].clip(0, 1) * 20 +
        (segments["avg_urgency"] / 5).clip(0, 1) * 15 +
        normalize(segments["avg_budget_aed"]) * 10
    ).round(2)

    segments["pilot_priority"] = segments["pilot_readiness_score"].apply(
        priority_label
    )

    segments["pilot_segment"] = (
        segments["service_category"].astype(str)
        + " | "
        + segments["region"].astype(str)
        + " | "
        + segments["occupation"].astype(str)
        + " | "
        + segments["age_group"].astype(str)
    )

    segments["suggested_business_idea"] = segments["service_category"].apply(
        get_business_idea
    )

    segments = segments.sort_values(
        by="pilot_readiness_score",
        ascending=False
    )

    return segments

def build_customer_targeting_summary(
    region_metrics,
    occupation_metrics,
    age_group_metrics,
    gender_metrics,
    budget_metrics
):

    rows = []

    if not region_metrics.empty:
        score_col = "region_market_strength_score"
        if score_col not in region_metrics.columns:
            score_col = "market_strength_score"

        top_region = region_metrics.sort_values(score_col, ascending=False).iloc[0]

        rows.append({
            "target_type": "Region",
            "target_group": top_region["region"],
            "score": top_region[score_col],
            "meaning": "Best region to test first based on need, payment readiness, and urgency."
        })

    if not occupation_metrics.empty:
        score_col = "occupation_market_strength_score"
        if score_col not in occupation_metrics.columns:
            score_col = "market_strength_score"

        top_occupation = occupation_metrics.sort_values(score_col, ascending=False).iloc[0]

        rows.append({
            "target_type": "Occupation",
            "target_group": top_occupation["occupation"],
            "score": top_occupation[score_col],
            "meaning": "Occupation group with strongest business signal."
        })

    if not age_group_metrics.empty:
        score_col = "age_group_market_strength_score"
        if score_col not in age_group_metrics.columns:
            score_col = "market_strength_score"

        top_age_group = age_group_metrics.sort_values(score_col, ascending=False).iloc[0]

        rows.append({
            "target_type": "Age group",
            "target_group": top_age_group["age_group"],
            "score": top_age_group[score_col],
            "meaning": "Age group with strongest need and payment readiness."
        })

    if not gender_metrics.empty:
        score_col = "gender_market_strength_score"
        if score_col not in gender_metrics.columns:
            score_col = "market_strength_score"

        top_gender = gender_metrics.sort_values(score_col, ascending=False).iloc[0]

        rows.append({
            "target_type": "Gender",
            "target_group": top_gender["gender"],
            "score": top_gender[score_col],
            "meaning": "Gender group with strongest market signal in the collected sample."
        })

    if not budget_metrics.empty:
        score_col = "budget_market_strength_score"
        if score_col not in budget_metrics.columns:
            score_col = "market_strength_score"

        top_budget = budget_metrics.sort_values(score_col, ascending=False).iloc[0]

        rows.append({
            "target_type": "Budget group",
            "target_group": top_budget["monthly_budget"],
            "score": top_budget[score_col],
            "meaning": "Budget group with strongest payment-readiness signal."
        })

    return pd.DataFrame(rows)

def build_tableau_export(df, recommendations):
    """
    Join row-level NLP output with category-level recommendation scores.

    Tableau can connect to this file directly.
    """

    recommendation_columns = [
        "service_category",
        "feasibility_score",
        "scalability_score",
        "testability_score",
        "business_opportunity_score",
        "recommendation",
        "priority_level",
        "suggested_business_idea",
        "first_pilot_segment",
        "best_test_region",
        "best_test_occupation",
        "best_test_age_group",
        "why_this_opportunity",
    ]

    available_columns = [
        column for column in recommendation_columns
        if column in recommendations.columns
    ]

    tableau_export = df.merge(
        recommendations[available_columns],
        on="service_category",
        how="left"
    )

    return tableau_export

def main():
    df = read_required_csv(NLP_CSV)
    category_metrics = read_required_csv(CATEGORY_METRICS_CSV)
    region_metrics = read_required_csv(REGION_METRICS_CSV)
    occupation_metrics = read_required_csv(OCCUPATION_METRICS_CSV)
    age_group_metrics = read_required_csv(AGE_GROUP_METRICS_CSV)
    gender_metrics = read_required_csv(GENDER_METRICS_CSV)
    budget_metrics = read_required_csv(BUDGET_METRICS_CSV)
    customer_segments = read_required_csv(CUSTOMER_SEGMENTS_CSV)

    recommendations = build_recommendations(
        df=df,
        category_metrics=category_metrics,
        customer_segments=customer_segments
    )

    region_needs = build_region_needs(df)

    segment_recommendations = build_segment_recommendations(
        customer_segments
    )

    customer_targeting_summary = build_customer_targeting_summary(
        region_metrics=region_metrics,
        occupation_metrics=occupation_metrics,
        age_group_metrics=age_group_metrics,
        gender_metrics=gender_metrics,
        budget_metrics=budget_metrics
    )

    tableau_export = build_tableau_export(
        df=df,
        recommendations=recommendations
    )

    recommendations.to_csv(
        RECOMMENDATIONS_CSV,
        index=False,
        encoding="utf-8"
    )

    region_needs.to_csv(
        REGION_NEEDS_CSV,
        index=False,
        encoding="utf-8"
    )

    segment_recommendations.to_csv(
        SEGMENT_RECOMMENDATIONS_CSV,
        index=False,
        encoding="utf-8"
    )

    customer_targeting_summary.to_csv(
        CUSTOMER_TARGETING_CSV,
        index=False,
        encoding="utf-8"
    )

    tableau_export.to_csv(
        TABLEAU_EXPORT_CSV,
        index=False,
        encoding="utf-8"
    )

    top_recommendation = (
        recommendations.iloc[0].to_dict()
        if not recommendations.empty
        else {}
    )

    top_segment = (
        segment_recommendations.iloc[0].to_dict()
        if not segment_recommendations.empty
        else {}
    )

    report = {
        "agent": "Agent 4 - Trend / Business Intelligence Agent",
        "top_recommendation": top_recommendation,
        "top_customer_segment": top_segment,
        "outputs": {
            "business_recommendations_file": str(RECOMMENDATIONS_CSV),
            "region_needs_file": str(REGION_NEEDS_CSV),
            "segment_recommendations_file": str(SEGMENT_RECOMMENDATIONS_CSV),
            "customer_targeting_summary_file": str(CUSTOMER_TARGETING_CSV),
            "tableau_ready_export": str(TABLEAU_EXPORT_CSV),
        },
        "note": (
            "Scores are prototype decision-support metrics. "
            "They should be validated through real user interviews, pilots, and field testing."
        )
    }

    TREND_REPORT_JSON.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8"
    )

    print("Agent 4 completed successfully.")
    print()
    print(f"Saved business recommendations to: {RECOMMENDATIONS_CSV}")
    print(f"Saved region needs to: {REGION_NEEDS_CSV}")
    print(f"Saved segment recommendations to: {SEGMENT_RECOMMENDATIONS_CSV}")
    print(f"Saved customer targeting summary to: {CUSTOMER_TARGETING_CSV}")
    print(f"Saved Tableau-ready export to: {TABLEAU_EXPORT_CSV}")
    print(f"Saved trend report to: {TREND_REPORT_JSON}")
    print()
    print("Top business recommendations:")
    print(
        recommendations[
            [
                "service_category",
                "business_opportunity_score",
                "feasibility_score",
                "scalability_score",
                "testability_score",
                "recommendation",
                "suggested_business_idea",
                "first_pilot_segment",
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()