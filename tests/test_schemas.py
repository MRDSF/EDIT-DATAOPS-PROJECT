import pytest
from models.schemas import MonthlyBar, ApiResponse


class TestMonthlyBar:
    """Tests for the MonthlyBar Pydantic model."""

    def test_parse_valid_bar(self):
        """MonthlyBar should correctly parse aliased API fields."""
        raw = {
            "1. open": "250.00",
            "2. high": "260.50",
            "3. low": "245.30",
            "4. close": "258.75",
            "5. adjusted close": "258.75",
            "6. volume": "12345678",
            "7. dividend amount": "0.00",
        }
        bar = MonthlyBar(**raw)

        assert bar.open == 250.00
        assert bar.high == 260.50
        assert bar.low == 245.30
        assert bar.close == 258.75
        assert bar.adjusted_close == 258.75
        assert bar.volume == 12345678
        assert bar.dividend_amount == 0.00

    def test_missing_field_raises(self):
        """MonthlyBar should reject incomplete data."""
        raw = {
            "1. open": "250.00",
            "2. high": "260.50",
        }
        with pytest.raises(Exception):
            MonthlyBar(**raw)


class TestApiResponse:
    """Tests for the ApiResponse Pydantic model."""

    def test_parse_full_response(self):
        """ApiResponse should correctly map 'Monthly Adjusted Time Series'."""
        raw = {
            "Monthly Adjusted Time Series": {
                "2025-01-31": {
                    "1. open": "100.00",
                    "2. high": "110.00",
                    "3. low": "95.00",
                    "4. close": "105.00",
                    "5. adjusted close": "105.00",
                    "6. volume": "9999999",
                    "7. dividend amount": "0.50",
                },
            }
        }
        resp = ApiResponse(**raw)

        assert "2025-01-31" in resp.series
        assert resp.series["2025-01-31"].close == 105.00
        assert resp.series["2025-01-31"].volume == 9999999
