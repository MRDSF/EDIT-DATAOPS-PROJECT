# Airflow DAGs

## Overview

| DAG | Schedule | Description |
|---|---|---|
| `stock_pipeline` | Monthly (1st at 06:00 UTC) | Extract stock data from API → Load to DB → dbt transform |
| `news_pipeline` | Daily (07:00 UTC) | Scrape Tesla news sources → Load CSVs to DB → dbt transform |

## stock_pipeline

```
extract_stock_data → load_stock_data → dbt_run_silver_stock → dbt_run_gold_stock → dbt_test_stock
```

| Task | What it does |
|---|---|
| `extract_stock_data` | Calls AlphaVantage API → saves JSON |
| `load_stock_data` | Loads JSON → `bronze_stock_data` |
| `dbt_run_silver_stock` | Casts types → `silver_stock_data` view |
| `dbt_run_gold_stock` | Aggregates → `gold_stock_monthly_summary` table |
| `dbt_test_stock` | Runs dbt tests on both models |

## news_pipeline

```
[scrape_notateslaapp, scrape_euronews] → load_news_data → dbt_run_silver_news → dbt_run_gold_news → dbt_test_news
```

| Task | What it does |
|---|---|
| `scrape_notateslaapp` | Scrapes Tesla news from NotATeslaApp source → writes CSV |
| `scrape_euronews` | Scrapes Tesla news from Euronews source → writes CSV |
| `load_news_data` | Loads CSVs → `bronze_news` (deduplication on conflict) |
| `dbt_run_silver_news` | Cleans/types → `silver_news` view |
| `dbt_run_gold_news` | Builds gold layer → `gold_news_monthly_summary` and `gold_news_info` |
| `dbt_test_news` | Runs dbt tests on `silver_news`, `gold_news_monthly_summary`, and `gold_news_info` |

## Design Decisions

### `BashOperator` vs `PythonOperator` (Best Practice)

| Operator | Best for | Why | Trade-offs |
|---|---|---|---|
| `BashOperator` | Running existing CLI/scripts with minimal changes | Fast to integrate; reproduces local command behavior (`cd /workspace && python ...`) | Weaker typing/XCom integration; command strings can be harder to maintain |
| `PythonOperator` | Airflow-native orchestration with reusable Python modules | Better observability, structured params, easier XCom usage, cleaner retries/error handling | Requires scripts to be importable, path-agnostic modules |

### Recommendation for this project

Use **`BashOperator` for extraction/load scripts right now** because the current scripts assume project-root execution (`/workspace`), relative paths, and local-style imports.

Use **`DockerOperator` for dbt tasks** so each dbt step runs in an isolated dbt image with explicit mounts and environment.

### dbt in Airflow: `DockerOperator` vs `docker exec`

**Decision:** use **`DockerOperator`** for dbt tasks, **do not use `docker exec`**.

| Approach | Recommendation | Why |
|---|---|---|
| `DockerOperator` running `dbt run`/`dbt test` in ephemeral containers | ✅ Keep | Airflow-native retries/logging, no dependency on a pre-running dbt container, clear task isolation |
| `docker exec` into a running dbt container | ❌ Avoid | Couples DAG logic to container lifecycle/name, adds operational fragility, and complicates portability |

This project now runs dbt through `DockerOperator` in both `news_pipeline` and `stock_pipeline`.

### Why this choice is correct today

- Current scripts rely on cwd-sensitive behavior (`../data`, `load_dotenv()`, and imports like `models.schemas`).
- `PythonOperator` runs inside the Airflow worker process, where cwd/module resolution differs unless explicitly refactored.
- `BashOperator` keeps extraction/load behavior consistent between local execution and Airflow execution.
- `DockerOperator` gives dbt task isolation and avoids PATH/permission issues inside the Airflow runtime container.

### Current dbt `DockerOperator` setup

- dbt image: `ghcr.io/dbt-labs/dbt-postgres:1.8.latest`
- Network is environment-driven via `DBT_DOCKER_NETWORK` (for example, `projeto-dataops_app_network`)
- Host mount sources are environment-driven via:
  - `HOST_DBT_PROJECT_DIR` → mounted to `/usr/app`
  - `HOST_DBT_PROFILES_DIR` → mounted to `/root/.dbt`
- dbt container env uses `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`

### When to move to `PythonOperator`

Switch extraction/load tasks to `PythonOperator` when scripts are refactored to:

1. Expose callable functions (for example, `main()` with explicit args)
2. Use absolute/config-driven paths (no cwd dependence)
3. Remove runtime path hacks and implicit `load_dotenv()` assumptions
4. Be packaged/importable from the Airflow runtime image

At that stage, `PythonOperator` becomes the better long-term practice for maintainability and Airflow-native features.

### What is `/workspace`?

`/workspace` is a Docker bind mount defined in `docker-compose.yml`:

```yaml
volumes:
  - ./:/workspace
```

This maps the **entire project root** on the host (`./`) to `/workspace` inside the Airflow containers. The result:

| Host path | Container path |
|---|---|
| `./load/load_stocks.py` | `/workspace/load/load_stocks.py` |
| `./load/load_news.py` | `/workspace/load/load_news.py` |
| `./extract/collect_api_data.py` | `/workspace/extract/collect_api_data.py` |
| `./data/` | `/workspace/data/` |
| `./models/` | `/workspace/models/` |
| `./dbt/` | `/workspace/dbt/` |

That's why every `BashOperator` command starts with `cd /workspace && ...` — it sets the working directory so that relative paths, imports (`from models.schemas import ...`), and data file references all resolve correctly, just like running locally.

### Is mounting `/workspace` best practice?

| Approach | When to use |
|---|---|
| Mount `/workspace` | Local dev, small teams, learning |
| Package scripts into the Docker image (`COPY`) | Staging/production — immutable, versioned |
| Use Airflow connections + operators | Production — `PostgresOperator`, `HttpOperator` instead of raw scripts |
| Dedicated dbt container (`DockerOperator`) | Run dbt in its own isolated container |

**Typical evolution path:**

1. `BashOperator` + mounted volume (current — works, fast iteration)
2. `PythonOperator` with refactored modules baked into the image
3. `DockerOperator` / `KubernetesPodOperator` to isolate each step in its own container

### Other decisions

- **Web scraping stays external** — Selenium requires a browser, not practical inside Airflow containers. The news DAG picks up whatever CSVs are available.
- **`POSTGRES_HOST=database`** is injected via `env` so scripts connect through Docker's network.
- **dbt uses `--profiles-dir /root/.dbt`** (mounted from `HOST_DBT_PROFILES_DIR`) to find `profiles.yml`.
- **Tests run as a final task** — if dbt tests fail, the DAG run is marked as failed.
