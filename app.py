"""Retail Revenue & Customer Analytics dashboard.

Real transactions from a UK online gift retailer (UCI Online Retail II,
Dec 2009 - Dec 2011). Analysis is done in SQL (see sql/), this file only
handles layout and charts.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an

st.set_page_config(page_title="Retail Revenue & Customer Analytics", page_icon="📊", layout="wide")

ACCENT = "#2E6FDB"
SEGMENT_ORDER = ["Champions", "Loyal", "New / Promising", "Needs Attention", "At Risk", "Lost / Hibernating"]
SEGMENT_COLOURS = {
    "Champions": "#2E6FDB",
    "Loyal": "#5B9BEA",
    "New / Promising": "#2BA38A",
    "Needs Attention": "#C9A227",
    "At Risk": "#D9622B",
    "Lost / Hibernating": "#9AA0A6",
}


@st.cache_resource
def get_connection():
    return an.connect()


@st.cache_data(show_spinner=False)
def query(name: str, filters: an.Filters, **extra) -> pd.DataFrame:
    return an.run(get_connection(), name, filters, **extra)


def gbp(x: float, decimals: int = 0) -> str:
    if pd.isna(x):
        return "–"
    if abs(x) >= 1_000_000:
        return f"£{x / 1_000_000:.2f}M"
    if abs(x) >= 10_000:
        return f"£{x / 1_000:.0f}k"
    return f"£{x:,.{decimals}f}"


def pct(x: float, decimals: int = 1) -> str:
    return "–" if pd.isna(x) else f"{x * 100:.{decimals}f}%"


def delta(cur: float, prev: float) -> str | None:
    if pd.isna(prev) or not prev:
        return None
    return f"{(cur / prev - 1) * 100:+.1f}% vs prior period"


def style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified",
                      legend=dict(orientation="h", y=1.08, x=0, title=None))
    return fig


# ---------------------------------------------------------------- sidebar
con = get_connection()
data_start, data_end = an.date_bounds(con)
all_countries = an.countries(con)

st.sidebar.header("Filters")
picked = st.sidebar.date_input(
    "Date range", value=(data_start, data_end), min_value=data_start, max_value=data_end
)
start, end = (picked if isinstance(picked, tuple) and len(picked) == 2 else (data_start, data_end))
countries = st.sidebar.multiselect("Countries", all_countries, placeholder="All countries")

filters = an.Filters(start, end + timedelta(days=1), tuple(countries))
period_days = (end - start).days + 1
prior = an.Filters(start - timedelta(days=period_days), start, tuple(countries))

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) — "
    "1.07M real line items from a UK online gift wholesaler/retailer, "
    f"{data_start:%d %b %Y} to {data_end:%d %b %Y}. December 2011 is a partial month."
)

# ---------------------------------------------------------------- header + KPIs
st.title("Retail Revenue & Customer Analytics")
st.caption("Where the revenue comes from, which customers drive it, and where it leaks.")

k = query("kpis", filters).iloc[0]
kp = query("kpis", prior).iloc[0]

if pd.isna(k["gross_revenue"]):
    st.warning("No sales in the selected filters.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Net revenue", gbp(k["net_revenue"]), delta(k["net_revenue"], kp["net_revenue"]))
c2.metric("Orders", f"{int(k['orders']):,}", delta(k["orders"], kp["orders"]))
c3.metric("Customers", f"{int(k['customers']):,}", delta(k["customers"], kp["customers"]))
c4.metric("Avg order value", gbp(k["avg_order_value"], 2), delta(k["avg_order_value"], kp["avg_order_value"]))
c5.metric("Returns (% of sales)", pct(k["return_rate"]),
          delta(k["return_rate"], kp["return_rate"]), delta_color="inverse")

overview, customers_tab, products_tab, markets_tab, method_tab = st.tabs(
    ["Revenue", "Customers", "Products & returns", "Markets & timing", "Data & method"]
)

# ---------------------------------------------------------------- revenue
with overview:
    monthly = query("monthly_revenue", filters)
    if len(monthly) >= 2:
        peak = monthly.loc[monthly["net_revenue"].idxmax()]
        q4 = monthly[monthly["month"].dt.month.isin([9, 10, 11])]["net_revenue"].sum()
        st.info(
            f"**Strongly seasonal.** The peak month was **{peak['month']:%B %Y}** "
            f"({gbp(peak['net_revenue'])}). September–November delivered "
            f"**{pct(q4 / monthly['net_revenue'].sum(), 0)}** of revenue in this period — "
            "stock, staffing and marketing need to be planned around the run-up to Christmas."
        )
    fig = px.bar(monthly, x="month", y="net_revenue", labels={"month": "", "net_revenue": "Net revenue (£)"},
                 color_discrete_sequence=[ACCENT])
    st.plotly_chart(style(fig), width="stretch")

    left, right = st.columns(2)
    with left:
        st.markdown("**Orders per month**")
        st.plotly_chart(style(px.line(monthly, x="month", y="orders", markers=True,
                                      labels={"month": "", "orders": "Orders"},
                                      color_discrete_sequence=[ACCENT]), 260),
                        width="stretch")
    with right:
        st.markdown("**Active customers per month**")
        st.plotly_chart(style(px.line(monthly, x="month", y="active_customers", markers=True,
                                      labels={"month": "", "active_customers": "Customers"},
                                      color_discrete_sequence=[ACCENT]), 260),
                        width="stretch")

# ---------------------------------------------------------------- customers
with customers_tab:
    pareto = query("customer_concentration", filters)
    segments = query("rfm_segments", filters)

    if not pareto.empty:
        top1 = pareto.loc[pareto["customer_share"] <= 0.01, "revenue_share"].max()
        top20 = pareto.loc[pareto["customer_share"] <= 0.20, "revenue_share"].max()
        at_risk = segments.set_index("segment").reindex(["At Risk"]).iloc[0]
        st.info(
            f"**Revenue is highly concentrated.** The top 1% of customers generate **{pct(top1, 0)}** of revenue "
            f"and the top 20% generate **{pct(top20, 0)}**. "
            + (f"**{int(at_risk['customers']):,} 'At Risk' customers** — previously frequent buyers who have gone "
               f"quiet (median {int(at_risk['median_recency_days'])} days since last order) — account for "
               f"{gbp(at_risk['revenue'])} of revenue: the obvious win-back target."
               if pd.notna(at_risk["customers"]) else "")
        )

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("**RFM segments** — customers scored on Recency, Frequency and Monetary value")
        seg = segments.set_index("segment").reindex(SEGMENT_ORDER).dropna(how="all").reset_index()
        fig = px.bar(seg, x="revenue", y="segment", orientation="h", color="segment",
                     color_discrete_map=SEGMENT_COLOURS, text=seg["revenue_share"].map(lambda v: pct(v, 0 if v >= 0.01 else 1)),
                     custom_data=["customers", "median_recency_days", "median_orders"],
                     labels={"revenue": "Revenue (£)", "segment": ""})
        fig.update_traces(hovertemplate="%{y}<br>Revenue £%{x:,.0f}<br>%{customdata[0]:,} customers"
                                        "<br>Median %{customdata[1]:.0f} days since last order"
                                        "<br>Median %{customdata[2]:.0f} orders<extra></extra>")
        fig.update_layout(showlegend=False, yaxis=dict(categoryorder="array", categoryarray=SEGMENT_ORDER[::-1]),
                          hovermode="closest")
        st.plotly_chart(style(fig), width="stretch")
    with right:
        st.markdown("**Customer concentration** — cumulative share of revenue")
        fig = go.Figure()
        fig.add_scatter(x=pareto["customer_share"], y=pareto["revenue_share"], mode="lines",
                        line=dict(color=ACCENT, width=3), name="Actual",
                        hovertemplate="Top %{x:.0%} of customers → %{y:.0%} of revenue<extra></extra>")
        fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dot", color="#9AA0A6"),
                        name="If every customer spent the same", hoverinfo="skip")
        fig.update_layout(xaxis=dict(tickformat=".0%", title="Share of customers (highest spenders first)"),
                          yaxis=dict(tickformat=".0%", title="Share of revenue"), hovermode="closest")
        st.plotly_chart(style(fig), width="stretch")

    st.markdown("**Monthly cohort retention** — share of each month's new customers who ordered again N months later")
    cohorts = query("cohort_retention", filters)
    if not cohorts.empty:
        grid = cohorts.pivot(index="cohort_month", columns="months_since_first", values="retention_rate")
        grid.index = grid.index.strftime("%b %Y")
        fig = px.imshow(grid, color_continuous_scale="Blues", zmin=0, zmax=0.5, aspect="auto",
                        labels=dict(x="Months since first order", y="First-order month", color="Retained"))
        fig.update_traces(hovertemplate="%{y} cohort, month %{x}: %{z:.0%} ordered<extra></extra>")
        fig.update_coloraxes(colorbar_tickformat=".0%")
        st.plotly_chart(style(fig, 520), width="stretch")
        later = cohorts[(cohorts["cohort_month"] > cohorts["cohort_month"].min()) & (cohorts["months_since_first"] == 1)]
        if not later.empty:
            st.caption(
                f"On average only **{pct(later['active_customers'].sum() / later['cohort_size'].sum(), 0)}** of new "
                "customers order again the following month. The first cohort looks unusually loyal because it "
                "includes existing customers whose earlier orders pre-date the dataset."
            )

# ---------------------------------------------------------------- products
with products_tab:
    top = query("top_products", filters, limit=15)
    returned = query("most_returned", filters, limit=10, min_sales=5_000)

    left, right = st.columns(2)
    with left:
        st.markdown("**Top 15 products by net revenue**")
        top["label"] = top["description"].str.title().str.slice(0, 38)
        fig = px.bar(top, x="net_revenue", y="label", orientation="h", color_discrete_sequence=[ACCENT],
                     custom_data=["units_sold", "return_rate"],
                     labels={"net_revenue": "Net revenue (£)", "label": ""})
        fig.update_traces(hovertemplate="%{y}<br>£%{x:,.0f}<br>%{customdata[0]:,.0f} units"
                                        "<br>%{customdata[1]:.1%} returned<extra></extra>")
        fig.update_layout(yaxis=dict(autorange="reversed"), hovermode="closest")
        st.plotly_chart(style(fig, 480), width="stretch")
    with right:
        st.markdown("**Biggest losses to returns and cancellations**")
        st.dataframe(
            returned.assign(description=returned["description"].str.title(),
                            return_rate=returned["return_rate"] * 100)[
                ["description", "gross_revenue", "returned_value", "return_rate"]],
            column_config={
                "description": "Product",
                "gross_revenue": st.column_config.NumberColumn("Sold", format="£%.0f"),
                "returned_value": st.column_config.NumberColumn("Returned", format="£%.0f"),
                "return_rate": st.column_config.NumberColumn("Return rate", format="%.0f%%"),
            },
            hide_index=True, width="stretch",
        )
        st.caption(
            "Items near 100% returned are mostly **order-entry errors**, not unhappy customers: e.g. a single "
            "order of 80,995 'Paper Craft, Little Birdie' (£168k) was cancelled 12 minutes later. Two such "
            "mistakes make up about a third of all returned value in the dataset — a data-quality issue worth "
            "a validation rule (e.g. flag orders far above a customer's normal quantity)."
        )

# ---------------------------------------------------------------- markets + timing
with markets_tab:
    geo = query("country_revenue", filters)
    timing = query("weekday_hour", filters)

    left, right = st.columns(2)
    with left:
        st.markdown("**Revenue by country**")
        top_geo = geo.head(12).copy()
        top_geo.loc[len(top_geo)] = ["All other countries", geo["net_revenue"].iloc[12:].sum(),
                                     geo["customers"].iloc[12:].sum(), geo["orders"].iloc[12:].sum(),
                                     geo["revenue_share"].iloc[12:].sum()]
        top_geo = top_geo[top_geo["net_revenue"] > 0]
        fig = px.bar(top_geo, x="net_revenue", y="country", orientation="h", color_discrete_sequence=[ACCENT],
                     text=top_geo["revenue_share"].map(lambda v: pct(v, 1)),
                     labels={"net_revenue": "Net revenue (£)", "country": ""})
        fig.update_layout(yaxis=dict(autorange="reversed"), hovermode="closest")
        st.plotly_chart(style(fig, 440), width="stretch")
        if len(geo) > 1:
            note = f"{geo.iloc[0]['country']} accounts for {pct(geo.iloc[0]['revenue_share'], 0)} of revenue."
            eire = geo[geo["country"] == "EIRE"]
            if not eire.empty and eire.iloc[0]["customers"] <= 5:
                note += (f" Some export markets are a handful of wholesale accounts — EIRE is "
                         f"{pct(eire.iloc[0]['revenue_share'])} of revenue from just "
                         f"{int(eire.iloc[0]['customers'])} identified customers, a concentration risk.")
            st.caption(note)
    with right:
        st.markdown("**When orders are placed** (orders by weekday and hour)")
        if not timing.empty:
            heat = timing.pivot_table(index="weekday", columns="hour", values="orders", aggfunc="sum").fillna(0)
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            heat = heat.reindex([d for d in order if d in heat.index])
            fig = px.imshow(heat, color_continuous_scale="Blues", aspect="auto",
                            labels=dict(x="Hour of day", y="", color="Orders"))
            fig.update_traces(hovertemplate="%{y} %{x}:00 — %{z:,} orders<extra></extra>")
            st.plotly_chart(style(fig, 440), width="stretch")
            busiest = timing.groupby("weekday")["orders"].sum().idxmax()
            st.caption(f"Orders cluster on weekday lunchtimes (busiest day: {busiest}), with almost no Saturday "
                       "trading — consistent with a business-to-business customer base.")

# ---------------------------------------------------------------- method
with method_tab:
    import json
    from pathlib import Path

    report = json.loads((Path(__file__).parent / "data" / "cleaning_report.json").read_text())
    st.markdown(
        f"""
**Source.** [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii): every transaction
of a UK-based, non-store online retailer of giftware (many customers are wholesalers), 1 Dec 2009 – 9 Dec 2011.

**Pipeline.** `etl/build_dataset.py` downloads the raw Excel file ({report['raw_rows']:,} rows), applies the
cleaning rules below and writes a compressed Parquet file. The dashboard loads it into an in-memory
**DuckDB** database, and every chart is driven by a plain SQL file in `sql/` (CTEs, window functions,
`NTILE` scoring for RFM, a table macro for filters).

**Definitions.**
- *Net revenue* = sales minus returns/cancellations (invoices starting with `C`).
- *Return rate* = value returned ÷ value sold.
- *Customers* counts identified customers only; {report['rows_without_customer_id']:,} rows (guest checkouts)
  have no customer ID — they count towards revenue but not customer metrics.
- *RFM*: each customer is scored 1–5 (quintiles, with tied customers sharing a score) on days since last order, number of orders and net spend;
  score combinations map to the six named segments.
"""
    )
    steps = pd.DataFrame(report["steps"])
    st.dataframe(steps, column_config={"rule": "Cleaning rule", "rows_removed": "Rows removed",
                                       "rows_left": "Rows remaining"},
                 hide_index=True, width="stretch")
