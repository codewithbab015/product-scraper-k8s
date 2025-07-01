import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple, Union

import pandas as pd
import psycopg2


# Dataclass Definitio
@dataclass
class DataFields:
    name: str
    price: float
    currency: str
    image_url: str
    product_detail_url: str
    page_url: str
    marketplace_name: str
    date_collected: datetime
    category: str
    subcategory: str
    amazon_category: str
    review_score: float
    total_reviews: float
    brand: str
    about: str
    description: str


@dataclass
class DataLoader(DataFields):

    @staticmethod
    def _parse_date(val) -> datetime:
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def from_series(row: pd.Series) -> "DataLoader":
        kwargs = {
            f.name: row.get(f.name, "" if f.type == str else 0.0)
            for f in fields(DataLoader)
        }
        kwargs["date_collected"] = DataLoader._parse_date(row.get("date_collected"))
        return DataLoader(**kwargs)

    @classmethod
    def get_field_names(cls) -> List[str]:
        return [f.name for f in fields(cls)]

    @classmethod
    def to_tuple(cls, instance: Any) -> Tuple:
        if not is_dataclass(instance):
            raise ValueError("Expected a dataclass instance")
        return tuple(getattr(instance, f.name) for f in fields(cls))

    @classmethod
    def get_sql_schema(cls) -> str:
        type_map = {
            str: "TEXT",
            float: "NUMERIC(10, 2)",
            int: "INTEGER",
            datetime: "TIMESTAMP",
        }
        lines = ["id SERIAL PRIMARY KEY"]
        for f in fields(cls):
            sql_type = type_map.get(f.type, "TEXT")
            constraints = []
            if f.name in {"name", "price"}:
                constraints.append("NOT NULL")
            if f.name == "product_detail_url":
                constraints.append("UNIQUE")
            lines.append(f"{f.name} {sql_type} {' '.join(constraints)}".strip())
        return ",\n    ".join(lines)

    @classmethod
    def create_table_and_insert(
        cls, table_name: str, conn, cur, data: Union["DataLoader", List["DataLoader"]]
    ):
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {cls.get_sql_schema()}\n);"
        )

        if isinstance(data, cls):
            data = [cls.to_tuple(data)]
        elif isinstance(data, list):
            data = [cls.to_tuple(d) if isinstance(d, cls) else d for d in data]
        else:
            raise ValueError("Unsupported data format.")

        columns = ", ".join(cls.get_field_names())
        placeholders = ", ".join(["%s"] * len(cls.get_field_names()))
        insert_query = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT (product_detail_url) DO NOTHING;
        """
        cur.executemany(insert_query, data)
        conn.commit()
        print(f"Inserted {len(data)} record(s) into '{table_name}' table.")


def run_loader_db(args_parser: ArgumentParser) -> None:
    # Load runtime args/parameters
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = os.getenv("DB_PORT")

    connector = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    # Load CSV & Insert Data
    # Extract and sort timestamps from CSV filenames
    path = Path(args_parser.path)
    timestamps = sorted(
        [
            "_".join(re.findall(r"\d+", f.name))
            for f in path.glob("*.csv")
            if re.search(r"\d+", f.name)
        ],
        reverse=True,
    )
    # Get latest file based on timestamp
    latest_file = next(f for f in path.glob("*.csv") if timestamps[0] in f.name)
    # print(latest_file)
    df = pd.read_csv(latest_file)

    processed_data = [DataLoader.from_series(row) for _, row in df.iterrows()]
    extract_run_name = path.as_posix().rsplit("/", maxsplit=1)[-1]
    schema_table = "_".join(extract_run_name.split("-"))

    with connector.cursor() as cursor:
        DataLoader.create_table_and_insert(
            schema_table, connector, cursor, processed_data
        )
