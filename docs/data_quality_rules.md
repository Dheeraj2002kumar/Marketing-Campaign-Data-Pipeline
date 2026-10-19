# Data Quality Rules & Validation Framework

## Overview

Data quality is enforced through automated validation filters before any record is committed to the relational data store. The pipeline follows a strict **"fail safe, never silently drop"** policy: records that fail any validation rule are rejected, stamped with detailed failure reason(s), written to `data/rejected/rejected_records.csv`, and recorded in audit logs.

---

## 1. Summary of Quality Rules

| Rule ID | Rule Name | Target Field(s) | Condition / Constraint | Action on Failure |
|---|---|---|---|---|
| **DQR-01** | Mandatory Fields | `record_id`, `campaign_id`, `campaign_name`, `channel` | Value must be non-empty and non-whitespace | Reject record with `Missing required field: <field>` |
| **DQR-02** | Unique Key Check | `record_id` | Must be globally unique within the batch | Reject subsequent occurrences as duplicates |
| **DQR-03** | Date Validation | `report_date` | Must conform to valid ISO date (`YYYY-MM-DD`) | Reject record with `Invalid or missing report_date` |
| **DQR-04** | Non-Negative Impressions | `impressions` | Must be numeric integer and $\ge 0$ | Reject record if negative or non-numeric |
| **DQR-05** | Non-Negative Clicks | `clicks` | Must be numeric integer and $\ge 0$ | Reject record if negative or non-numeric |
| **DQR-06** | Non-Negative Conversions | `conversions` | Must be numeric integer and $\ge 0$ | Reject record if negative or non-numeric |
| **DQR-07** | Non-Negative Spend | `spend` | Must be numeric decimal and $\ge 0.00$ | Reject record if negative or non-numeric |
| **DQR-08** | Non-Negative Revenue | `revenue` | Must be numeric decimal and $\ge 0.00$ | Reject record if negative or non-numeric |
| **DQR-09** | Funnel Consistency: Clicks vs Impressions | `clicks`, `impressions` | `clicks` $\le$ `impressions` | Reject record with `Metric violation: clicks cannot exceed impressions` |
| **DQR-10** | Funnel Consistency: Conversions vs Clicks | `conversions`, `clicks` | `conversions` $\le$ `clicks` | Reject record with `Metric violation: conversions cannot exceed clicks` |
| **DQR-11** | Channel Normalization | `channel` | Normalized to Title Case standard (e.g. `Email`, `Social Media`, etc.) | Transformed automatically; rejected if empty |

---

## 2. Rejection Handling and Schema

All rejected records are written to `data/rejected/rejected_records.csv` with their original values preserved alongside a composite `rejection_reason` column.

### Example Rejection Log Entry:

```csv
record_id,campaign_id,campaign_name,channel,report_date,impressions,clicks,conversions,spend,revenue,rejection_reason
REC-ERR-01,CMP-101,Summer Sale Blitz,Email,2026-09-06,-5000,200,20,100.00,500.00,"Negative impressions not allowed: -5000.0"
REC-ERR-06,CMP-106,Back to School,Social Media,2026-09-06,1000,2500,50,300.00,900.00,"Metric violation: clicks (2500.0) cannot exceed impressions (1000.0)"
REC-001,CMP-101,Summer Sale Blitz Duplicate,Email,2026-09-01,12500,620,62,250.00,1860.00,"Duplicate record_id: 'REC-001' already seen in batch"
```

---

## 3. Safe Metric Calculations (Zero Division Safeguards)

To eliminate runtime errors and database calculation anomalies:
- **CTR**: `np.where(impressions > 0, (clicks / impressions) * 100, None)`
- **Conversion Rate**: `np.where(clicks > 0, (conversions / clicks) * 100, None)`
- **Cost Per Conversion**: `np.where(conversions > 0, spend / conversions, None)`
- **ROAS**: `np.where(spend > 0, revenue / spend, None)`
- In SQL: wrapped with `NULLIF(denominator, 0)` throughout all analytic queries.
