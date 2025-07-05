# 📤 ETL Export Script: Transform → Excel & CSV

This script finalizes the ETL pipeline by **cleaning**, **validating**, and **exporting** the enriched product metadata to structured file formats.


## ⚙️ Features

* CLI-based usage for seamless integration with other ETL stages.
* Loads enriched product data from:

  ```
  transform_<marketplace>_<category>_<subcategory>.json
  ```
* Cleans and validates fields like:

  * `price`, `review_score`, `brand`, `description`, `url`
* Exports final dataset to:

  * `.xlsx` (Excel)
  * `.csv` (UTF-8)
* Logs runtime activity and missing value summaries to file and console.

## 🚀 Usage

```bash
python load/filesys_loader.py -m <marketplace> -c <category> -s <subcategory>
```

### Arguments:

| Flag | Description                         | Default    |
| ---- | ----------------------------------- | ---------- |
| `-m` | Marketplace name (e.g., `amazonae`) | `amazonae` |
| `-c` | Product category                    | `pet food` |
| `-s` | Product subcategory                 | `wet food` |

> ✅ Wrap space-containing values in quotes:
> `-c "pet food"`

## 📂 Input

The script expects this enriched JSON input file:

```
output/<marketplace>/<category>/<subcategory>/transform_<marketplace>_<category>_<subcategory>.json
```

✅ Example:

```
output/amazonae/pet_food/wet_food/transform_amazonae_pet_food_wet_food.json
```

## 📤 Output

Two cleaned files are written in the same directory:

* `final_<marketplace>_<category>_<subcategory>_<timestamp>.xlsx`
* `final_<marketplace>_<category>_<subcategory>_<timestamp>.csv`

✅ Logs are stored in:

```
logs/summary.log
```

## 🔄 Workflow

1. Load enriched JSON records.
2. Validate required fields:

   * Numeric types for `price`, `review_score`
   * Drop missing or duplicate values.
3. Export cleaned data:

   * Excel (`sheet_name='Products'`)
   * CSV (UTF-8 encoding)
4. Log statistics, warnings, and outputs.

## 📌 Notes

* Expected fields:

  ```
  category, subcategory, marketplace, brand, name, price, currency,
  description, url, image_url, review_score, date_collected
  ```
* Extra fields from JSON are appended automatically.
* Directory must exist before running this script.

---

# 🚦 ETL Routing Script: Filesystem or Database Export

This script is the **final orchestration step** in the ETL pipeline. It determines whether cleaned product data should be:

* exported to **Excel/CSV files** (`dir`), or
* inserted into a **PostgreSQL database** (`db`).


## ⚙️ Features

* Unified CLI routing interface.
* Delegates logic to:

  * `filesys_loader.run_loader()` for file export
  * `db_loader.run_loader_db()` for database load
* Compatible with existing pipeline arguments.


## 🚀 Usage

```bash
python load/run_data_loader.py -m <marketplace> -c <category> -s <subcategory> -d <destination>
```

### Arguments:

| Flag | Description                                       | Default      |
| ---- | ------------------------------------------------- | ------------ |
| `-m` | Marketplace name (e.g., `amazonae`)               | `amazonae`   |
| `-c` | Product category (e.g., `pet food`)               | `pet food`   |
| `-s` | Product subcategory (e.g., `wet food`)            | `wet food`   |
| `-d` | Destination: `dir` for files or `db` for database | **Required** |

✅ File export example:

```bash
python load/run_data_loader.py -m amazonae -c "pet food" -s "wet food" -d dir
```

✅ Database load example:

```bash
python load/run_data_loader.py -m amazonae -c "pet food" -s "wet food" -d db
```

## 📁 Output Behavior

### If `-d dir`:

* Calls `filesys_loader.run_loader()`
* Exports data to:

  ```
  output/<marketplace>/<category>/<subcategory>/
  ```
* Output files:

  * `.xlsx` and `.csv`
  * Log file at `logs/summary.log`

### If `-d db`:

* Calls `db_loader.run_loader_db()`
* Inserts data into a configured PostgreSQL table.
* Credentials and schema handled in `db_loader.py`.


## 📌 Notes

* Invalid destination values will raise an error.
* Ensure the appropriate output folder or DB connection is prepared.
* Compatible with all standard marketplaces and categories used in earlier stages.
