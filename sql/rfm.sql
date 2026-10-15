-- RFM segmentation: score every customer 1-5 on Recency, Frequency and
-- Monetary value, then map score combinations to named segments.
WITH base AS (
    SELECT * FROM filtered($start_date, $end_date, $countries)
    WHERE customer_id IS NOT NULL
),
ref AS (
    SELECT MAX(invoice_date)::DATE + 1 AS ref_date FROM base
),
per_customer AS (
    SELECT
        customer_id,
        date_diff('day', MAX(invoice_date) FILTER (WHERE NOT is_return)::DATE,
                  (SELECT ref_date FROM ref))                    AS recency_days,
        COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return)     AS frequency,
        SUM(revenue)                                             AS monetary
    FROM base
    GROUP BY customer_id
    HAVING COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return) > 0
       AND SUM(revenue) > 0
),
scored AS (
    SELECT
        *,
        6 - NTILE(5) OVER (ORDER BY recency_days) AS r_score,  -- recent = high
        NTILE(5) OVER (ORDER BY frequency)        AS f_score,
        NTILE(5) OVER (ORDER BY monetary)         AS m_score
    FROM per_customer
)
SELECT
    *,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost / Hibernating'
        ELSE 'Needs Attention'
    END AS segment
FROM scored;
