"""
Agent 3 — NLP + Market Segmentation Agent
Upgrades VADER to multilingual sentiment:
cardiffnlp/twitter-xlm-roberta-base-sentiment
"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_CSV = PROJECT_ROOT / "data" / "cleaned" / "responses_cleaned.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
AGENT3_DIR = PROCESSED_DIR / "agent3_nlp"
AGENT3_DIR.mkdir(parents=True, exist_ok=True)

NLP_OUTPUT = AGENT3_DIR / "nlp_insights.csv"
KEYWORDS_OUTPUT = AGENT3_DIR / "topic_keywords.csv"
CATEGORY_METRICS_OUTPUT = AGENT3_DIR / "category_metrics.csv"
REGION_METRICS_OUTPUT = AGENT3_DIR / "region_metrics.csv"
OCCUPATION_METRICS_OUTPUT = AGENT3_DIR / "occupation_metrics.csv"
AGE_GROUP_METRICS_OUTPUT = AGENT3_DIR / "age_group_metrics.csv"
GENDER_METRICS_OUTPUT = AGENT3_DIR / "gender_metrics.csv"
BUDGET_METRICS_OUTPUT = AGENT3_DIR / "budget_metrics.csv"
CUSTOMER_SEGMENTS_OUTPUT = AGENT3_DIR / "customer_segments.csv"
MARKET_SIGNALS_OUTPUT = AGENT3_DIR / "market_signals.csv"
NLP_REPORT = AGENT3_DIR / "nlp_report.json"

def get_top_value(series):
    series = series.dropna()
    if series.empty:
        return ""
    counts = series.value_counts()
    return "" if counts.empty else counts.index[0]

def safe_normalize(series):
    series = pd.to_numeric(series, errors="coerce").fillna(0)
    max_value = series.max()
    if pd.isna(max_value) or max_value == 0:
        return pd.Series([0] * len(series), index=series.index)
    return series / max_value

def require_columns(df, required):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError("Agent 3 cannot run. Missing columns: " + ", ".join(missing) + ". Run cleaning_agent.py first.")

def load_multilingual_sentiment_pipeline():
    try:
        from transformers import pipeline
        return pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            truncation=True,
            max_length=512,
        )
    except Exception as error:
        warnings.warn(
            "Could not load multilingual transformer sentiment model. "
            f"Using fallback sentiment. Error: {type(error).__name__}: {error}"
        )
        return None

def normalize_transformer_sentiment(result):
    label = str(result.get("label", "")).lower()
    confidence = float(result.get("score", 0))
    mapping = {
        "label_0": "negative", "0": "negative", "negative": "negative",
        "label_1": "neutral", "1": "neutral", "neutral": "neutral",
        "label_2": "positive", "2": "positive", "positive": "positive",
    }
    sentiment = mapping.get(label, "neutral")
    if sentiment == "positive":
        score = confidence
    elif sentiment == "negative":
        score = -confidence
    else:
        score = 0.0
    return sentiment, round(score, 4)

def fallback_sentiment(text):
    text = str(text).lower()
    positive = ["help", "useful", "good", "need", "support", "benefit", "save time", "فرصة", "مفيد", "جيد", "نحتاج", "يساعد"]
    negative = ["hard", "difficult", "delay", "expensive", "problem", "struggle", "صعب", "مشكلة", "تأخير", "غالي"]
    p = sum(1 for w in positive if w in text)
    n = sum(1 for w in negative if w in text)
    if p > n:
        return "positive", 0.35
    if n > p:
        return "negative", -0.35
    return "neutral", 0.0

def add_sentiment(df):
    df = df.copy()
    df["analysis_text"] = df["analysis_text"].fillna("").astype(str)
    sentiment_pipeline = load_multilingual_sentiment_pipeline()
    labels, scores = [], []
    if sentiment_pipeline is None:
        for text in df["analysis_text"].tolist():
            label, score = fallback_sentiment(text)
            labels.append(label); scores.append(score)
        df["sentiment_model"] = "fallback_keyword_sentiment"
    else:
        texts = df["analysis_text"].tolist()
        for start in range(0, len(texts), 16):
            for result in sentiment_pipeline(texts[start:start + 16]):
                label, score = normalize_transformer_sentiment(result)
                labels.append(label); scores.append(score)
        df["sentiment_model"] = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    df["sentiment_label"] = labels
    df["sentiment_score"] = scores
    return df

def extract_tfidf_keywords(df, top_n=8):
    rows = []
    for category, group in df.groupby("service_category"):
        texts = group["analysis_text"].fillna("").astype(str).str.strip().tolist()
        texts = [text for text in texts if text]
        if len(texts) < 2:
            rows.append({"service_category": category, "method": "tfidf", "topic_id": "", "keywords": ""})
            continue
        try:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=150)
            matrix = vectorizer.fit_transform(texts)
            scores = np.asarray(matrix.mean(axis=0)).ravel()
            terms = np.array(vectorizer.get_feature_names_out())
            top_indices = scores.argsort()[::-1][:top_n]
            rows.append({"service_category": category, "method": "tfidf", "topic_id": "", "keywords": ", ".join(terms[top_indices].tolist())})
        except ValueError:
            rows.append({"service_category": category, "method": "tfidf", "topic_id": "", "keywords": ""})
    return pd.DataFrame(rows)

def try_bertopic(df):
    try:
        from bertopic import BERTopic
        texts = df["analysis_text"].fillna("").astype(str).str.strip().tolist()
        texts = [text if text else "empty response" for text in texts]
        if len([t for t in texts if t != "empty response"]) < 5:
            raise ValueError("Not enough meaningful text rows for BERTopic.")
        topic_model = BERTopic(language="multilingual", calculate_probabilities=False, verbose=False)
        topics, _ = topic_model.fit_transform(texts)
        df = df.copy(); df["bertopic_topic"] = topics
        rows = []
        for topic_id in topic_model.get_topic_info()["Topic"].tolist():
            if topic_id == -1:
                continue
            words = topic_model.get_topic(topic_id)
            if words:
                rows.append({"service_category": "all", "method": "bertopic_multilingual", "topic_id": topic_id, "keywords": ", ".join([w for w, _ in words[:8]])})
        keyword_df = pd.DataFrame(rows)
        if keyword_df.empty:
            return df, extract_tfidf_keywords(df), "tfidf_fallback"
        return df, keyword_df, "bertopic_multilingual"
    except Exception:
        df = df.copy(); df["bertopic_topic"] = "not_used"
        return df, extract_tfidf_keywords(df), "tfidf_fallback"

def build_group_metrics(df, group_columns):
    metrics = df.groupby(group_columns).agg(
        response_count=("response_id", "count"),
        avg_importance=("importance_score", "mean"),
        avg_frequency=("frequency_score", "mean"),
        avg_budget_aed=("budget_midpoint_aed", "mean"),
        avg_sentiment=("sentiment_score", "mean"),
        top_service_category=("service_category", get_top_value),
        top_region=("region", get_top_value),
        top_occupation=("occupation", get_top_value),
        top_age_group=("age_group", get_top_value),
        top_gender=("gender", get_top_value),
        top_solution_type=("preferred_solution_type", get_top_value),
        unique_regions=("region", "nunique"),
        unique_occupations=("occupation", "nunique"),
        unique_age_groups=("age_group", "nunique"),
        unique_genders=("gender", "nunique"),
    ).reset_index()
    metrics["volume_score"] = safe_normalize(metrics["response_count"])
    metrics["budget_score"] = safe_normalize(metrics["avg_budget_aed"])
    metrics["need_score"] = ((metrics["avg_importance"] / 5) * 35 + (metrics["avg_frequency"] / 4) * 35 + metrics["volume_score"] * 20 + ((1 - metrics["avg_sentiment"].clip(-1, 1)) / 2) * 10).round(2)
    metrics["payment_readiness_score"] = (metrics["budget_score"] * 70 + (metrics["avg_importance"] / 5) * 30).round(2)
    metrics["testability_score"] = (metrics["volume_score"] * 35 + (metrics["avg_frequency"] / 4) * 25 + (metrics["avg_importance"] / 5) * 25 + metrics["budget_score"] * 15).round(2)
    metrics["market_strength_score"] = (metrics["need_score"] * 0.45 + metrics["payment_readiness_score"] * 0.30 + metrics["testability_score"] * 0.25).round(2)
    return metrics.sort_values("market_strength_score", ascending=False)

def build_category_metrics(df): return build_group_metrics(df, ["service_category"]).rename(columns={"market_strength_score": "category_market_strength_score"})
def build_region_metrics(df): return build_group_metrics(df, ["region"]).rename(columns={"market_strength_score": "region_market_strength_score"})
def build_occupation_metrics(df): return build_group_metrics(df, ["occupation"]).rename(columns={"market_strength_score": "occupation_market_strength_score"})
def build_age_group_metrics(df): return build_group_metrics(df, ["age_group"]).rename(columns={"market_strength_score": "age_group_market_strength_score"})
def build_gender_metrics(df): return build_group_metrics(df, ["gender"]).rename(columns={"market_strength_score": "gender_market_strength_score"})
def build_budget_metrics(df): return build_group_metrics(df, ["monthly_budget"]).rename(columns={"market_strength_score": "budget_market_strength_score"})

def build_customer_segments(df):
    segments = build_group_metrics(df, ["service_category", "region", "occupation", "age_group"])
    segments = segments.rename(columns={"market_strength_score": "segment_market_strength_score"})
    return segments.sort_values(["segment_market_strength_score", "response_count", "avg_budget_aed", "avg_frequency"], ascending=False)

def build_market_signals(category_metrics, region_metrics, occupation_metrics, age_group_metrics, gender_metrics, budget_metrics):
    rows = []
    config = [
        (category_metrics, "service_category", "category_market_strength_score", "top_service_category", "Service category with strongest market signal."),
        (region_metrics, "region", "region_market_strength_score", "top_region", "Region with strongest demand and test potential."),
        (occupation_metrics, "occupation", "occupation_market_strength_score", "top_occupation", "Occupation group most likely to be a strong customer segment."),
        (age_group_metrics, "age_group", "age_group_market_strength_score", "top_age_group", "Age group with strongest demand and payment readiness."),
        (gender_metrics, "gender", "gender_market_strength_score", "top_gender", "Gender group with strongest market signal."),
        (budget_metrics, "monthly_budget", "budget_market_strength_score", "top_budget_group", "Budget group with strongest demand and payment-readiness signal."),
    ]
    for df, name_col, score_col, signal_type, meaning in config:
        if not df.empty:
            top = df.iloc[0]
            rows.append({"signal_type": signal_type, "signal_name": top[name_col], "score": top[score_col], "meaning": meaning})
    return pd.DataFrame(rows)

def main():
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"Cannot find {CLEANED_CSV}. Run cleaning_agent.py first.")
    df = pd.read_csv(CLEANED_CSV)
    require_columns(df, [
        "response_id", "age_group", "gender", "region", "occupation", "source", "service_category",
        "importance_score", "frequency_score", "budget_midpoint_aed", "monthly_budget",
        "preferred_solution_type", "analysis_text",
    ])
    df = add_sentiment(df)
    df_topics, keyword_df, method_used = try_bertopic(df)
    category_metrics = build_category_metrics(df_topics)
    region_metrics = build_region_metrics(df_topics)
    occupation_metrics = build_occupation_metrics(df_topics)
    age_group_metrics = build_age_group_metrics(df_topics)
    gender_metrics = build_gender_metrics(df_topics)
    budget_metrics = build_budget_metrics(df_topics)
    customer_segments = build_customer_segments(df_topics)
    market_signals = build_market_signals(category_metrics, region_metrics, occupation_metrics, age_group_metrics, gender_metrics, budget_metrics)
    df_topics.to_csv(NLP_OUTPUT, index=False, encoding="utf-8")
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
        "sentiment_model": df_topics["sentiment_model"].iloc[0] if not df_topics.empty else "unknown",
        "method_used": method_used,
        "rows_analyzed": int(len(df_topics)),
        "sentiment_counts": df_topics["sentiment_label"].value_counts().to_dict(),
    }
    NLP_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Agent 3 completed successfully.")
    print(f"NLP method used: {method_used}")
    print(customer_segments.head(10))

if __name__ == "__main__":
    main()
