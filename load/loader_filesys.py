import json
import logging
import os
from argparse import ArgumentParser

import pandas as pd

# Loggings
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Writing data to current local directory as a CSV file
def write_details_to_csv(df: pd.DataFrame, file_name: str) -> None:
    logger.info("Writing file to local file.")
    df.to_csv(file_name, index=False, encoding="utf-8")
    logger.info("Data '%s' written successfully.", file_name)


def run_filesys(args_parser: ArgumentParser) -> None:

    os.makedirs(args_parser.path, exist_ok=True)

    # Load product data from JSON file
    with open(args_parser.transform, encoding="utf-8") as f:
        product_data = json.load(f)

    # Create a DataFrame from the loaded data
    df = pd.DataFrame(product_data)

    # Add a new column for the marketplace name
    # df["marketplace_name"] = "amazon ae"
    # df['url'] = 'https://www.amazon.ae'
    # Rename 'link' column to 'product_detail_url'
    # df.rename({"link": "product_detail_url"}, axis=1, inplace=True)

    # Convert 'date_collected' to datetime format, coerce errors
    df["date_collected"] = pd.to_datetime(df["date_collected"], errors="coerce")
    df["currency"] = "AE Dirham"
    # Define float columns and exceptions
    float_columns = ["price", "total_reviews", "review_score"]
    except_cols = float_columns + ["date_collected"]

    # Identify columns that should be strings
    string_columns = [c for c in df.columns if c not in except_cols]

    # Convert string columns to string data type
    for c in string_columns:
        df[c] = df[c].astype(str)

    # Convert float columns to float data type
    df["total_reviews"] = df["total_reviews"].str.replace(r"\W+", "", regex=True)
    for c in float_columns:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(",", "", regex=True), errors="coerce"
        )

    # Reset index of the DataFrame
    df.drop("tags_with_errors", axis=1, inplace=True)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    fields = [
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

    sorted_cols = fields + list(set(df.columns) - set(fields))
    print(sorted_cols)
    df = df[sorted_cols]
    df = df.dropna().drop_duplicates().reset_index()
    print(
        "Overall Missing Values: \n",
        (
            df.isna()
            .sum()
            .reset_index(name="N/A Count")
            .rename(columns={"index": "Column Names"})
        ),
    )
    # Data Overview
    print(f"Total records: {len(df)}")
    print(df.head())

    write_details_to_csv(df, args_parser.name)
