from pathlib import Path
from datetime import datetime, timedelta
import argparse
import json
import random
import re
import shutil
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
UPLOAD_ARCHIVE_DIR = DATA_DIR / "uploaded_files"
RAW_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = RAW_DIR / "responses_raw.csv"
OUTPUT_METADATA = RAW_DIR / "collection_metadata.json"

MANDATORY_COLUMNS = ["region", "main_problem", "needed_service", "service_category", "opinion_text"]
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
    "response_id", "age_group", "gender", "region", "occupation", "source",
    "main_problem", "needed_service", "service_category", "importance_level",
    "frequency_of_problem", "preferred_solution_type", "monthly_budget",
    "opinion_text", "date_collected", "import_batch_id", "imported_at", "source_file_name",
]
COLUMN_ALIASES = {
    "area": "region", "location": "region", "community": "region", "village": "region",
    "job": "occupation", "work": "occupation", "profession": "occupation",
    "problem": "main_problem", "issue": "main_problem", "challenge": "main_problem", "pain_point": "main_problem",
    "need": "needed_service", "needed": "needed_service", "service_needed": "needed_service",
    "requested_service": "needed_service", "business_need": "needed_service",
    "category": "service_category", "service_type": "service_category", "business_category": "service_category",
    "importance": "importance_level", "priority": "importance_level", "severity": "importance_level",
    "frequency": "frequency_of_problem", "how_often": "frequency_of_problem",
    "preferred_solution": "preferred_solution_type", "solution_type": "preferred_solution_type",
    "budget": "monthly_budget", "price_range": "monthly_budget", "willing_to_pay": "monthly_budget",
    "opinion": "opinion_text", "comment": "opinion_text", "comments": "opinion_text",
    "feedback": "opinion_text", "response": "opinion_text", "text": "opinion_text",
    "date": "date_collected", "collected_date": "date_collected", "submission_date": "date_collected",
}

GENDERS = ["male", "female", "prefer not to say"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
REGIONS = ["Al Qua'a", "Al Ain outskirts", "Sweihan", "Al Wathba", "Liwa", "Ghayathi", "Al Sila", "Al Madam", "Masfout", "Hatta"]
OCCUPATIONS = [
    "camel farm owner", "camel farm worker", "date farmer", "small grocery owner",
    "home-based food seller", "teacher", "student", "driver", "tourism guide",
    "craft seller", "healthcare worker", "homemaker", "mechanic", "livestock supplier",
]
SOURCES = ["volunteer", "survey", "government information", "other"]
FREQUENCIES = ["daily", "weekly", "monthly", "occasionally"]
SOLUTIONS = ["WhatsApp bot", "mobile app", "phone call service", "SMS updates", "in-person kiosk", "web dashboard", "volunteer-assisted form"]
BUDGETS = ["0-50 AED", "51-100 AED", "101-250 AED", "251-500 AED", "501-1000 AED", "1000+ AED"]

SERVICE_SCENARIOS = {
    "Veterinary & Camel Care": [
        ("Camel farms in Al Qua'a struggle to get fast veterinary help when an animal is sick.", "same-day mobile camel vet booking", "A WhatsApp booking service for camel vets would help farm families avoid long delays."),
        ("Livestock medicine is not always easy to access without travelling to Al Ain city.", "livestock medicine delivery", "A trusted medicine delivery route from Al Ain to Al Qua'a farms would save time."),
        ("Farmers cannot easily compare camel feed suppliers or veterinary costs.", "camel feed and vet price comparison", "A simple comparison tool for feed, vet visits, and medicine could reduce farm costs."),
    ],
    "Tourism & Stargazing": [
        ("Visitors come to Al Qua'a for dark skies but local tourism services are informal.", "guided stargazing experience booking", "A guided stargazing package with local guides, telescopes, and camping support could create income."),
        ("Tourists ask where to camp safely and how to find local guides.", "stargazing visitor information hub", "A local tourism hub could show safe routes, guide contacts, camping rules, and local sellers."),
        ("Families want to sell food and handmade products to astronomy visitors.", "visitor marketplace for stargazing nights", "A marketplace for local food, dates, crafts, and camel products could serve weekend visitors."),
    ],
    "Market Access": [
        ("Small sellers rely on word of mouth and cannot reach buyers in Al Ain or Abu Dhabi.", "marketplace for camel milk, dates, and local products", "A community marketplace could help families sell camel milk, dates, crafts, and home food."),
        ("Home-based sellers receive orders manually and lose track of demand.", "WhatsApp catalog and order helper", "A WhatsApp catalog tool could help local sellers organize orders and understand demand."),
        ("Farm products are produced before sellers know what customers actually want.", "local demand forecasting for farm products", "A simple demand tracker could help farmers decide what to prepare before market days."),
    ],
    "Farm Operations": [
        ("Irrigation and water pump issues take too long to repair on remote farms.", "farm equipment maintenance coordination", "A maintenance coordination service for irrigation, pumps, and farm equipment would reduce downtime."),
        ("Solar-powered farm equipment needs maintenance but providers are far away.", "solar farm equipment repair scheduling", "A booking tool for solar and irrigation technicians could help farms schedule repairs faster."),
        ("Farmers sometimes need equipment for short periods but cannot justify buying it.", "farm equipment rental coordination", "Equipment rental coordination would help small farms access tools without large upfront costs."),
    ],
    "Rural Transport": [
        ("Transport to services in Al Ain is difficult for families and workers.", "scheduled rural shuttle", "A scheduled shuttle to Al Ain for errands, clinics, and supplies would help the community."),
        ("Delivery drivers do not consistently serve remote farms.", "rural delivery network", "A shared delivery route could bring groceries, pharmacy items, and parcels to remote farms."),
    ],
    "Mobile Healthcare": [
        ("Clinic visits require long travel, especially for elderly residents and farm workers.", "mobile health checkup visits", "Mobile checkup visits would help residents get basic care without frequent long trips."),
        ("Medicine pickup from Al Ain is inconvenient.", "medicine pickup and delivery", "A medicine pickup service from pharmacies in Al Ain would save travel time."),
    ],
    "Education & Tutoring": [
        ("Students in rural areas need tutoring but cannot always travel after school.", "hybrid tutoring for rural students", "Hybrid tutoring using online sessions plus occasional in-person visits would support students."),
        ("Some residents need help using digital government services and online forms.", "basic digital skills training", "Digital skills workshops would help residents use forms, payments, and government apps."),
    ],
    "Utilities & Maintenance": [
        ("Home maintenance providers are difficult to find quickly in remote areas.", "verified mobile maintenance directory", "A verified directory for AC repair, plumbing, electrical, and farm maintenance would help households."),
        ("Internet issues are repeated but hard to document clearly.", "connectivity issue reporting dashboard", "A simple issue tracker could show repeated connectivity problems by area."),
    ],
}

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

def to_snake_case(column_name: str) -> str:
    column_name = str(column_name).strip().lower()
    column_name = re.sub(r"[^a-z0-9]+", "_", column_name).strip("_")
    return column_name

def read_input_file(input_path: Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    ext = input_path.suffix.lower()
    if ext == ".csv":
        try:
            return pd.read_csv(input_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(input_path, encoding="latin-1")
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(input_path, sheet_name=sheet_name)
    raise ValueError("Unsupported file type. Please provide a .csv, .xlsx, or .xls file.")

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: COLUMN_ALIASES.get(to_snake_case(c), to_snake_case(c)) for c in df.columns})

def validate_mandatory_columns(df: pd.DataFrame) -> None:
    missing = [col for col in MANDATORY_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Uploaded file is missing mandatory columns: {missing}. Minimum required: {MANDATORY_COLUMNS}")

def add_missing_optional_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    missing = []
    for col, default in OPTIONAL_COLUMNS_WITH_DEFAULTS.items():
        if col not in df.columns:
            missing.append(col)
            df[col] = datetime.today().strftime("%Y-%m-%d") if col == "date_collected" else default
    return df, missing

def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    today = datetime.today().strftime("%Y-%m-%d")
    parsed = pd.to_datetime(df.get("date_collected", today), errors="coerce")
    df["date_collected"] = parsed.dt.strftime("%Y-%m-%d").fillna(today)
    return df

def normalize_importance_level(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {"low": 1, "medium": 3, "high": 5, "very high": 5}
    text = df["importance_level"].astype(str).str.strip().str.lower()
    mapped = text.map(mapping)
    numeric = pd.to_numeric(df["importance_level"], errors="coerce")
    df["importance_level"] = numeric.fillna(mapped).fillna(3)
    df.loc[~df["importance_level"].between(1, 5), "importance_level"] = 3
    return df

def generate_response_ids(df: pd.DataFrame, batch_id: str) -> pd.DataFrame:
    if "response_id" not in df.columns:
        df["response_id"] = None
    df["response_id"] = df["response_id"].astype("object")
    for idx in df.index:
        if pd.isna(df.at[idx, "response_id"]) or str(df.at[idx, "response_id"]).strip() == "":
            df.at[idx, "response_id"] = f"{batch_id}_R{idx + 1:04d}"
    return df

def select_and_order_columns(df: pd.DataFrame) -> pd.DataFrame:
    first = [col for col in FINAL_COLUMN_ORDER if col in df.columns]
    extra = [col for col in df.columns if col not in first]
    return df[first + extra]

def save_output(df: pd.DataFrame, mode: str) -> None:
    if mode == "append" and OUTPUT_CSV.exists():
        old = pd.read_csv(OUTPUT_CSV)
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

def save_metadata(df: pd.DataFrame, batch_id: str, mode: str, missing_optional_columns: list[str], is_synthetic: bool, input_path: Path | None = None, archived_file_path: Path | None = None) -> None:
    metadata = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_path) if input_path else None,
        "archived_original_file": str(archived_file_path) if archived_file_path else None,
        "output_csv": str(OUTPUT_CSV),
        "mode": mode,
        "rows_imported": len(df),
        "columns": list(df.columns),
        "mandatory_columns": MANDATORY_COLUMNS,
        "missing_optional_columns_filled": missing_optional_columns,
        "is_synthetic": is_synthetic,
    }
    OUTPUT_METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

def collect_uploaded_file(input_file: str, mode: str = "overwrite", sheet_name: str | int | None = 0) -> pd.DataFrame:
    input_path = Path(input_file)
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()
    batch_id = datetime.now().strftime("B%Y%m%d_%H%M%S")
    df = read_input_file(input_path, sheet_name=sheet_name)
    if df.empty:
        raise ValueError("The uploaded file is empty.")
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df = standardize_column_names(df)
    validate_mandatory_columns(df)
    for col in MANDATORY_COLUMNS:
        if df[col].isna().all() or df[col].astype(str).str.strip().eq("").all():
            raise ValueError(f"Mandatory column is empty: {col}")
    df, missing = add_missing_optional_columns(df)
    df = normalize_dates(df)
    df = normalize_importance_level(df)
    df = generate_response_ids(df, batch_id)
    df["import_batch_id"] = batch_id
    df["imported_at"] = datetime.now().isoformat(timespec="seconds")
    df["source_file_name"] = input_path.name
    df = select_and_order_columns(df)
    archived = UPLOAD_ARCHIVE_DIR / f"{batch_id}_{input_path.name}"
    shutil.copy2(input_path, archived)
    save_output(df, mode)
    save_metadata(df, batch_id, mode, missing, False, input_path, archived)
    print(f"Collection completed. Rows imported: {len(df)}. Saved to {OUTPUT_CSV}")
    return df

def generate_demo_response(n: int) -> dict:
    categories = list(SERVICE_SCENARIOS.keys())
    category = weighted_choice(categories, [1.55, 1.45, 1.35, 1.25, 0.95, 0.9, 0.85, 0.8])
    problem, service, opinion = random.choice(SERVICE_SCENARIOS[category])
    region = weighted_choice(REGIONS, [4.0, 1.5, 1.0, 0.8, 0.7, 0.6, 0.5, 0.5, 0.4, 0.4])
    if category in ["Veterinary & Camel Care", "Farm Operations", "Market Access"]:
        occupation = weighted_choice(OCCUPATIONS, [2.4, 2.0, 1.5, 0.8, 0.8, 0.4, 0.4, 0.6, 0.6, 0.5, 0.4, 0.6, 1.0, 1.4])
    elif category == "Tourism & Stargazing":
        occupation = weighted_choice(OCCUPATIONS, [0.8, 0.6, 0.5, 0.9, 1.2, 0.8, 0.8, 0.7, 2.0, 1.6, 0.5, 0.8, 0.4, 0.4])
    else:
        occupation = random.choice(OCCUPATIONS)
    return {
        "response_id": f"DEMO_R{n:04d}",
        "age_group": random.choice(AGE_GROUPS),
        "gender": random.choice(GENDERS),
        "region": region,
        "occupation": occupation,
        "source": weighted_choice(SOURCES, [1.4, 1.3, 0.8, 0.5]),
        "main_problem": problem,
        "needed_service": service,
        "service_category": category,
        "importance_level": weighted_choice([1, 2, 3, 4, 5], [0.2, 0.4, 0.9, 1.6, 2.0]),
        "frequency_of_problem": weighted_choice(FREQUENCIES, [1.2, 1.5, 1.0, 0.5]),
        "preferred_solution_type": weighted_choice(SOLUTIONS, [1.7, 1.0, 1.2, 0.8, 0.9, 0.8, 1.0]),
        "monthly_budget": weighted_choice(BUDGETS, [1.0, 1.2, 1.6, 1.2, 0.7, 0.4]),
        "opinion_text": opinion,
        "date_collected": (datetime.today() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"),
        "import_batch_id": "DEMO",
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "source_file_name": "synthetic_al_quaa_demo",
    }

def create_demo_dataset(rows: int = 300, mode: str = "overwrite") -> pd.DataFrame:
    random.seed(42)
    df = pd.DataFrame([generate_demo_response(i) for i in range(1, rows + 1)])
    df = select_and_order_columns(df)
    save_output(df, mode)
    save_metadata(df, "DEMO", mode, [], True)
    print(f"Demo data generated. Rows: {len(df)}. Saved to {OUTPUT_CSV}")
    return df

def main():
    parser = argparse.ArgumentParser(description="Agent 1: collect uploaded CSV/Excel or generate Al Qua'a demo data.")
    parser.add_argument("--input", required=False, help="Path to CSV or Excel file.")
    parser.add_argument("--demo", action="store_true", help="Generate synthetic Al Qua'a demo data.")
    parser.add_argument("--rows", type=int, default=300)
    parser.add_argument("--mode", choices=["overwrite", "append"], default="overwrite")
    parser.add_argument("--sheet", default=0)
    args = parser.parse_args()
    try:
        if args.input and not args.demo:
            df = collect_uploaded_file(args.input, mode=args.mode, sheet_name=args.sheet)
        else:
            df = create_demo_dataset(rows=args.rows, mode=args.mode)
        print(df.head())
    except Exception as error:
        print("Collection failed.")
        print(f"Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
