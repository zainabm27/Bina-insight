"""
Cleaning Agent
--------------
Role:
1. Read raw collected community opinion data.
2. Standardize categories, text, dates, and scoring fields.
3. Remove duplicates.
4. Add useful numeric features for later analysis.
5. Save one clean CSV and category-specific CSV files.

This agent is intentionally simple and explainable for hackathon judging.
"""

from pathlib import Path
import json
import re
import pandas as pd


# ============================================================
# 1. Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_CSV = PROJECT_ROOT / "data" / "raw" / "responses_raw.csv"

CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
CATEGORY_DIR = CLEANED_DIR / "categories"

CLEANED_CSV = CLEANED_DIR / "responses_cleaned.csv"
REPORT_JSON = CLEANED_DIR / "cleaning_report.json"

CLEANED_DIR.mkdir(parents=True, exist_ok=True)
CATEGORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. Expected columns
# ============================================================

EXPECTED_COLUMNS = [
    "response_id",
    "age_group",
    "gender",
    "region",
    "occupation",
    "source",
    "main_problem",
    "needed_service",
    "service_category",
    "importance_level",
    "current_solution",
    "satisfaction_level",
    "would_pay",
    "monthly_budget",
    "urgency_level",
    "frequency_of_problem",
    "preferred_solution_type",
    "opinion_text",
    "date_collected",
]


# ============================================================
# 3. Standardization maps
# ============================================================

CATEGORY_MAP = {
    "delivery": "Delivery",
    "grocery": "Delivery",
    "pharmacy": "Delivery",

    "education": "Education",
    "tutoring": "Education",
    "school": "Education",
    "student": "Education",

    "transport": "Transport",
    "taxi": "Transport",
    "shuttle": "Transport",
    "bus": "Transport",

    "agriculture": "Agriculture",
    "farm": "Agriculture",
    "farmer": "Agriculture",
    "produce": "Agriculture",

    "repair": "Repair",
    "maintenance": "Repair",
    "technician": "Repair",
    "appliance": "Repair",
    "ac repair": "Repair",

    "tourism": "Tourism",
    "tourist": "Tourism",
    "farm visit": "Tourism",
    "local experience": "Tourism",
}

IMPORTANCE_SCORE = {
    "low": 1,
    "medium": 3,
    "high": 5,
}

SATISFACTION_SCORE = {
    "very dissatisfied": 1,
    "dissatisfied": 2,
    "neutral": 3,
    "satisfied": 4,
    "very satisfied": 5,
}

WOULD_PAY_SCORE = {
    "no": 0,
    "maybe": 0.5,
    "yes": 1,
}

URGENCY_SCORE = {
    "not urgent": 1,
    "soon": 3,
    "very urgent": 5,
}

FREQUENCY_SCORE = {
    "rarely": 1,
    "monthly": 2,
    "weekly": 3,
    "daily": 4,
}

BUDGET_MIDPOINT = {
    "0 aed": 0,
    "10-30 aed": 20,
    "31-50 aed": 40,
    "51-100 aed": 75,
    "100+ aed": 120,
}


# ============================================================
# 4. Helper functions
# ============================================================

def clean_text(value):
    """
    Clean text by removing extra spaces and converting missing values to empty strings.
    """
    if pd.isna(value):
        return ""

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_key(value):
    """
    Normalize text for dictionary lookup.
    Example:
        "High" -> "high"
        "  Very urgent " -> "very urgent"
    """
    return clean_text(value).lower()


def standardize_category(value):
    """
    Convert messy category names into clean standard category names.
    """
    value_clean = clean_text(value)

    if not value_clean:
        return "Other"

    lower_value = value_clean.lower()

    for keyword, category in CATEGORY_MAP.items():
        if keyword in lower_value:
            return category

    return value_clean.title()


def safe_filename(value):
    """
    Convert category names into safe filenames.
    Example:
        "Local Delivery" -> "local_delivery.csv"
    """
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)

    return value.strip("_")


def clean_data(df):
    """
    Main cleaning function.
    """

    # Check missing columns
    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Keep only expected columns, in the correct order
    df = df[EXPECTED_COLUMNS].copy()

    # Clean all text columns
    for col in EXPECTED_COLUMNS:
        df[col] = df[col].apply(clean_text)

    # Standardize simple text fields
    df["gender"] = df["gender"].str.title()
    df["region"] = df["region"].str.title()
    df["occupation"] = df["occupation"].str.title()
    df["source"] = df["source"].str.lower()
    df["main_problem"] = df["main_problem"].str.strip()
    df["needed_service"] = df["needed_service"].str.strip()
    df["preferred_solution_type"] = df["preferred_solution_type"].str.strip()

    # Standardize service category
    df["service_category"] = df["service_category"].apply(standardize_category)

    # Convert date
    df["date_collected"] = pd.to_datetime(df["date_collected"], errors="coerce")

    # Drop rows with invalid dates
    before_date_drop = len(df)
    df = df.dropna(subset=["date_collected"])
    invalid_dates_removed = before_date_drop - len(df)

    # Remove duplicate response IDs
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["response_id"])
    duplicates_removed = before_dedup - len(df)

    # Remove empty opinions
    before_empty_drop = len(df)
    df = df[df["opinion_text"].str.len() > 0]
    empty_opinions_removed = before_empty_drop - len(df)

    # Create normalized helper columns
    df["importance_key"] = df["importance_level"].apply(normalize_key)
    df["satisfaction_key"] = df["satisfaction_level"].apply(normalize_key)
    df["would_pay_key"] = df["would_pay"].apply(normalize_key)
    df["urgency_key"] = df["urgency_level"].apply(normalize_key)
    df["frequency_key"] = df["frequency_of_problem"].apply(normalize_key)
    df["budget_key"] = df["monthly_budget"].apply(normalize_key)

    # Numeric scores for later analysis
    df["importance_score"] = df["importance_key"].map(IMPORTANCE_SCORE).fillna(3)
    df["satisfaction_score"] = df["satisfaction_key"].map(SATISFACTION_SCORE).fillna(3)
    df["would_pay_score"] = df["would_pay_key"].map(WOULD_PAY_SCORE).fillna(0)
    df["urgency_score"] = df["urgency_key"].map(URGENCY_SCORE).fillna(1)
    df["frequency_score"] = df["frequency_key"].map(FREQUENCY_SCORE).fillna(1)
    df["budget_midpoint_aed"] = df["budget_key"].map(BUDGET_MIDPOINT).fillna(0)

    # Pain score:
    # Low satisfaction means higher pain.
    # Example:
    # satisfaction 1 -> pain 5
    # satisfaction 5 -> pain 1
    df["pain_score"] = 6 - df["satisfaction_score"]

    # Combined text for NLP analysis
    df["analysis_text"] = (
        df["main_problem"] + ". " +
        df["needed_service"] + ". " +
        df["current_solution"] + ". " +
        df["opinion_text"]
    )

    # Make date cleaner when saved
    df["date_collected"] = df["date_collected"].dt.strftime("%Y-%m-%d")

    report_stats = {
        "invalid_dates_removed": int(invalid_dates_removed),
        "duplicates_removed": int(duplicates_removed),
        "empty_opinions_removed": int(empty_opinions_removed),
    }

    return df, report_stats


def save_category_files(df):
    """
    Save one CSV file per service category.
    """
    created_files = []

    for category, group in df.groupby("service_category"):
        filename = CATEGORY_DIR / f"{safe_filename(category)}.csv"
        group.to_csv(filename, index=False, encoding="utf-8")
        created_files.append(str(filename))

    return created_files


# ============================================================
# 5. Main function
# ============================================================

def main():
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"Cannot find {RAW_CSV}. Run the data collection notebook first."
        )

    raw_df = pd.read_csv(RAW_CSV)

    cleaned_df, report_stats = clean_data(raw_df)

    cleaned_df.to_csv(CLEANED_CSV, index=False, encoding="utf-8")

    category_files = save_category_files(cleaned_df)

    report = {
        "input_file": str(RAW_CSV),
        "output_file": str(CLEANED_CSV),
        "rows_before_cleaning": int(len(raw_df)),
        "rows_after_cleaning": int(len(cleaned_df)),
        "invalid_dates_removed": report_stats["invalid_dates_removed"],
        "duplicates_removed": report_stats["duplicates_removed"],
        "empty_opinions_removed": report_stats["empty_opinions_removed"],
        "category_files_created": category_files,
        "categories": sorted(cleaned_df["service_category"].unique().tolist()),
        "columns": cleaned_df.columns.tolist(),
    }

    REPORT_JSON.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print(f"Saved cleaned data to: {CLEANED_CSV}")
    print(f"Saved cleaning report to: {REPORT_JSON}")
    print(f"Created {len(category_files)} category files in: {CATEGORY_DIR}")
    print()
    print("Preview:")
    print(cleaned_df.head())


if __name__ == "__main__":
    main()