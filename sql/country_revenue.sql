-- Net revenue and customers by country.
SELECT
    country,
    SUM(revenue)                                             AS net_revenue,
    COUNT(DISTINCT customer_id) FILTER (WHERE NOT is_return) AS customers,
    COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return)     AS orders,
    SUM(revenue) / SUM(SUM(revenue)) OVER ()                 AS revenue_share
FROM filtered($start_date, $end_date, $countries)
GROUP BY country
ORDER BY net_revenue DESC;
