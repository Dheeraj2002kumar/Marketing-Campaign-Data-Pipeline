"""Integration tests for end-to-end pipeline execution."""

from pathlib import Path
from sqlalchemy import create_engine, text
from src.pipeline import run_pipeline


def test_pipeline_end_to_end(tmp_path: Path):
    """Verify end-to-end pipeline execution from CSV to processed files and database."""
    # 1. Create a temporary CSV dataset with 1 valid and 1 invalid record
    test_csv = tmp_path / "raw_campaigns.csv"
    test_csv.write_text(
        "record_id,campaign_id,campaign_name,channel,report_date,impressions,clicks,conversions,spend,revenue\n"
        "R1,C1,Summer Sale,Email,2026-09-01,1000,100,10,50.00,200.00\n"
        "R2,C2,Invalid Funnel,Email,2026-09-01,500,800,10,50.00,200.00\n"
    )

    # 2. Setup SQLite in-memory engine
    db_engine = create_engine("sqlite:///:memory:")
    with db_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE campaigns (
                campaign_id TEXT PRIMARY KEY,
                campaign_name TEXT NOT NULL,
                channel TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.execute(text("""
            CREATE TABLE campaign_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                campaign_id TEXT NOT NULL,
                report_date TEXT NOT NULL,
                impressions INTEGER NOT NULL DEFAULT 0,
                clicks INTEGER NOT NULL DEFAULT 0,
                conversions INTEGER NOT NULL DEFAULT 0,
                spend REAL NOT NULL DEFAULT 0.0,
                revenue REAL NOT NULL DEFAULT 0.0,
                ctr REAL,
                conversion_rate REAL,
                cost_per_conversion REAL,
                roas REAL,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.execute(text("""
            CREATE TABLE pipeline_runs (
                run_id TEXT PRIMARY KEY,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                records_processed INTEGER DEFAULT 0,
                records_accepted INTEGER DEFAULT 0,
                records_rejected INTEGER DEFAULT 0,
                records_loaded INTEGER DEFAULT 0,
                error_summary TEXT
            );
        """))

    temp_proc = tmp_path / "proc.csv"
    temp_rej = tmp_path / "rej.csv"

    # 3. Execute pipeline without analytics (using isolated engine)
    summary = run_pipeline(
        raw_data_path=test_csv,
        engine=db_engine,
        run_analytics=False,
        processed_data_path=temp_proc,
        rejected_data_path=temp_rej,
    )

    assert summary["status"] == "SUCCESS"
    assert summary["records_processed"] == 2
    assert summary["records_accepted"] == 1
    assert summary["records_rejected"] == 1
    assert summary["records_loaded"] == 1
    assert Path(summary["processed_file"]).exists()
    assert Path(summary["rejected_file"]).exists()

    # 4. Confirm database content
    with db_engine.connect() as conn:
        metrics_count = conn.execute(text("SELECT COUNT(*) FROM campaign_metrics")).scalar()
        assert metrics_count == 1
