# Data Dictionary — Marketing Campaign Data Pipeline

## Overview

This document provides complete technical and business definitions for all entities and attributes used across the Marketing Campaign Data Pipeline, from raw CSV ingestion to processed tables and analytics outputs.

---

## 1. Raw Dataset (`data/raw/campaign_data.csv`)

| Column Name | Data Type | Nullable | Description | Example |
|---|---|---|---|---|
| `record_id` | String | No | Unique natural key identifier for the daily campaign record | `REC-001` |
| `campaign_id` | String | No | Unique identifier for the parent marketing campaign | `CMP-101` |
| `campaign_name` | String | No | Human-readable campaign title | `Summer Sale Blitz` |
| `channel` | String | No | Ingestion channel (Email, Social Media, Search Ads, etc.) | `Email` |
| `report_date` | String / Date | No | Activity reporting date (YYYY-MM-DD) | `2026-09-01` |
| `impressions` | Integer | No | Number of ad/content impressions served | `12500` |
| `clicks` | Integer | No | Number of clicks registered on the campaign | `620` |
| `conversions` | Integer | No | Number of attributed conversion actions (e.g., purchases/leads) | `62` |
| `spend` | Decimal | No | Total expenditure incurred in USD | `250.00` |
| `revenue` | Decimal | No | Attributed gross revenue generated in USD | `1860.00` |

---

## 2. Processed Relational Tables (`marketing_analytics` MySQL Database)

### 2.1 Table: `campaigns` (Dimension Table)

Stores distinct campaign-level attributes.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `campaign_id` | VARCHAR(50) | PRIMARY KEY, NOT NULL | Unique campaign identifier |
| `campaign_name` | VARCHAR(255) | NOT NULL | Standardized campaign name |
| `channel` | VARCHAR(100) | NOT NULL, INDEXED | Normalized marketing channel name |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP | Record last update timestamp |

### 2.2 Table: `campaign_metrics` (Fact Table)

Stores daily performance measurements and derived business indicators.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | AUTO_INCREMENT, PRIMARY KEY | Surrogate sequence key |
| `record_id` | VARCHAR(50) | UNIQUE, NOT NULL | Source record identifier for idempotency |
| `campaign_id` | VARCHAR(50) | NOT NULL, FOREIGN KEY (`campaigns.campaign_id`) | Associated campaign key |
| `report_date` | DATE | NOT NULL, INDEXED | Daily activity date |
| `impressions` | INT | NOT NULL, DEFAULT 0 | Validated impressions count |
| `clicks` | INT | NOT NULL, DEFAULT 0 | Validated clicks count |
| `conversions` | INT | NOT NULL, DEFAULT 0 | Validated conversions count |
| `spend` | DECIMAL(12, 2) | NOT NULL, DEFAULT 0.00 | Total spend in USD |
| `revenue` | DECIMAL(12, 2) | NOT NULL, DEFAULT 0.00 | Attributed revenue in USD |
| `ctr` | DECIMAL(6, 4) | NULLABLE | Click-Through Rate (`clicks / impressions * 100`) |
| `conversion_rate` | DECIMAL(6, 4) | NULLABLE | Conversion Rate (`conversions / clicks * 100`) |
| `cost_per_conversion` | DECIMAL(12, 2) | NULLABLE | Spend per conversion (`spend / conversions`) |
| `roas` | DECIMAL(8, 2) | NULLABLE | Return on Ad Spend (`revenue / spend`) |
| `loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Ingestion timestamp |

### 2.3 Table: `pipeline_runs` (Audit & Observability Table)

Tracks execution metadata for every pipeline run.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `run_id` | VARCHAR(64) | PRIMARY KEY, NOT NULL | Unique execution run token |
| `started_at` | DATETIME | NOT NULL | Pipeline execution start timestamp |
| `completed_at` | DATETIME | NULLABLE | Pipeline execution finish timestamp |
| `status` | VARCHAR(20) | NOT NULL (`RUNNING`, `SUCCESS`, `FAILED`) | Final execution status |
| `records_processed` | INT | DEFAULT 0 | Total records read from source |
| `records_accepted` | INT | DEFAULT 0 | Records successfully passing validation |
| `records_rejected` | INT | DEFAULT 0 | Records failing one or more validation checks |
| `records_loaded` | INT | DEFAULT 0 | Records upserted into database |
| `error_summary` | TEXT | NULLABLE | Error message stack trace if run failed |

---

## 3. Rejected Records (`data/rejected/rejected_records.csv`)

Contains all unprocessed/rejected records with raw inputs preserved and an additional `rejection_reason` column specifying semicolon-delimited rule violations (e.g., `Negative spend not allowed: -100.0; Metric violation: clicks (2500) cannot exceed impressions (1000)`).
