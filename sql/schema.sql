-- Marketing Campaign Data Pipeline Schema
-- Database: marketing_analytics

CREATE DATABASE IF NOT EXISTS marketing_analytics;
USE marketing_analytics;

-- Drop tables in reverse order of foreign key dependencies if recreating
DROP TABLE IF EXISTS campaign_metrics;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS pipeline_runs;

-- Table: campaigns (stores unique campaign dimensions)
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id VARCHAR(50) NOT NULL PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    channel VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_channel (channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: campaign_metrics (stores daily fact measurements)
CREATE TABLE IF NOT EXISTS campaign_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_id VARCHAR(50) NOT NULL UNIQUE,
    campaign_id VARCHAR(50) NOT NULL,
    report_date DATE NOT NULL,
    impressions INT NOT NULL DEFAULT 0,
    clicks INT NOT NULL DEFAULT 0,
    conversions INT NOT NULL DEFAULT 0,
    spend DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    revenue DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    ctr DECIMAL(6, 4) NULL,
    conversion_rate DECIMAL(6, 4) NULL,
    cost_per_conversion DECIMAL(12, 2) NULL,
    roas DECIMAL(8, 2) NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_metrics_campaign FOREIGN KEY (campaign_id)
        REFERENCES campaigns(campaign_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_campaign_date (campaign_id, report_date),
    INDEX idx_report_date (report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: pipeline_runs (tracks audit execution logs and batch statistics)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(64) NOT NULL PRIMARY KEY,
    started_at DATETIME NOT NULL,
    completed_at DATETIME NULL,
    status VARCHAR(20) NOT NULL,
    records_processed INT DEFAULT 0,
    records_accepted INT DEFAULT 0,
    records_rejected INT DEFAULT 0,
    records_loaded INT DEFAULT 0,
    error_summary TEXT NULL,
    INDEX idx_run_status (status),
    INDEX idx_run_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
