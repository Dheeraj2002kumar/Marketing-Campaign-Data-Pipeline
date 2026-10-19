"""Unit tests for data transformation module."""

import pandas as pd
from src.transform import transform_data, normalize_channel


def test_normalize_channel():
    """Verify channel standardization logic."""
    assert normalize_channel("email") == "Email"
    assert normalize_channel("EMAIL") == "Email"
    assert normalize_channel("  social media  ") == "Social Media"
    assert normalize_channel("search") == "Search Ads"
    assert normalize_channel("affiliate") == "Affiliate"
    assert normalize_channel("influencer") == "Influencer"


def test_transform_columns_and_whitespace():
    """Test standardizing column casing and trimming whitespace."""
    raw_df = pd.DataFrame([
        {
            "Record_ID": "  R100  ",
            "Campaign_ID": " C100 ",
            "Campaign_Name": "  Summer Campaign  ",
            "Channel": "  EMAIL  ",
            "Report_Date": "2026-09-01",
            "Impressions": "1000",
            "Clicks": "100",
            "Conversions": "10",
            "Spend": "50.00",
            "Revenue": "250.00",
        }
    ])

    transformed = transform_data(raw_df)

    assert "record_id" in transformed.columns
    assert transformed.iloc[0]["record_id"] == "R100"
    assert transformed.iloc[0]["campaign_id"] == "C100"
    assert transformed.iloc[0]["campaign_name"] == "Summer Campaign"
    assert transformed.iloc[0]["channel"] == "Email"
    assert transformed.iloc[0]["impressions"] == 1000
    assert transformed.iloc[0]["clicks"] == 100


def test_transform_metric_calculations():
    """Verify calculated metrics (CTR, conversion_rate, cost_per_conversion, roas)."""
    raw_df = pd.DataFrame([
        {
            "record_id": "R1",
            "campaign_id": "C1",
            "campaign_name": "Test",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "10000",
            "clicks": "500",
            "conversions": "50",
            "spend": "200.00",
            "revenue": "1000.00",
        }
    ])

    transformed = transform_data(raw_df)
    row = transformed.iloc[0]

    # CTR = 500 / 10000 * 100 = 5.0%
    assert row["ctr"] == 5.0
    # Conversion Rate = 50 / 500 * 100 = 10.0%
    assert row["conversion_rate"] == 10.0
    # Cost per conversion = 200 / 50 = 4.0
    assert row["cost_per_conversion"] == 4.0
    # ROAS = 1000 / 200 = 5.0
    assert row["roas"] == 5.0


def test_transform_zero_division_safety():
    """Verify zero denominators result in None rather than runtime exception."""
    raw_df = pd.DataFrame([
        {
            "record_id": "R2",
            "campaign_id": "C2",
            "campaign_name": "Test Zero",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": "0",
            "clicks": "0",
            "conversions": "0",
            "spend": "0.00",
            "revenue": "0.00",
        }
    ])

    transformed = transform_data(raw_df)
    row = transformed.iloc[0]

    assert row["ctr"] is None
    assert row["conversion_rate"] is None
    assert row["cost_per_conversion"] is None
    assert row["roas"] is None
