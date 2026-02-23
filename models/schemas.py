from pydantic import BaseModel, Field
from typing import Dict


class MonthlyBar(BaseModel):
    open: float = Field(alias="1. open") # Alias is needed because the API JSON keys have a specific format (e.g. "1. open", "2. high") that is not a valid Python attribute name. Field with alias maps these keys to friendlier Python attributes.
    high: float = Field(alias="2. high")
    low: float = Field(alias="3. low")
    close: float = Field(alias="4. close")
    adjusted_close: float = Field(alias="5. adjusted close")
    volume: int = Field(alias="6. volume")
    dividend_amount: float = Field(alias="7. dividend amount")


class ApiResponse(BaseModel):
    series: Dict[str, MonthlyBar] = Field( # Dict[str, MonthlyBar] means the key is a string (representing the date) and the value is a MonthlyBar object. Field with alias maps the "Monthly Adjusted Time Series" JSON key to the "series" attribute.
        alias="Monthly Adjusted Time Series"
    )
