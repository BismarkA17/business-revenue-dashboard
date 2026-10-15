-- Products losing the most money to returns (minimum sales threshold so a
-- single cancelled order on a niche item doesn't dominate).
SELECT
    stock_code,
    ANY_VALUE(description) FILTER (WHERE NOT is_return)  AS description,
    SUM(revenue) FILTER (WHERE NOT is_return)            AS gross_revenue,
    -SUM(revenue) FILTER (WHERE is_return)               AS returned_value,
    -SUM(revenue) FILTER (WHERE is_return)
        / NULLIF(SUM(revenue) FILTER (WHERE NOT is_return), 0) AS return_rate
FROM filtered($start_date, $end_date, $countries)
GROUP BY stock_code
HAVING SUM(revenue) FILTER (WHERE NOT is_return) >= $min_sales
   AND SUM(revenue) FILTER (WHERE is_return) < 0
ORDER BY returned_value DESC
LIMIT $limit;
