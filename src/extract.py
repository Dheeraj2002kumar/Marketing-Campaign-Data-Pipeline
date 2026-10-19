"""Data extraction module for CSV files and optional REST APIs."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Dict, Any
import pandas as pd
import requests

from src.config import setup_logger

logger = setup_logger("extract")

REQUIRED_COLUMNS = [
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
]


class ExtractionError(Exception):
    """Raised when data extraction fails."""
    pass


def extract_from_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Extract marketing campaign data from a CSV file.

    Args:
        filepath: Path to the target CSV file.

    Returns:
        pd.DataFrame: Extracted raw dataset with extraction metadata attached.

    Raises:
        ExtractionError: If file is missing, empty, or unparseable.
    """
    file_path = Path(filepath)
    logger.info(f"Initiating extraction from file: {file_path}")

    if not file_path.exists():
        msg = f"Extraction failed: file does not exist at {file_path}"
        logger.error(msg)
        raise ExtractionError(msg)

    if file_path.stat().st_size == 0:
        msg = f"Extraction failed: file is empty at {file_path}"
        logger.error(msg)
        raise ExtractionError(msg)

    try:
        # Read CSV with string dtypes first to preserve raw inputs for audit/validation
        df = pd.read_csv(file_path, dtype=str, skipinitialspace=True)
    except Exception as e:
        msg = f"Failed to parse CSV file at {file_path}: {e}"
        logger.error(msg)
        raise ExtractionError(msg) from e

    if df.empty:
        msg = f"Extraction failed: no records found in CSV file at {file_path}"
        logger.error(msg)
        raise ExtractionError(msg)

    # Standardize column names check (case insensitive check)
    current_cols = [str(c).strip().lower() for c in df.columns]
    missing_cols = [col for col in REQUIRED_COLUMNS if col.lower() not in current_cols]
    if missing_cols:
        msg = f"CSV file missing required columns: {missing_cols}. Found: {list(df.columns)}"
        logger.error(msg)
        raise ExtractionError(msg)

    # Attach audit metadata to dataframe attrs
    extraction_time = datetime.now(timezone.utc).isoformat()
    df.attrs["source_file"] = str(file_path)
    df.attrs["extracted_at"] = extraction_time
    df.attrs["raw_record_count"] = len(df)

    logger.info(f"Successfully extracted {len(df)} records from {file_path.name}")
    return df


def extract_from_api(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> pd.DataFrame:
    """
    Extract marketing campaign data from a REST API endpoint.

    Args:
        url: API endpoint URL.
        params: Optional query parameters.
        timeout: Request timeout in seconds.

    Returns:
        pd.DataFrame: Extracted dataset.

    Raises:
        ExtractionError: If API call fails or response format is invalid.
    """
    logger.info(f"Initiating extraction from API: {url}")
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        # Check if data is a list of records or a dict with a data key
        if isinstance(data, dict):
            records = data.get("data", data.get("records", [data]))
        elif isinstance(data, list):
            records = data
        else:
            raise ValueError(f"Unexpected JSON response structure: {type(data)}")

        df = pd.DataFrame(records)
        df.attrs["source_api"] = url
        df.attrs["extracted_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Successfully extracted {len(df)} records from API")
        return df
    except Exception as e:
        msg = f"API extraction failed for {url}: {e}"
        logger.error(msg)
        raise ExtractionError(msg) from e
