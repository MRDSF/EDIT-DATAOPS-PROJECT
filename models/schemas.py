from pydantic import BaseModel, Field
from typing import Dict


class MonthlyBar(BaseModel):
    open: float = Field(alias="1. open")
    high: float = Field(alias="2. high")
    low: float = Field(alias="3. low")
    close: float = Field(alias="4. close")
    adjusted_close: float = Field(alias="5. adjusted close")
    volume: int = Field(alias="6. volume")
    dividend_amount: float = Field(alias="7. dividend amount")


class ApiResponse(BaseModel):
    series: Dict[str, MonthlyBar] = Field(
        alias="Monthly Adjusted Time Series"
    )
