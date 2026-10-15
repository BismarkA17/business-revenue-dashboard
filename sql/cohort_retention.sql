-- Monthly cohort retention: of the customers whose first order was in month X,
-- what share ordered again N months later?
WITH orders AS (
    SELECT DISTINCT
        customer_id,
        date_trunc('month', invoice_date) AS order_month
    FROM filtered($start_date, $end_date, $countries)
    WHERE NOT is_return AND customer_id IS NOT NULL
),
first_orders AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM orders
    GROUP BY customer_id
),
activity AS (
    SELECT
        f.cohort_month,
        date_diff('month', f.cohort_month, o.order_month) AS months_since_first,
        COUNT(DISTINCT o.customer_id)                      AS active_customers
    FROM orders o
    JOIN first_orders f USING (customer_id)
    GROUP BY 1, 2
)
SELECT
    cohort_month,
    months_since_first,
    active_customers,
    FIRST_VALUE(active_customers) OVER (
        PARTITION BY cohort_month ORDER BY months_since_first
    ) AS cohort_size,
    active_customers::DOUBLE / FIRST_VALUE(active_customers) OVER (
        PARTITION BY cohort_month ORDER BY months_since_first
    ) AS retention_rate
FROM activity
ORDER BY cohort_month, months_since_first;
