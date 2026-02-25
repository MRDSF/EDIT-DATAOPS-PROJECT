# Tesla DataOps Project

End-to-end data pipeline for Tesla stock prices and news articles — from raw extraction to analytical tables, orchestrated with Airflow.

## Architecture

```
Extract (API + Web Scraping)
    │
    ▼
data/ (JSON + CSVs on disk)
    │
    ▼
Load (Python → PostgreSQL bronze schema)
    │
    ▼
Bronze (raw tables: bronze_news, bronze_stock_data)
    │  dbt
    ▼
Silver (views: typed, cleaned, deduplicated)
    │  dbt
    ▼
Gold (tables: aggregated metrics, curated data)
```

## Tech Stack

| Component | Technology |
|---|---|
| Database | PostgreSQL 15 |
| DB Admin | pgAdmin 4 |
| Transformation | dbt-postgres 1.8 |
| Orchestration | Apache Airflow 2.9.3 |
| Language | Python 3.11 |
| Validation | Pydantic 2.x |
| Testing | pytest + dbt tests |
| Containers | Docker Compose |

## Data Sources

| Source | Method | Schedule | Output |
|---|---|---|---|
| [Alpha Vantage API](https://www.alphavantage.co/) | REST API + Pydantic validation | Monthly | `data/stocks/stocks_data_tesla.json` |
| [notateslaapp.com](https://www.notateslaapp.com) | Web scraping (requests + BeautifulSoup) | Daily | `data/tesla_news/notateslaapp_YYYY_MM.csv` |
| [euronews.com](https://euronews.com) | Web scraping (Selenium, headless Chrome) | Daily | `data/tesla_news/euronews_YYYY_MM.csv` |

## Docker Compose Services

```bash
docker-compose up -d
```

| Service | Container | Port | Description |
|---|---|---|---|
| `database` | `postgres_database_dataops` | 5432 | PostgreSQL 15 with healthcheck |
| `pgadmin` | `pgadmin_service_dataops` | 5051 | pgAdmin web UI |
| `dbt` | `dbt_to_postgres_dataops` | — | dbt-postgres (run on demand) |
| `airflow-init` | `airflow_init_dataops` | — | Runs `airflow db migrate`, then exits |
| `airflow-webserver` | `airflow_webserver_dataops` | 8080 | Airflow web UI |
| `airflow-scheduler` | `airflow_scheduler_dataops` | — | Triggers DAGs on schedule |

### Startup Order

```
database (healthcheck: pg_isready)
    ├── pgadmin
    ├── dbt
    └── airflow-init (db migrate)
            ├── airflow-webserver
            └── airflow-scheduler
```

### Access

| Service | URL | Credentials |
|---|---|---|
| pgAdmin | http://localhost:5051 | See `.env` |
| Airflow | http://localhost:8080 | admin / admin |

## Database Schemas

| Schema | Layer | Contents |
|---|---|---|
| `bronze` | Raw | `bronze_news`, `bronze_stock_data` — raw data as-is from sources |
| `silver` | Cleaned | `silver_news`, `silver_stock_data` — typed, trimmed, deduplicated (views) |
| `gold` | Analytical | `gold_news_info`, `gold_news_monthly_summary`, `gold_stock_monthly_summary` (tables) |

### Bronze Tables

| Table | PK / Unique Constraint | Load Strategy |
|---|---|---|
| `bronze_news` | `bigserial` PK + unique on `(source, title, date_raw)` | `ON CONFLICT DO NOTHING` (immutable data) |
| `bronze_stock_data` | `date TEXT` PK | `ON CONFLICT DO UPDATE` (mutable data — corrections) |

### Silver Models (views, deduplicated)

| Model | Source | Deduplication Key | Keeps |
|---|---|---|---|
| `silver_news` | `bronze_news` | `(source, title, date_raw)` | Latest `ingested_at` |
| `silver_stock_data` | `bronze_stock_data` | `trade_date` | Latest `ingested_at` |

Deduplication uses `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ingested_at DESC) = 1`.

### Gold Models (tables, aggregated)

| Model | Description | Key Metrics |
|---|---|---|
| `gold_news_info` | Curated news articles | `published_date`, `title`, `link`, `source` |
| `gold_news_monthly_summary` | Monthly news aggregation per source | `total_articles`, `distinct_days_with_articles`, `avg_articles_per_day` |
| `gold_stock_monthly_summary` | Monthly stock aggregation | `month_low`, `month_high`, `avg_close_price`, `total_volume`, `total_dividends`, `trading_days` |

## Airflow DAGs

### `news_pipeline` — Daily at 07:00 UTC

```
[scrape_notateslaapp, scrape_euronews]  (parallel)
        ↓
    load_news_data
        ↓
  dbt_run_silver_news
        ↓
  dbt_run_gold_news  (gold_news_monthly_summary + gold_news_info)
        ↓
    dbt_test_news
```

### `stock_pipeline` — Monthly (1st at 06:00 UTC)

```
extract_stock_data  (Alpha Vantage API)
        ↓
    load_stock_data
        ↓
  dbt_run_silver_stock
        ↓
  dbt_run_gold_stock
        ↓
    dbt_test_stock
```

## Data Quality

### dbt Schema Tests

| Model | Tests |
|---|---|
| `silver_stock_data` | `trade_date` — unique, not_null |
| `silver_news` | `published_date`, `title`, `link`, `source` — not_null |
| `gold_news_info` | `link` — unique, not_null; all columns — not_null |
| `gold_stock_monthly_summary` | `month` — unique, not_null |
| `gold_news_monthly_summary` | `source`, `month` — not_null |

### dbt Singular Tests

| Test | Asserts |
|---|---|
| `assert_stock_values_not_negative` | All prices, volume, and dividends in `silver_stock_data` are >= 0 |
| `assert_gold_stock_values_not_negative` | All aggregated values in `gold_stock_monthly_summary` are >= 0 |

## Project Structure

```
projeto-dataops/
├── docker-compose.yml
├── .env                          # Credentials (not committed)
├── requirements.txt              # Python deps (local dev)
│
├── extract/                      # Data extraction
│   ├── collect_api_data.py           # Alpha Vantage stock API
│   ├── web_scrap_tesla_news_source1.py   # notateslaapp (requests)
│   └── web_scrap_tesla_news_source2.py   # euronews (Selenium headless)
│
├── load/                         # Bronze layer loaders
│   ├── load_news.py                  # CSVs → bronze.bronze_news
│   ├── load_stocks.py                # JSON → bronze.bronze_stock_data
│   └── README.md
│
├── models/                       # Pydantic schemas
│   └── schemas.py                    # API response validation
│
├── data/                         # Raw data files
│   ├── stocks/                       # Stock JSON
│   └── tesla_news/                   # News CSVs (monthly partitioned)
│
├── dbt/                          # dbt project
│   ├── profiles/
│   │   └── profiles.yml
│   ├── tesla_dbt_proj/
│   │   ├── models/
│   │   │   ├── sources.yml
│   │   │   ├── silver/               # Typed/cleaned/deduped views
│   │   │   └── gold/                 # Aggregated tables
│   │   ├── tests/                    # Singular tests (not_negative)
│   │   └── macros/                   # generate_schema_name override
│   └── README.md
│
├── airflow/                      # Airflow setup
│   ├── Dockerfile                    # Custom image with Python deps
│   ├── requirements.txt
│   ├── dags/                         # DAG definitions
│   │   ├── dag_news_pipeline.py
│   │   ├── dag_stock_pipeline.py
│   │   └── README.md
│   └── README.md
│
├── tests/                        # Python unit tests (pytest)
│   ├── test_schemas.py               # Pydantic model tests
│   ├── test_load_news.py             # CSV validation tests
│   └── README.md
│
└── sentiment_analysis_test/      # Kafka sentiment (experimental)
```

## Quick Start

```bash
# 1. Clone and configure
cp .env-example .env  # edit with your credentials

# 2. Start infrastructure
docker-compose up -d

# 3. Create Airflow admin user (first time only)
docker exec airflow_webserver_dataops airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com

# 4. Open Airflow UI → enable DAGs
#    http://localhost:8080

# 5. Run dbt models manually (optional)
docker-compose run --rm dbt run

# 6. Run Python tests locally
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Documentation

| Folder | README |
|---|---|
| [load/](load/README.md) | Load scripts — chunking, conflict strategies, path resolution |
| [dbt/](dbt/README.md) | dbt commands, env_var flow, deduplication strategy |
| [airflow/](airflow/README.md) | Airflow setup, custom Dockerfile |
| [airflow/dags/](airflow/dags/README.md) | DAG docs, design decisions, BashOperator vs PythonOperator |
| [tests/](tests/README.md) | Test descriptions and run commands |