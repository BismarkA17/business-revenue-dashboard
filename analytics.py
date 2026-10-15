"""Thin data-access layer: loads the cleaned transactions into DuckDB and runs
the SQL files in sql/ with the dashboard's filters as parameters.

All the analysis logic lives in the .sql files; this module only wires them up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"
DEFAULT_PARQUET = ROOT / "data" / "transactions.parquet"


@dataclass(frozen=True)
class Filters:
    start_date: date
    end_date: date  # exclusive
    countries: tuple[str, ...] = field(default_factory=tuple)

    def params(self) -> dict:
        return {
            "start_date": pd.Timestamp(self.start_date),
            "end_date": pd.Timestamp(self.end_date),
            "countries": list(self.countries),
        }


def _read_sql(name: str) -> str:
    return (SQL_DIR / f"{name}.sql").read_text().strip().rstrip(";")


def connect(source: Path | pd.DataFrame = DEFAULT_PARQUET) -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB database holding the transactions table."""
    con = duckdb.connect(database=":memory:")
    if isinstance(source, pd.DataFrame):
        con.register("transactions_df", source)
        con.execute("CREATE TABLE transactions AS SELECT * FROM transactions_df")
        con.unregister("transactions_df")
    else:
        con.execute("CREATE TABLE transactions AS SELECT * FROM read_parquet(?)", [str(source)])
    con.execute(_read_sql("00_setup"))
    return con


def run(con: duckdb.DuckDBPyConnection, name: str, filters: Filters, **extra) -> pd.DataFrame:
    """Run sql/<name>.sql with the given filters (plus any extra named params)."""
    sql = _read_sql(name)
    if name == "rfm_segments":
        sql = f"WITH rfm AS ({_read_sql('rfm')})\n{sql}"
    # A cursor gives each call its own connection to the shared database,
    # which keeps concurrent Streamlit sessions from interfering.
    cur = con.cursor()
    try:
        params = filters.params() | extra
        # Only pass the parameters the query actually uses.
        params = {k: v for k, v in params.items() if f"${k}" in sql}
        return cur.execute(sql, params).df()
    finally:
        cur.close()


def date_bounds(con: duckdb.DuckDBPyConnection) -> tuple[date, date]:
    lo, hi = con.execute("SELECT MIN(invoice_date)::DATE, MAX(invoice_date)::DATE FROM transactions").fetchone()
    return lo, hi


def countries(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute(
        "SELECT country FROM transactions GROUP BY country ORDER BY SUM(revenue) DESC"
    ).fetchall()
    return [r[0] for r in rows]
