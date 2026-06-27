"""
Agent 2 — Cleaning Agent
Fixes schema mismatch by using the reduced columns only.
No current_solution, satisfaction_level, would_pay, urgency_level, or pain_score.
"""
from pathlib import Path
import json
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "responses_raw.csv"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
CATEGORY_DIR = CLEANED_DIR / "categories"
CLEANED_CSV = CLEANED_DIR / "responses_cleaned.csv"
REPORT_JSON = CLEANED_DIR / "cleaning_report.json"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
CATEGORY_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_COLUMNS = [
    "response_id", "age_group", "gender", "region", "occupation", "source",
    "main_problem", "needed_service", "service_category", "importance_level",
    "frequency_of_problem", "preferred_solution_type", "monthly_budget",
    "opinion_text", "date_collected",
]
OPTIONAL_METADATA_COLUMNS = ["import_batch_id", "imported_at", "source_file_name"]

CATEGORY_MAP = {
    "camel": "Veterinary & Camel Care", "vet": "Veterinary & Camel Care", "veterinary": "Veterinary & Camel Care",
    "livestock": "Veterinary & Camel Care", "medicine": "Veterinary & Camel Care", "feed": "Veterinary & Camel Care",
    "farm equipment": "Farm Operations", "irrigation": "Farm Operations", "solar": "Farm Operations", "pump": "Farm Operations",
    "water tank": "Farm Operations", "farm maintenance": "Farm Operations", "equipment rental": "Farm Operations",
    "stargazing": "Tourism & Stargazing", "telescope": "Tourism & Stargazing", "astronomy": "Tourism & Stargazing",
    "camping": "Tourism & Stargazing", "tourism": "Tourism & Stargazing", "tourist": "Tourism & Stargazing",
    "dates": "Market Access", "date farmer": "Market Access", "camel milk": "Market Access", "camel products": "Market Access",
    "sell": "Market Access", "marketplace": "Market Access", "market access": "Market Access", "catalog": "Market Access",
    "delivery": "Rural Transport", "grocery": "Rural Transport", "pharmacy": "Rural Transport", "transport": "Rural Transport",
    "taxi": "Rural Transport", "shuttle": "Rural Transport", "bus": "Rural Transport",
    "health": "Mobile Healthcare", "clinic": "Mobile Healthcare", "doctor": "Mobile Healthcare", "checkup": "Mobile Healthcare",
    "education": "Education & Tutoring", "tutoring": "Education & Tutoring", "school": "Education & Tutoring",
    "student": "Education & Tutoring", "digital skills": "Education & Tutoring",
    "repair": "Utilities & Maintenance", "maintenance": "Utilities & Maintenance", "technician": "Utilities & Maintenance",
    "appliance": "Utilities & Maintenance", "ac repair": "Utilities & Maintenance", "internet": "Utilities & Maintenance", "utility": "Utilities & Maintenance",
}
FREQUENCY_SCORE = {"unknown": 1, "rarely": 1, "occasionally": 1, "monthly": 2, "weekly": 3, "daily": 4}
BUDGET_MIDPOINT = {
    "unknown": 0, "0 aed": 0, "0-50 aed": 25, "10-30 aed": 20, "31-50 aed": 40,
    "51-100 aed": 75, "101-250 aed": 175, "251-500 aed": 375,
    "501-1000 aed": 750, "100+ aed": 120, "1000+ aed": 1200,
}

def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())

def normalize_key(value):
    return clean_text(value).lower()

def standardize_category(value):
    value_clean = clean_text(value)
    if not value_clean:
        return "Other"
    lower_value = value_clean.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in lower_value:
            return category
    known = {
        "veterinary & camel care", "farm operations", "rural transport", "mobile healthcare",
        "education & tutoring", "tourism & stargazing", "market access", "utilities & maintenance",
    }
    if lower_value in known:
        return value_clean.title()
    return value_clean.title()

def safe_filename(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")

def parse_importance(value):
    key = normalize_key(value)
    mapping = {"low": 1, "medium": 3, "high": 5, "very high": 5}
    if key in mapping:
        return mapping[key]
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return 3
    return max(1, min(5, float(number)))

def clean_data(df):
    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Cleaning Agent cannot run. Missing columns: {missing}. Run collector_agent.py first.")
    keep = EXPECTED_COLUMNS + [col for col in OPTIONAL_METADATA_COLUMNS if col in df.columns]
    df = df[keep].copy()
    for col in df.columns:
        df[col] = df[col].apply(clean_text)
    df["gender"] = df["gender"].str.lower().replace({"m": "male", "f": "female", "prefer not say": "prefer not to say"})
    df["occupation"] = df["occupation"].str.lower()
    df["source"] = df["source"].str.lower()
    df["frequency_of_problem"] = df["frequency_of_problem"].str.lower()
    df["service_category"] = df["service_category"].apply(standardize_category)
    df["date_collected"] = pd.to_datetime(df["date_collected"], errors="coerce")
    before_dates = len(df)
    df = df.dropna(subset=["date_collected"])
    invalid_dates_removed = before_dates - len(df)
    before_dupes = len(df)
    df = df.drop_duplicates(subset=["response_id"])
    duplicates_removed = before_dupes - len(df)
    before_empty = len(df)
    df = df[(df["opinion_text"].str.len() > 0) | (df["main_problem"].str.len() > 0) | (df["needed_service"].str.len() > 0)]
    empty_text_rows_removed = before_empty - len(df)
    df["importance_score"] = df["importance_level"].apply(parse_importance)
    df["frequency_key"] = df["frequency_of_problem"].apply(normalize_key)
    df["budget_key"] = df["monthly_budget"].apply(normalize_key)
    df["frequency_score"] = df["frequency_key"].map(FREQUENCY_SCORE).fillna(1)
    df["budget_midpoint_aed"] = df["budget_key"].map(BUDGET_MIDPOINT).fillna(0)
    df["analysis_text"] = (
        df["main_problem"].fillna("").astype(str) + ". " +
        df["needed_service"].fillna("").astype(str) + ". " +
        df["opinion_text"].fillna("").astype(str)
    )
    df["date_collected"] = df["date_collected"].dt.strftime("%Y-%m-%d")
    return df, {
        "invalid_dates_removed": int(invalid_dates_removed),
        "duplicates_removed": int(duplicates_removed),
        "empty_text_rows_removed": int(empty_text_rows_removed),
    }

def save_category_files(df):
    created = []
    for category, group in df.groupby("service_category"):
        path = CATEGORY_DIR / f"{safe_filename(category)}.csv"
        group.to_csv(path, index=False, encoding="utf-8")
        created.append(str(path))
    return created

def main():
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"Cannot find {RAW_CSV}. Run collector_agent.py first.")
    raw_df = pd.read_csv(RAW_CSV)
    cleaned_df, stats = clean_data(raw_df)
    cleaned_df.to_csv(CLEANED_CSV, index=False, encoding="utf-8")
    category_files = save_category_files(cleaned_df)
    report = {
        "agent": "Agent 2 - Cleaning Agent",
        "input_file": str(RAW_CSV),
        "output_file": str(CLEANED_CSV),
        "rows_before_cleaning": int(len(raw_df)),
        "rows_after_cleaning": int(len(cleaned_df)),
        **stats,
        "category_files_created": category_files,
        "categories": sorted(cleaned_df["service_category"].unique().tolist()),
        "columns": cleaned_df.columns.tolist(),
        "schema_note": "Reduced schema: no current_solution, satisfaction_level, would_pay, urgency_level, or pain_score.",
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Agent 2 completed successfully.")
    print(f"Saved cleaned data to: {CLEANED_CSV}")
    print(f"Created {len(category_files)} category files in: {CATEGORY_DIR}")
    print(cleaned_df.head())

if __name__ == "__main__":
    main()
