-- Seed data for testing database tables independently
-- Database: marketing_analytics

USE marketing_analytics;

-- Seed campaigns
INSERT INTO campaigns (campaign_id, campaign_name, channel)
VALUES 
    ('CMP-101', 'Summer Sale Blitz', 'Email'),
    ('CMP-102', 'Fall Clearance', 'Social Media'),
    ('CMP-103', 'Tech Gadgets Promo', 'Search Ads')
ON DUPLICATE KEY UPDATE 
    campaign_name = VALUES(campaign_name),
    channel = VALUES(channel);

-- Seed campaign metrics
INSERT INTO campaign_metrics (record_id, campaign_id, report_date, impressions, clicks, conversions, spend, revenue, ctr, conversion_rate, cost_per_conversion, roas)
VALUES
    ('REC-001', 'CMP-101', '2026-09-01', 12500, 620, 62, 250.00, 1860.00, 4.9600, 10.0000, 4.03, 7.44),
    ('REC-002', 'CMP-102', '2026-09-01', 24000, 960, 48, 480.00, 1440.00, 4.0000, 5.0000, 10.00, 3.00),
    ('REC-003', 'CMP-103', '2026-09-01', 18000, 720, 72, 400.00, 2520.00, 4.0000, 10.0000, 5.56, 6.30)
ON DUPLICATE KEY UPDATE
    impressions = VALUES(impressions),
    clicks = VALUES(clicks),
    conversions = VALUES(conversions),
    spend = VALUES(spend),
    revenue = VALUES(revenue),
    ctr = VALUES(ctr),
    conversion_rate = VALUES(conversion_rate),
    cost_per_conversion = VALUES(cost_per_conversion),
    roas = VALUES(roas);
