"""Analytics and reporting module executing SQL queries and generating business reports."""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config import Config, setup_logger
from src.load import get_engine

logger = setup_logger("analytics")


ANALYTICS_QUERIES = {
    "campaign_performance_summary": """
        SELECT 
            c.campaign_id,
            c.campaign_name,
            c.channel,
            SUM(m.impressions) AS total_impressions,
            SUM(m.clicks) AS total_clicks,
            SUM(m.conversions) AS total_conversions,
            ROUND(SUM(m.spend), 2) AS total_spend,
            ROUND(SUM(m.revenue), 2) AS total_revenue,
            ROUND(SUM(m.revenue) - SUM(m.spend), 2) AS net_profit,
            ROUND(SUM(m.revenue) / NULLIF(SUM(m.spend), 0), 2) AS roas,
            ROUND((SUM(m.clicks) / NULLIF(SUM(m.impressions), 0)) * 100, 2) AS ctr_pct,
            ROUND((SUM(m.conversions) / NULLIF(SUM(m.clicks), 0)) * 100, 2) AS conversion_rate_pct
        FROM campaigns c
        INNER JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
        GROUP BY c.campaign_id, c.campaign_name, c.channel
        ORDER BY total_revenue DESC;
    """,
    "campaign_conversion_rankings": """
        SELECT 
            DENSE_RANK() OVER (ORDER BY SUM(m.conversions) DESC) AS conversion_rank,
            c.campaign_id,
            c.campaign_name,
            c.channel,
            SUM(m.conversions) AS total_conversions,
            ROUND(SUM(m.spend), 2) AS total_spend,
            ROUND(SUM(m.spend) / NULLIF(SUM(m.conversions), 0), 2) AS cost_per_conversion,
            ROUND(SUM(m.revenue), 2) AS total_revenue
        FROM campaigns c
        INNER JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
        GROUP BY c.campaign_id, c.campaign_name, c.channel
        ORDER BY conversion_rank ASC;
    """,
    "channel_performance_comparison": """
        SELECT 
            c.channel,
            COUNT(DISTINCT c.campaign_id) AS active_campaigns,
            SUM(m.impressions) AS total_impressions,
            SUM(m.clicks) AS total_clicks,
            SUM(m.conversions) AS total_conversions,
            ROUND(SUM(m.spend), 2) AS total_spend,
            ROUND(SUM(m.revenue), 2) AS total_revenue,
            ROUND((SUM(m.clicks) / NULLIF(SUM(m.impressions), 0)) * 100, 2) AS channel_ctr_pct,
            ROUND((SUM(m.conversions) / NULLIF(SUM(m.clicks), 0)) * 100, 2) AS channel_conversion_rate_pct,
            ROUND(SUM(m.spend) / NULLIF(SUM(m.conversions), 0), 2) AS avg_cost_per_conversion,
            ROUND(SUM(m.revenue) / NULLIF(SUM(m.spend), 0), 2) AS channel_roas
        FROM campaigns c
        INNER JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
        GROUP BY c.channel
        ORDER BY channel_roas DESC;
    """,
    "daily_performance_trends": """
        SELECT 
            m.report_date,
            COUNT(DISTINCT m.campaign_id) AS active_campaigns_count,
            SUM(m.impressions) AS daily_impressions,
            SUM(m.clicks) AS daily_clicks,
            SUM(m.conversions) AS daily_conversions,
            ROUND(SUM(m.spend), 2) AS daily_spend,
            ROUND(SUM(m.revenue), 2) AS daily_revenue,
            ROUND(SUM(m.revenue) / NULLIF(SUM(m.spend), 0), 2) AS daily_roas
        FROM campaign_metrics m
        GROUP BY m.report_date
        ORDER BY m.report_date ASC;
    """,
    "low_efficiency_campaigns": """
        WITH campaign_aggregates AS (
            SELECT 
                c.campaign_id,
                c.campaign_name,
                c.channel,
                SUM(m.spend) AS total_spend,
                SUM(m.conversions) AS total_conversions,
                ROUND(SUM(m.spend) / NULLIF(SUM(m.conversions), 0), 2) AS cost_per_conversion,
                ROUND(SUM(m.revenue) / NULLIF(SUM(m.spend), 0), 2) AS roas
            FROM campaigns c
            INNER JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
            GROUP BY c.campaign_id, c.campaign_name, c.channel
        ),
        benchmarks AS (
            SELECT 
                AVG(total_spend) AS avg_spend,
                AVG(total_conversions) AS avg_conversions
            FROM campaign_aggregates
        )
        SELECT 
            ca.campaign_id,
            ca.campaign_name,
            ca.channel,
            ROUND(ca.total_spend, 2) AS total_spend,
            ca.total_conversions,
            ca.cost_per_conversion,
            ca.roas,
            ROUND(b.avg_spend, 2) AS benchmark_avg_spend,
            ROUND(b.avg_conversions, 1) AS benchmark_avg_conversions,
            'High Spend / Low Conversion Risk' AS status_flag
        FROM campaign_aggregates ca
        CROSS JOIN benchmarks b
        WHERE ca.total_spend >= b.avg_spend AND ca.total_conversions <= b.avg_conversions
        ORDER BY ca.total_spend DESC;
    """,
    "campaign_performance_tiers": """
        SELECT 
            c.campaign_id,
            c.campaign_name,
            c.channel,
            ROUND(SUM(m.spend), 2) AS total_spend,
            ROUND(SUM(m.revenue), 2) AS total_revenue,
            ROUND(SUM(m.revenue) / NULLIF(SUM(m.spend), 0), 2) AS roas,
            CASE 
                WHEN (SUM(m.revenue) / NULLIF(SUM(m.spend), 0)) >= 5.0 THEN 'Tier 1: High Performer (ROAS >= 5.0)'
                WHEN (SUM(m.revenue) / NULLIF(SUM(m.spend), 0)) >= 3.0 THEN 'Tier 2: Moderate Performer (3.0 <= ROAS < 5.0)'
                WHEN (SUM(m.revenue) / NULLIF(SUM(m.spend), 0)) >= 1.0 THEN 'Tier 3: Breakeven (1.0 <= ROAS < 3.0)'
                ELSE 'Tier 4: Loss Making (ROAS < 1.0)'
            END AS performance_tier
        FROM campaigns c
        INNER JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
        GROUP BY c.campaign_id, c.campaign_name, c.channel
        ORDER BY roas DESC;
    """,
    "campaign_date_continuity": """
        SELECT 
            c.campaign_id,
            c.campaign_name,
            MIN(m.report_date) AS first_reported_date,
            MAX(m.report_date) AS last_reported_date,
            COUNT(DISTINCT m.report_date) AS actual_reported_days
        FROM campaigns c
        INNER JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
        GROUP BY c.campaign_id, c.campaign_name
        ORDER BY actual_reported_days DESC;
    """
}


def generate_analytics_reports(
    engine: Optional[Engine] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Execute business analytical queries against database and export CSV reports.

    Args:
        engine: SQLAlchemy database engine.
        output_dir: Output directory for reports (defaults to Config.REPORTS_DIR).

    Returns:
        Dict[str, Any]: Dictionary mapping report names to row counts and file paths.
    """
    db_engine = engine or get_engine()
    reports_path = Path(output_dir or Config.REPORTS_DIR)
    reports_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating analytics reports in {reports_path}")
    results = {}

    with db_engine.connect() as conn:
        for report_name, query in ANALYTICS_QUERIES.items():
            try:
                df = pd.read_sql(text(query), conn)
                csv_file = reports_path / f"{report_name}.csv"
                df.to_csv(csv_file, index=False)
                results[report_name] = {
                    "rows": len(df),
                    "file": str(csv_file),
                }
                logger.info(f"Generated report '{report_name}.csv' ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Failed to generate report '{report_name}': {e}")
                results[report_name] = {
                    "rows": 0,
                    "error": str(e),
                }

    return results
