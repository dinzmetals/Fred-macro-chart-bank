import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os

# -----------------------------
# CONFIG
# -----------------------------
API_KEY = os.getenv("FRED_API_KEY")

# -----------------------------
# CHART CONFIG (WITH CATEGORIES)
# -----------------------------
CHART_CONFIG = {

    # ACTIVITY
    "Nonfarm Payrolls": {
        "series_id": "PAYEMS",
        "transform": None,
        "title": "US Nonfarm Payrolls",
        "category": "Activity"
    },
    "Retail Sales": {
        "series_id": "RSAFS",
        "transform": None,
        "title": "US Retail Sales",
        "category": "Activity"
    },

    # INFLATION
    "US CPI YoY": {
        "series_id": "CPIAUCSL",
        "transform": "yoy",
        "title": "US CPI (YoY %)",
        "category": "Inflation"
    },
    "Core CPI YoY": {
        "series_id": "CPILFESL",
        "transform": "yoy",
        "title": "US Core CPI (YoY %)",
        "category": "Inflation"
    },

    # RATES
    "Fed Funds Rate": {
        "series_id": "FEDFUNDS",
        "transform": None,
        "title": "Fed Funds Rate (%)",
        "category": "Rates"
    },
    "US 10Y Yield": {
        "series_id": "DGS10",
        "transform": None,
        "title": "US 10Y Treasury Yield (%)",
        "category": "Rates"
    }
}

# -----------------------------
# DATA FUNCTIONS
# -----------------------------
def fetch_fred_series(series_id):
    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json"
    }

    r = requests.get(url, params=params)
    data = r.json()

    if "observations" not in data:
        return pd.DataFrame()

    df = pd.DataFrame(data["observations"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df


def apply_transform(df, transform):
    if df.empty:
        return df

    if transform == "yoy":
        df["value"] = df["value"].pct_change(12) * 100

    return df


def filter_time(df, time_option):
    if df.empty:
        return df

    df = df.dropna()
    end_date = df["date"].max()

    if time_option == "1 Year":
        start_date = end_date - pd.DateOffset(years=1)
    elif time_option == "5 Years":
        start_date = end_date - pd.DateOffset(years=5)
    else:
        return df

    return df[df["date"] >= start_date]

# -----------------------------
# CHART FUNCTION
# -----------------------------
def plot_chart(df, title):

    plt.rcParams["font.family"] = "Arial"

    fig, ax = plt.subplots(figsize=(5, 3))  # half-width size

    main_color = (32/255, 32/255, 118/255)
    grid_color = (0.85, 0.85, 0.85)

    ax.plot(df["date"], df["value"], color=main_color, linewidth=2)

    # remove gap
    ax.margins(x=0)
    if len(df) > 0:
        ax.set_xlim(df["date"].min(), df["date"].max())

    # title
    ax.set_title(title, loc="left", fontsize=8, fontweight="bold")

    # labels
    ax.set_xlabel("")
    ax.set_ylabel("")

    # grid
    ax.grid(True, linewidth=0.5, color=grid_color)

    # clean
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(axis="both", labelsize=7)

    # % formatting
    if "YoY" in title or "%" in title:
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _: f"{x:.1f}%")
        )

    plt.tight_layout()

    return fig

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Chart Bank", layout="wide")

st.title("📊 Macro Dashboard")

# TIME FILTER (GLOBAL)
time_option = st.radio(
    "Time Horizon",
    ["1 Year", "5 Years", "All"],
    horizontal=True
)

# -----------------------------
# SORT CHARTS BY CATEGORY
# -----------------------------
categories = {}
for name, config in CHART_CONFIG.items():
    cat = config["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append((name, config))

# -----------------------------
# RENDER DASHBOARD
# -----------------------------
for category, charts in categories.items():

    st.markdown(f"## {category}")   # section header
    st.markdown("---")

    # 2 charts per row
    cols = st.columns(2)

    for i, (name, config) in enumerate(charts):

        df = fetch_fred_series(config["series_id"])
        df = apply_transform(df, config.get("transform"))
        df = filter_time(df, time_option)

        with cols[i % 2]:
            if df.empty:
                st.warning(f"{name}: No data")
            else:
                fig = plot_chart(df, config["title"])
                st.pyplot(fig)
