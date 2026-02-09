import requests
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import date
from models.schemas import ApiResponse
from pydantic import ValidationError

load_dotenv()
symbol = "TSLA"
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

        # Simular um erro de validação para testar o tratamento de erros (descomente para testar)
        # first_key = next(iter(data["Monthly Adjusted Time Series"]))

        # Valida aqui com pydantic, se não for válido, levanta um ValidationError
        try:
            parsed = ApiResponse.model_validate(data) 
        except ValidationError as e:
            raise ValueError(f"API response inválida: {e}") from e

        time_series = parsed.series  # <-- já validado com pydantic, agora é só pegar a série de dados

        # Convertendo os objetos MonthlyBar para dicionários usando model_dump com os nomes das colunas certos
        # Example: Open instead of 1. open, High instead of 2. high, etc.
        time_series = {k: v.model_dump(by_alias=False) for k, v in parsed.series.items()} 

        df = pd.DataFrame.from_dict(time_series, orient='index') # index é a data e os valores são as colunas
        df = df.reset_index().rename(columns={"index": "date"}) # renomear a coluna do índice para "date" e resetar o índice para um índice numérico

        df["date"] = pd.to_datetime(df["date"]) # Converte a coluna de data para o formato datetime (estava como string) 2026-01-30 00:00:00
        df = df.sort_values("date", ascending=False) # Ordena os dados por data em ordem crescente (do mais antigo para o mais recente)

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