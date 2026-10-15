"""Check each SQL query against a tiny dataset with hand-computed answers."""
from datetime import date

import pandas as pd
import pytest

import analytics as an


def tx(invoice, when, customer, qty, price, country="United Kingdom", code="10001", desc="WIDGET"):
    return {
        "invoice": invoice, "invoice_date": pd.Timestamp(when), "stock_code": code, "description": desc,
        "quantity": qty, "unit_price": price, "revenue": round(qty * price, 2),
        "customer_id": customer, "country": country, "is_return": invoice.startswith("C"),
    }


@pytest.fixture(scope="module")
def con():
    rows = [
        # customer 1: orders in Jan and Feb (retained), big spender
        tx("1", "2010-01-04 10:00", 1, 10, 10.0),          # 100
        tx("2", "2010-02-10 11:00", 1, 10, 10.0),          # 100
        # customer 2: one order in Jan, part returned
        tx("3", "2010-01-20 12:00", 2, 5, 10.0, code="10002", desc="GADGET"),   # 50
        tx("C4", "2010-01-21 12:00", 2, -2, 10.0, code="10002", desc="GADGET"),  # -20
        # customer 3: one order in Feb, in France
        tx("5", "2010-02-15 09:00", 3, 3, 10.0, country="France"),               # 30
        # guest checkout (no customer id)
        tx("6", "2010-02-20 14:00", None, 1, 10.0),                              # 10
    ]
    df = pd.DataFrame(rows)
    df["customer_id"] = df["customer_id"].astype("Int64")
    return an.connect(df)


ALL = an.Filters(date(2010, 1, 1), date(2010, 3, 1))


def test_kpis(con):
    k = an.run(con, "kpis", ALL).iloc[0]
    assert k["gross_revenue"] == pytest.approx(290)
    assert k["returned_value"] == pytest.approx(20)
    assert k["net_revenue"] == pytest.approx(270)
    assert k["orders"] == 5
    assert k["customers"] == 3          # guest not counted
    assert k["avg_order_value"] == pytest.approx(58)
    assert k["return_rate"] == pytest.approx(20 / 290)


def test_filters_country_and_exclusive_end_date(con):
    france = an.run(con, "kpis", an.Filters(date(2010, 1, 1), date(2010, 3, 1), ("France",))).iloc[0]
    assert france["net_revenue"] == pytest.approx(30)
    jan = an.run(con, "kpis", an.Filters(date(2010, 1, 1), date(2010, 2, 1))).iloc[0]
    assert jan["net_revenue"] == pytest.approx(130)


def test_monthly_revenue(con):
    m = an.run(con, "monthly_revenue", ALL)
    assert m["net_revenue"].tolist() == pytest.approx([130, 140])
    assert m["active_customers"].tolist() == [2, 2]


def test_cohort_retention(con):
    c = an.run(con, "cohort_retention", ALL)
    jan = c[c["cohort_month"] == pd.Timestamp("2010-01-01")].set_index("months_since_first")
    assert jan.loc[0, "cohort_size"] == 2
    assert jan.loc[1, "retention_rate"] == pytest.approx(0.5)   # only customer 1 came back


def test_rfm_ties_share_a_score(con):
    r = an.run(con, "rfm", ALL).set_index("customer_id")
    assert set(r.index) == {1, 2, 3}
    # customers 2 and 3 both have exactly one order, so they must share an F score
    assert r.loc[2, "f_score"] == r.loc[3, "f_score"]
    assert r.loc[1, "f_score"] > r.loc[2, "f_score"]
    assert r.loc[1, "monetary"] == pytest.approx(200)


def test_rfm_segments_cover_all_customers(con):
    s = an.run(con, "rfm_segments", ALL)
    assert s["customers"].sum() == 3
    assert s["revenue_share"].sum() == pytest.approx(1)


def test_customer_concentration_ends_at_100_percent(con):
    p = an.run(con, "customer_concentration", ALL)
    assert p["revenue_share"].iloc[0] == pytest.approx(200 / 260)
    assert p["revenue_share"].iloc[-1] == pytest.approx(1)
    assert p["customer_share"].iloc[-1] == pytest.approx(1)


def test_products_and_returns(con):
    top = an.run(con, "top_products", ALL, limit=5)
    assert top.iloc[0]["stock_code"] == "10001"
    assert top.iloc[0]["net_revenue"] == pytest.approx(240)
    ret = an.run(con, "most_returned", ALL, limit=5, min_sales=40)
    assert ret["stock_code"].tolist() == ["10002"]
    assert ret.iloc[0]["return_rate"] == pytest.approx(0.4)
    assert an.run(con, "most_returned", ALL, limit=5, min_sales=60).empty


def test_country_and_timing(con):
    geo = an.run(con, "country_revenue", ALL)
    assert geo.iloc[0]["country"] == "United Kingdom"
    assert geo["revenue_share"].sum() == pytest.approx(1)
    t = an.run(con, "weekday_hour", ALL)
    assert t["orders"].sum() == 5
