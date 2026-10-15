import pandas as pd

from etl.build_dataset import clean


def raw_rows(rows):
    cols = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
    return pd.DataFrame(rows, columns=cols)


def test_cleaning_rules():
    t = pd.Timestamp("2010-01-05 10:00")
    raw = raw_rows([
        ["1001", "85123A", "HEART HOLDER", 6, t, 2.55, 17850, "United Kingdom"],   # kept
        ["1001", "85123A", "HEART HOLDER", 6, t, 2.55, 17850, "United Kingdom"],   # exact duplicate
        ["1001", "POST", "POSTAGE", 1, t, 18.0, 17850, "United Kingdom"],         # non-product
        ["1002", "22423", "CAKESTAND", 2, t, 0.0, 12346, "France"],               # zero price
        ["C1003", "22423", "CAKESTAND", -1, t, 12.75, 12346, "France"],            # return, kept
        ["1004", "22423", "CAKESTAND", -5, t, 12.75, None, "United Kingdom"],      # write-off
        ["A1005", "B", "Adjust bad debt", 1, t, 100.0, None, "United Kingdom"],    # adjustment
    ])
    df, report = clean(raw)

    assert len(df) == 2
    assert report["raw_rows"] == 7
    assert sum(s["rows_removed"] for s in report["steps"]) == 5
    sale = df[~df["is_return"]].iloc[0]
    assert sale["revenue"] == 15.30
    ret = df[df["is_return"]].iloc[0]
    assert ret["revenue"] == -12.75
