"""Database loading and pipeline audit execution module."""

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import Config, setup_logger

logger = setup_logger("load")


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Create and return a SQLAlchemy engine with connection pool settings."""
    url = db_url or Config.get_database_url()
    return create_engine(url, pool_pre_ping=True)


def record_pipeline_run(
    engine: Engine,
    run_id: str,
    started_at: datetime,
    status: str,
    records_processed: int,
    records_accepted: int,
    records_rejected: int,
    records_loaded: int,
    completed_at: Optional[datetime] = None,
    error_summary: Optional[str] = None,
) -> None:
    """Insert or update audit record in the pipeline_runs table."""
    is_sqlite = engine.dialect.name == "sqlite"
    
    if is_sqlite:
        upsert_query = text("""
            INSERT INTO pipeline_runs (
                run_id, started_at, completed_at, status, 
                records_processed, records_accepted, records_rejected, records_loaded, error_summary
            ) VALUES (
                :run_id, :started_at, :completed_at, :status,
                :records_processed, :records_accepted, :records_rejected, :records_loaded, :error_summary
            ) ON CONFLICT(run_id) DO UPDATE SET
                completed_at = :completed_at,
                status = :status,
                records_processed = :records_processed,
                records_accepted = :records_accepted,
                records_rejected = :records_rejected,
                records_loaded = :records_loaded,
                error_summary = :error_summary;
        """)
    else:
        upsert_query = text("""
            INSERT INTO pipeline_runs (
                run_id, started_at, completed_at, status, 
                records_processed, records_accepted, records_rejected, records_loaded, error_summary
            ) VALUES (
                :run_id, :started_at, :completed_at, :status,
                :records_processed, :records_accepted, :records_rejected, :records_loaded, :error_summary
            ) ON DUPLICATE KEY UPDATE
                completed_at = VALUES(completed_at),
                status = VALUES(status),
                records_processed = VALUES(records_processed),
                records_accepted = VALUES(records_accepted),
                records_rejected = VALUES(records_rejected),
                records_loaded = VALUES(records_loaded),
                error_summary = VALUES(error_summary);
        """)

    with engine.begin() as conn:
        conn.execute(
            upsert_query,
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": completed_at,
                "status": status,
                "records_processed": records_processed,
                "records_accepted": records_accepted,
                "records_rejected": records_rejected,
                "records_loaded": records_loaded,
                "error_summary": error_summary,
            },
        )


def load_validated_data(
    valid_df: pd.DataFrame,
    engine: Optional[Engine] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load validated marketing data into MySQL (or SQLite) tables with transaction safety.

    Upserts into:
    1. campaigns (dimensions: campaign_id, campaign_name, channel)
    2. campaign_metrics (facts: record_id, campaign_id, report_date, metrics...)

    Args:
        valid_df: DataFrame containing validated records.
        engine: Optional SQLAlchemy engine.
        run_id: Execution run identifier.

    Returns:
        Dict[str, Any]: Summary of loaded records.
    """
    db_engine = engine or get_engine()
    is_sqlite = db_engine.dialect.name == "sqlite"
    logger.info(f"Loading {len(valid_df)} validated records into database ({db_engine.dialect.name})")

    if valid_df.empty:
        logger.warning("No validated records to load")
        return {"campaigns_loaded": 0, "metrics_loaded": 0}

    # Extract unique campaigns
    campaigns_df = valid_df[["campaign_id", "campaign_name", "channel"]].drop_duplicates(
        subset=["campaign_id"], keep="last"
    )

    campaigns_loaded = 0
    metrics_loaded = 0

    try:
        with db_engine.begin() as conn:
            # 1. Upsert campaigns
            if is_sqlite:
                campaign_sql = text("""
                    INSERT INTO campaigns (campaign_id, campaign_name, channel)
                    VALUES (:campaign_id, :campaign_name, :channel)
                    ON CONFLICT(campaign_id) DO UPDATE SET
                        campaign_name = :campaign_name,
                        channel = :channel;
                """)
            else:
                campaign_sql = text("""
                    INSERT INTO campaigns (campaign_id, campaign_name, channel)
                    VALUES (:campaign_id, :campaign_name, :channel)
                    ON DUPLICATE KEY UPDATE
                        campaign_name = VALUES(campaign_name),
                        channel = VALUES(channel);
                """)

            campaign_records = campaigns_df.to_dict(orient="records")
            conn.execute(campaign_sql, campaign_records)
            campaigns_loaded = len(campaign_records)
            logger.info(f"Upserted {campaigns_loaded} unique campaigns")

            # 2. Upsert metrics
            if is_sqlite:
                metrics_sql = text("""
                    INSERT INTO campaign_metrics (
                        record_id, campaign_id, report_date, impressions, clicks,
                        conversions, spend, revenue, ctr, conversion_rate, cost_per_conversion, roas
                    ) VALUES (
                        :record_id, :campaign_id, :report_date, :impressions, :clicks,
                        :conversions, :spend, :revenue, :ctr, :conversion_rate, :cost_per_conversion, :roas
                    ) ON CONFLICT(record_id) DO UPDATE SET
                        campaign_id = :campaign_id,
                        report_date = :report_date,
                        impressions = :impressions,
                        clicks = :clicks,
                        conversions = :conversions,
                        spend = :spend,
                        revenue = :revenue,
                        ctr = :ctr,
                        conversion_rate = :conversion_rate,
                        cost_per_conversion = :cost_per_conversion,
                        roas = :roas;
                """)
            else:
                metrics_sql = text("""
                    INSERT INTO campaign_metrics (
                        record_id, campaign_id, report_date, impressions, clicks,
                        conversions, spend, revenue, ctr, conversion_rate, cost_per_conversion, roas
                    ) VALUES (
                        :record_id, :campaign_id, :report_date, :impressions, :clicks,
                        :conversions, :spend, :revenue, :ctr, :conversion_rate, :cost_per_conversion, :roas
                    ) ON DUPLICATE KEY UPDATE
                        campaign_id = VALUES(campaign_id),
                        report_date = VALUES(report_date),
                        impressions = VALUES(impressions),
                        clicks = VALUES(clicks),
                        conversions = VALUES(conversions),
                        spend = VALUES(spend),
                        revenue = VALUES(revenue),
                        ctr = VALUES(ctr),
                        conversion_rate = VALUES(conversion_rate),
                        cost_per_conversion = VALUES(cost_per_conversion),
                        roas = VALUES(roas);
                """)

            # Prepare records dict, converting pandas nulls to python None
            metrics_records = []
            for _, row in valid_df.iterrows():
                metrics_records.append({
                    "record_id": str(row["record_id"]),
                    "campaign_id": str(row["campaign_id"]),
                    "report_date": str(row["report_date"]),
                    "impressions": int(row["impressions"]),
                    "clicks": int(row["clicks"]),
                    "conversions": int(row["conversions"]),
                    "spend": float(row["spend"]),
                    "revenue": float(row["revenue"]),
                    "ctr": float(row["ctr"]) if pd.notna(row.get("ctr")) else None,
                    "conversion_rate": float(row["conversion_rate"]) if pd.notna(row.get("conversion_rate")) else None,
                    "cost_per_conversion": float(row["cost_per_conversion"]) if pd.notna(row.get("cost_per_conversion")) else None,
                    "roas": float(row["roas"]) if pd.notna(row.get("roas")) else None,
                })

            conn.execute(metrics_sql, metrics_records)
            metrics_loaded = len(metrics_records)
            logger.info(f"Upserted {metrics_loaded} campaign metric rows successfully")

    except Exception as e:
        logger.error(f"Database load transaction failed: {e}")
        raise

    return {
        "campaigns_loaded": campaigns_loaded,
        "metrics_loaded": metrics_loaded,
    }
