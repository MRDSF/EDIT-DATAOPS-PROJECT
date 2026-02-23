# Load Scripts

## Overview

These scripts load raw data into the PostgreSQL `bronze` schema:

| Script | Source | Target Table | Format |
|---|---|---|---|
| `load_news.py` | CSV files from `data/tesla_news/` | `bronze.bronze_news` | CSV |
| `load_stocks.py` | JSON file from `data/stocks/` | `bronze.bronze_stock_data` | JSON |

## How to run

```bash
# from project root
python load/load_news.py
python load/load_stocks.py
```

Or inside Docker (Airflow container):

```bash
docker exec -e POSTGRES_HOST=database -e POSTGRES_PORT=5432 \
  airflow_webserver_dataops bash -c "cd /workspace/load && python load_news.py"
```

## Reading strategy: CSV vs JSON

The two scripts handle chunking differently due to format constraints:

### `load_news.py` — True streaming (CSV)

```python
df_iter = pd.read_csv(csv_file, dtype=str, chunksize=50_000)
for df in df_iter:
    # only 50,000 rows in memory at a time
    ...
```

`pd.read_csv` supports native chunked reading. It returns an **iterator** — each iteration reads the next 50,000 rows from disk. The full file is **never** loaded into memory.

### `load_stocks.py` — Full read + chunked insert (JSON)

```python
df = pd.read_json(json_path)  # loads entire file into memory
for start in range(0, len(df), chunk_size):
    chunk = df.iloc[start:start + chunk_size]
    # insert chunk into DB
    ...
```

`pd.read_json` does **not** support `chunksize` for standard JSON files (only for JSON Lines format with `lines=True`). So the entire file is loaded into a DataFrame first, then sliced into chunks for the database insert.

For ~200 stock rows this is fine. If the file grew to millions of rows, alternatives would be:

| Approach | When to use |
|---|---|
| `pd.read_json()` (current) | Small-medium files (<100MB) |
| Convert to JSON Lines + `chunksize` | When you control the file format |
| `ijson` (streaming parser) | Very large JSON files (GB+) |

### Summary

| | `load_news.py` | `load_stocks.py` |
|---|---|---|
| **Read** | `pd.read_csv(..., chunksize=50000)` — streaming | `pd.read_json()` — full file in memory |
| **Insert** | Chunked via `execute_values` | Chunked via `iloc` slices + `execute_values` |
| **Memory** | Only `CHUNK_SIZE` rows at a time | Full DataFrame + chunk slice |
| **Deduplication** | `ON CONFLICT (source, title, date_raw) DO NOTHING` | `ON CONFLICT (date) DO UPDATE` |

## Why `DO NOTHING` vs `DO UPDATE`?

The two scripts use different conflict strategies because the data has different characteristics:

### `load_news.py` — `ON CONFLICT DO NOTHING`

News articles are **immutable** — once published, the title, date, and link don't change. If a duplicate row arrives (same `source`, `title`, `date_raw`), it's silently skipped and the original row is preserved.

| Benefit | Explanation |
|---|---|
| Performance | Skips fast, no unnecessary writes |
| `ingested_at` preserved | Keeps the original ingestion timestamp |
| Idempotent | Safe to re-run the same CSVs multiple times |

### `load_stocks.py` — `ON CONFLICT DO UPDATE`

Stock data is **mutable** — a price correction or adjusted value might arrive in a later API call. If a duplicate date arrives, all columns are overwritten with the latest values.

| Benefit | Explanation |
|---|---|
| Data freshness | Always reflects the latest API response |
| Corrections applied | Adjusted close, dividends may be revised |
| `ingested_at` updated | Tracks when the latest version was loaded |

### When to use which

| Strategy | Use when |
|---|---|
| `DO NOTHING` | Data is immutable (news, logs, events) |
| `DO UPDATE` | Data can be corrected or revised (prices, metrics, configs) |

## Path resolution

Both scripts resolve file paths relative to the script's own location using:

```python
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
```

This ensures they work correctly regardless of the current working directory (project root, `load/` folder, or inside a Docker container).
