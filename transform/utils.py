from argparse import ArgumentParser

import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--path",
        required=True,
        help="Path to save results (should include category/subcategory)",
    )
    parser.add_argument("--extract", required=True, help="File name of previous run")
    parser.add_argument("--name", required=True, help="Output file name for results")
    parser.add_argument("--limit_records", default="", help="Limit the maximum record values are required.")
    return parser.parse_args()


def extract_keys(path: str):
    prefix, subcategory_key = path.rsplit("/", 1)
    _, category_key = prefix.rsplit("/", 1)
    return category_key, subcategory_key
