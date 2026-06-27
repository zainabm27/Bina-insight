from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import sys
from typing import Any

import pandas as pd

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
CLEANED_CSV = DATA_DIR / "cleaned" / "responses_cleaned.csv"

OUTPUT_DIR = DATA_DIR / "processed" / "agent3_nlp"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_NLP_INSIGHTS = OUTPUT_DIR / "nlp_insights.csv"
OUTPUT_CATEGORY_METRICS = OUTPUT_DIR / "category_metrics.csv"
OUTPUT_REGION_METRICS = OUTPUT_DIR / "region_metrics.csv"
OUTPUT_CUSTOMER_SEGMENTS = OUTPUT_DIR / "customer_segments.csv"
OUTPUT_AGE_GROUP_METRICS = OUTPUT_DIR / "age_group_metrics.csv"
OUTPUT_GENDER_METRICS = OUTPUT_DIR / "gender_metrics.csv"
OUTPUT_OCCUPATION_METRICS = OUTPUT_DIR / "occupation_metrics.csv"
OUTPUT_BUDGET_METRICS = OUTPUT_DIR / "budget_metrics.csv"
OUTPUT_TOPIC_KEYWORDS = OUTPUT_DIR / "topic_keywords.csv"
OUTPUT_MARKET_SIGNALS = OUTPUT_DIR / "market_signals.csv"
OUTPUT_REPORT = OUTPUT_DIR / "nlp_report.json"

TRANSFORMER_MODEL_NAME = os.getenv(
    "SENTIMENT_MODEL",
    "cardiffnlp/twitter-xlm-roberta-base-sentiment",
)

# ---------------------------------------------------------------------------
# USE_TRANSFORMER controls whether the heavy XLM-RoBERTa model is loaded.
#
# Default: FALSE — uses the fast keyword fallback.
# This is the right default for Streamlit Cloud and any environment where
# downloading a ~500 MB model is impractical.
#
# To enable the full transformer locally, set in .env:
#   USE_TRANSFORMER=true
# ---------------------------------------------------------------------------
USE_TRANSFORMER = os.getenv("USE_TRANSFORMER", "false").strip().lower() == "true"

ENGLISH_POSITIVE_WORDS = {
    "good", "great", "excellent", "helpful", "needed", "important", "useful",
    "affordable", "easy", "safe", "reliable", "fast", "better", "improve",
    "support", "opportunity", "benefit", "like", "love", "want",
}

ENGLISH_NEGATIVE_WORDS = {
    "bad", "poor", "expensive", "difficult", "hard", "slow", "unsafe",
    "unreliable", "problem", "issue", "lack", "missing", "far", "delay",
    "costly", "urgent", "struggle", "cannot", "can't", "no", "not",
}

ARABIC_POSITIVE_WORDS = {
    "جيد", "ممتاز", "مهمة", "مهم", "مفيد", "سهل", "آمن", "موثوق",
    "سريع", "أفضل", "نحتاج", "احتاج", "فرصة", "يساعد", "تحسين", "مناسب",
}

ARABIC_NEGATIVE_WORDS = {
    "مشكلة", "صعب", "بعيد", "غالي", "مكلف", "ضعيف", "تأخير", "خطر",
    "غير", "لا", "نقص", "أزمة", "سيء", "بطيء", "مستعجل", "ضروري",
}


def normalize_text(text: Any) -> str:
    text = "" if pd.isna(text) else str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_words(text: str) -> list[str]:
    text = normalize_text(text).lower()
    tokens = re.findall(r"[\w\u0600-\u06FF']+", text)
    return [token for token in tokens if len(token) > 2]


def build_analysis_text(row: pd.Series) -> str:
    parts = [
        row.get("main_problem", ""),
        row.get("needed_service", ""),
        row.get("opinion_text", ""),
    ]
    return " ".join(normalize_text(part) for part in parts if normalize_text(part))


def convert_budget_to_midpoint(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    text = str(value).lower().strip()
    text = text.replace("aed", "").replace("درهم", "").replace(",", "").strip()
    if "+" in text:
        number = re.findall(r"\d+", text)
        return float(number[0]) if number else 0.0
    numbers = re.findall(r"\d+", text)
    if len(numbers) >= 2:
        return (float(numbers[0]) + float(numbers[1])) / 2
    if len(numbers) == 1:
        return float(numbers[0])
    return 0.0


def importance_to_score(value: Any) -> float:
    if pd.isna(value):
        return 3.0
    text = str(value).strip().lower()
    mapping = {
        "very low": 1, "low": 2, "medium": 3, "high": 4, "very high": 5,
        "urgent": 5, "not important": 1, "slightly important": 2,
        "important": 4, "very important": 5,
        "منخفض": 2, "متوسط": 3, "مرتفع": 4, "مهم": 4, "مهم جداً": 5, "ضروري": 5,
    }
    if text in mapping:
        return float(mapping[text])
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if numbers:
        number = float(numbers[0])
        if number <= 5:
            return number
        if number <= 100:
            return max(1.0, min(5.0, number / 20))
    return 3.0


def frequency_to_score(value: Any) -> float:
    if pd.isna(value):
        return 3.0
    text = str(value).strip().lower()
    mapping = {
        "rarely": 1, "occasionally": 2, "monthly": 3, "weekly": 4, "daily": 5,
        "always": 5, "نادراً": 1, "أحياناً": 2, "شهري": 3, "أسبوعي": 4,
        "يومي": 5, "دائماً": 5,
    }
    if text in mapping:
        return float(mapping[text])
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if numbers:
        return max(1.0, min(5.0, float(numbers[0])))
    return 3.0


def fallback_sentiment(text: str) -> dict[str, Any]:
    """
    Fast keyword-based sentiment. No model download required.
    Used by default and as a safety net if the transformer fails.
    """
    text = normalize_text(text)
    tokens = tokenize_words(text)

    positive_hits = 0
    negative_hits = 0

    for token in tokens:
        if token in ENGLISH_POSITIVE_WORDS or token in ARABIC_POSITIVE_WORDS:
            positive_hits += 1
        if token in ENGLISH_NEGATIVE_WORDS or token in ARABIC_NEGATIVE_WORDS:
            negative_hits += 1

    raw_score = positive_hits - negative_hits

    if raw_score > 0:
        label = "positive"
    elif raw_score < 0:
        label = "negative"
    else:
        label = "neutral"

    confidence = min(0.95, 0.50 + (abs(raw_score) * 0.10))

    return {
        "sentiment_label": label,
        "sentiment_score": round(confidence, 4),
        "sentiment_method": "keyword_fallback",
        "positive_keyword_hits": positive_hits,
        "negative_keyword_hits": negative_hits,
    }


def load_transformer_pipeline():
    """
    Only called when USE_TRANSFORMER=true.
    Downloads ~500 MB on first run — not suitable for Streamlit Cloud.
    """
    if not USE_TRANSFORMER:
        print(
            "INFO: USE_TRANSFORMER is false (default). "
            "Using fast keyword sentiment. "
            "Set USE_TRANSFORMER=true in .env to enable XLM-RoBERTa."
        )
        return None

    try:
        from transformers import pipeline

        print(f"Loading multilingual transformer: {TRANSFORMER_MODEL_NAME}")
        return pipeline(
            "sentiment-analysis",
            model=TRANSFORMER_MODEL_NAME,
            tokenizer=TRANSFORMER_MODEL_NAME,
        )
    except Exception as exc:
        print(
            f"WARNING: Could not load transformer model ({exc}). "
            "Falling back to keyword sentiment."
        )
        return None


def normalize_transformer_label(label: str) -> str:
    label = str(label).lower().strip()
    mapping = {
        "label_0": "negative",
        "label_1": "neutral",
        "label_2": "positive",
        "negative": "negative",
        "neutral": "neutral",
        "positive": "positive",
    }
    return mapping.get(label, label)


def analyze_sentiment(text: str, sentiment_pipeline=None) -> dict[str, Any]:
    text = normalize_text(text)

    if sentiment_pipeline is None:
        return fallback_sentiment(text)

    try:
        result = sentiment_pipeline(text[:512])[0]
        return {
            "sentiment_label": normalize_transformer_label(result.get("label", "")),
            "sentiment_score": float(result.get("score", 0.0)),
            "sentiment_method": "xlm_roberta",
            "positive_keyword_hits": None,
            "negative_keyword_hits": None,
        }
    except Exception:
        return fallback_sentiment(text)


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "need", "needs", "service", "problem", "people", "community",
    "because", "about", "there", "their", "would", "could", "should",
    "في", "من", "على", "إلى", "عن", "هذا", "هذه", "هناك", "نحتاج",
    "خدمة", "مشكلة", "الناس", "المجتمع",
}


def extract_top_keywords(texts: list[str], top_n: int = 12) -> list[tuple[str, int]]:
    counter = Counter()
    for text in texts:
        for token in tokenize_words(text):
            if token not in STOPWORDS and not token.isdigit():
                counter[token] += 1
    return counter.most_common(top_n)


def create_topic_keywords(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if "service_category" not in df.columns:
        return pd.DataFrame(columns=["service_category", "keyword", "count"])
    for category, group in df.groupby("service_category"):
        texts = group["analysis_text"].dropna().astype(str).tolist()
        for keyword, count in extract_top_keywords(texts, top_n=10):
            rows.append({"service_category": category, "keyword": keyword, "count": count})
    return pd.DataFrame(rows)


def add_analysis_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "analysis_text" not in df.columns:
        df["analysis_text"] = df.apply(build_analysis_text, axis=1)

    if "importance_score" not in df.columns:
        df["importance_score"] = df.get(
            "importance_level", pd.Series([3] * len(df))
        ).apply(importance_to_score)
    else:
        df["importance_score"] = pd.to_numeric(
            df["importance_score"], errors="coerce"
        ).fillna(3)

    if "frequency_score" not in df.columns:
        df["frequency_score"] = df.get(
            "frequency_of_problem", pd.Series([3] * len(df))
        ).apply(frequency_to_score)
    else:
        df["frequency_score"] = pd.to_numeric(
            df["frequency_score"], errors="coerce"
        ).fillna(3)

    if "budget_midpoint_aed" not in df.columns:
        df["budget_midpoint_aed"] = df.get(
            "monthly_budget", pd.Series([0] * len(df))
        ).apply(convert_budget_to_midpoint)
    else:
        df["budget_midpoint_aed"] = pd.to_numeric(
            df["budget_midpoint_aed"], errors="coerce"
        ).fillna(0)

    return df


def add_sentiment_columns(df: pd.DataFrame, sentiment_pipeline=None) -> pd.DataFrame:
    df = df.copy()
    sentiment_results = [
        analyze_sentiment(text, sentiment_pipeline=sentiment_pipeline)
        for text in df["analysis_text"].fillna("").astype(str).tolist()
    ]
    sentiment_df = pd.DataFrame(sentiment_results)
    for column in sentiment_df.columns:
        df[column] = sentiment_df[column].values
    return df


def normalize_0_100(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0)
    min_value = values.min()
    max_value = values.max()
    if max_value == min_value:
        return pd.Series([50.0] * len(values), index=values.index)
    return ((values - min_value) / (max_value - min_value) * 100).round(2)


def create_group_metrics(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    existing_columns = [col for col in group_columns if col in df.columns]
    if not existing_columns:
        return pd.DataFrame()

    metrics = (
        df.groupby(existing_columns)
        .agg(
            response_count=(
                "response_id", "count"
            ) if "response_id" in df.columns else ("analysis_text", "count"),
            avg_importance=("importance_score", "mean"),
            avg_frequency=("frequency_score", "mean"),
            avg_budget_aed=("budget_midpoint_aed", "mean"),
            positive_share=("sentiment_label", lambda x: (x == "positive").mean()),
            negative_share=("sentiment_label", lambda x: (x == "negative").mean()),
            neutral_share=("sentiment_label", lambda x: (x == "neutral").mean()),
            top_problem=("main_problem", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
            top_needed_service=("needed_service", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
            top_solution_type=(
                "preferred_solution_type",
                lambda x: x.mode().iloc[0]
                if "preferred_solution_type" in df.columns and not x.mode().empty
                else "",
            ),
        )
        .reset_index()
    )

    metrics["need_score"] = (
        (metrics["avg_importance"] / 5 * 45)
        + (metrics["avg_frequency"] / 5 * 35)
        + normalize_0_100(metrics["response_count"]) * 0.20
    ).round(2)

    metrics["payment_readiness_score"] = normalize_0_100(metrics["avg_budget_aed"]).round(2)

    return metrics.sort_values("need_score", ascending=False)


def create_market_signals(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)
    if total == 0:
        return pd.DataFrame()

    if "service_category" in df.columns:
        for category, count in df["service_category"].value_counts().items():
            rows.append({
                "signal_type": "category_demand",
                "signal_name": str(category),
                "value": int(count),
                "share": round(float(count / total), 4),
                "meaning": "Share of responses mentioning this service category",
            })

    if "region" in df.columns:
        for region, count in df["region"].value_counts().items():
            rows.append({
                "signal_type": "regional_demand",
                "signal_name": str(region),
                "value": int(count),
                "share": round(float(count / total), 4),
                "meaning": "Share of responses from this region",
            })

    return pd.DataFrame(rows)


def run_nlp_agent() -> dict[str, Any]:
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(
            f"Cleaned data not found: {CLEANED_CSV}. Run agents/cleaning_agent.py first."
        )

    df = pd.read_csv(CLEANED_CSV)

    if df.empty:
        raise ValueError("Cleaned data is empty. Cannot run NLP analysis.")

    df = add_analysis_columns(df)

    # Transformer is only loaded when USE_TRANSFORMER=true.
    # Default is keyword fallback — works on Streamlit Cloud with no model download.
    sentiment_pipeline = load_transformer_pipeline()
    df = add_sentiment_columns(df, sentiment_pipeline=sentiment_pipeline)

    category_metrics = create_group_metrics(df, ["service_category"])
    region_metrics = create_group_metrics(df, ["region"])
    customer_segments = create_group_metrics(
        df, ["service_category", "region", "occupation", "age_group"]
    )
    age_group_metrics = create_group_metrics(df, ["age_group"])
    gender_metrics = create_group_metrics(df, ["gender"])
    occupation_metrics = create_group_metrics(df, ["occupation"])
    budget_metrics = create_group_metrics(df, ["monthly_budget"])

    topic_keywords = create_topic_keywords(df)
    market_signals = create_market_signals(df)

    df.to_csv(OUTPUT_NLP_INSIGHTS, index=False)
    category_metrics.to_csv(OUTPUT_CATEGORY_METRICS, index=False)
    region_metrics.to_csv(OUTPUT_REGION_METRICS, index=False)
    customer_segments.to_csv(OUTPUT_CUSTOMER_SEGMENTS, index=False)
    age_group_metrics.to_csv(OUTPUT_AGE_GROUP_METRICS, index=False)
    gender_metrics.to_csv(OUTPUT_GENDER_METRICS, index=False)
    occupation_metrics.to_csv(OUTPUT_OCCUPATION_METRICS, index=False)
    budget_metrics.to_csv(OUTPUT_BUDGET_METRICS, index=False)
    topic_keywords.to_csv(OUTPUT_TOPIC_KEYWORDS, index=False)
    market_signals.to_csv(OUTPUT_MARKET_SIGNALS, index=False)

    if sentiment_pipeline is None:
        if USE_TRANSFORMER:
            analysis_mode = "transformer_requested_but_unavailable_used_keyword_fallback"
        else:
            analysis_mode = "keyword_fallback"
        sentiment_mode = "keyword_fallback"
    else:
        analysis_mode = "full_transformer"
        sentiment_mode = "xlm_roberta"

    report = {
        "agent": "nlp_agent",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(CLEANED_CSV.relative_to(PROJECT_ROOT)),
        "outputs": {
            "nlp_insights": str(OUTPUT_NLP_INSIGHTS.relative_to(PROJECT_ROOT)),
            "category_metrics": str(OUTPUT_CATEGORY_METRICS.relative_to(PROJECT_ROOT)),
            "region_metrics": str(OUTPUT_REGION_METRICS.relative_to(PROJECT_ROOT)),
            "customer_segments": str(OUTPUT_CUSTOMER_SEGMENTS.relative_to(PROJECT_ROOT)),
            "topic_keywords": str(OUTPUT_TOPIC_KEYWORDS.relative_to(PROJECT_ROOT)),
            "market_signals": str(OUTPUT_MARKET_SIGNALS.relative_to(PROJECT_ROOT)),
        },
        "use_transformer": USE_TRANSFORMER,
        "analysis_mode": analysis_mode,
        "sentiment_mode": sentiment_mode,
        "transformer_model": TRANSFORMER_MODEL_NAME if USE_TRANSFORMER else "not_loaded",
        "rows_analyzed": int(len(df)),
        "service_categories": int(df["service_category"].nunique()) if "service_category" in df.columns else 0,
        "regions": int(df["region"].nunique()) if "region" in df.columns else 0,
        "sentiment_distribution": df["sentiment_label"].value_counts(dropna=False).to_dict()
        if "sentiment_label" in df.columns
        else {},
        "deployment_note": (
            "Keyword fallback is the default mode and works on Streamlit Cloud with no model download. "
            "Set USE_TRANSFORMER=true in .env to enable full XLM-RoBERTa multilingual analysis locally."
        ),
    }

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(f"Agent 3 complete. Mode: {analysis_mode}. Rows analyzed: {len(df)}.")
    print(f"Saved: {OUTPUT_NLP_INSIGHTS}")

    return report


def main():
    try:
        run_nlp_agent()
    except Exception as exc:
        print(f"Agent 3 failed: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
