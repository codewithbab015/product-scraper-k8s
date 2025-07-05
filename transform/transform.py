"""
Product Detail Enrichment Script
--------------------------------

This script enriches product-level metadata by scraping additional information
(e.g., brand, description, review score) from product detail pages using Playwright.

Usage:
    python extract/extraction.py -m <marketplace> -c <category> -s <subcategory>

Arguments:
    -m, --marketplace   Marketplace name (e.g., "amazonae")
    -c, --category      Product category (e.g., "pet food")
    -s, --subcategory   Product subcategory (e.g., "wet food")

Functionality:
    - Reads a JSON file from the output directory containing product URLs.
    - For each product (limited to first 5 for demo), scrapes details from its URL.
    - Enriches the original metadata and saves the updated results as JSON.
    - Logs progress and errors for traceability.

Output:
    - A JSON file named `transform_<marketplace>_<category>_<subcategory>.json`
      saved in the same output directory structure.
"""

import json
import logging
import re
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def product_level_scraper(url: str) -> Optional[dict]:
    def block_requests(route, request):
        blocked_resources = ["media", "audio"]
        blocked_extensions = (".mp4", ".m3u8", ".webm", ".mov", ".avi", ".flv")
        ad_domains = [
            "doubleclick.net",
            "google-analytics.com",
            "googletagmanager.com",
            "adsystem.com",
            "amazon-adsystem.com",
            "facebook.net",
        ]
        if (
            request.resource_type in blocked_resources
            or request.url.endswith(blocked_extensions)
            or any(domain in request.url for domain in ad_domains)
        ):
            route.abort()
        else:
            route.continue_()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.route("**/*", block_requests)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=100_000)
            page.wait_for_selector("div#dp-container", timeout=60_000)

            soup = BeautifulSoup(page.inner_html("div#dp-container"), "html.parser")
            center = soup.find("div", id="centerCol")
            if not center:
                logger.warning("centerCol not found on %s", url)
                return

            brand_el = center.select_one(
                "tr.a-spacing-small.po-brand span.a-size-base.po-break-word"
            )
            about_items = center.select("div#feature-bullets li span.a-list-item")
            about_text = (
                "\n".join(i.get_text(strip=True) for i in about_items)
                if about_items
                else ""
            )

            desc_el = soup.find("div", id="productDescription")
            desc_text = desc_el.get_text(strip=True) if desc_el else ""

            reviews_el = center.select_one(
                "div#averageCustomerReviews span#acrCustomerReviewText"
            )
            score_el = center.select_one(
                "div#averageCustomerReviews span.a-size-base.a-color-base"
            )

            reviews_num = None
            if reviews_el:
                match = re.search(r"([\d,]+)", reviews_el.get_text())
                if match:
                    reviews_num = float(match.group(1).replace(",", ""))

            score_num = None
            if score_el:
                match = re.search(r"([\d.]+)", score_el.get_text())
                if match:
                    score_num = float(match.group(1))

            details = {
                "brand": brand_el.get_text(strip=True).lower() if brand_el else None,
                "description": f"{about_text}\n{desc_text}".lower().strip(),
                "total_reviews": reviews_num,
                "review_score": score_num,
            }
            return details

        except TimeoutError:
            logger.error("Timeout while loading %s", url)
        except Exception as exc:
            logger.exception("Scrape error: %s", exc)
        finally:
            browser.close()


def normalize_strings(text_str: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text_str).lower()
    return "_".join(cleaned.split())


def cli_arguments() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("-m", "--marketplace", default="amazonae")
    parser.add_argument("-c", "--category", default="pet food")
    parser.add_argument("-s", "--subcategory", default="wet food")
    return parser.parse_args()


def main() -> None:
    # Parse CLI arguments
    call_args = cli_arguments()
    marketplace = call_args.marketplace
    category = call_args.category
    subcategory = call_args.subcategory

    # Construct normalized output file name
    filename_base = f"{marketplace} {category} {subcategory}"
    file_name = normalize_strings(filename_base) + ".json"

    # Sanitize directory names for safe paths
    safe_category = re.sub(r"\W+", "_", category).replace(" ", "_")
    safe_subcategory = re.sub(r"\W+", "_", subcategory).replace(" ", "_")

    # Build absolute output path
    output_path = Path("output") / marketplace / safe_category / safe_subcategory
    output_dir = Path.cwd() / output_path

    if not output_dir.is_dir():
        logger.error("Directory [%s] does not exist.", output_path)
        exit(1)

    input_filepath = output_dir / file_name
    if not input_filepath.is_file():
        logger.error("File [%s] does not exist.", file_name)
        exit(1)

    # Load product metadata to enrich
    with open(input_filepath, encoding="utf-8") as f:
        data = json.load(f)

    product_collections = []
    for index, product in enumerate(data, 1):
        if index > 5:
            break
        logger.info("Index [%s] - product name: %s ...", index, product["name"][:50])
        enriched_product = product_level_scraper(product["product_detail_url"])
        product.update(enriched_product or {})
        product_collections.append(product)

    # Preview enriched results
    print(json.dumps(product_collections[:3], indent=3))

    # Save enriched product data
    transformed_path = output_dir / f"transform_{file_name}"
    with open(transformed_path, "w", encoding="utf-8") as f:
        json.dump(product_collections, f, indent=3)

    logger.info("Scraping completed. Data saved to: %s", transformed_path)


if __name__ == "__main__":
    main()
