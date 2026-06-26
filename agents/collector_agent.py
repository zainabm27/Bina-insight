from pathlib import Path
from datetime import datetime
import argparse
import json
import shutil
import sys
import re
import pandas as pd


DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
UPLOAD_ARCHIVE_DIR = DATA_DIR / "uploaded_files"

RAW_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = RAW_DIR / "responses_raw.csv"
OUTPUT_METADATA = RAW_DIR / "collection_metadata.json"


MANDATORY_COLUMNS = [
    "region",
    "main_problem",
    "needed_service",
    "service_category",
    "opinion_text",
]

OPTIONAL_COLUMNS_WITH_DEFAULTS = {
    "response_id": None,
    "age_group": "unknown",
    "gender": "unknown",
    "occupation": "unknown",
    "source": "uploaded_file",
    "importance_level": None,
    "frequency_of_problem": "unknown",
    "preferred_solution_type": "unknown",
    "monthly_budget": "unknown",
    "date_collected": None,
}

FINAL_COLUMN_ORDER = [
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
    "frequency_of_problem",
    "preferred_solution_type",
    "monthly_budget",
    "opinion_text",
    "date_collected",
    "import_batch_id",
    "imported_at",
    "source_file_name",
]

COLUMN_ALIASES = {
    "area": "region",
    "location": "region",
    "community": "region",
    "village": "region",

    "job": "occupation",
    "work": "occupation",
    "profession": "occupation",

    "problem": "main_problem",
    "issue": "main_problem",
    "challenge": "main_problem",
    "pain_point": "main_problem",

    "need": "needed_service",
    "needed": "needed_service",
    "service_needed": "needed_service",
    "requested_service": "needed_service",
    "business_need": "needed_service",

    "category": "service_category",
    "service_type": "service_category",
    "business_category": "service_category",

    "importance": "importance_level",
    "priority": "importance_level",
    "severity": "importance_level",

    "frequency": "frequency_of_problem",
    "how_often": "frequency_of_problem",

    "preferred_solution": "preferred_solution_type",
    "solution_type": "preferred_solution_type",

    "budget": "monthly_budget",
    "price_range": "monthly_budget",
    "willing_to_pay": "monthly_budget",

    "opinion": "opinion_text",
    "comment": "opinion_text",
    "comments": "opinion_text",
    "feedback": "opinion_text",
    "response": "opinion_text",
    "text": "opinion_text",

    "date": "date_collected",
    "collected_date": "date_collected",
    "submission_date": "date_collected",
}


def to_snake_case(column_name: str) -> str:
    """
    Converts column names like:
    'Main Problem' -> 'main_problem'
    'Date Collected' -> 'date_collected'
    """
    column_name = str(column_name).strip().lower()
    column_name = re.sub(r"[^a-z0-9]+", "_", column_name)
    column_name = column_name.strip("_")
    return column_name


def read_input_file(input_path: Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    """
    Reads either a CSV or Excel file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    file_extension = input_path.suffix.lower()

    if file_extension == ".csv":
        try:
            return pd.read_csv(input_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(input_path, encoding="latin-1")

    if file_extension in [".xlsx", ".xls"]:
        return pd.read_excel(input_path, sheet_name=sheet_name)

    raise ValueError("Unsupported file type. Please provide a .csv, .xlsx, or .xls file.")


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts column names to snake_case and applies aliases.
    """
    renamed_columns = {}

    for original_column in df.columns:
        snake_column = to_snake_case(original_column)
        final_column = COLUMN_ALIASES.get(snake_column, snake_column)
        renamed_columns[original_column] = final_column

    df = df.rename(columns=renamed_columns)
    return df


def remove_empty_rows_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows and columns that are completely empty.
    This is common when people export Excel files.
    """
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    return df


def validate_mandatory_columns(df: pd.DataFrame) -> None:
    """
    Checks that the required columns exist.
    """
    missing_columns = [col for col in MANDATORY_COLUMNS if col not in df.columns]

    if missing_columns:
        raise ValueError(
            "The uploaded file is missing mandatory columns: "
            f"{missing_columns}\n\n"
            "Minimum required columns are:\n"
            f"{MANDATORY_COLUMNS}"
        )


def validate_mandatory_values(df: pd.DataFrame) -> None:
    """
    Checks that mandatory columns are not completely empty.
    """
    empty_mandatory_columns = []

    for col in MANDATORY_COLUMNS:
        if df[col].isna().all() or df[col].astype(str).str.strip().eq("").all():
            empty_mandatory_columns.append(col)

    if empty_mandatory_columns:
        raise ValueError(
            "These mandatory columns exist but are completely empty: "
            f"{empty_mandatory_columns}"
        )


def add_missing_optional_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Adds optional columns if they are missing.
    """
    missing_optional_columns = []

    for col, default_value in OPTIONAL_COLUMNS_WITH_DEFAULTS.items():
        if col not in df.columns:
            missing_optional_columns.append(col)

            if col == "date_collected":
                df[col] = datetime.today().strftime("%Y-%m-%d")
            else:
                df[col] = default_value

    return df, missing_optional_columns


def generate_response_ids(df: pd.DataFrame, batch_id: str) -> pd.DataFrame:
    """
    Creates response IDs if they are missing or empty.
    """
    if "response_id" not in df.columns:
        df["response_id"] = None

    df["response_id"] = df["response_id"].astype("object")

    for index in df.index:
        value = df.at[index, "response_id"]

        if pd.isna(value) or str(value).strip() == "":
            df.at[index, "response_id"] = f"{batch_id}_R{index + 1:04d}"

    return df


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts date_collected into YYYY-MM-DD format where possible.
    If a date is missing or invalid, today's date is used.
    """
    today = datetime.today().strftime("%Y-%m-%d")

    if "date_collected" not in df.columns:
        df["date_collected"] = today
        return df

    parsed_dates = pd.to_datetime(df["date_collected"], errors="coerce")
    df["date_collected"] = parsed_dates.dt.strftime("%Y-%m-%d")
    df["date_collected"] = df["date_collected"].fillna(today)

    return df


def normalize_importance_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts importance_level to a number when possible.
    Keeps missing values as None.
    """
    if "importance_level" not in df.columns:
        df["importance_level"] = None
        return df

    df["importance_level"] = pd.to_numeric(df["importance_level"], errors="coerce")

    # Keep only values from 1 to 5.
    # Invalid values become empty.
    df.loc[~df["importance_level"].between(1, 5), "importance_level"] = None

    return df


def add_import_metadata(df: pd.DataFrame, input_path: Path, batch_id: str) -> pd.DataFrame:
    """
    Adds metadata columns to every row so we know where the data came from.
    """
    imported_at = datetime.now().isoformat(timespec="seconds")

    df["import_batch_id"] = batch_id
    df["imported_at"] = imported_at
    df["source_file_name"] = input_path.name

    return df


def select_and_order_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keeps expected columns first, then preserves any extra columns at the end.
    """
    existing_final_columns = [col for col in FINAL_COLUMN_ORDER if col in df.columns]
    extra_columns = [col for col in df.columns if col not in existing_final_columns]

    return df[existing_final_columns + extra_columns]


def archive_original_file(input_path: Path, batch_id: str) -> Path:
    """
    Saves a copy of the original uploaded file.
    This is useful because raw data should be traceable.
    """
    archived_file_path = UPLOAD_ARCHIVE_DIR / f"{batch_id}_{input_path.name}"
    shutil.copy2(input_path, archived_file_path)
    return archived_file_path


def save_output(df: pd.DataFrame, mode: str) -> None:
    """
    Saves the collected data to data/raw/responses_raw.csv.

    mode='overwrite':
        Replaces the old raw CSV.

    mode='append':
        Adds new rows to the old raw CSV.
    """
    if mode == "append" and OUTPUT_CSV.exists():
        old_df = pd.read_csv(OUTPUT_CSV)
        combined_df = pd.concat([old_df, df], ignore_index=True)
        combined_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    else:
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")


def save_metadata(
    df: pd.DataFrame,
    input_path: Path,
    archived_file_path: Path,
    batch_id: str,
    mode: str,
    missing_optional_columns: list[str],
) -> None:
    """
    Saves metadata about the collection process.
    """
    metadata = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_path),
        "archived_original_file": str(archived_file_path),
        "output_csv": str(OUTPUT_CSV),
        "mode": mode,
        "rows_imported": len(df),
        "columns": list(df.columns),
        "mandatory_columns": MANDATORY_COLUMNS,
        "missing_optional_columns_filled": missing_optional_columns,
        "is_synthetic": False,
        "data_type": "entrepreneur_uploaded_csv_or_excel",
        "note": "Raw uploaded data collected from CSV/Excel. Minimal standardization was applied, but deeper cleaning should happen in cleaning_agent.py."
    }

    OUTPUT_METADATA.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def collect_uploaded_file(
    input_file: str,
    mode: str = "overwrite",
    sheet_name: str | int | None = 0,
) -> pd.DataFrame:
    """
    Main function that reads, validates, standardizes, and saves uploaded data.
    """
    input_path = Path(input_file)
    batch_id = datetime.now().strftime("B%Y%m%d_%H%M%S")

    print(f"Reading file: {input_path}")

    df = read_input_file(input_path=input_path, sheet_name=sheet_name)

    if df.empty:
        raise ValueError("The uploaded file is empty.")

    df = remove_empty_rows_and_columns(df)
    df = standardize_column_names(df)

    validate_mandatory_columns(df)
    validate_mandatory_values(df)

    df, missing_optional_columns = add_missing_optional_columns(df)

    df = normalize_dates(df)
    df = normalize_importance_level(df)
    df = generate_response_ids(df, batch_id=batch_id)
    df = add_import_metadata(df, input_path=input_path, batch_id=batch_id)
    df = select_and_order_columns(df)

    archived_file_path = archive_original_file(input_path, batch_id=batch_id)

    save_output(df, mode=mode)

    save_metadata(
        df=df,
        input_path=input_path,
        archived_file_path=archived_file_path,
        batch_id=batch_id,
        mode=mode,
        missing_optional_columns=missing_optional_columns,
    )

    print("\nCollection completed successfully.")
    print(f"Rows imported: {len(df)}")
    print(f"Saved raw CSV to: {OUTPUT_CSV}")
    print(f"Saved metadata to: {OUTPUT_METADATA}")
    print(f"Archived original file to: {archived_file_path}")

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Collector Agent: collect entrepreneur-uploaded CSV/Excel opinion data."
    )

    parser.add_argument(
        "--input",
        required=False,
        help="Path to the CSV or Excel file to collect."
    )

    parser.add_argument(
        "--mode",
        choices=["overwrite", "append"],
        default="overwrite",
        help="Use 'overwrite' to replace old raw data or 'append' to add to it."
    )

    parser.add_argument(
        "--sheet",
        default=0,
        help="Excel sheet name or index. Default is first sheet."
    )

    args = parser.parse_args()

    input_file = args.input

    if not input_file:
        input_file = input("Enter path to CSV or Excel file: ").strip()

    try:
        df = collect_uploaded_file(
            input_file=input_file,
            mode=args.mode,
            sheet_name=args.sheet,
        )

        print("\nPreview:")
        print(df.head())

    except Exception as error:
        print("\nCollection failed.")
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()