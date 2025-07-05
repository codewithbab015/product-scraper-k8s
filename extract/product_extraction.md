# 🛒 Amazon Product Scraper (CLI-Based)
This Python script automates product data extraction from Amazon (currently set for Amazon AE marketplace). It collects product details such as name, price, currency, image URL, and product link by navigating through paginated search results.

---

## ⚙️ Features

* Command-line interface (CLI) for easy usage.
* Scrapes all paginated results.
* Extracts product name, price, currency, image URL, and link.
* Saves data in structured JSON format by marketplace, category, and subcategory.

---

## 🚀 Usage

### Run:

```bash
python extract/extraction.py -m <marketplace> -c <category> -s <subcategory>
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

## 📂 Output

Data is saved to:

```
output/<marketplace>/<category>/<subcategory>/<marketplace>_<category>_<subcategory>.json
```

---

## 🏷️ Supported Categories (Default)

* **pet food** → dry food, wet food
* **pet accessories** → collars & leashes, pet bowls & containers, carriers & travel gear
* **pet health & grooming** → supplements & vitamins, treatments, pet toiletries
* **pet toys & entertainment** → chew toys & balls, interactive toys, scratching posts

---

## 🔧 Requirements

* Python 3.8+
* Install dependencies:

```bash
pip install -r requirements.txt
```

Then install browser binaries:

```bash
playwright install
```

---

## 📌 Notes

* Marketplace, category, and subcategory values must match those defined in the script.
* Output directories are auto-created.
* Logs scraping progress and sample product preview are shown.
