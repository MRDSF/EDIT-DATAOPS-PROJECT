from pydantic import BaseModel, Field
from typing import Dict


class MonthlyBar(BaseModel):
    open: float = Field(alias="1. open") # O alias é necessário porque as chaves do JSON da API têm um formato específico (ex: "1. open", "2. high", etc.) que não é um nome de atributo Python válido. O Field com alias permite mapear essas chaves para atributos Python mais amigáveis.
    high: float = Field(alias="2. high")
    low: float = Field(alias="3. low")
    close: float = Field(alias="4. close")
    adjusted_close: float = Field(alias="5. adjusted close")
    volume: int = Field(alias="6. volume")
    dividend_amount: float = Field(alias="7. dividend amount")


class ApiResponse(BaseModel):
    series: Dict[str, MonthlyBar] = Field( # O tipo Dict[str, MonthlyBar] indica que a chave é uma string (representando a data) e o valor é um objeto MonthlyBar. O Field com alias mapeia a chave "Monthly Adjusted Time Series" do JSON para o atributo "series" do modelo.
        alias="Monthly Adjusted Time Series"
    )
