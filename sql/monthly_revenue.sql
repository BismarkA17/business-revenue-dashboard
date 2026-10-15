-- Net revenue, orders and active customers per calendar month.
SELECT
    date_trunc('month', invoice_date)                         AS month,
    SUM(revenue)                                              AS net_revenue,
    COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return)      AS orders,
    COUNT(DISTINCT customer_id) FILTER (WHERE NOT is_return)  AS active_customers
FROM filtered($start_date, $end_date, $countries)
GROUP BY 1
ORDER BY 1;
