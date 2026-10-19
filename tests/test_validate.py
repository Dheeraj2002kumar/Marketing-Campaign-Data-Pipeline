"""Unit tests for data validation module."""

import pandas as pd
from src.transform import transform_data
from src.validate import validate_records


def test_validate_clean_records():
    """Verify clean record passes validation."""
    raw = pd.DataFrame([
        {
            "record_id": "REC-01",
            "campaign_id": "CMP-01",
            "campaign_name": "Valid Campaign",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "1000",
            "clicks": "100",
            "conversions": "10",
            "spend": "50.00",
            "revenue": "200.00",
        }
    ])

    transformed = transform_data(raw)
    valid_df, rejected_df = validate_records(transformed)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0


def test_validate_negative_metrics():
    """Verify negative metrics trigger rejection."""
    raw = pd.DataFrame([
        {
            "record_id": "REC-02",
            "campaign_id": "CMP-01",
            "campaign_name": "Bad Spend",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "1000",
            "clicks": "100",
            "conversions": "10",
            "spend": "-50.00",
            "revenue": "200.00",
        }
    ])

    transformed = transform_data(raw)
    valid_df, rejected_df = validate_records(transformed)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert "Negative spend not allowed" in rejected_df.iloc[0]["rejection_reason"]


def test_validate_funnel_consistency():
    """Verify clicks > impressions or conversions > clicks fail validation."""
    raw = pd.DataFrame([
        {
            "record_id": "REC-03",
            "campaign_id": "CMP-01",
            "campaign_name": "Clicks Exceed Impressions",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "500",
            "clicks": "800",
            "conversions": "10",
            "spend": "50.00",
            "revenue": "200.00",
        },
        {
            "record_id": "REC-04",
            "campaign_id": "CMP-02",
            "campaign_name": "Conversions Exceed Clicks",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "1000",
            "clicks": "50",
            "conversions": "70",
            "spend": "50.00",
            "revenue": "200.00",
        }
    ])

    transformed = transform_data(raw)
    valid_df, rejected_df = validate_records(transformed)

    assert len(valid_df) == 0
    assert len(rejected_df) == 2
    assert "clicks (800) cannot exceed impressions (500)" in rejected_df.iloc[0]["rejection_reason"]
    assert "conversions (70) cannot exceed clicks (50)" in rejected_df.iloc[1]["rejection_reason"]


def test_validate_duplicate_records():
    """Verify duplicate record_ids are detected and rejected."""
    raw = pd.DataFrame([
        {
            "record_id": "REC-DUP",
            "campaign_id": "CMP-01",
            "campaign_name": "Campaign First",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "1000",
            "clicks": "100",
            "conversions": "10",
            "spend": "50.00",
            "revenue": "200.00",
        },
        {
            "record_id": "REC-DUP",
            "campaign_id": "CMP-01",
            "campaign_name": "Campaign Duplicate",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "1000",
            "clicks": "100",
            "conversions": "10",
            "spend": "50.00",
            "revenue": "200.00",
        }
    ])

    transformed = transform_data(raw)
    valid_df, rejected_df = validate_records(transformed)

    assert len(valid_df) == 1
    assert len(rejected_df) == 1
    assert "Duplicate record_id: 'REC-DUP'" in rejected_df.iloc[0]["rejection_reason"]


def test_validate_missing_required_fields():
    """Verify missing campaign_id or record_id triggers rejection."""
    raw = pd.DataFrame([
        {
            "record_id": "",
            "campaign_id": "CMP-01",
            "campaign_name": "Missing Record ID",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "1000",
            "clicks": "100",
            "conversions": "10",
            "spend": "50.00",
            "revenue": "200.00",
        }
    ])

    transformed = transform_data(raw)
    valid_df, rejected_df = validate_records(transformed)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert "Missing required field: record_id" in rejected_df.iloc[0]["rejection_reason"]
