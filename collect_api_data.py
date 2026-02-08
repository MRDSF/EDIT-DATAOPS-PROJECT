import requests
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import date

load_dotenv()
symbol = "TSLA" #BCP.LS
company = "tesla"


def fetch_data():
    try:
        api_key = os.getenv("api_key")

        url = "https://www.alphavantage.co/query"

        params = {
        "function": "TIME_SERIES_MONTHLY_ADJUSTED",
        "symbol": symbol, 
        "apikey": api_key,
        "datatype": "json",
        }


        response = requests.get(url=url, params=params)
        response.raise_for_status() # Raise an error for bad status codes

        data = response.json()
        if "Monthly Adjusted Time Series" not in data:
                raise ValueError(f"Not expected response: keys={list(data.keys())[:10]}") # Check if the expected key is in the response

        time_series = data["Monthly Adjusted Time Series"]

        df = pd.DataFrame.from_dict(time_series, orient='index') # index é a data e os valores são as colunas
        df = df.reset_index().rename(columns={"index": "date"}) # renomear a coluna do índice para "date" e resetar o índice para um índice numérico

        # Renomear as colunas para nomes mais amigáveis
        df.columns = [
            "date", "open", "high", "low", "close", 
            "adjusted_close", "volume", "dividend_amount", 
        ]

        df = df.sort_index() # Orderna pelo indice numerico (apenas para visualização)
        df["date"] = pd.to_datetime(df["date"]) # Converte a coluna de data para o formato datetime (estava como string) 2026-01-30 00:00:00

        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Exception Message Found: {e}")
        raise e 


def save_to_json(df):
    os.makedirs("./data/stocks", exist_ok=True) # Create data directory if it doesn't exist
    file_path = f"./data/stocks/stocks_data_{company}_{date.today()}.json" # File path with current date
    df.to_json(file_path, orient="records", date_format="iso") # Save DataFrame to JSON (orient="records" creates a list of records each line as a JSON object)
    print(f"Data saved to {file_path}")

if __name__ == "__main__":
    extracted_data = fetch_data()
    save_to_json(extracted_data)