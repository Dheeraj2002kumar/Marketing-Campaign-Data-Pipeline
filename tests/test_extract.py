"""Unit tests for data extraction module."""

import pytest
import pandas as pd
from pathlib import Path
from src.extract import extract_from_csv, ExtractionError


def test_extract_valid_csv(tmp_path: Path):
    """Test extracting data from a valid CSV file."""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(
        "record_id,campaign_id,campaign_name,channel,report_date,impressions,clicks,conversions,spend,revenue\n"
        "R1,C1,Summer Sale,Email,2026-09-01,1000,100,10,50.00,200.00\n"
    )

    df = extract_from_csv(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "source_file" in df.attrs
    assert "extracted_at" in df.attrs
    assert df.iloc[0]["record_id"] == "R1"


def test_extract_missing_file():
    """Test extracting from a non-existent path raises ExtractionError."""
    with pytest.raises(ExtractionError, match="file does not exist"):
        extract_from_csv("non_existent_file.csv")


def test_extract_empty_file(tmp_path: Path):
    """Test extracting an empty file raises ExtractionError."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")

    with pytest.raises(ExtractionError, match="file is empty"):
        extract_from_csv(empty_file)


def test_extract_missing_required_columns(tmp_path: Path):
    """Test extracting a CSV missing required columns raises ExtractionError."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("record_id,campaign_id\nR1,C1\n")

    with pytest.raises(ExtractionError, match="missing required columns"):
        extract_from_csv(bad_csv)
