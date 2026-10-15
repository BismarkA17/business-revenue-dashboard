-- When do orders come in? Orders by day of week and hour of day.
SELECT
    dayname(invoice_date)                 AS weekday,
    isodow(invoice_date)                  AS weekday_num,
    hour(invoice_date)                    AS hour,
    COUNT(DISTINCT invoice)               AS orders,
    SUM(revenue)                          AS revenue
FROM filtered($start_date, $end_date, $countries)
WHERE NOT is_return
GROUP BY ALL
ORDER BY weekday_num, hour;
