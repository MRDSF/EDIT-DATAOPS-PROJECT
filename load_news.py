import os
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

# ----------------------
# Database configuration
# ----------------------
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# --------------------
# Files folder
# --------------------
DATA_DIR = "./data/tesla_news"
TABLE_NAME = "bronze_news"

REQUIRED_COLUMNS = ["date", "title", "link", "source"]
CHUNK_SIZE = 50_000  # ajusta: 10_000 / 50_000 / 100_000 dependendo do tamanho dos arquivos e da memória disponível


def ensure_table(conn):
    with conn.cursor() as cur:
        
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
              id          bigserial PRIMARY KEY,
              date_raw    text,
              title       text,
              link        text,
              source      text,
              file_name   text NOT NULL,
              ingested_at timestamptz DEFAULT now()
            );
        """)

        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS bronze_news_dedupe
            ON bronze_news (source, title, date_raw);
        """)

    conn.commit()

def upload_all_csvs_to_raw(data_dir, conn):
    csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv"))) # gets a list of all CSV files in the data directory (ex: ["data/tesla_news/file1.csv", "data/tesla_news/file2.csv", ...])
    if not csv_files:
        print("No CSV files found.")
        return

    ensure_table(conn)

    total = 0
    for csv_file in csv_files:
        file_name = os.path.basename(csv_file)

        try:
            # iterator de chunks
            df_iter = pd.read_csv(csv_file, dtype=str, chunksize=CHUNK_SIZE) # Controls the number of rows read into memory at once (adjust as needed) (iterator that reads the CSV file in chunks, treating all columns as strings)
            
            file_total = 0
            for df in df_iter:
                missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
                if missing:
                    raise ValueError(f"{file_name} missing columns: {missing}")

                df = df[REQUIRED_COLUMNS].copy()
                df = df.rename(columns={"date": "date_raw"})
                df["file_name"] = file_name

                # limpeza simples
                df = df.astype("string").apply(lambda s: s.str.strip())
                df = df.dropna(how="all", subset=["date_raw", "title", "link", "source"])

                if df.empty:
                    continue

                rows = df[["date_raw", "title", "link", "source", "file_name"]].itertuples(index=False, name=None)

                with conn.cursor() as cur:
                    execute_values(
                        cur,
                        f"""
                        INSERT INTO {TABLE_NAME} (date_raw, title, link, source, file_name)
                        VALUES %s
                        ON CONFLICT (source, title, date_raw) DO NOTHING
                        """,
                        rows,
                        page_size=5000 # Controls the batch size for the insert operation (one insert per 5000 rows, adjust as needed)
                    )

                conn.commit()
                n = len(df)
                file_total += n
                total += n

            print(f"Loaded {file_name} ({file_total} rows)")

        except Exception as e:
            conn.rollback()
            print(f"Error in {file_name}: {e}")

    print(f"Finished: {total} rows loaded.")

def main():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        print("Connection with database established.")

        upload_all_csvs_to_raw(DATA_DIR, conn)

    except Exception as e:
        print(f"Error trying to connect to database: {e}")

    finally:
        if conn:
            conn.close()
            print("Connection with database closed.")

if __name__ == "__main__":
    main()
