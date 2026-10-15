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
        ROUND(SUM(revenue), 2)                                   AS monetary
    FROM base
    GROUP BY customer_id
    HAVING COUNT(DISTINCT invoice) FILTER (WHERE NOT is_return) > 0
       AND ROUND(SUM(revenue), 2) > 0
),
scored AS (
    SELECT
        *,
        -- Quintile scores 1-5 via CUME_DIST so tied customers always share a
        -- score (NTILE would split ties arbitrarily, e.g. one-time buyers).
        CEIL(CUME_DIST() OVER (ORDER BY recency_days DESC) * 5)::INT AS r_score,  -- recent = high
        CEIL(CUME_DIST() OVER (ORDER BY frequency) * 5)::INT         AS f_score,
        CEIL(CUME_DIST() OVER (ORDER BY monetary) * 5)::INT          AS m_score
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
