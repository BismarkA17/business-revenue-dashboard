-- Segment-level summary of the RFM model (rfm.sql is inlined by analytics.py
-- as the `rfm` CTE).
SELECT
    segment,
    COUNT(*)                                  AS customers,
    SUM(monetary)                             AS revenue,
    SUM(monetary) / SUM(SUM(monetary)) OVER () AS revenue_share,
    MEDIAN(recency_days)                      AS median_recency_days,
    MEDIAN(frequency)                         AS median_orders
FROM rfm
GROUP BY segment
ORDER BY revenue DESC;
