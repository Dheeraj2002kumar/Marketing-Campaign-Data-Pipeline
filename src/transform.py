"""Data transformation and standardization module for marketing data."""

from typing import Dict
import pandas as pd
import numpy as np

from src.config import setup_logger

logger = setup_logger("transform")

CHANNEL_MAPPINGS: Dict[str, str] = {
    "email": "Email",
    "social": "Social Media",
    "social media": "Social Media",
    "social_media": "Social Media",
    "search": "Search Ads",
    "search ads": "Search Ads",
    "search_ads": "Search Ads",
    "display": "Display Ads",
    "display ads": "Display Ads",
    "display_ads": "Display Ads",
    "influencer": "Influencer",
    "affiliate": "Affiliate",
    "video": "Video Ads",
    "video ads": "Video Ads",
}


def normalize_channel(channel: str) -> str:
    """Standardize channel names into a canonical format."""
    if pd.isna(channel):
        return ""
    cleaned = str(channel).strip().lower()
    return CHANNEL_MAPPINGS.get(cleaned, str(channel).strip().title())


def clean_text_field(val: any) -> str:
    """Trim whitespaces and convert nulls to empty string."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def parse_date_safe(val: any) -> any:
    """Attempt parsing date into standard YYYY-MM-DD string, returning None on failure."""
    if pd.isna(val) or not str(val).strip():
        return None
    try:
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return None


def transform_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names, clean text fields, normalize dates and channels,
    convert numeric fields, and compute derived marketing metrics.

    Args:
        raw_df: Raw Pandas DataFrame extracted from CSV or API.

    Returns:
        pd.DataFrame: Cleaned and structured DataFrame ready for validation.
    """
    logger.info(f"Starting transformation for {len(raw_df)} records")
    df = raw_df.copy()

    # Preserve any attributes
    attrs = dict(df.attrs)

    # 1. Standardize column names (lowercase, stripped, replace spaces with underscores)
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    # 2. Clean text fields (trim whitespace)
    text_columns = ["record_id", "campaign_id", "campaign_name", "channel"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text_field)

    # 3. Normalize channel names
    if "channel" in df.columns:
        df["channel"] = df["channel"].apply(normalize_channel)

    # 4. Standardize dates
    if "report_date" in df.columns:
        # Keep raw string for date validation check, and parsed date column
        df["raw_report_date"] = df["report_date"]
        df["report_date"] = df["report_date"].apply(parse_date_safe)

    # 5. Convert numeric columns safely to numeric types (invalid entries become NaN)
    numeric_int_cols = ["impressions", "clicks", "conversions"]
    for col in numeric_int_cols:
        if col in df.columns:
            df[f"raw_{col}"] = df[col]
            df[col] = pd.to_numeric(df[col], errors="coerce")

    numeric_float_cols = ["spend", "revenue"]
    for col in numeric_float_cols:
        if col in df.columns:
            df[f"raw_{col}"] = df[col]
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Calculate derived business metrics where inputs are valid
    # CTR (Click-Through Rate): clicks / impressions * 100
    df["ctr"] = np.where(
        (df["impressions"] > 0) & (df["clicks"] >= 0),
        np.round((df["clicks"] / df["impressions"]) * 100, 4),
        None,
    )

    # Conversion Rate: conversions / clicks * 100
    df["conversion_rate"] = np.where(
        (df["clicks"] > 0) & (df["conversions"] >= 0),
        np.round((df["conversions"] / df["clicks"]) * 100, 4),
        None,
    )

    # Cost Per Conversion: spend / conversions
    df["cost_per_conversion"] = np.where(
        (df["conversions"] > 0) & (df["spend"] >= 0),
        np.round(df["spend"] / df["conversions"], 2),
        None,
    )

    # ROAS (Return On Ad Spend): revenue / spend
    df["roas"] = np.where(
        (df["spend"] > 0) & (df["revenue"] >= 0),
        np.round(df["revenue"] / df["spend"], 2),
        None,
    )

    df.attrs = attrs
    logger.info(f"Transformation complete for {len(df)} records")
    return df
