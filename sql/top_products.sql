-- Best-selling products by net revenue, with their return rate.
SELECT
    stock_code,
    ANY_VALUE(description) FILTER (WHERE NOT is_return)  AS description,
    SUM(revenue) FILTER (WHERE NOT is_return)            AS gross_revenue,
    -COALESCE(SUM(revenue) FILTER (WHERE is_return), 0)  AS returned_value,
    SUM(revenue)                                         AS net_revenue,
    SUM(quantity) FILTER (WHERE NOT is_return)           AS units_sold,
    -COALESCE(SUM(revenue) FILTER (WHERE is_return), 0)
        / NULLIF(SUM(revenue) FILTER (WHERE NOT is_return), 0) AS return_rate
FROM filtered($start_date, $end_date, $countries)
GROUP BY stock_code
ORDER BY net_revenue DESC
LIMIT $limit;
