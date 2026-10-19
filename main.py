"""Main CLI entrypoint for Marketing Campaign Data Pipeline."""

import sys
import argparse
from pathlib import Path

from src.config import Config, setup_logger
from src.pipeline import run_pipeline, PipelineExecutionError

logger = setup_logger("main")


def print_summary(summary: dict) -> None:
    """Print formatted execution summary."""
    print("\n" + "=" * 60)
    print("       MARKETING CAMPAIGN DATA PIPELINE EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  Run ID            : {summary.get('run_id')}")
    print(f"  Status            : {summary.get('status')}")
    print(f"  Started At        : {summary.get('started_at')}")
    print(f"  Completed At      : {summary.get('completed_at')}")
    print("-" * 60)
    print(f"  Records Processed : {summary.get('records_processed')}")
    print(f"  Records Accepted  : {summary.get('records_accepted')}")
    print(f"  Records Rejected  : {summary.get('records_rejected')}")
    print(f"  Records Loaded    : {summary.get('records_loaded')}")
    print("-" * 60)
    print(f"  Cleaned Output    : {summary.get('processed_file')}")
    print(f"  Rejected Output   : {summary.get('rejected_file')}")
    
    reports = summary.get("reports", {})
    if reports:
        print("\n  Generated Reports:")
        for name, meta in reports.items():
            print(f"    - {name}.csv ({meta.get('rows', 0)} rows)")
    print("=" * 60 + "\n")


def main() -> int:
    """Parse CLI options and execute the pipeline."""
    parser = argparse.ArgumentParser(
        description="Marketing Campaign Data Pipeline - Automated ETL & Analytics"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to raw campaign CSV file (defaults to data/raw/campaign_data.csv)",
    )
    parser.add_argument(
        "--no-analytics",
        action="store_true",
        help="Skip generating SQL analytics CSV reports",
    )

    args = parser.parse_args()
    input_path = Path(args.input) if args.input else Config.RAW_DATA_PATH

    try:
        summary = run_pipeline(
            raw_data_path=input_path,
            run_analytics=not args.no_analytics,
        )
        print_summary(summary)
        return 0
    except PipelineExecutionError as e:
        logger.error(f"Pipeline execution encountered fatal error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
