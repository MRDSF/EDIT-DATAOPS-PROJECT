import os
import pandas as pd
from sqlalchemy import create_engine, text
from tqdm.auto import tqdm


# ---------- CONFIG ----------
TABLE_NAME = "raw_stock_data"
JSON_FILE = "./data/stocks/stocks_data_tesla.json"
CHUNKSIZE = 50000

PG_USER = os.getenv("POSTGRES_USER", "root")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "root")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", 5432)
PG_DB   = os.getenv("POSTGRES_DB", "stocks")


# ---------- TYPES ----------
DTYPE = {
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "adjusted_close": "float64",
    "volume": "Int64",
    "dividend_amount": "float64",
}


def main():
    engine = create_engine(
        f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    )

    # ---------- READ DATA ----------
    df = pd.read_json(JSON_FILE)

    wanted_cols = [
        "date", "open", "high", "low", "close",
        "adjusted_close", "volume", "dividend_amount"
    ]
    df = df[wanted_cols].copy()

    df["date"] = pd.to_datetime(df["date"]).dt.date

    for col, dt in DTYPE.items():
        df[col] = df[col].astype(dt)

    df["ingested_at"] = pd.Timestamp.now(tz="UTC")

    # NaN → NULL for Postgres
    df = df.where(pd.notnull(df), None)

    # ---------- INGEST ----------
    total = len(df)
    first = True

    for start in tqdm(range(0, total, CHUNKSIZE)):
        chunk = df.iloc[start : start + CHUNKSIZE]

        if first:
            # Create table
            chunk.head(0).to_sql(
                name=TABLE_NAME,
                con=engine,
                if_exists="replace",
                index=False,
            )

            # Add primary key
            with engine.begin() as conn:
                conn.execute(text(f"""
                    ALTER TABLE {TABLE_NAME}
                    ADD CONSTRAINT {TABLE_NAME}_pk PRIMARY KEY (date);
                """))

            first = False

        chunk.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=5000,
        )

    print(f"{total} rows loaded.")


if __name__ == "__main__":
    main()
