-- ============================================================================
-- Phase 2: SQL Analytics Layer
-- Dynamic Pricing & Revenue Management — On-Demand Platform
-- Dialect: ANSI SQL / SQLite-compatible (minor tweaks noted for Postgres)
-- Source table: hourly_ops (loaded from dynamic_pricing_synthetic_data.csv)
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Q1. Hourly Demand-Supply Gap Ratio by Zone & Hour-of-Day
-- Business question: which zones/hours are structurally supply-constrained?
-- gap_ratio = (demand - supply) / supply  ->  averaged across all days in window
-- ----------------------------------------------------------------------------
CREATE DATABASE dynamic_pricing;
USE dynamic_pricing;
SELECT
    zone_id,
    hour,
    ROUND(AVG(demand_requests), 1)              AS avg_demand,
    ROUND(AVG(available_drivers), 1)             AS avg_supply,
    ROUND(AVG(demand_supply_gap_ratio), 3)       AS avg_gap_ratio,
    ROUND(AVG(surge_multiplier), 3)              AS avg_surge,
    ROUND(AVG(conversion_rate), 3)               AS avg_conversion
FROM hourly_ops
GROUP BY zone_id, hour
ORDER BY zone_id, avg_gap_ratio DESC;


-- ----------------------------------------------------------------------------
-- Q2. Surge Frequency & Distribution by Zone
-- Business question: how often — and how intensely — is surge pricing active?
-- ----------------------------------------------------------------------------
SELECT
    zone_id,
    CASE
        WHEN surge_multiplier <= 1.0 THEN '1.0x (base)'
        WHEN surge_multiplier <= 1.3 THEN '1.0x - 1.3x'
        WHEN surge_multiplier <= 1.6 THEN '1.3x - 1.6x'
        WHEN surge_multiplier <= 2.0 THEN '1.6x - 2.0x'
        ELSE '2.0x+'
    END                                          AS surge_bucket,
    COUNT(*)                                     AS hours_count,
    ROUND(100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM hourly_ops h2
         WHERE h2.zone_id = hourly_ops.zone_id), 1) AS pct_of_zone_hours,
    ROUND(AVG(conversion_rate), 3)               AS avg_conversion_in_bucket,
    ROUND(SUM(revenue), 0)                       AS total_revenue_in_bucket
FROM hourly_ops
GROUP BY zone_id, surge_bucket
ORDER BY zone_id, surge_bucket;


-- ----------------------------------------------------------------------------
-- Q3. Conversion Drop: Surge vs Non-Surge Hours (paired comparison)
-- Business question: what's the direct conversion cost of surge pricing?
-- ----------------------------------------------------------------------------
SELECT
    zone_id,
    ROUND(AVG(CASE WHEN surge_multiplier <= 1.05 THEN conversion_rate END), 3)
        AS conversion_at_base_price,
    ROUND(AVG(CASE WHEN surge_multiplier > 1.05 THEN conversion_rate END), 3)
        AS conversion_during_surge,
    ROUND(
        AVG(CASE WHEN surge_multiplier <= 1.05 THEN conversion_rate END) -
        AVG(CASE WHEN surge_multiplier > 1.05 THEN conversion_rate END)
    , 3)                                          AS absolute_conversion_drop,
    ROUND(
        100.0 * (
            AVG(CASE WHEN surge_multiplier <= 1.05 THEN conversion_rate END) -
            AVG(CASE WHEN surge_multiplier > 1.05 THEN conversion_rate END)
        ) / NULLIF(AVG(CASE WHEN surge_multiplier <= 1.05 THEN conversion_rate END), 0)
    , 1)                                          AS pct_conversion_drop
FROM hourly_ops
GROUP BY zone_id;


-- ----------------------------------------------------------------------------
-- Q4. Top 10 Most Supply-Constrained Hours (operational stress points)
-- Business question: where should driver incentive programs be targeted first?
-- ----------------------------------------------------------------------------
SELECT
    zone_id, timestamp, hour, day_of_week, weather,
    demand_requests, available_drivers, demand_supply_gap_ratio,
    surge_multiplier, fulfillment_rate
FROM hourly_ops
ORDER BY demand_supply_gap_ratio DESC
LIMIT 10;
SELECT COUNT(*) FROM hourly_ops;


-- ----------------------------------------------------------------------------
-- Q5. Revenue Concentration by Surge Bucket (Pareto check)
-- Business question: how much of total revenue depends on surge pricing?
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN surge_multiplier <= 1.05 THEN 'Base price' ELSE 'Surge-priced' END AS pricing_state,
    COUNT(*)                                     AS hours_count,
    ROUND(SUM(revenue), 0)                       AS total_revenue,
    ROUND(100.0 * SUM(revenue) /
        (SELECT SUM(revenue) FROM hourly_ops), 1) AS pct_of_total_revenue
FROM hourly_ops
GROUP BY pricing_state;


-- ----------------------------------------------------------------------------
-- Q6. Driver Payout Floor Violations — labor/fairness risk audit
-- Business question: how often does base pricing fail to clear the minimum
-- driver payout threshold (a churn-of-supply risk)?
-- ----------------------------------------------------------------------------
SELECT
    zone_id,
    COUNT(*)                                                       AS total_hours,
    SUM(CASE WHEN payout_below_floor_flag THEN 1 ELSE 0 END)       AS floor_violation_hours,
    ROUND(100.0 * SUM(CASE WHEN payout_below_floor_flag THEN 1 ELSE 0 END)
          / COUNT(*), 1)                                           AS pct_violation_hours
FROM hourly_ops
GROUP BY zone_id
ORDER BY pct_violation_hours DESC;


-- ----------------------------------------------------------------------------
-- Q7. Weekday vs Weekend Demand-Supply & Revenue Comparison
-- ----------------------------------------------------------------------------
SELECT
    zone_id,
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END      AS day_type,
    ROUND(AVG(demand_supply_gap_ratio), 3)                          AS avg_gap_ratio,
    ROUND(AVG(surge_multiplier), 3)                                 AS avg_surge,
    ROUND(AVG(conversion_rate), 3)                                  AS avg_conversion,
    ROUND(AVG(revenue), 0)                                          AS avg_hourly_revenue
FROM hourly_ops
GROUP BY zone_id, day_type
ORDER BY zone_id, day_type;


-- ----------------------------------------------------------------------------
-- Q8. Weather Impact on Operational Metrics
-- Business question: does bad weather worsen the gap ratio AND suppress
-- conversion simultaneously (a compounding risk period)?
-- ----------------------------------------------------------------------------
SELECT
    weather,
    ROUND(AVG(demand_supply_gap_ratio), 3)       AS avg_gap_ratio,
    ROUND(AVG(surge_multiplier), 3)              AS avg_surge,
    ROUND(AVG(conversion_rate), 3)               AS avg_conversion,
    ROUND(AVG(est_churn_risk), 4)                AS avg_churn_risk
FROM hourly_ops
GROUP BY weather
ORDER BY avg_gap_ratio DESC;


-- ----------------------------------------------------------------------------
-- Q9. Rolling 7-Day Revenue Trend by Zone (window function)
-- Note: SQLite 3.25+/Postgres support window functions natively.
-- ----------------------------------------------------------------------------
SELECT
    zone_id,
    date,
    SUM(revenue) AS daily_revenue,
    ROUND(AVG(SUM(revenue)) OVER (
        PARTITION BY zone_id
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) AS rolling_7day_avg_revenue
FROM hourly_ops
GROUP BY zone_id, date
ORDER BY zone_id, date;