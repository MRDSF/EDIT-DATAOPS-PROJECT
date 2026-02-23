# Tests

## How to run

Run all tests:
```bash
python -m pytest tests/ -v
```

Run a specific test file:
```bash
python -m pytest tests/test_schemas.py -v
```

Run a specific test class:
```bash
python -m pytest tests/test_schemas.py::TestMonthlyBar -v
```

Run a single test:
```bash
python -m pytest tests/test_schemas.py::TestMonthlyBar::test_parse_valid_bar -v
```

## Test files

### test_schemas.py — Pydantic model tests

#### TestMonthlyBar
- **test_parse_valid_bar** — validates that aliased API fields (e.g. `"1. open"`) are correctly parsed into typed attributes
- **test_missing_field_raises** — ensures incomplete data is rejected

#### TestApiResponse
- **test_parse_full_response** — verifies the `"Monthly Adjusted Time Series"` alias mapping works end-to-end

### test_load_news.py — CSV ingestion logic tests

#### TestNewsDataValidation
- **test_valid_csv_has_no_missing_columns** — a DataFrame with all required columns passes validation
- **test_missing_column_detected** — missing columns (`link`, `source`) are correctly identified
