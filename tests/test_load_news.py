import pandas as pd


class TestNewsDataValidation:
    """Tests for the CSV column-validation logic used in load_news.py."""

    REQUIRED_COLUMNS = ["date", "title", "link", "source"]

    def test_valid_csv_has_no_missing_columns(self):
        """A DataFrame with all required columns should pass validation."""
        df = pd.DataFrame(
            {
                "date": ["2025-01-01"],
                "title": ["Tesla news headline"],
                "link": ["https://example.com/article"],
                "source": ["euronews"],
            }
        )
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        assert missing == []

    def test_missing_column_detected(self):
        """Validation should detect a missing required column."""
        df = pd.DataFrame(
            {
                "date": ["2025-01-01"],
                "title": ["Tesla news headline"],
                # 'link' and 'source' are missing
            }
        )
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        assert "link" in missing
        assert "source" in missing
