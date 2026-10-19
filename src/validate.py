"""Data quality validation module implementing FR-03 rules."""

from typing import Tuple, List
import pandas as pd

from src.config import setup_logger

logger = setup_logger("validate")


def validate_records(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate transformed marketing records against business rules and constraints.

    Rules checked:
    1. Required fields presence (record_id, campaign_id, campaign_name, channel, report_date).
    2. Duplicate record_id detection.
    3. Invalid or unparseable report_date.
    4. Non-numeric or missing metrics.
    5. Negative metrics (impressions, clicks, conversions, spend, revenue < 0).
    6. Relational business consistency: clicks cannot exceed impressions.
    7. Relational business consistency: conversions cannot exceed clicks.

    Args:
        df: Transformed Pandas DataFrame.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (valid_df, rejected_df)
    """
    logger.info(f"Initiating validation on {len(df)} records")

    rejection_reasons: List[List[str]] = [[] for _ in range(len(df))]
    seen_record_ids = set()

    for idx, row in df.iterrows():
        reasons = rejection_reasons[idx]

        # 1. Missing required string fields
        record_id = str(row.get("record_id", "")).strip()
        campaign_id = str(row.get("campaign_id", "")).strip()
        campaign_name = str(row.get("campaign_name", "")).strip()
        channel = str(row.get("channel", "")).strip()

        if not record_id:
            reasons.append("Missing required field: record_id")
        if not campaign_id:
            reasons.append("Missing required field: campaign_id")
        if not campaign_name:
            reasons.append("Missing required field: campaign_name")
        if not channel:
            reasons.append("Missing required field: channel")

        # 2. Duplicate record_id check
        if record_id:
            if record_id in seen_record_ids:
                reasons.append(f"Duplicate record_id: '{record_id}' already seen in batch")
            else:
                seen_record_ids.add(record_id)

        # 3. Invalid report_date check
        report_date = row.get("report_date")
        if pd.isna(report_date) or not report_date:
            raw_date = row.get("raw_report_date", "missing")
            reasons.append(f"Invalid or missing report_date: '{raw_date}'")

        # 4. Numeric metric existence & non-negativity checks
        impressions = row.get("impressions")
        clicks = row.get("clicks")
        conversions = row.get("conversions")
        spend = row.get("spend")
        revenue = row.get("revenue")

        if pd.isna(impressions):
            reasons.append(f"Non-numeric impressions value: '{row.get('raw_impressions', '')}'")
        elif impressions < 0:
            reasons.append(f"Negative impressions not allowed: {impressions}")

        if pd.isna(clicks):
            reasons.append(f"Non-numeric clicks value: '{row.get('raw_clicks', '')}'")
        elif clicks < 0:
            reasons.append(f"Negative clicks not allowed: {clicks}")

        if pd.isna(conversions):
            reasons.append(f"Non-numeric conversions value: '{row.get('raw_conversions', '')}'")
        elif conversions < 0:
            reasons.append(f"Negative conversions not allowed: {conversions}")

        if pd.isna(spend):
            reasons.append(f"Non-numeric spend value: '{row.get('raw_spend', '')}'")
        elif spend < 0:
            reasons.append(f"Negative spend not allowed: {spend}")

        if pd.isna(revenue):
            reasons.append(f"Non-numeric revenue value: '{row.get('raw_revenue', '')}'")
        elif revenue < 0:
            reasons.append(f"Negative revenue not allowed: {revenue}")

        # 5. Relational consistency checks
        if not pd.isna(impressions) and not pd.isna(clicks):
            if impressions >= 0 and clicks >= 0 and clicks > impressions:
                reasons.append(f"Metric violation: clicks ({clicks}) cannot exceed impressions ({impressions})")

        if not pd.isna(clicks) and not pd.isna(conversions):
            if clicks >= 0 and conversions >= 0 and conversions > clicks:
                reasons.append(f"Metric violation: conversions ({conversions}) cannot exceed clicks ({clicks})")

    # Split into valid and rejected DataFrames
    rejected_mask = [len(r) > 0 for r in rejection_reasons]
    valid_mask = [not m for m in rejected_mask]

    # Target columns for database loading
    target_columns = [
        "record_id",
        "campaign_id",
        "campaign_name",
        "channel",
        "report_date",
        "impressions",
        "clicks",
        "conversions",
        "spend",
        "revenue",
        "ctr",
        "conversion_rate",
        "cost_per_conversion",
        "roas",
    ]

    valid_df = df[valid_mask].copy()
    valid_cols = [c for c in target_columns if c in valid_df.columns]
    valid_df = valid_df[valid_cols]

    # Cast integer columns safely
    for col in ["impressions", "clicks", "conversions"]:
        if col in valid_df.columns:
            valid_df[col] = valid_df[col].astype(int)

    # Prepare rejected DataFrame with reasons
    rejected_df = df[rejected_mask].copy()
    rejected_reasons_filtered = ["; ".join(reasons) for reasons, is_rej in zip(rejection_reasons, rejected_mask) if is_rej]
    rejected_df["rejection_reason"] = rejected_reasons_filtered

    # Clean up temporary raw_* columns if present in rejected_df
    cleaned_rejected_cols = [c for c in rejected_df.columns if not c.startswith("raw_")]
    rejected_df = rejected_df[cleaned_rejected_cols]

    logger.info(
        f"Validation complete. Total: {len(df)}, Valid: {len(valid_df)}, Rejected: {len(rejected_df)}"
    )

    return valid_df, rejected_df
