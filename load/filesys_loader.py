"""
ETL Data Export Script (Transform Output → CSV & Excel)
--------------------------------------------------------

This script performs the final step of the ETL process by reading the transformed
JSON file, cleaning the data, and exporting it to both CSV and Excel formats.

Usage:
    python transform/transform.py -m <marketplace> -c <category> -s <subcategory>

Arguments:
    -m, --marketplace   Name of the marketplace (e.g., 'amazonae')
    -c, --category      Product category (wrap in quotes if it contains spaces)
    -s, --subcategory   Product subcategory (wrap in quotes if it contains spaces)

Outputs:
    - Excel (.xlsx) file saved in the marketplace/category/subcategory directory
    - CSV (.csv) file saved in the same directory
    - A log file (logs/summary.log) with details of the current run

Notes:
    - The script expects a JSON file (transform_<marketplace>_<category>_<subcategory>.json)
      to be present in the appropriate output directory.
    - Log messages are printed to both the console and a file for traceability.
"""

import json
import logging
import re
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import pandas as pd

# ───────────────────────────── Logging setup ──────────────────────────────
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "summary.log"
current_date = datetime.now().strftime("%d%m%Y_%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ──────────────────────────────  Functions  ───────────────────────────────


# Export the DataFrame to an Excel file
def write_details_to_excel(df: pd.DataFrame, file_path: Path) -> None:
    logger.info("Saving data to Excel file: %s", file_path.name)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Products")
    logger.info("Excel file saved.")


# Export the DataFrame to a CSV file
def write_details_to_csv(df: pd.DataFrame, file_path: Path) -> None:
    logger.info("Saving data to CSV file: %s", file_path.name)
    df.to_csv(file_path, index=False, encoding="utf-8")
    logger.info("CSV file saved.")


# Make a string lowercase, remove special chars, and replace spaces with underscores
def normalize_strings(text_str: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text_str).lower()
    return "_".join(cleaned.split())


# Ensure numeric fields, drop NA, and deduplicate the DataFrame
def validate_dataframe(df: pd.DataFrame, fields: list) -> pd.DataFrame:
    missing = [c for c in fields if c not in df.columns]
    if missing:
        logger.warning("Missing expected columns: %s", missing)

    for col in ("price", "review_score"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[c for c in fields if c != "review_score"])
    df = df.drop_duplicates(fields).reset_index(drop=True)
    return df


# Orchestrate loading JSON, cleaning data, and exporting to Excel/CSV
def run_loader(args: ArgumentParser) -> None:
    marketplace, category, subcategory = (
        args.marketplace,
        args.category,
        args.subcategory,
    )

    base = normalize_strings(f"{marketplace} {category} {subcategory}")
    json_file = f"transform_{base}.json"
    excel_file = f"final_{base}_{current_date}.xlsx"
    csv_file = f"final_{base}_{current_date}.csv"

    safe_cat = re.sub(r"\W+", "_", category).replace(" ", "_")
    safe_sub = re.sub(r"\W+", "_", subcategory).replace(" ", "_")
    output_dir = Path.cwd() / "output" / marketplace / safe_cat / safe_sub

    if not output_dir.is_dir():
        logger.error("Directory [%s] does not exist.", output_dir)
        exit(1)

    input_path = output_dir / json_file
    if not input_path.is_file():
        logger.error("Input file [%s] not found.", json_file)
        exit(1)

    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    priority = [
        "category",
        "subcategory",
        "marketplace",
        "brand",
        "name",
        "price",
        "currency",
        "description",
        "url",
        "image_url",
        "review_score",
        "date_collected",
    ]
    df = pd.DataFrame(data)[priority + list(set(data[0]).difference(priority))]

    logger.info(
        "Missing Value Summary:\n%s",
        (
            df.isna()
            .sum()
            .reset_index(name="Missing Count")
            .rename(columns={"index": "Column"})
            .to_string(index=False)
        ),
    )

    df = validate_dataframe(df, priority)

    logger.info("Final record count: %s", len(df))
    logger.info("Saving cleaned data...")

    write_details_to_excel(df, output_dir / excel_file)
    write_details_to_csv(df, output_dir / csv_file)

    logger.info("✔️ Export completed. Files saved to: %s", output_dir)


if __name__ == "__run_loader__":
    run_loader()
