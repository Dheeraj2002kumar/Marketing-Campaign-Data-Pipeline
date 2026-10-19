"""Configuration management and logging setup for Marketing Campaign Data Pipeline."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration container."""

    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "marketing_analytics")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Optional SQLite override for tests/isolated environments
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")
    SQLITE_PATH: Path = BASE_DIR / "marketing_analytics.db"

    # Paths
    RAW_DATA_PATH: Path = BASE_DIR / os.getenv("RAW_DATA_PATH", "data/raw/campaign_data.csv")
    PROCESSED_DATA_PATH: Path = BASE_DIR / os.getenv("PROCESSED_DATA_PATH", "data/processed/campaign_data_cleaned.csv")
    REJECTED_DATA_PATH: Path = BASE_DIR / os.getenv("REJECTED_DATA_PATH", "data/rejected/rejected_records.csv")
    REPORTS_DIR: Path = BASE_DIR / os.getenv("REPORTS_DIR", "reports")
    LOGS_DIR: Path = BASE_DIR / os.getenv("LOGS_DIR", "logs")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def get_database_url(cls) -> str:
        """Construct SQLAlchemy database URL without exposing credentials in plaintext."""
        if cls.USE_SQLITE:
            return f"sqlite:///{cls.SQLITE_PATH}"
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4"

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required folders exist."""
        for path in [
            cls.RAW_DATA_PATH.parent,
            cls.PROCESSED_DATA_PATH.parent,
            cls.REJECTED_DATA_PATH.parent,
            cls.REPORTS_DIR,
            cls.LOGS_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str = "pipeline", log_file: str = "pipeline.log") -> logging.Logger:
    """Set up and configure a structured logger."""
    Config.ensure_directories()
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_path = Config.LOGS_DIR / log_file
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
