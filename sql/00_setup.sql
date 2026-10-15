-- Base objects every analysis query builds on.
-- `transactions` is loaded from data/transactions.parquet by analytics.py.

-- Table macro: the transactions inside the dashboard's current filters.
-- An empty country list means "all countries".
CREATE OR REPLACE MACRO filtered(start_date, end_date, countries) AS TABLE
    SELECT *
    FROM transactions
    WHERE invoice_date >= start_date
      AND invoice_date < end_date
      AND (len(countries) = 0 OR list_contains(countries, country));
