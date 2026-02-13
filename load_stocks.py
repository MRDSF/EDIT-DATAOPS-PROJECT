import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()


TABLE_NAME = "bronze_stock_data"
JSON_FILE = f"./data/stocks/stocks_data_tesla.json"


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                date TEXT PRIMARY KEY,
                open TEXT,
                high TEXT,
                low TEXT,
                close TEXT,
                adjusted_close TEXT,
                volume TEXT,
                dividend_amount TEXT,
                ingested_at TIMESTAMP
            );
        """)
    conn.commit()


def load_json_to_db(conn, json_path):
    df = pd.read_json(json_path)


    # ingestion timestamp
    df["ingested_at"] = pd.Timestamp.now('UTC')

    rows = df.itertuples(index=False, name=None)

    with conn.cursor() as cur:
        execute_values(
            cur,
            f"""
            INSERT INTO {TABLE_NAME}
            (date, open, high, low, close,
             adjusted_close, volume, dividend_amount, ingested_at)
            VALUES %s
            ON CONFLICT (date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                adjusted_close = EXCLUDED.adjusted_close,
                volume = EXCLUDED.volume,
                dividend_amount = EXCLUDED.dividend_amount,
                ingested_at = EXCLUDED.ingested_at
            RETURNING 1
            """,
            rows,
            page_size=5000 # set to 5000 for better performance, adjust as needed based on the size of your data and memory constraints
        )

        num_of_rows = len(cur.fetchall())
    conn.commit()
    print(f"{num_of_rows} rows inserted/updated.")


def main():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

    create_table(conn)      
    load_json_to_db(conn, JSON_FILE)

    conn.close()


if __name__ == "__main__":
    main()
