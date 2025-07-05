# 🛍️ Amazon Product Detail Enricher (CLI-Based)

This Python script enhances product data by extracting additional information such as brand, description, review score, and total reviews directly from individual Amazon product pages.

---

## ⚙️ Features

* CLI interface for flexible usage.
* Uses **Playwright** for dynamic rendering and **BeautifulSoup** for parsing.
* Extracts product-level metadata:

  * Brand
  * Description (about bullets + full description)
  * Total number of reviews
  * Average review score
* Saves enriched data in structured JSON format using marketplace, category, and subcategory.

---

## 🚀 Usage

### Run:

```bash
python transform/transform.py -m <marketplace> -c <category> -s <subcategory>
```

### Arguments:

| Flag | Description                          | Default    |
| ---- | ------------------------------------ | ---------- |
| `-m` | Marketplace name (must match script) | `amazonae` |
| `-c` | Product category                     | `pet food` |
| `-s` | Product subcategory                  | `wet food` |

> ✅ Wrap values containing spaces in quotes:
> `-c "pet food"`

---

### Example:

```bash
python extract/extraction.py -m amazonae -c "pet food" -s "wet food"
```

---

## 📂 Input

The script expects a previously extracted JSON file containing basic product metadata with detail page URLs at:

```
output/<marketplace>/<category>/<subcategory>/<marketplace>_<category>_<subcategory>.json
```

Example:

```
output/amazonae/pet_food/wet_food/amazonae_pet_food_wet_food.json
```

---

## 📤 Output

A new JSON file with enriched product details is saved in the same directory:

```
output/<marketplace>/<category>/<subcategory>/transform_<marketplace>_<category>_<subcategory>.json
```

---

## 🔄 Functionality

1. Load product metadata from an existing JSON file.
2. For each product (first 5 by default for testing), fetch its detail page.
3. Extract additional metadata:

   * Brand name
   * Feature bullets and full description
   * Review score and number of reviews
4. Update the original product data with enriched fields.
5. Save the results to a new transformed JSON file.
6. Log scraping progress and sample preview to console.

---

## 🔧 Requirements

* Python 3.8+
* [Playwright](https://playwright.dev/python/)
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)

### Install dependencies:

```bash
pip install -r requirements.txt
playwright install
```

---

## 📌 Notes

* Scrapes only the first 5 products for demo purposes. Update the limit in the code if needed.
* Uses request blocking to avoid loading media and ad-related assets for faster execution.
* Logging is configured for real-time feedback on scraping progress and potential issues.