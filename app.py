import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Revenue & Performance Dashboard", layout="wide")

DATA_PATH = "data/sample_sales.csv"


def generate_sample_data(days: int = 365):
    rng = np.random.default_rng(42)

    dates = pd.date_range(
        start=datetime.today() - timedelta(days=days),
        periods=days,
        freq="D"
    )

    categories = {
        "Beverages": ["Cola", "Orange Juice", "Water"],
        "Snacks": ["Chips", "Chocolate", "Nuts"],
        "Household": ["Detergent", "Paper Towels", "Dish Soap"],
        "Personal Care": ["Shampoo", "Toothpaste", "Deodorant"],
    }

    rows = []

    for date in dates:
        seasonal = 1 + 0.2 * np.sin(2 * np.pi * date.dayofyear / 365)

        for cat, prods in categories.items():
            for prod in prods:
                price = {
                    "Beverages": 1.5,
                    "Snacks": 1.2,
                    "Household": 4.0,
                    "Personal Care": 3.0,
                }[cat] * rng.normal(1, 0.1)

                promo = rng.random() < 0.05
                if promo:
                    price *= 0.85

                units = int(rng.poisson(25 * seasonal * (1.3 if promo else 1)))
                revenue = max(units, 0) * price

                rows.append({
                    "Date": date,
                    "Category": cat,
                    "Product": prod,
                    "Unit_Price": round(price, 2),
                    "Units_Sold": units,
                    "Revenue": round(revenue, 2),
                    "Channel": rng.choice(["Online", "In-store"]),
                    "Region": rng.choice(["North", "South", "East", "West"]),
                })

    return pd.DataFrame(rows)


@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            df["Date"] = pd.to_datetime(df["Date"])
            return df
        except Exception as e:
            st.warning(f"Error loading data file: {e}. Generating fresh data.")
    
    # Generate data (either file doesn't exist or couldn't be read/written)
    df = generate_sample_data()
    
    # Try to save, but don't fail if we can't (e.g., in read-only deployment)
    try:
        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
    except (OSError, PermissionError) as e:
        # In deployment, file system might be read-only - that's okay
        pass
    
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.title("📊 Business Revenue & Performance Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
categories = st.sidebar.multiselect("Category", df["Category"].unique())
channels = st.sidebar.multiselect("Channel", df["Channel"].unique())
regions = st.sidebar.multiselect("Region", df["Region"].unique())

filtered = df.copy()
if categories:
    filtered = filtered[filtered["Category"].isin(categories)]
if channels:
    filtered = filtered[filtered["Channel"].isin(channels)]
if regions:
    filtered = filtered[filtered["Region"].isin(regions)]

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"£{filtered['Revenue'].sum():,.0f}")
col2.metric("Units Sold", f"{filtered['Units_Sold'].sum():,.0f}")
asp = filtered["Revenue"].sum() / max(filtered["Units_Sold"].sum(), 1)
col3.metric("Avg Selling Price", f"£{asp:.2f}")

# Revenue trend
trend = (
    filtered
    .groupby(pd.Grouper(key="Date", freq="W"))["Revenue"]
    .sum()
    .reset_index()
)

fig = px.line(trend, x="Date", y="Revenue", title="Weekly Revenue Trend")
st.plotly_chart(fig, use_container_width=True)