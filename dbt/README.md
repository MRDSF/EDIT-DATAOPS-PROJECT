# dbt – Running with Docker

## Prerequisites

Make sure the containers are up:

```bash
docker-compose up -d
```

## How `profiles.yml` accesses environment variables

The credentials flow through 3 layers:

1. **`.env`** — defines `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
2. **`docker-compose.yml`** — the `dbt` service passes those values into the container via the `environment` block using `${POSTGRES_USER}` syntax
3. **`profiles.yml`** — dbt uses Jinja templating with `{{ env_var('POSTGRES_USER') }}` to read the environment variables at runtime inside the container

This avoids hardcoding credentials and keeps secrets in one place (`.env`).

## Commands

### Debug (test connection)

```bash
docker-compose run --rm dbt debug
```

### Run all models

```bash
docker-compose run --rm dbt run
```

### Run a specific model

```bash
docker-compose run --rm dbt run --select silver_news
```

### Run all models in a layer

```bash
docker-compose run --rm dbt run --select silver.*
docker-compose run --rm dbt run --select gold.*
```

### Run tests

```bash
docker-compose run --rm dbt test
```

### Run tests for a specific model

```bash
docker-compose run --rm dbt test --select silver_stock_data
```

### Generate and serve docs

```bash
docker-compose run --rm dbt docs generate
```

## Deduplication Strategy

The silver models use `ROW_NUMBER()` window functions to remove duplicate rows coming from the bronze layer. This ensures that if the same record is loaded multiple times (e.g. re-running a load script), only the most recent version passes through.

### How it works

```sql
row_number() over (
    partition by <unique_key_columns>
    order by ingested_at desc
) as rn
```

- **`PARTITION BY`** — groups rows that represent the same logical record
- **`ORDER BY ingested_at DESC`** — ranks them by ingestion time, newest first
- **`WHERE rn = 1`** — keeps only the latest version of each record

### Deduplication keys per model

| Model | Partition by | Keeps |
|---|---|---|
| `silver_news` | `source`, `title`, `date_raw` | Latest `ingested_at` |
| `silver_stock_data` | `trade_date` | Latest `ingested_at` |

### Example

If `bronze_stock_data` has two rows for the same date (loaded at different times):

| date | open | ingested_at |
|---|---|---|
| 2025-01-02 | 410.50 | 2025-01-03 08:00 |
| 2025-01-02 | 411.00 | 2025-01-05 08:00 |

After deduplication, `silver_stock_data` keeps only the second row (`rn = 1`) because it has the latest `ingested_at`.
