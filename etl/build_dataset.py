"""Download and clean the UCI Online Retail II dataset.

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
(real transactions from a UK-based online gift retailer, Dec 2009 - Dec 2011)

Usage:
    python etl/build_dataset.py              # downloads the raw file if missing
    python etl/build_dataset.py --raw path/to/online_retail_II.xlsx

Outputs:
    data/transactions.parquet   cleaned line items (sales and returns)
    data/cleaning_report.json   how many rows each cleaning rule removed
"""

from __future__ import annotations

import argparse
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_PARQUET = ROOT / "data" / "transactions.parquet"
OUT_REPORT = ROOT / "data" / "cleaning_report.json"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"

# Real product codes are five digits, sometimes followed by a letter variant
# (e.g. 85123A). Everything else is postage, fees, discounts, manual
# adjustments, test rows, etc. and is not product revenue.
PRODUCT_CODE_PATTERN = r"^\d{5}[A-Za-z]{0,2}$"


def download_raw() -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / "online_retail_II.xlsx"
    if target.exists():
        return target
    print(f"Downloading {SOURCE_URL} ...")
    with urllib.request.urlopen(SOURCE_URL, timeout=300) as resp:
        payload = resp.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".xlsx"))
        target.write_bytes(zf.read(name))
    return target


def load_raw(path: Path) -> pd.DataFrame:
    # The workbook has one sheet per year (2009-2010 and 2010-2011).
    sheets = pd.read_excel(path, sheet_name=None, dtype={"Invoice": str, "StockCode": str})
    return pd.concat(sheets.values(), ignore_index=True)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply cleaning rules in order and record how many rows each removes."""
    report: dict = {"raw_rows": int(len(raw)), "steps": []}
    df = raw.rename(
        columns={
            "Invoice": "invoice",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "Price": "unit_price",
            "Customer ID": "customer_id",
            "Country": "country",
        }
    )
    df["invoice"] = df["invoice"].astype(str).str.strip()
    df["stock_code"] = df["stock_code"].astype(str).str.strip().str.upper()

    def step(name: str, mask: pd.Series) -> None:
        nonlocal df
        removed = int((~mask).sum())
        df = df[mask].copy()
        report["steps"].append({"rule": name, "rows_removed": removed, "rows_left": int(len(df))})

    step("drop exact duplicate rows", ~df.duplicated())
    step("drop non-product codes (postage, fees, discounts, manual adjustments)",
         df["stock_code"].str.match(PRODUCT_CODE_PATTERN))
    # 'A' invoices are bad-debt adjustments, not customer transactions.
    step("drop bad-debt adjustment invoices", ~df["invoice"].str.startswith("A"))
    step("drop zero or negative unit prices", df["unit_price"] > 0)
    step("drop zero quantities", df["quantity"] != 0)

    df["is_return"] = df["invoice"].str.startswith("C")
    # A negative quantity on a non-cancellation invoice is a stock write-off, not a sale.
    step("drop stock write-offs (negative qty without a cancellation invoice)",
         df["is_return"] | (df["quantity"] > 0))

    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["customer_id"] = df["customer_id"].astype("Int64")
    df["description"] = df["description"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip()

    report["clean_rows"] = int(len(df))
    report["sales_rows"] = int((~df["is_return"]).sum())
    report["return_rows"] = int(df["is_return"].sum())
    report["rows_without_customer_id"] = int(df["customer_id"].isna().sum())
    report["date_min"] = str(df["invoice_date"].min())
    report["date_max"] = str(df["invoice_date"].max())

    cols = ["invoice", "invoice_date", "stock_code", "description", "quantity",
            "unit_price", "revenue", "customer_id", "country", "is_return"]
    return df[cols].sort_values("invoice_date").reset_index(drop=True), report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, help="path to online_retail_II.xlsx")
    args = parser.parse_args()

    raw_path = args.raw or download_raw()
    raw = load_raw(raw_path)
    cleaned, report = clean(raw)

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(OUT_PARQUET, index=False, compression="zstd")
    OUT_REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
