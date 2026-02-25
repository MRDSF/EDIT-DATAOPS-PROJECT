# Airflow

## How to run

Make sure the containers are up:

```bash
docker-compose up -d
```

## Access

- **URL:** http://localhost:8080
- **Username:** `admin`
- **Password:** `admin`

## Create admin user (if needed)

```bash
docker exec airflow_webserver_dataops airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

## Services

| Container | Description |
|---|---|
| `airflow_init_dataops` | Runs `airflow db migrate` and exits |
| `airflow_webserver_dataops` | Web UI (port 8080) |
| `airflow_scheduler_dataops` | Scheduler that triggers DAGs |

## Structure

```
airflow/
├── Dockerfile
├── requirements.txt # In case airflow needs to use specific libs
├── dags/            # Airflow DAGs
├── logs/            # Execution logs
└── plugins/         # Custom plugins
```

## Why a Custom Dockerfile

The official `apache/airflow` image is designed to be lightweight. Any extra Python libraries your DAGs or operators require (e.g. `pandas`, `sqlalchemy`, `requests`, `dbt`) must be installed inside the container.

Using a `requirements.txt` allows you to version-control your Python dependencies.

### How to build a custom Airflow image

A simple example:

```dockerfile
# Start from the official Airflow image
FROM apache/airflow:2.10.3-python3.11

# Switch to root to install packages
USER root

# Copy your requirements.txt into the container
COPY requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Switch back to airflow user
USER airflow
```

Then, in your `docker-compose.yml` for Airflow services:

```yaml
build:
  context: ./airflow
  dockerfile: Dockerfile
```

And keep a `requirements.txt` like:

```
pandas==2.1.0
requests
dbt-postgres==1.8.0
```

### Best Practices

- Use pinned versions (`package==version`) to avoid breaking changes
- Install system dependencies in the Dockerfile if needed (`apt-get install ...`)
- Keep the image lightweight by cleaning caches (`pip install --no-cache-dir`)
- Rebuild the image whenever you update `requirements.txt`
