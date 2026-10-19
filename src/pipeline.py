"""End-to-end ETL Pipeline orchestrator for Marketing Campaign Data."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.engine import Engine

from src.config import Config, setup_logger
from src.extract import extract_from_csv
from src.transform import transform_data
from src.validate import validate_records
from src.load import get_engine, load_validated_data, record_pipeline_run
from src.analytics import generate_analytics_reports

logger = setup_logger("pipeline")


class PipelineExecutionError(Exception):
    """Raised when critical pipeline execution failure occurs."""
    pass


def run_pipeline(
    raw_data_path: Optional[Path] = None,
    engine: Optional[Engine] = None,
    run_analytics: bool = True,
    processed_data_path: Optional[Path] = None,
    rejected_data_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Execute the full ETL workflow:
    Extract -> Transform -> Validate -> Save Cleaned & Rejected -> Load MySQL -> Analytics -> Audit.

    Args:
        raw_data_path: Path to raw CSV file (defaults to Config.RAW_DATA_PATH).
        engine: Optional SQLAlchemy engine.
        run_analytics: Whether to execute analytics queries and export CSV reports.
        processed_data_path: Optional destination for cleaned CSV records.
        rejected_data_path: Optional destination for rejected CSV records.

    Returns:
        Dict[str, Any]: Pipeline execution summary.
    """
    Config.ensure_directories()
    input_file = Path(raw_data_path or Config.RAW_DATA_PATH)
    processed_file = Path(processed_data_path or Config.PROCESSED_DATA_PATH)
    rejected_file = Path(rejected_data_path or Config.REJECTED_DATA_PATH)
    db_engine = engine or get_engine()

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    started_at = datetime.now(timezone.utc)

    logger.info(f"=== Starting Marketing Campaign Data Pipeline Run: {run_id} ===")
    logger.info(f"Source file: {input_file}")

    records_processed = 0
    records_accepted = 0
    records_rejected = 0
    records_loaded = 0
    status = "FAILED"
    error_summary = None

    try:
        # Initial audit log entry
        record_pipeline_run(
            engine=db_engine,
            run_id=run_id,
            started_at=started_at,
            status="RUNNING",
            records_processed=0,
            records_accepted=0,
            records_rejected=0,
            records_loaded=0,
        )

        # 1. Extraction
        raw_df = extract_from_csv(input_file)
        records_processed = len(raw_df)

        # 2. Transformation
        transformed_df = transform_data(raw_df)

        # 3. Validation
        valid_df, rejected_df = validate_records(transformed_df)
        records_accepted = len(valid_df)
        records_rejected = len(rejected_df)

        # 4. Save Processed & Rejected Data files
        processed_file.parent.mkdir(parents=True, exist_ok=True)
        valid_df.to_csv(processed_file, index=False)
        logger.info(f"Saved {records_accepted} cleaned records to {processed_file}")

        rejected_file.parent.mkdir(parents=True, exist_ok=True)
        rejected_df.to_csv(rejected_file, index=False)
        logger.info(f"Saved {records_rejected} rejected records to {rejected_file}")

        # 5. Database Loading
        load_summary = load_validated_data(valid_df, engine=db_engine, run_id=run_id)
        records_loaded = load_summary["metrics_loaded"]

        # 6. Analytics Reports Generation
        analytics_summary = {}
        if run_analytics and records_loaded > 0:
            analytics_summary = generate_analytics_reports(engine=db_engine)

        status = "SUCCESS"
        completed_at = datetime.now(timezone.utc)

        # 7. Final Audit Log Record
        record_pipeline_run(
            engine=db_engine,
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            records_processed=records_processed,
            records_accepted=records_accepted,
            records_rejected=records_rejected,
            records_loaded=records_loaded,
            error_summary=None,
        )

        logger.info(f"=== Pipeline Run {run_id} Completed Successfully ===")
        return {
            "run_id": run_id,
            "status": status,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "records_processed": records_processed,
            "records_accepted": records_accepted,
            "records_rejected": records_rejected,
            "records_loaded": records_loaded,
            "processed_file": str(processed_file),
            "rejected_file": str(rejected_file),
            "reports": analytics_summary,
        }

    except Exception as e:
        completed_at = datetime.now(timezone.utc)
        error_summary = str(e)
        status = "FAILED"
        logger.error(f"Pipeline Run {run_id} FAILED: {error_summary}", exc_info=True)

        try:
            record_pipeline_run(
                engine=db_engine,
                run_id=run_id,
                started_at=started_at,
                completed_at=completed_at,
                status=status,
                records_processed=records_processed,
                records_accepted=records_accepted,
                records_rejected=records_rejected,
                records_loaded=records_loaded,
                error_summary=error_summary,
            )
        except Exception as log_err:
            logger.error(f"Failed to record pipeline failure state: {log_err}")

        raise PipelineExecutionError(f"Pipeline failed: {error_summary}") from e
