import json
import re
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

# --- Helper Functions ---


def get_doc_filenames(file_extension: str) -> List[Path]:
    return sorted(Path("data").rglob(f"*.{file_extension}"), reverse=True)


def extract_file_subname(file_path: Path) -> str:
    path_without_digits = re.split(r"\d+", file_path.as_posix())[0]
    base_name = path_without_digits.split("/")[-1]
    sub_parts = base_name.split("_")[1:-1]
    return "_".join(sub_parts)


# --- Main Function ---


def get_entries_with_missing_field(
    doc_index: int = 0, field_name: str = "brand"
) -> List[Dict]:
    all_csv_paths = sorted(Path("data").rglob("*.csv"), reverse=True)
    file_categories = [re.split(r"\d+", path.name)[0] for path in all_csv_paths]

    seen = set()
    unique_csv_paths = [
        path
        for path, category in zip(all_csv_paths, file_categories)
        if category not in seen and not seen.add(category)
    ]

    total_files = len(unique_csv_paths)
    if doc_index < 0 or doc_index >= total_files:
        raise ValueError(
            f"Invalid index: {doc_index}. Must be in range 0 to {total_files - 1}."
        )

    selected_csv_path = unique_csv_paths[doc_index]
    df = pd.read_csv(selected_csv_path)
    category = df["category"].unique()[0]
    sub_category = df["subcategory"].unique()[0]
    missing_counts = df.isna().sum()
    print(missing_counts[missing_counts > 0])

    # Find matching JSON file
    csv_subname = extract_file_subname(selected_csv_path)
    matching_json = next(
        (
            path
            for path in get_doc_filenames("json")
            if csv_subname in path.as_posix() and "main" in path.as_posix()
        ),
        None,
    )

    if matching_json is None:
        print(f"No matching JSON file found for: {csv_subname}")
        sys.exit(1)

    with open(matching_json, mode="r", encoding="utf-8") as f:
        product_data = json.load(f)

    missing_urls = set(df[df[field_name].isna()]["product_detail_url"].values)

    filtered_products = [
        product for product in product_data if product["link"] in missing_urls
    ]

    print(f"Filtered products with missing '{field_name}': {len(filtered_products)}")
    return csv_subname, category, sub_category, filtered_products
