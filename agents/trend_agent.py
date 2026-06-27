"""
Agent 4 — Trend / Business Intelligence Agent
Generates feasibility, scalability, testability, and contextual Claude recommendations.
If ANTHROPIC_API_KEY is missing, it safely uses Al Qua'a-specific fallback ideas.
"""
from pathlib import Path
import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

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

RECOMMENDATIONS_CSV = AGENT4_DIR / "business_recommendations.csv"
REGION_NEEDS_CSV = AGENT4_DIR / "region_needs.csv"
SEGMENT_RECOMMENDATIONS_CSV = AGENT4_DIR / "segment_recommendations.csv"
CUSTOMER_TARGETING_CSV = AGENT4_DIR / "customer_targeting_summary.csv"
TREND_REPORT_JSON = AGENT4_DIR / "trend_report.json"
AI_RECOMMENDATION_CACHE_JSON = AGENT4_DIR / "ai_recommendation_cache.json"
TABLEAU_EXPORT_CSV = TABLEAU_DIR / "tableau_ready_export.csv"

FALLBACK_IDEAS = {
    "Veterinary & Camel Care": "Mobile vet booking app for camel farms in Al Qua'a, with same-day medicine delivery from Al Ain city.",
    "Tourism & Stargazing": "Stargazing experience booking platform connecting Al Qua'a's dark skies with astronomy tourists — with local guide and camping packages.",
    "Market Access": "Community marketplace for camel milk, dates, and local products, with logistics to Al Ain and Abu Dhabi markets.",
    "Farm Operations": "Farm equipment rental and maintenance coordination for camel and date farms across the Al Qua'a region.",
    "Rural Transport": "Scheduled rural shuttle and shared delivery network connecting Al Qua'a families and farms with Al Ain services.",
    "Mobile Healthcare": "Mobile health checkup and pharmacy pickup service for Al Qua'a families, elderly residents, and farm workers.",
    "Education & Tutoring": "Hybrid tutoring and digital-skills workshops for rural students and young entrepreneurs in Al Qua'a.",
    "Utilities & Maintenance": "Verified mobile maintenance directory for AC repair, irrigation, solar, internet, and farm equipment issues in Al Qua'a.",
}

def read_required_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path}. Run Agent 3 first.")
    return pd.read_csv(path)

def normalize(series):
    series = pd.to_numeric(series, errors="coerce").fillna(0)
    max_value, min_value = series.max(), series.min()
    if max_value == min_value:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_value) / (max_value - min_value)

def safe_top_value(series):
    series = series.dropna()
    if series.empty:
        return ""
    counts = series.value_counts()
    return "" if counts.empty else counts.index[0]

def recommendation_label(score):
    if score >= 80: return "Strong opportunity"
    if score >= 65: return "Promising, test with pilot"
    if score >= 50: return "Needs validation"
    return "Low priority for now"

def priority_label(score):
    if score >= 75: return "High priority"
    if score >= 55: return "Medium priority"
    return "Low priority"

def load_cache():
    if not AI_RECOMMENDATION_CACHE_JSON.exists():
        return {}
    try:
        return json.loads(AI_RECOMMENDATION_CACHE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

def save_cache(cache):
    AI_RECOMMENDATION_CACHE_JSON.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

def get_business_idea(category: str, metrics: dict) -> str:
    fallback = FALLBACK_IDEAS.get(category, "Run more community research before choosing a business idea.")
    if not os.getenv("ANTHROPIC_API_KEY"):
        return fallback
    cache = load_cache()
    cache_key = f"{category}|{round(float(metrics.get('need_score', 0)), 1)}|{round(float(metrics.get('avg_budget_aed', 0)), 0)}"
    if cache_key in cache:
        return cache[cache_key]
    try:
        import anthropic
        client = anthropic.Anthropic()
        model_name = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        best_region = metrics.get("best_test_region", "Al Qua'a")
        prompt = f"""You are a rural business advisor for Al Qua'a, a remote community in Al Ain, UAE.
The community has camel farms as a primary income source, and is one of the world's best stargazing locations due to very low light pollution.

A community survey shows strong demand in the '{category}' category.
Key metrics: need score {float(metrics.get('need_score', 0)):.1f}/100, average monthly budget {float(metrics.get('avg_budget_aed', 0)):.0f} AED, top occupation: {metrics.get('top_occupation', 'unknown')}, top solution type: {metrics.get('top_solution_type', 'unknown')}, best pilot region: {best_region}.

Suggest one specific, realistic business idea for a first-time local entrepreneur.
Be concrete. Mention Al Qua'a specifically. Keep it to 2 sentences."""
        message = client.messages.create(
            model=model_name,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        if not text:
            return fallback
        cache[cache_key] = text
        save_cache(cache)
        return text
    except Exception as error:
        print(f"Claude recommendation failed for {category}: {type(error).__name__}: {error}")
        return fallback

def recommendation_source():
    return "anthropic_claude" if os.getenv("ANTHROPIC_API_KEY") else "fallback_no_api_key"

def calculate_growth(df):
    df = df.copy()
    if "date_collected" not in df.columns:
        return pd.DataFrame({"service_category": sorted(df["service_category"].dropna().unique()), "recent_30_day_count": 0, "previous_30_day_count": 0, "growth_rate_percent": 0})
    df["date_collected"] = pd.to_datetime(df["date_collected"], errors="coerce")
    df = df.dropna(subset=["date_collected"])
    if df.empty:
        return pd.DataFrame(columns=["service_category", "recent_30_day_count", "previous_30_day_count", "growth_rate_percent"])
    latest = df["date_collected"].max()
    recent_start = latest - pd.Timedelta(days=30)
    previous_start = latest - pd.Timedelta(days=60)
    recent_counts = df[df["date_collected"] > recent_start].groupby("service_category").size()
    previous_counts = df[(df["date_collected"] > previous_start) & (df["date_collected"] <= recent_start)].groupby("service_category").size()
    rows = []
    for category in sorted(df["service_category"].dropna().unique()):
        recent = int(recent_counts.get(category, 0))
        previous = int(previous_counts.get(category, 0))
        if previous == 0 and recent > 0: growth = 100
        elif previous == 0: growth = 0
        else: growth = ((recent - previous) / previous) * 100
        rows.append({"service_category": category, "recent_30_day_count": recent, "previous_30_day_count": previous, "growth_rate_percent": round(growth, 2)})
    return pd.DataFrame(rows)

def build_segment_summary(customer_segments):
    segments = customer_segments.copy()
    if "segment_market_strength_score" not in segments.columns:
        segments["segment_market_strength_score"] = segments.get("market_strength_score", 0)
    for col in ["service_category", "region", "occupation", "age_group"]:
        if col not in segments.columns: segments[col] = ""
    for col in ["response_count", "avg_budget_aed", "need_score", "payment_readiness_score", "testability_score", "segment_market_strength_score"]:
        if col not in segments.columns: segments[col] = 0
        segments[col] = pd.to_numeric(segments[col], errors="coerce").fillna(0)
    best = segments.sort_values(["segment_market_strength_score", "response_count", "avg_budget_aed"], ascending=False).groupby("service_category").head(1).copy()
    best = best[["service_category", "region", "occupation", "age_group", "response_count", "avg_budget_aed", "need_score", "payment_readiness_score", "testability_score", "segment_market_strength_score"]]
    best = best.rename(columns={
        "region": "best_test_region", "occupation": "best_test_occupation", "age_group": "best_test_age_group",
        "response_count": "best_segment_response_count", "avg_budget_aed": "best_segment_avg_budget_aed",
        "need_score": "best_segment_need_score", "payment_readiness_score": "best_segment_payment_readiness_score",
        "testability_score": "best_segment_testability_score", "segment_market_strength_score": "best_segment_market_strength_score",
    })
    counts = segments.groupby("service_category").agg(
        total_customer_segments=("service_category", "count"),
        testable_segments=("response_count", lambda x: int((x >= 2).sum())),
        avg_segment_market_strength=("segment_market_strength_score", "mean"),
        max_segment_market_strength=("segment_market_strength_score", "max"),
    ).reset_index()
    return best.merge(counts, on="service_category", how="left")

def build_source_confidence(df):
    summary = df.groupby("service_category").agg(
        source_count=("source", "nunique"), top_source=("source", safe_top_value),
        gender_groups=("gender", "nunique"), sample_regions=("region", "nunique"), sample_occupations=("occupation", "nunique"),
    ).reset_index()
    summary["source_diversity_score"] = (normalize(summary["source_count"]) * 50 + normalize(summary["sample_regions"]) * 30 + normalize(summary["sample_occupations"]) * 20).round(2)
    return summary

def build_recommendations(df, category_metrics, customer_segments):
    category = category_metrics.copy()
    if "category_market_strength_score" not in category.columns:
        category["category_market_strength_score"] = category.get("demand_score", 0)
    if "testability_score" in category.columns:
        category = category.rename(columns={"testability_score": "agent3_category_testability_score"})
    for col in ["response_count", "avg_importance", "avg_frequency", "avg_budget_aed", "avg_sentiment", "unique_regions", "unique_occupations", "category_market_strength_score", "need_score", "payment_readiness_score", "agent3_category_testability_score"]:
        if col not in category.columns: category[col] = 0
        category[col] = pd.to_numeric(category[col], errors="coerce").fillna(0)
    merged = category.merge(calculate_growth(df), on="service_category", how="left")
    merged = merged.merge(build_segment_summary(customer_segments), on="service_category", how="left")
    merged = merged.merge(build_source_confidence(df), on="service_category", how="left")
    for col in ["recent_30_day_count", "previous_30_day_count", "growth_rate_percent", "best_segment_response_count", "best_segment_avg_budget_aed", "best_segment_need_score", "best_segment_payment_readiness_score", "best_segment_testability_score", "best_segment_market_strength_score", "total_customer_segments", "testable_segments", "avg_segment_market_strength", "max_segment_market_strength", "source_count", "gender_groups", "sample_regions", "sample_occupations", "source_diversity_score"]:
        if col not in merged.columns: merged[col] = 0
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)
    for col in ["best_test_region", "best_test_occupation", "best_test_age_group", "top_source", "top_solution_type"]:
        if col not in merged.columns: merged[col] = ""
        merged[col] = merged[col].fillna("")
    merged["budget_norm"] = normalize(merged["avg_budget_aed"])
    merged["region_norm"] = normalize(merged["unique_regions"])
    merged["occupation_norm"] = normalize(merged["unique_occupations"])
    merged["growth_norm"] = normalize(merged["growth_rate_percent"])
    merged["segment_strength_norm"] = normalize(merged["best_segment_market_strength_score"])
    merged["source_confidence_norm"] = normalize(merged["source_diversity_score"])
    merged["opportunity_gap_score"] = (((1 - merged["avg_sentiment"].clip(-1, 1)) / 2) * 40 + (merged["avg_frequency"] / 4).clip(0, 1) * 30 + (merged["avg_importance"] / 5).clip(0, 1) * 30).round(2)
    merged["feasibility_score"] = (normalize(merged["need_score"]) * 35 + normalize(merged["payment_readiness_score"]) * 25 + merged["budget_norm"] * 15 + merged["source_confidence_norm"] * 10 + normalize(merged["opportunity_gap_score"]) * 15).round(2)
    merged["scalability_score"] = (merged["region_norm"] * 30 + merged["occupation_norm"] * 20 + merged["growth_norm"] * 25 + normalize(merged["response_count"]) * 15 + merged["source_confidence_norm"] * 10).round(2)
    merged["testability_score"] = (merged["segment_strength_norm"] * 35 + normalize(merged["best_segment_response_count"]) * 20 + (merged["avg_frequency"] / 4).clip(0, 1) * 20 + (merged["avg_importance"] / 5).clip(0, 1) * 15 + normalize(merged["testable_segments"]) * 10).round(2)
    merged["business_opportunity_score"] = (merged["feasibility_score"] * 0.40 + merged["scalability_score"] * 0.30 + merged["testability_score"] * 0.30).round(2)
    merged["recommendation"] = merged["business_opportunity_score"].apply(recommendation_label)
    merged["priority_level"] = merged["business_opportunity_score"].apply(priority_label)
    merged["suggested_business_idea"] = [get_business_idea(row["service_category"], row.to_dict()) for _, row in merged.iterrows()]
    merged["recommendation_source"] = recommendation_source()
    merged["first_pilot_segment"] = merged["best_test_region"].astype(str) + " | " + merged["best_test_occupation"].astype(str) + " | " + merged["best_test_age_group"].astype(str)
    merged["why_this_opportunity"] = "Need score: " + merged["need_score"].round(1).astype(str) + ", payment readiness: " + merged["payment_readiness_score"].round(1).astype(str) + ", best pilot segment: " + merged["first_pilot_segment"].astype(str)
    return merged.sort_values("business_opportunity_score", ascending=False)

def build_region_needs(df):
    out = df.groupby(["region", "service_category"]).agg(
        response_count=("response_id", "count"), avg_importance=("importance_score", "mean"), avg_frequency=("frequency_score", "mean"),
        avg_budget_aed=("budget_midpoint_aed", "mean"), avg_sentiment=("sentiment_score", "mean"),
        top_occupation=("occupation", safe_top_value), top_age_group=("age_group", safe_top_value), common_solution_type=("preferred_solution_type", safe_top_value),
    ).reset_index()
    out["local_need_score"] = (normalize(out["response_count"]) * 30 + (out["avg_importance"] / 5).clip(0, 1) * 25 + (out["avg_frequency"] / 4).clip(0, 1) * 25 + normalize(out["avg_budget_aed"]) * 20).round(2)
    out["local_priority"] = out["local_need_score"].apply(priority_label)
    return out.sort_values(["region", "local_need_score"], ascending=[True, False])

def build_segment_recommendations(customer_segments):
    segments = customer_segments.copy()
    if "segment_market_strength_score" not in segments.columns:
        segments["segment_market_strength_score"] = segments.get("market_strength_score", 0)
    for col in ["response_count", "avg_budget_aed", "avg_frequency", "need_score", "payment_readiness_score", "testability_score", "segment_market_strength_score"]:
        if col not in segments.columns: segments[col] = 0
        segments[col] = pd.to_numeric(segments[col], errors="coerce").fillna(0)
    segments["pilot_readiness_score"] = (normalize(segments["segment_market_strength_score"]) * 40 + normalize(segments["response_count"]) * 20 + (segments["avg_frequency"] / 4).clip(0, 1) * 20 + normalize(segments["avg_budget_aed"]) * 20).round(2)
    segments["pilot_priority"] = segments["pilot_readiness_score"].apply(priority_label)
    segments["pilot_segment"] = segments["service_category"].astype(str) + " | " + segments["region"].astype(str) + " | " + segments["occupation"].astype(str) + " | " + segments["age_group"].astype(str)
    segments["suggested_business_idea"] = segments.apply(lambda row: get_business_idea(row["service_category"], row.to_dict()), axis=1)
    return segments.sort_values("pilot_readiness_score", ascending=False)

def build_customer_targeting_summary(region_metrics, occupation_metrics, age_group_metrics, gender_metrics, budget_metrics):
    rows = []
    config = [(region_metrics, "region", "region_market_strength_score", "Region"), (occupation_metrics, "occupation", "occupation_market_strength_score", "Occupation"), (age_group_metrics, "age_group", "age_group_market_strength_score", "Age group"), (gender_metrics, "gender", "gender_market_strength_score", "Gender"), (budget_metrics, "monthly_budget", "budget_market_strength_score", "Budget group")]
    for df, group_col, score_col, target_type in config:
        if not df.empty:
            if score_col not in df.columns: score_col = "market_strength_score"
            top = df.sort_values(score_col, ascending=False).iloc[0]
            rows.append({"target_type": target_type, "target_group": top[group_col], "score": top[score_col], "meaning": f"Strongest {target_type.lower()} signal in the collected sample."})
    return pd.DataFrame(rows)

def build_tableau_export(df, recommendations):
    cols = ["service_category", "feasibility_score", "scalability_score", "testability_score", "business_opportunity_score", "recommendation", "priority_level", "suggested_business_idea", "recommendation_source", "first_pilot_segment", "best_test_region", "best_test_occupation", "best_test_age_group", "why_this_opportunity"]
    cols = [c for c in cols if c in recommendations.columns]
    return df.merge(recommendations[cols], on="service_category", how="left")

def main():
    df = read_required_csv(NLP_CSV)
    category_metrics = read_required_csv(CATEGORY_METRICS_CSV)
    region_metrics = read_required_csv(REGION_METRICS_CSV)
    occupation_metrics = read_required_csv(OCCUPATION_METRICS_CSV)
    age_group_metrics = read_required_csv(AGE_GROUP_METRICS_CSV)
    gender_metrics = read_required_csv(GENDER_METRICS_CSV)
    budget_metrics = read_required_csv(BUDGET_METRICS_CSV)
    customer_segments = read_required_csv(CUSTOMER_SEGMENTS_CSV)
    recommendations = build_recommendations(df, category_metrics, customer_segments)
    region_needs = build_region_needs(df)
    segment_recommendations = build_segment_recommendations(customer_segments)
    targeting = build_customer_targeting_summary(region_metrics, occupation_metrics, age_group_metrics, gender_metrics, budget_metrics)
    tableau = build_tableau_export(df, recommendations)
    recommendations.to_csv(RECOMMENDATIONS_CSV, index=False, encoding="utf-8")
    region_needs.to_csv(REGION_NEEDS_CSV, index=False, encoding="utf-8")
    segment_recommendations.to_csv(SEGMENT_RECOMMENDATIONS_CSV, index=False, encoding="utf-8")
    targeting.to_csv(CUSTOMER_TARGETING_CSV, index=False, encoding="utf-8")
    tableau.to_csv(TABLEAU_EXPORT_CSV, index=False, encoding="utf-8")
    report = {
        "agent": "Agent 4 - Trend / Business Intelligence Agent",
        "top_recommendation": recommendations.iloc[0].to_dict() if not recommendations.empty else {},
        "top_customer_segment": segment_recommendations.iloc[0].to_dict() if not segment_recommendations.empty else {},
        "anthropic_enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
        "claude_model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
        "outputs": {
            "business_recommendations_file": str(RECOMMENDATIONS_CSV),
            "region_needs_file": str(REGION_NEEDS_CSV),
            "segment_recommendations_file": str(SEGMENT_RECOMMENDATIONS_CSV),
            "customer_targeting_summary_file": str(CUSTOMER_TARGETING_CSV),
            "tableau_ready_export": str(TABLEAU_EXPORT_CSV),
        },
    }
    TREND_REPORT_JSON.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print("Agent 4 completed successfully.")
    print(recommendations[["service_category", "business_opportunity_score", "feasibility_score", "scalability_score", "testability_score", "recommendation", "suggested_business_idea", "first_pilot_segment", "recommendation_source"]].head(10))

if __name__ == "__main__":
    main()
