import json
import logging
import os
import re
import sys
import time
from typing import Optional

import utils
from playwright.sync_api import Page, sync_playwright

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_products(file_path: str) -> list:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            all_products = json.load(f)
            data = [p for p in all_products if p.get("name")]
        return data

    except FileNotFoundError:
        print(f"File does not exists: {file_path.split('/')[-1]}")
        sys.exit(1)


def save_to_json(data: list, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def wait_for_main_selectors(page: Page) -> None:
    page.wait_for_selector("div#desktop-breadcrumbs_feature_div", timeout=60000)
    page.wait_for_selector("div#ppd", timeout=60000)


def extract_category(page: Page) -> Optional[str]:

    container = page.query_selector("div#desktop-breadcrumbs_feature_div")
    ul_element = (
        container.query_selector("ul.a-unordered-list.a-horizontal.a-size-small")
        if container
        else None
    )
    category_elements = (
        ul_element.query_selector_all("span.a-list-item") if ul_element else []
    )

    group = tuple(
        val
        for idx, el in enumerate(category_elements, 1)
        if idx != 1 and (val := re.sub(r"\W+", "\t", el.inner_text()))
    )
    items_group = [c for c in group if c != "\t"]
    return "\t".join(items_group) if items_group else None


def extract_title(page: Page) -> Optional[str]:

    center_col = page.query_selector("div#centerCol")
    title_el = center_col.query_selector("span#productTitle") if center_col else None
    return title_el.inner_text().strip() if title_el else None


def extract_reviews(page: Page, errors: list) -> tuple[float, str]:
    try:
        center_col = page.query_selector("div#centerCol")
        scores_el = (
            center_col.query_selector("div#averageCustomerReviews")
            if center_col
            else None
        )
        score_el = scores_el.query_selector("span.a-icon-alt") if scores_el else None
        total_reviews_el = (
            scores_el.query_selector("span#acrCustomerReviewText")
            if scores_el
            else None
        )

        score = float(score_el.inner_text().split()[0]) if score_el else 0.0
        total_reviews = (
            total_reviews_el.inner_text().split()[0] if total_reviews_el else "0"
        )
        return score, total_reviews
    except Exception:
        errors.append("Review: div#averageCustomerReviews or child elements")
        return 0.0, "0"


def extract_brand(page: Page, errors: list) -> Optional[str]:
    try:
        brand_el = page.query_selector("tr.po-brand td.a-span9")
        if brand_el is None:
            brand_el = page.query_selector("a#bylineInfo")
        brand_text = brand_el.inner_text().strip() if brand_el else None
        if brand_text and ":" in brand_text:
            brand_text = "".join(re.split(":", brand_text)[-1]).strip()
            print(brand_text)
        return brand_text
    except Exception:
        errors.append("Brand: tr.po-brand td.a-span9")
        return None


def extract_about(page: Page, errors: list) -> str:
    try:
        desc_els = page.query_selector_all(
            "div#feature-bullets ul.a-unordered-list.a-vertical li"
        )
        return (
            "\n\n".join([li.inner_text().strip() for li in desc_els])
            if desc_els
            else ""
        )
    except Exception:
        errors.append(
            "Description: div#feature-bullets ul.a-unordered-list.a-vertical li"
        )
        return ""


def extract_description(page: Page, errors: list) -> str:
    # Description
    try:
        desc = page.query_selector_all("div#productDescription_feature_div")
        description_text = ""
        for c in desc:
            get_desc = c.query_selector("div#productDescription")
            if get_desc:
                description_text = get_desc.inner_text()
                break
    except Exception as e:
        errors.append(
            "Description: div#productDescription_feature_div#productDescription"
        )
        description_text = ""
        print(e)
    return description_text


def extract_product_details(
    page: Page, product: dict, category: str, subcategory: str
) -> dict:
    url = product.get("product_detail_url", "")

    # Initialize variables before the loop
    amazon_category = None
    title = None
    score = 0.0
    total_reviews = "0"
    brand = None
    about = ""
    description = ""
    errors = []

    for attempt in range(5):
        try:
            logger.info("Attempt Number - [%s]", attempt + 1)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            errors = []  # Reset errors for each attempt

            wait_for_main_selectors(page)

            amazon_category = extract_category(page)
            title = extract_title(page)
            score, total_reviews = extract_reviews(page, errors)
            brand = extract_brand(page, errors)
            about = extract_about(page, errors)
            description = extract_description(page, errors)

            # If we get here, extraction succeeded
            break

        except TimeoutError:
            print(f"Timeout on attempt {attempt + 1}")
            time.sleep(3)
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
            time.sleep(5)
    else:
        # This runs if the loop completes without breaking
        errors.append("All attempts failed")

    return {
        **{k: v for k, v in product.items() if k != "index"},
        "name": title,
        "category": category,
        "subcategory": subcategory,
        "amazon_category": amazon_category,
        "review_score": score,
        "total_reviews": total_reviews,
        "brand": brand,
        "about": about,
        "description": description,
        "tags_with_errors": errors,
    }


def process_product_detail(products: list, category: str, subcategory: str) -> list:
    detailed_product_list = []

    logger.info("Launching browser with Playwright...")
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        page = browser.new_page()

        for idx, product in enumerate(products, 1):
            try:
                product_details = extract_product_details(
                    page, product, category, subcategory
                )
                detailed_product_list.append(product_details)
                print(f"[{idx}] Collected: {product_details['name'][:60]}...")
            except Exception as error:
                print(
                    f"[{idx}] Failed to extract from {product['product_detail_url']}: {error}"
                )

        browser.close()

    return detailed_product_list


from argparse import ArgumentParser


def run_transformer(args: ArgumentParser, limit_records: str = ""):

    logger.info("Starting detail extraction script...")

    os.makedirs(args.path, exist_ok=True)

    config = utils.load_config("configs.yml")
    category_key, subcategory_key = utils.extract_keys(args.path)

    category = config[category_key]["name"]
    subcategory = config[category_key][subcategory_key]["name"]

    products_ = load_products(args.extract)

    if limit_records != "":
        products_ = products_[: int(limit_records)]
        # products_ = products_[int(limit_records) + 13:int(limit_records) + 15]

    detailed_products = []

    logger.info("Launching browser with Playwright...")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        for idx, product in enumerate(products_, 1):
            try:
                details = extract_product_details(page, product, category, subcategory)
                detailed_products.append(details)
                print(f"[{idx}] Collected: {details['name'][:60]}...")
            except Exception as e:
                print(
                    f"[{idx}] Failed to extract from {product['product_detail_url']}: {e}"
                )

        browser.close()

    save_to_json(detailed_products, args.name)
    print(f"\nSaved {len(detailed_products)} products to '{args.name}'")


def main() -> None:
    args = utils.parse_args()
    limited_rec = (
        int(args.limit_records) if args.limit_records != "" else args.limit_records
    )
    # print(limited_rec)
    run_transformer(args, limited_rec)


if __name__ == "__main__":

    main()
