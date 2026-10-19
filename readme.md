# Marketing Campaign Data Pipeline

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-dheeraj73%2Fmarketing--campaign--pipeline-blue?logo=docker)](https://hub.docker.com/repository/docker/dheeraj73/marketing-campaign-pipeline/general)

A Python and SQL-based data engineering project that automates the extraction, cleaning, validation, storage, and analysis of marketing campaign data. The pipeline converts raw marketing data into reliable, structured datasets that support campaign performance measurement and business decision-making.

## 1. Project Overview

Marketing teams collect campaign data from different sources, including CSV files, advertising platforms, email marketing systems, and REST APIs. These sources may contain missing values, duplicate records, inconsistent formats, and invalid data.

This project builds an ETL (Extract, Transform, Load) pipeline to process marketing campaign data and store validated records in a MySQL database.

The project focuses on data reliability, automated validation, reproducible processing, and SQL-based analytics.

## 2. Problem Statement

Raw marketing data is often difficult to analyze because of inconsistent formats, duplicate records, missing values, and incorrect metrics.

The objective is to build an automated pipeline that:

- Extracts data from CSV files and optionally REST APIs.
- Cleans and transforms raw marketing data using Python and Pandas.
- Validates data quality using configurable rules.
- Separates valid records from rejected records.
- Loads validated records into MySQL.
- Generates campaign performance reports using SQL.
- Logs pipeline execution details and data quality issues.
- Documents the dataset, schema, processing rules, and known limitations.

## 3. Project Objectives

1. Implement a modular ETL pipeline using Python.
2. Develop reusable data cleaning and validation functions.
3. Store processed data in a relational database.
4. Prevent duplicate records and handle invalid input safely.
5. Create SQL queries for campaign analytics and customer segmentation.
6. Write automated tests for data transformations and validation.
7. Maintain clear technical documentation and reproducible setup instructions.

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Pipeline implementation |
| Pandas | Data extraction, transformation, and cleaning |
| MySQL 8+ | Persistent storage and SQL analytics |
| SQLAlchemy | Database connections and data loading |
| Requests | Optional REST API ingestion |
| python-dotenv | Environment variable management |
| Logging | Pipeline execution and error tracking |
| Git and GitHub | Version control and project documentation |
| Docker Compose | Reproducible multi-container environment (MySQL + Pipeline) |
| Docker Hub | Container registry: [Dockerhub repository](https://hub.docker.com/repository/docker/dheeraj73/marketing-campaign-pipeline/general) |

Use compatible versions of the selected libraries and record them in `requirements.txt`.

## 5. System Architecture

```text
CSV Files / REST API
        |
        v
   Data Extraction
        |
        v
 Raw Data Validation
        |
        v
 Cleaning and Transformation
        |
        v
   Quality Validation
        |
        +---------------------+
        |                     |
        v                     v
   Valid Records       Rejected Records
        |                     |
        v                     v
  MySQL Database       Error Report / Logs
        |
        v
   SQL Analytics
        |
        v
 Campaign Performance Reports
```

## 6. Project Folder Structure

```text
marketing-campaign-data-pipeline/
│
├── data/
│   ├── raw/
│   │   └── campaign_data.csv
│   ├── processed/
│   └── rejected/
│
├── src/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   ├── validate.py
│   ├── load.py
│   ├── analytics.py
│   ├── config.py
│   └── pipeline.py
│
├── sql/
│   ├── schema.sql
│   ├── analytics.sql
│   └── seed_data.sql
│
├── tests/
│   ├── test_extract.py
│   ├── test_transform.py
│   ├── test_validate.py
│   ├── test_load.py
│   └── test_pipeline.py
│
├── reports/
│   └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
├── docs/
│   ├── data_dictionary.md
│   ├── data_quality_rules.md
│   └── architecture.md
│
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── README.md
└── main.py
```

### Responsibilities of important files

| File | Responsibility |
|---|---|
| `extract.py` | Read CSV files and optionally fetch API data |
| `transform.py` | Standardize columns, types, and formats |
| `validate.py` | Check required fields, ranges, and duplicates |
| `load.py` | Insert validated records into MySQL |
| `analytics.py` | Execute analytical SQL queries and export reports |
| `config.py` | Read configuration and environment variables |
| `pipeline.py` | Coordinate the complete ETL workflow |
| `main.py` | Application entry point |
| `schema.sql` | Create database tables and constraints |
| `analytics.sql` | Store reusable business analysis queries |
| `tests/` | Verify functionality and data quality |
| `docs/` | Document data definitions, validation, and design |

## 7. Functional Requirements

### FR-01: Data Extraction

- Read marketing data from CSV files.
- Validate file existence and required column names.
- Handle empty files, malformed records, and invalid file formats.
- Optionally retrieve campaign data from a REST API.
- Record source filename, extraction timestamp, and execution identifier where applicable.

### FR-02: Data Transformation

- Standardize column names.
- Remove leading and trailing whitespace from text fields.
- Normalize channel names, such as `email`, `Email`, and `EMAIL`.
- Convert dates to a consistent format.
- Convert numerical columns to appropriate numeric types.
- Handle missing values according to documented business rules.
- Derive metrics such as conversion rate when valid inputs are available.

### FR-03: Data Quality Validation

Implement automated checks for:

- Missing required fields.
- Duplicate records.
- Invalid dates.
- Negative clicks, impressions, conversions, spend, or revenue.
- Conversions greater than clicks.
- Clicks greater than impressions, when these metrics share the same reporting scope.
- Invalid campaign or channel values.
- Incorrect data types and malformed records.

Each rejected record should have a clear rejection reason.

Do not silently discard invalid records. Preserve rejected records in a separate output and log the relevant validation issues.

### FR-04: Data Loading

- Create database tables using SQL scripts.
- Load validated records into MySQL.
- Use parameterized database operations.
- Prevent duplicate inserts using a defined record key or unique constraint.
- Use transactions where appropriate.
- Roll back failed transactions and record errors.
- Support safe reruns without duplicating previously loaded records.

### FR-05: Data Analytics

Generate reports that answer business questions such as:

- Which campaigns generated the most conversions?
- Which marketing channel has the highest conversion rate?
- What is the cost per conversion for each campaign?
- Which campaigns generated the most revenue?
- What is the return on advertising spend (ROAS)?
- How do campaign metrics change over time?

### FR-06: Logging and Reporting

- Record pipeline start and completion times.
- Log extraction, transformation, validation, and loading results.
- Track records processed, accepted, rejected, and loaded.
- Generate a data quality report for every pipeline run.
- Report database connection failures and processing errors.
- Avoid logging passwords, access tokens, or other secrets.

## 8. Dataset Requirements

Begin with a synthetic dataset that you create for development and testing. Clearly identify it as synthetic in the documentation.

Suggested file: `data/raw/campaign_data.csv`

| Column | Type | Description |
|---|---|---|
| record_id | String | Unique source record identifier |
| campaign_id | String | Unique campaign identifier |
| campaign_name | String | Campaign name |
| channel | String | Email, social media, search ads, etc. |
| report_date | Date | Date of the reported metrics |
| impressions | Integer | Number of times content was displayed |
| clicks | Integer | Number of clicks |
| conversions | Integer | Number of attributed conversions |
| spend | Decimal | Marketing expenditure |
| revenue | Decimal | Revenue attributed to the campaign |

Example CSV:

```csv
record_id,campaign_id,campaign_name,channel,report_date,impressions,clicks,conversions,spend,revenue
R001,C001,Summer Sale,Email,2026-09-01,10000,500,50,200.00,1500.00
R002,C002,Winter Offer,Social Media,2026-09-01,20000,800,40,400.00,1200.00
R003,C003,Spring Launch,Search Ads,2026-09-02,15000,600,60,350.00,2100.00
```

Ensure the example values satisfy the validation rules. Create additional test records containing missing values, duplicates, invalid dates, and negative metrics to test the pipeline.

## 9. Database Design

Create a MySQL database named `marketing_analytics`.

Recommended tables:

### `campaigns`

Stores campaign-level information.

- `campaign_id` — Primary key
- `campaign_name`
- `channel`
- `created_at`

### `campaign_metrics`

Stores campaign performance measurements.

- `id` — Primary key
- `record_id` — Source record identifier
- `campaign_id` — Foreign key
- `report_date`
- `impressions`
- `clicks`
- `conversions`
- `spend`
- `revenue`
- `loaded_at`

Add suitable constraints and indexes. Define a unique key that reflects the actual source record identity, rather than assuming every campaign has only one daily record.

### `pipeline_runs`

Stores execution summaries.

- `run_id` — Primary key
- `started_at`
- `completed_at`
- `status`
- `records_processed`
- `records_accepted`
- `records_rejected`
- `records_loaded`
- `error_summary`

For the first version, rejected records can be stored in CSV files. A dedicated rejected-records table can be added later.

## 10. Business Metrics and SQL Queries

Implement the following metrics:

**Conversion Rate**

`Conversions / Clicks × 100`

**Click-Through Rate (CTR)**

`Clicks / Impressions × 100`

**Cost Per Conversion**

`Spend / Conversions`

**Return on Advertising Spend (ROAS)**

`Attributed Revenue / Advertising Spend`

Use `NULLIF` or equivalent safeguards to avoid division by zero. Define how zero denominators and missing revenue are handled.

Suggested SQL tasks:

1. Calculate total spend and revenue by campaign.
2. Rank campaigns by conversion count.
3. Compare conversion rates across channels.
4. Calculate daily and monthly campaign performance.
5. Identify campaigns with high spend and low conversions.
6. Segment campaign performance into configurable categories.
7. Detect missing reporting dates or incomplete campaign metrics.

## 11. Non-Functional Requirements

- **Reliability:** Failed loads should not leave partially committed batches.
- **Idempotency:** Rerunning the same input should not duplicate database records.
- **Maintainability:** Separate extraction, transformation, validation, and loading logic.
- **Security:** Keep credentials in environment variables.
- **Observability:** Maintain useful logs and execution summaries.
- **Testability:** Use automated tests for valid and invalid records.
- **Documentation:** Explain setup, schema, validation rules, and known limitations.
- **Scalability:** Process data in configurable batches where appropriate.

## 12. Environment Setup

### Prerequisites

Install:

- Python 3.11 or a compatible version.
- MySQL 8 or a compatible MySQL server.
- Git.
- A code editor such as VS Code.

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

Create `requirements.txt` with the required libraries:

```text
pandas
SQLAlchemy
PyMySQL
python-dotenv
requests
pytest
```

Then install:

```bash
pip install -r requirements.txt
```

Pin tested dependency versions before publishing a reproducible release.

### Configure environment variables

Create a local `.env` file based on `.env.example`.

Example `.env.example`:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=marketing_analytics
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

Use your actual local MySQL credentials in `.env`. Never commit `.env` or real credentials to GitHub.

### Create the database

Connect to MySQL and execute:

```sql
CREATE DATABASE marketing_analytics;
```

Run the schema script:

```bash
mysql -u your_database_user -p marketing_analytics < sql/schema.sql
```

Replace the placeholder username with your configured database user.

### Docker & Docker Hub Setup

The complete pipeline and database stack is containerized and published on Docker Hub:
- **Repository:** [Dockerhub repository](https://hub.docker.com/repository/docker/dheeraj73/marketing-campaign-pipeline/general)
- **Image:** `dheeraj73/marketing-campaign-pipeline:latest`

To run the entire system (MySQL 8 + Pipeline ETL) in isolated containers:

```bash
# Pull the latest image from Docker Hub
docker pull dheeraj73/marketing-campaign-pipeline:latest

# Start MySQL database and run the pipeline
docker compose up
```

## 13. Running the Pipeline

### Option A: Local Virtual Environment
```bash
python main.py
```

### Option B: Docker Compose
```bash
docker compose up
```

The pipeline should perform these steps:

1. Read the input data.
2. Normalize and transform the records.
3. Validate data quality.
4. Save rejected records and validation reasons.
5. Load valid records into MySQL.
6. Generate SQL analytics reports.
7. Write a summary of the run to the logs.

The program should exit with an appropriate status when a critical stage fails.

## 14. Testing Requirements

Use Pytest to test:

- Successful extraction of valid CSV files.
- Handling of missing or empty files.
- Column-name normalization.
- Duplicate detection.
- Missing required fields.
- Invalid dates and numeric values.
- Data validation boundaries.
- Database insertion and duplicate prevention.
- Transaction rollback on failure.
- Safe reruns of the same input.
- Correct calculation of campaign metrics.
- End-to-end pipeline execution.

Use temporary test databases or isolated test schemas for database tests. Avoid running destructive tests against production data.

Run the tests with:

```bash
pytest -v
```

## 15. Expected Outputs

The finished project should produce:

- A cleaned dataset in `data/processed/`.
- Rejected records and reasons in `data/rejected/`.
- Validated records in MySQL.
- SQL-based campaign performance reports in `reports/`.
- Pipeline execution logs in `logs/`.
- A summary of processed, accepted, rejected, and loaded records.
- Automated test results.

### Actual Pipeline Run Summary

```text
============================================================
       MARKETING CAMPAIGN DATA PIPELINE EXECUTION SUMMARY
============================================================
  Run ID            : run_20261019_151729_cc6a7e
  Status            : SUCCESS
  Records Processed : 62
  Records Accepted  : 50
  Records Rejected  : 12
  Records Loaded    : 50
------------------------------------------------------------
  Cleaned Output    : data/processed/campaign_data_cleaned.csv
  Rejected Output   : data/rejected/rejected_records.csv
  Logs Location     : logs/pipeline.log

  Generated Analytics Reports:
    - campaign_performance_summary.csv (10 rows)
    - campaign_conversion_rankings.csv (10 rows)
    - channel_performance_comparison.csv (6 rows)
    - daily_performance_trends.csv (5 rows)
    - low_efficiency_campaigns.csv (2 rows)
    - campaign_performance_tiers.csv (10 rows)
    - campaign_date_continuity.csv (10 rows)
============================================================
```

### Automated Test Verification

```text
======================== 17 passed, 5 warnings in 0.66s ========================
- test_extract_valid_csv: PASSED
- test_extract_missing_file: PASSED
- test_extract_empty_file: PASSED
- test_extract_missing_required_columns: PASSED
- test_load_and_idempotency: PASSED
- test_record_pipeline_run: PASSED
- test_mysql_load_integration: PASSED
- test_pipeline_end_to_end: PASSED
- test_normalize_channel: PASSED
- test_transform_columns_and_whitespace: PASSED
- test_transform_metric_calculations: PASSED
- test_transform_zero_division_safety: PASSED
- test_validate_clean_records: PASSED
- test_validate_negative_metrics: PASSED
- test_validate_funnel_consistency: PASSED
- test_validate_duplicate_records: PASSED
- test_validate_missing_required_fields: PASSED
```

## 16. Implementation Roadmap

### Phase 1 — Foundation
- [x] Create the repository and folder structure.
- [x] Prepare a synthetic marketing dataset (`data/raw/campaign_data.csv`).
- [x] Set up the Python virtual environment.
- [x] Install dependencies (`requirements.txt`).

### Phase 2 — ETL Development
- [x] Implement CSV extraction (`src/extract.py`).
- [x] Implement cleaning and transformation functions (`src/transform.py`).
- [x] Implement validation rules (`src/validate.py`).
- [x] Generate rejected-record reports (`data/rejected/rejected_records.csv`).

### Phase 3 — Database Integration
- [x] Design and create the MySQL schema (`sql/schema.sql`).
- [x] Implement database loading (`src/load.py`).
- [x] Add unique constraints and duplicate prevention (`record_id` UNIQUE).
- [x] Add transaction handling and error logging (`pipeline_runs` audit table).

### Phase 4 — Analytics
- [x] Write campaign performance SQL queries (`sql/analytics.sql`).
- [x] Calculate CTR, conversion rate, cost per conversion, and ROAS.
- [x] Export query results to CSV reports (`src/analytics.py` -> `reports/`).

### Phase 5 — Testing and Documentation
- [x] Add unit and integration tests (`tests/`).
- [x] Verify safe reruns and error handling.
- [x] Document data quality rules and schema (`docs/`).
- [x] Add setup instructions and example output.
- [ ] Push the completed project to GitHub.

### Phase 6 — Optional Enhancements
- [x] Add REST API ingestion (`extract_from_api` in `src/extract.py`).
- [x] Add Docker Compose for multi-container setup (`docker-compose.yml`).
- [x] Containerize and publish image to [Dockerhub repository](https://hub.docker.com/repository/docker/dheeraj73/marketing-campaign-pipeline/general) (`dheeraj73/marketing-campaign-pipeline:latest`).
- [x] Add interactive Jupyter Notebook for campaign analytics & visualizations (`notebooks/marketing_campaign_analysis.ipynb`).
- [ ] Schedule recurring pipeline execution.
- [ ] Add AWS or Snowflake integration.
- [ ] Add a dashboard for campaign analytics.
- [ ] Explore dbt for SQL transformations and data testing.

## 17. Success Criteria

The project is complete when:

- Raw data can be processed from start to finish.
- Transformation and validation rules are automated.
- Invalid records are traceable and not silently discarded.
- Valid records are stored in MySQL.
- Repeated pipeline runs do not create duplicates.
- SQL reports produce correct results on known test data.
- Automated tests pass.
- Setup and usage instructions allow another developer to reproduce the project.

## 18. Resume Description

After completing and testing the project, you can describe it on your resume as follows:

**Marketing Campaign Data Pipeline | Python, Pandas, SQL, MySQL**

- Developed an ETL pipeline to extract, clean, validate, and load marketing campaign data into MySQL using Python and Pandas.
- Implemented automated data quality checks for missing values, duplicate records, and invalid metrics, with rejection reporting and execution logs.
- Wrote SQL queries to analyze campaign performance, conversion rates, advertising spend, and return on advertising spend.

Only include features that you have actually implemented and verified.

## 19. Learning Resources

- Python: https://docs.python.org/3/
- Pandas: https://pandas.pydata.org/docs/
- MySQL: https://dev.mysql.com/doc/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pytest: https://docs.pytest.org/
- Git: https://git-scm.com/doc

## 20. Final Goal

Build a small but reliable data engineering system that demonstrates practical knowledge of Python, SQL, ETL workflows, data quality, database integration, testing, and documentation.

The project is designed as a learning and portfolio project aligned with the TIAA Data Engineering Analyst role. It is not intended to represent a production-scale enterprise data platform.
