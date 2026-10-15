-- Headline numbers for the selected period.
SELECT
    SUM(revenue) FILTER (WHERE NOT is_return)                      AS gross_revenue,
    -SUM(revenue) FILTER (WHERE is_return)                         AS returned_value,
    SUM(revenue)                                                   AS net_revenue,
    COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return)           AS orders,
    COUNT(DISTINCT customer_id) FILTER (WHERE NOT is_return)       AS customers,
    SUM(revenue) FILTER (WHERE NOT is_return)
        / NULLIF(COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return), 0) AS avg_order_value,
    -SUM(revenue) FILTER (WHERE is_return)
        / NULLIF(SUM(revenue) FILTER (WHERE NOT is_return), 0)     AS return_rate
FROM filtered($start_date, $end_date, $countries);
