"""
Agent 3: NLP + Market Segmentation Agent
----------------------------------------

Role:
1. Read cleaned community response data.
2. Analyze opinion text using sentiment analysis.
3. Extract keywords/topics from community responses.
4. Analyze demand by service category.
5. Analyze demand by region, occupation, age group, gender, and budget.
6. Find the strongest customer segments for entrepreneurs to test first.

BERTopic is optional.
If BERTopic is not installed, the agent automatically uses TF-IDF.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ============================================================
# 1. Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_CSV = PROJECT_ROOT / "data" / "cleaned" / "responses_cleaned.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

NLP_OUTPUT = PROCESSED_DIR / "nlp_insights.csv"
KEYWORDS_OUTPUT = PROCESSED_DIR / "topic_keywords.csv"

CATEGORY_METRICS_OUTPUT = PROCESSED_DIR / "category_metrics.csv"
REGION_METRICS_OUTPUT = PROCESSED_DIR / "region_metrics.csv"
OCCUPATION_METRICS_OUTPUT = PROCESSED_DIR / "occupation_metrics.csv"
AGE_GROUP_METRICS_OUTPUT = PROCESSED_DIR / "age_group_metrics.csv"
GENDER_METRICS_OUTPUT = PROCESSED_DIR / "gender_metrics.csv"
BUDGET_METRICS_OUTPUT = PROCESSED_DIR / "budget_metrics.csv"

CUSTOMER_SEGMENTS_OUTPUT = PROCESSED_DIR / "customer_segments.csv"
MARKET_SIGNALS_OUTPUT = PROCESSED_DIR / "market_signals.csv"

NLP_REPORT = PROCESSED_DIR / "nlp_report.json"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. Helper functions
# ============================================================

def sentiment_label(score):
    """
    Convert VADER compound sentiment score into a simple label.
    """

    if score >= 0.25:
        return "positive"

    if score <= -0.25:
        return "negative"

    return "neutral"


def get_top_value(series):
    """
    Return the most common value in a column.
    """

    series = series.dropna()

    if series.empty:
        return ""

    value_counts = series.value_counts()

    if value_counts.empty:
        return ""

    return value_counts.index[0]


def safe_normalize(series):
    """
    Normalize numbers into a 0-1 range.

    If max is 0, return 0 to avoid division errors.
    """

    max_value = series.max()

    if pd.isna(max_value) or max_value == 0:
        return pd.Series([0] * len(series), index=series.index)

    return series / max_value


def require_columns(df, required_columns):
    """
    Make sure the cleaned dataset has all columns needed by Agent 3.
    """

    missing_columns = []

    for column in required_columns:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(
            "Agent 3 cannot run because these columns are missing: "
            + ", ".join(missing_columns)
            + "\nRun cleaning_agent.py first and make sure it creates these columns."
        )


# ============================================================
# 3. Sentiment analysis
# ============================================================

def add_sentiment(df):
    """
    Analyze each response text and add:
    - sentiment_score
    - sentiment_label
    """

    analyzer = SentimentIntensityAnalyzer()

    df = df.copy()

    df["analysis_text"] = df["analysis_text"].fillna("").astype(str)

    df["sentiment_score"] = df["analysis_text"].apply(
        lambda text: analyzer.polarity_scores(text)["compound"]
    )

    df["sentiment_label"] = df["sentiment_score"].apply(sentiment_label)

    return df


# ============================================================
# 4. Keyword extraction
# ============================================================

def extract_tfidf_keywords(df, top_n=8):
    """
    Extract top keywords for each service category using TF-IDF.

    Example:
    Delivery -> grocery, pharmacy, late, remote, expensive
    Education -> tutoring, students, online, school
    """

    rows = []

    for category, group in df.groupby("service_category"):
        texts = (
            group["analysis_text"]
            .fillna("")
            .astype(str)
            .str.strip()
            .tolist()
        )

        texts = [text for text in texts if text]

        if len(texts) < 2:
            rows.append({
                "service_category": category,
                "method": "tfidf",
                "topic_id": "",
                "keywords": ""
            })
            continue

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                max_features=150
            )

            matrix = vectorizer.fit_transform(texts)

            scores = np.asarray(matrix.mean(axis=0)).ravel()
            terms = np.array(vectorizer.get_feature_names_out())

            top_indices = scores.argsort()[::-1][:top_n]
            keywords = terms[top_indices].tolist()

            rows.append({
                "service_category": category,
                "method": "tfidf",
                "topic_id": "",
                "keywords": ", ".join(keywords)
            })

        except ValueError:
            rows.append({
                "service_category": category,
                "method": "tfidf",
                "topic_id": "",
                "keywords": ""
            })

    return pd.DataFrame(rows)


def try_bertopic(df):
    """
    Try BERTopic topic modeling.

    Important:
    BERTopic is optional for this project.

    If BERTopic is not installed or fails, Agent 3 does not crash.
    It automatically falls back to TF-IDF.
    """

    try:
        from bertopic import BERTopic

        texts = (
            df["analysis_text"]
            .fillna("")
            .astype(str)
            .str.strip()
            .tolist()
        )

        # Keep the same number of texts as the dataframe rows.
        # This prevents row mismatch errors when assigning topics back to df.
        texts = [text if text else "empty response" for text in texts]

        meaningful_texts = [text for text in texts if text != "empty response"]

        if len(meaningful_texts) < 5:
            raise ValueError("Not enough meaningful text rows for BERTopic.")

        topic_model = BERTopic(
            language="english",
            calculate_probabilities=False,
            verbose=False
        )

        topics, _ = topic_model.fit_transform(texts)

        df = df.copy()
        df["bertopic_topic"] = topics

        topic_info = topic_model.get_topic_info()

        topic_rows = []

        for topic_id in topic_info["Topic"].tolist():
            if topic_id == -1:
                continue

            topic_words = topic_model.get_topic(topic_id)

            if not topic_words:
                continue

            keywords = ", ".join([word for word, score in topic_words[:8]])

            topic_rows.append({
                "service_category": "all",
                "method": "bertopic",
                "topic_id": topic_id,
                "keywords": keywords
            })

        keyword_df = pd.DataFrame(topic_rows)

        if keyword_df.empty:
            keyword_df = extract_tfidf_keywords(df)

            # Clean message. No scary error.
            method_used = "tfidf_fallback"
        else:
            method_used = "bertopic"

        return df, keyword_df, method_used

    except Exception:
        df = df.copy()
        df["bertopic_topic"] = "not_used"

        keyword_df = extract_tfidf_keywords(df)

        # BERTopic is optional.
        # If it is missing or fails, Agent 3 intentionally uses TF-IDF.
        method_used = "tfidf_fallback"

        return df, keyword_df, method_used


# ============================================================
# 5. General grouped metrics
# ============================================================

def build_group_metrics(df, group_columns):
    """
    Build useful business metrics for any grouping.

    Examples:
    - by service_category
    - by region
    - by occupation
    - by age_group
    - by gender
    - by monthly_budget
    - by service_category + region + occupation + age_group

    This helps answer:
    - Who has the highest need?
    - Who is most willing to pay?
    - Where is the pain strongest?
    - Which segment is easiest to test first?
    """

    metrics = (
        df.groupby(group_columns)
        .agg(
            response_count=("response_id", "count"),

            avg_importance=("importance_score", "mean"),
            avg_frequency=("frequency_score", "mean"),
            avg_urgency=("urgency_score", "mean"),
            avg_pain=("pain_score", "mean"),

            avg_budget_aed=("budget_midpoint_aed", "mean"),
            avg_would_pay=("would_pay_score", "mean"),
            avg_satisfaction=("satisfaction_score", "mean"),
            avg_sentiment=("sentiment_score", "mean"),

            top_service_category=("service_category", get_top_value),
            top_region=("region", get_top_value),
            top_occupation=("occupation", get_top_value),
            top_age_group=("age_group", get_top_value),
            top_gender=("gender", get_top_value),
            top_solution_type=("preferred_solution_type", get_top_value),
            top_current_solution=("current_solution", get_top_value),

            unique_regions=("region", "nunique"),
            unique_occupations=("occupation", "nunique"),
            unique_age_groups=("age_group", "nunique"),
            unique_genders=("gender", "nunique"),
        )
        .reset_index()
    )

    metrics["volume_score"] = safe_normalize(metrics["response_count"])
    metrics["budget_score"] = safe_normalize(metrics["avg_budget_aed"])

    metrics["willingness_to_pay_score"] = metrics["avg_would_pay"]

    metrics["need_score"] = (
        (metrics["avg_importance"] / 5) * 25 +
        (metrics["avg_frequency"] / 4) * 25 +
        (metrics["avg_urgency"] / 5) * 25 +
        (metrics["avg_pain"] / 5) * 25
    ).round(2)

    metrics["payment_readiness_score"] = (
        metrics["budget_score"] * 50 +
        metrics["willingness_to_pay_score"] * 50
    ).round(2)

    metrics["testability_score"] = (
        metrics["volume_score"] * 30 +
        (metrics["avg_urgency"] / 5) * 25 +
        metrics["willingness_to_pay_score"] * 25 +
        (metrics["avg_frequency"] / 4) * 20
    ).round(2)

    metrics["market_strength_score"] = (
        metrics["need_score"] * 0.45 +
        metrics["payment_readiness_score"] * 0.35 +
        metrics["testability_score"] * 0.20
    ).round(2)

    metrics = metrics.sort_values(
        by="market_strength_score",
        ascending=False
    )

    return metrics


# ============================================================
# 6. Business analysis tables
# ============================================================

def build_category_metrics(df):
    """
    Analyze each service category.

    Example:
    Delivery vs Education vs Transport vs Agriculture.
    """

    metrics = build_group_metrics(df, ["service_category"])

    metrics = metrics.rename(columns={
        "market_strength_score": "category_market_strength_score"
    })

    return metrics


def build_region_metrics(df):
    """
    Analyze each region.

    This answers:
    - Which region has the strongest need?
    - Which region has the highest willingness to pay?
    - Which region should the entrepreneur test in first?
    """

    metrics = build_group_metrics(df, ["region"])

    metrics = metrics.rename(columns={
        "market_strength_score": "region_market_strength_score"
    })

    return metrics


def build_occupation_metrics(df):
    """
    Analyze each occupation.

    This answers:
    - Which occupation is most affected?
    - Which occupation is most willing to pay?
    - Which occupation should the business target first?
    """

    metrics = build_group_metrics(df, ["occupation"])

    metrics = metrics.rename(columns={
        "market_strength_score": "occupation_market_strength_score"
    })

    return metrics


def build_age_group_metrics(df):
    """
    Analyze each age group.

    This answers:
    - Which age group has the strongest need?
    - Which age group is most likely to pay?
    - Which age group may adopt the solution?
    """

    metrics = build_group_metrics(df, ["age_group"])

    metrics = metrics.rename(columns={
        "market_strength_score": "age_group_market_strength_score"
    })

    return metrics


def build_gender_metrics(df):
    """
    Analyze responses by gender.

    This is useful for checking whether demand differs across gender groups.
    """

    metrics = build_group_metrics(df, ["gender"])

    metrics = metrics.rename(columns={
        "market_strength_score": "gender_market_strength_score"
    })

    return metrics


def build_budget_metrics(df):
    """
    Analyze budget groups.

    This answers:
    - Which budget group has the most demand?
    - Are higher-budget groups also more urgent?
    - Is there real payment readiness?
    """

    metrics = build_group_metrics(df, ["monthly_budget"])

    metrics = metrics.rename(columns={
        "market_strength_score": "budget_market_strength_score"
    })

    return metrics


def build_customer_segments(df):
    """
    Build customer segments.

    A segment is:
    service category + region + occupation + age group

    Example:
    Delivery + Hatta + Shop owner + 35-44

    This helps the entrepreneur choose who to interview,
    test with, and sell to first.
    """

    segments = build_group_metrics(
        df,
        ["service_category", "region", "occupation", "age_group"]
    )

    segments = segments.rename(columns={
        "market_strength_score": "segment_market_strength_score"
    })

    segments = segments.sort_values(
        by=[
            "segment_market_strength_score",
            "response_count",
            "avg_would_pay",
            "avg_budget_aed"
        ],
        ascending=False
    )

    return segments


def build_market_signals(
    category_metrics,
    region_metrics,
    occupation_metrics,
    age_group_metrics,
    gender_metrics,
    budget_metrics
):
    """
    Create a small summary table for dashboards and Agent 4.

    This does not make the final business decision.
    It gives signals that Agent 4 can later use for:
    - feasibility
    - scalability
    - testability
    - opportunity ranking
    """

    rows = []

    if not category_metrics.empty:
        top_category = category_metrics.iloc[0]
        rows.append({
            "signal_type": "top_service_category",
            "signal_name": top_category["service_category"],
            "score": top_category["category_market_strength_score"],
            "meaning": "Service category with strongest market signal."
        })

    if not region_metrics.empty:
        top_region = region_metrics.iloc[0]
        rows.append({
            "signal_type": "top_region",
            "signal_name": top_region["region"],
            "score": top_region["region_market_strength_score"],
            "meaning": "Region with strongest demand and test potential."
        })

    if not occupation_metrics.empty:
        top_occupation = occupation_metrics.iloc[0]
        rows.append({
            "signal_type": "top_occupation",
            "signal_name": top_occupation["occupation"],
            "score": top_occupation["occupation_market_strength_score"],
            "meaning": "Occupation group most likely to be a strong customer segment."
        })

    if not age_group_metrics.empty:
        top_age_group = age_group_metrics.iloc[0]
        rows.append({
            "signal_type": "top_age_group",
            "signal_name": top_age_group["age_group"],
            "score": top_age_group["age_group_market_strength_score"],
            "meaning": "Age group with strongest demand and payment readiness."
        })

    if not gender_metrics.empty:
        top_gender = gender_metrics.iloc[0]
        rows.append({
            "signal_type": "top_gender",
            "signal_name": top_gender["gender"],
            "score": top_gender["gender_market_strength_score"],
            "meaning": "Gender group with strongest market signal in the collected sample."
        })

    if not budget_metrics.empty:
        top_budget = budget_metrics.iloc[0]
        rows.append({
            "signal_type": "top_budget_group",
            "signal_name": top_budget["monthly_budget"],
            "score": top_budget["budget_market_strength_score"],
            "meaning": "Budget group with strongest demand and payment readiness."
        })

    return pd.DataFrame(rows)


# ============================================================
# 7. Main function
# ============================================================

def main():
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(
            f"Cannot find {CLEANED_CSV}. Run cleaning_agent.py first."
        )

    df = pd.read_csv(CLEANED_CSV)

    required_columns = [
        "response_id",
        "age_group",
        "gender",
        "region",
        "occupation",
        "source",
        "service_category",

        "importance_score",
        "frequency_score",
        "urgency_score",
        "pain_score",
        "satisfaction_score",
        "would_pay_score",
        "budget_midpoint_aed",

        "monthly_budget",
        "current_solution",
        "preferred_solution_type",
        "analysis_text",
    ]

    require_columns(df, required_columns)

    df = add_sentiment(df)

    df_with_topics, keyword_df, method_used = try_bertopic(df)

    category_metrics = build_category_metrics(df_with_topics)
    region_metrics = build_region_metrics(df_with_topics)
    occupation_metrics = build_occupation_metrics(df_with_topics)
    age_group_metrics = build_age_group_metrics(df_with_topics)
    gender_metrics = build_gender_metrics(df_with_topics)
    budget_metrics = build_budget_metrics(df_with_topics)
    customer_segments = build_customer_segments(df_with_topics)

    market_signals = build_market_signals(
        category_metrics=category_metrics,
        region_metrics=region_metrics,
        occupation_metrics=occupation_metrics,
        age_group_metrics=age_group_metrics,
        gender_metrics=gender_metrics,
        budget_metrics=budget_metrics
    )

    df_with_topics.to_csv(NLP_OUTPUT, index=False, encoding="utf-8")
    keyword_df.to_csv(KEYWORDS_OUTPUT, index=False, encoding="utf-8")

    category_metrics.to_csv(CATEGORY_METRICS_OUTPUT, index=False, encoding="utf-8")
    region_metrics.to_csv(REGION_METRICS_OUTPUT, index=False, encoding="utf-8")
    occupation_metrics.to_csv(OCCUPATION_METRICS_OUTPUT, index=False, encoding="utf-8")
    age_group_metrics.to_csv(AGE_GROUP_METRICS_OUTPUT, index=False, encoding="utf-8")
    gender_metrics.to_csv(GENDER_METRICS_OUTPUT, index=False, encoding="utf-8")
    budget_metrics.to_csv(BUDGET_METRICS_OUTPUT, index=False, encoding="utf-8")

    customer_segments.to_csv(CUSTOMER_SEGMENTS_OUTPUT, index=False, encoding="utf-8")
    market_signals.to_csv(MARKET_SIGNALS_OUTPUT, index=False, encoding="utf-8")

    report = {
        "agent": "Agent 3 - NLP + Market Segmentation Agent",
        "method_used": method_used,
        "topic_model_note": "BERTopic is optional. If unavailable, TF-IDF is used.",

        "rows_analyzed": int(len(df_with_topics)),
        "categories_analyzed": int(df_with_topics["service_category"].nunique()),
        "regions_analyzed": int(df_with_topics["region"].nunique()),
        "occupations_analyzed": int(df_with_topics["occupation"].nunique()),
        "age_groups_analyzed": int(df_with_topics["age_group"].nunique()),
        "gender_groups_analyzed": int(df_with_topics["gender"].nunique()),

        "sentiment_counts": df_with_topics["sentiment_label"].value_counts().to_dict(),

        "outputs": {
            "nlp_output": str(NLP_OUTPUT),
            "keywords_output": str(KEYWORDS_OUTPUT),
            "category_metrics_output": str(CATEGORY_METRICS_OUTPUT),
            "region_metrics_output": str(REGION_METRICS_OUTPUT),
            "occupation_metrics_output": str(OCCUPATION_METRICS_OUTPUT),
            "age_group_metrics_output": str(AGE_GROUP_METRICS_OUTPUT),
            "gender_metrics_output": str(GENDER_METRICS_OUTPUT),
            "budget_metrics_output": str(BUDGET_METRICS_OUTPUT),
            "customer_segments_output": str(CUSTOMER_SEGMENTS_OUTPUT),
            "market_signals_output": str(MARKET_SIGNALS_OUTPUT),
        }
    }

    NLP_REPORT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print("Agent 3 completed successfully.")
    print()
    print(f"Saved NLP insights to: {NLP_OUTPUT}")
    print(f"Saved keywords/topics to: {KEYWORDS_OUTPUT}")
    print(f"Saved category metrics to: {CATEGORY_METRICS_OUTPUT}")
    print(f"Saved region metrics to: {REGION_METRICS_OUTPUT}")
    print(f"Saved occupation metrics to: {OCCUPATION_METRICS_OUTPUT}")
    print(f"Saved age group metrics to: {AGE_GROUP_METRICS_OUTPUT}")
    print(f"Saved gender metrics to: {GENDER_METRICS_OUTPUT}")
    print(f"Saved budget metrics to: {BUDGET_METRICS_OUTPUT}")
    print(f"Saved customer segments to: {CUSTOMER_SEGMENTS_OUTPUT}")
    print(f"Saved market signals to: {MARKET_SIGNALS_OUTPUT}")
    print(f"Saved NLP report to: {NLP_REPORT}")
    print()
    print(f"NLP method used: {method_used}")
    print()
    print("Top customer segments:")
    print(customer_segments.head(10))


if __name__ == "__main__":
    main()