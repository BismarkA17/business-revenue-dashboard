-- Pareto curve: cumulative share of revenue vs share of customers,
-- customers ranked from highest to lowest net revenue.
WITH per_customer AS (
    SELECT customer_id, SUM(revenue) AS revenue
    FROM filtered($start_date, $end_date, $countries)
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
    HAVING ROUND(SUM(revenue), 2) > 0
)
SELECT
    ROW_NUMBER() OVER (ORDER BY revenue DESC)::DOUBLE / COUNT(*) OVER ()  AS customer_share,
    SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
        / SUM(revenue) OVER ()                                            AS revenue_share
FROM per_customer
ORDER BY customer_share;
