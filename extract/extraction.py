"""
Command-Line Interface (CLI) Usage:
-----------------------------------
Run this script using the following command:

    python extract/extraction.py <marketplace_name> <category> <subcategory>

Arguments:
- <marketplace_name>: Name of the marketplace (must be enclosed in quotes if it contains spaces).
- <category>: Product category (enclose in quotes if it contains spaces).
- <subcategory>: Product subcategory (enclose in quotes if it contains spaces).

Notes:
- All arguments must be enclosed in either single (' ') or double (" ") quotes.
- Available marketplace names, categories, and subcategories are predefined within this script.
- Ensure the specified marketplace, category, and subcategory exist in the predefined dictionaries.

Output:
The script scrapes product details such as name, price, currency, image URL, and product link from the specified marketplace and category.
Extracted product data is printed in JSON format (sample preview in console) and saved for further analysis.

Recommended Directory Structure for Saving Output (optional):
------------------------------------------------------------
    output/
        <marketplace_name>/
            <category>/
                <subcategory>/
                    <timestamp>.json

"""

import json
import logging
import re
import time
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from urllib import parse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Predefined search queries:
search_query_list = {
    "marketplace": {
        "amazonae": {
            "url": "https://www.amazon.ae",
            "categories": [
                "pet food",
                "pet accessories",
                "pet health & grooming",
                "pet toys & entertainment",
            ],
        },
        # Define additional marketplaces below by specifying their URL and categories
    }
}

categories = {
    "pet food": ["dry food", "wet food"],
    "pet accessories": [
        "collars & leashes",
        "pet bowls & containers",
        "carriers & travel gear",
    ],
    "pet health & grooming": ["supplements & vitamins", "treatments", "pet toiletries"],
    "pet toys & entertainment": [
        "chew toys & balls",
        "interactive toys",
        "scratching posts",
    ],
    # Define additional categories and subcategories below,
    # ensuring they align with those listed for each marketplace
}


# Build the search URL for a given query on Amazon marketplace
def build_search_url(base_url: str, query: str) -> str:
    params = {"k": query, "ref": "nb_sb_noss"}
    return f"{base_url}/s?{parse.urlencode(params)}"


# Normalize and clean category and subcategory into a query-friendly string
def normalize_query(category: str, subcategory: str) -> str:
    combined = f"{category} {subcategory}"
    cleaned = re.sub(r"[^\w\s]", "", combined).lower()
    return " ".join(cleaned.split())


def normalize_strings(text_str: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text_str).lower()
    return "_".join(cleaned.split())


# Generate search queries for all category and subcategory combinations for a marketplace
def build_search_query(marketplace_key: str) -> dict:
    marketplace = search_query_list["marketplace"].get(marketplace_key)
    if not marketplace:
        return {}

    base_url = marketplace["url"]
    category_list = marketplace["categories"]
    search_queries = {}

    for category in category_list:
        subcategories = categories.get(category, [])
        for subcategory in subcategories:
            query = normalize_query(category, subcategory)
            # logger.info("Building search for query: %s", query)
            search_url = build_search_url(base_url, query)
            search_queries[(category, subcategory)] = search_url

    return search_queries


# Extract product-level details such as name, price, currency, and image URL from HTML
def page_level_product_extraction(html_soup):
    img_tag = html_soup.select_one(
        'span[data-component-type="s-product-image"] img.s-image'
    )
    product_img_url = img_tag["src"] if img_tag else None

    try:
        name = html_soup.find("h2").find("span").get_text(strip=True)
    except Exception:
        name = None

    try:
        price_tag = html_soup.select_one(".a-price .a-offscreen")
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            parts = price_text.split()
            currency, price = parts if len(parts) == 2 else ("", parts[0])
            currency = str(currency)
            price = float(price)
        else:
            currency, price = None, None
    except Exception:
        currency, price = None, None

    return {
        "name": name.lower(),
        "price": price,
        "currency": currency,
        "image_url": product_img_url,
    }


# Scrape all paginated product pages starting from the given search URL
def click_through_all_pages(
    marketplace: str, parent_url: str, url: str, category: str, subcategory: str
):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

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

        page.route("**/*", block_requests)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=100_000)
            page.wait_for_timeout(60_000)
            page_num = 1
            product_data = []
            today = datetime.today().strftime("%Y-%m-%d")

            while True:
                logger.info("Scraping page %d", page_num)

                html_soup = BeautifulSoup(
                    page.query_selector(
                        "span.rush-component.s-latency-cf-section"
                    ).inner_html(),
                    "html.parser",
                )

                for idx, html in enumerate(
                    html_soup.find_all("div", class_="a-section a-spacing-base"), 1
                ):
                    try:
                        link = html.find("a", class_="a-link-normal")
                        href = link.get("href") if link else None
                        if href:
                            product_details = page_level_product_extraction(html)
                            product_details.update(
                                {
                                    "product_detail_url": parse.urljoin(
                                        parent_url, href
                                    ),
                                    "page_url": url,
                                    "marketplace": marketplace.lower(),
                                    "category": category.lower(),
                                    "subcategory": subcategory.lower(),
                                    "date_collected": today,
                                    "url": parent_url,
                                }
                            )
                            product_data.append(product_details)
                    except Exception as error:
                        logger.warning(
                            "Skipping product #%s due to error: %s", idx, error
                        )

                try:
                    pagination = page.locator("a.s-pagination-item", has_text="Next")
                    pagination.wait_for(state="visible", timeout=15_000)

                    if pagination.is_enabled():
                        time.sleep(3)
                        with page.expect_navigation(
                            wait_until="networkidle", timeout=100_000
                        ):
                            pagination.click()
                        page_num += 1
                    else:
                        logger.info("Next button found but not enabled.")
                        break

                except PlaywrightTimeoutError:
                    logger.info("Next button not found or not visible within timeout.")
                    break
                except Exception as error:
                    logger.error("Unexpected pagination error: %s", error)
                    break

            logger.info("Total pages visited: %d", page_num)
            logger.info("Total products collected: %d", len(product_data))
            print(json.dumps(product_data[:3], indent=3))

            return product_data

        except Exception as error:
            logger.error("Error occurred: %s", error)
        finally:
            browser.close()


# Parse command-line arguments for marketplace, category, and subcategory
def cli_arguments() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "-m",
        "--marketplace",
        help="Marketplace name to scrape product-level data.",
        default="amazonae",
    )
    parser.add_argument(
        "-c",
        "--category",
        help="Category name for search query construction.",
        default="pet food",
    )
    parser.add_argument(
        "-s",
        "--subcategory",
        help="Subcategory name for search query construction.",
        default="wet food",
    )
    return parser.parse_args()


def main() -> None:
    # Parse CLI arguments
    call_args = cli_arguments()
    marketplace = call_args.marketplace
    category = call_args.category
    subcategory = call_args.subcategory

    # Build search queries and retrieve URL based on provided category & subcategory
    search_queries = build_search_query(marketplace)
    key = (category, subcategory)
    url = search_queries.get(key)
    web_url = "https://www.amazon.ae"
    if not url:
        logger.error(
            "Search query for the provided category and subcategory was not found."
        )
        exit(1)

    logger.info("Starting scrape for: %s", url)
    print(call_args)

    # Generate filename using marketplace, category, and subcategory
    filename_base = f"{marketplace} {category} {subcategory}"
    file_name = normalize_strings(filename_base) + ".json"
    print(file_name)

    # Clean directory names (replace non-alphanumerics with underscores)
    safe_category = re.sub(r"\W+", "_", category).strip().replace(" ", "_")
    safe_subcategory = re.sub(r"\W+", "_", subcategory).strip().replace(" ", "_")

    # Define output directory path
    output_dir = Path.cwd() / "output" / marketplace / safe_category / safe_subcategory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Scrape products and save to JSON file in the output directory
    output_path = output_dir / file_name
    print(output_path)
    products = click_through_all_pages(marketplace, web_url, url, category, subcategory)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=3)

    logger.info("Scraping completed. Data saved to: %s", output_path)


if __name__ == "__main__":
    main()
