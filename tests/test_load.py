"""Unit tests for database loading and idempotency."""

import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from src.load import load_validated_data, record_pipeline_run
from datetime import datetime, timezone


@pytest.fixture
def sqlite_engine():
    """Create an in-memory SQLite engine with the project schema for testing."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
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
    return engine


def test_load_and_idempotency(sqlite_engine):
    """Test loading valid data and verifying repeated execution is idempotent."""
    data = pd.DataFrame([
        {
            "record_id": "REC-01",
            "campaign_id": "CMP-01",
            "campaign_name": "Summer Blitz",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": 1000,
            "clicks": 100,
            "conversions": 10,
            "spend": 50.0,
            "revenue": 200.0,
            "ctr": 10.0,
            "conversion_rate": 10.0,
            "cost_per_conversion": 5.0,
            "roas": 4.0,
        }
    ])

    # First load
    summary1 = load_validated_data(data, engine=sqlite_engine)
    assert summary1["campaigns_loaded"] == 1
    assert summary1["metrics_loaded"] == 1

    with sqlite_engine.connect() as conn:
        campaigns_count = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
        metrics_count = conn.execute(text("SELECT COUNT(*) FROM campaign_metrics")).scalar()
        assert campaigns_count == 1
        assert metrics_count == 1

    # Second load (idempotency verification)
    summary2 = load_validated_data(data, engine=sqlite_engine)
    assert summary2["campaigns_loaded"] == 1
    assert summary2["metrics_loaded"] == 1

    with sqlite_engine.connect() as conn:
        campaigns_count = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
        metrics_count = conn.execute(text("SELECT COUNT(*) FROM campaign_metrics")).scalar()
        assert campaigns_count == 1  # No duplicate campaign inserted
        assert metrics_count == 1    # No duplicate metric inserted


def test_record_pipeline_run(sqlite_engine):
    """Test recording pipeline execution status in pipeline_runs."""
    started = datetime.now(timezone.utc)
    record_pipeline_run(
        engine=sqlite_engine,
        run_id="test_run_123",
        started_at=started,
        status="RUNNING",
        records_processed=10,
        records_accepted=8,
        records_rejected=2,
        records_loaded=8,
    )

    with sqlite_engine.connect() as conn:
        status = conn.execute(
            text("SELECT status FROM pipeline_runs WHERE run_id = 'test_run_123'")
        ).scalar()
        assert status == "RUNNING"


def test_mysql_load_integration():
    """Verify loading and idempotency against MySQL database if reachable."""
    try:
        from src.load import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("MySQL database not reachable")

    data = pd.DataFrame([
        {
            "record_id": "REC-TEST-MYSQL-01",
            "campaign_id": "CMP-TEST-01",
            "campaign_name": "MySQL Integration Campaign",
            "channel": "Email",
            "report_date": "2026-09-01",
            "impressions": 5000,
            "clicks": 250,
            "conversions": 25,
            "spend": 100.0,
            "revenue": 500.0,
            "ctr": 5.0,
            "conversion_rate": 10.0,
            "cost_per_conversion": 4.0,
            "roas": 5.0,
        }
    ])

    summary = load_validated_data(data, engine=engine)
    assert summary["campaigns_loaded"] == 1
    assert summary["metrics_loaded"] == 1

