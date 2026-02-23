import requests
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import date
from models.schemas import ApiResponse
from pydantic import ValidationError
import json

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


        if "Monthly Adjusted Time Series" not in data:
            raise ValueError(f"Unexpected API response: {data}") # If the expected key is not present, raise a ValueError with the full API response to help with debugging

        # Validate with Pydantic; if invalid, raises a ValidationError
        try:
            parsed = ApiResponse.model_validate(data) # Validates that the data matches the expected types / is "convertible"
        except ValidationError as e:
            with open("debug_api_payload.json", "w") as f:
                json.dump(data, f, indent=2)

            raise ValueError(f"Invalid API response: {e} \n Payload saved to debug_api_payload.json") from e
        
        #time_series = parsed.series  # <-- already validated with Pydantic, now just grab the data series

        time_series = data["Monthly Adjusted Time Series"]
    

        df = pd.DataFrame.from_dict(time_series, orient='index') # index is the date and values are the columns
        df = df.reset_index().rename(columns={"index": "date"}) # rename the index column to "date" and reset to a numeric index

        df.columns = [
            "date", "open", "high", "low", "close", 
            "adjusted_close", "volume", "dividend_amount", 
        ]
        
        df["date"] = pd.to_datetime(df["date"]) # Convert the date column to datetime format (was string) e.g. 2026-01-30 00:00:00
        df = df.sort_values("date", ascending=False) # Sort data by date in descending order (most recent first)

        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Exception Message Found: {e}")
        raise e 


def save_to_json(df):
    os.makedirs("./data/stocks", exist_ok=True) # Create data directory if it doesn't exist
    file_path = f"./data/stocks/stocks_data_{company}.json" # File path with current date
    df.to_json(file_path, orient="records", date_format="iso") # Save DataFrame to JSON (orient="records" creates a list of records each line as a JSON object)
    print(f"Data saved to {file_path}")

if __name__ == "__main__":
    extracted_data = fetch_data()
    save_to_json(extracted_data)
