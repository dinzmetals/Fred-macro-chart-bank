import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# -----------------------------
# CONFIG
# -----------------------------
API_KEY = "b2c14d246471fd55d0d03a1c451b1c0e"

# -----------------------------
# CHART CONFIG
# -----------------------------
CHART_CONFIG = {

    # ACTIVITY
    "Industrial Production YoY": {
        "series_id": "INDPRO",
        "transform": "yoy",
        "title": "US Industrial Production (YoY %)",
        "category": "Activity"
    },
    "Industrial Production: Manufacturing YoY": {
        "series_id": "IPMAN",
        "transform": "yoy",
        "title": "US Industrial Production Manufacturing (YoY %)",
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

    # LABOUR
    "Unemployment Rate": {
        "series_id": "UNRATE",
        "transform": None,
        "title": "US Unemployment Rate (%)",
        "category": "Labour"
    },
    "Nonfarm Payrolls": {
        "series_id": "PAYEMS",
        "transform": None,
        "title": "US Nonfarm Payrolls",
        "category": "Labour"
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
        st.error(f"API error: {data}")
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


# -----------------------------
# TIME FILTER
# -----------------------------
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

    filtered = df[df["date"] >= start_date]

    # fallback if empty
    return filtered if not filtered.empty else df


# -----------------------------
# CHART FUNCTION
# -----------------------------
def plot_chart(df, title):

    if df.empty:
        raise ValueError("Empty dataset")

    plt.rcParams["font.family"] = "Arial"

    fig, ax = plt.subplots(figsize=(10, 5))

    main_color = (32/255, 32/255, 118/255)
    fill_color = (211/255, 214/255, 255/255)
    grid_color = (0.85, 0.85, 0.85)

    # line
    ax.plot(df["date"], df["value"], color=main_color, linewidth=2.5)

    # remove gap
    ax.margins(x=0)
    ax.set_xlim(df["date"].min(), df["date"].max())

    # yoy shading
    if "YoY" in title:
        ax.fill_between(
            df["date"],
            df["value"],
            0,
            where=(df["value"] < 0),
            color=fill_color,
            alpha=0.6
        )

    # labels
    ax.set_title(title, loc="left", fontsize=8, fontweight="bold")
    ax.set_xlabel("Date", fontsize=8)

    if "YoY" in title:
        ax.set_ylabel("% YoY", fontsize=8)
    else:
        ax.set_ylabel("Level", fontsize=8)

    # grid
    ax.grid(True, linewidth=0.6, color=grid_color)

    # clean axes
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(axis="both", labelsize=8)

    # percentage format
    if "YoY" in title:
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _: f"{x:.1f}%")
        )

    # last value
    last_x = df["date"].iloc[-1]
    last_y = df["value"].iloc[-1]
    ax.scatter(last_x, last_y, color=main_color)
    ax.text(last_x, last_y, f" {last_y:.1f}", fontsize=8)

    plt.tight_layout()

    return fig


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Chart Bank", layout="wide")

st.title("📊 Internal Macro Chart Bank")

# TIME SELECTOR
time_option = st.radio(
    "Time Horizon",
    ["1 Year", "5 Years", "All"],
    horizontal=True
)

# CATEGORY FILTER
categories = list(set(c["category"] for c in CHART_CONFIG.values()))
selected_category = st.sidebar.selectbox("Category", ["All"] + categories)

filtered_charts = {
    name: cfg for name, cfg in CHART_CONFIG.items()
    if selected_category == "All" or cfg["category"] == selected_category
}

selected_chart = st.sidebar.selectbox(
    "Chart",
    list(filtered_charts.keys())
)

config = filtered_charts[selected_chart]

# -----------------------------
# LOAD DATA (THIS WAS MISSING BEFORE)
# -----------------------------
with st.spinner("Loading data..."):
    df = fetch_fred_series(config["series_id"])
    df = apply_transform(df, config.get("transform"))
    df = filter_time(df, time_option)

# -----------------------------
# DISPLAY (SAFE)
# -----------------------------
if df.empty:
    st.warning("No data available for this selection")
else:
    try:
        fig = plot_chart(df, config["title"])
        st.pyplot(fig)
    except Exception as e:
        st.error("Chart failed")
        st.write(e)
        st.dataframe(df.tail(10))

# -----------------------------
# DATA TABLE
# -----------------------------
with st.expander("Show raw data"):
    st.dataframe(df.tail(20))

# -----------------------------
# DOWNLOAD
# -----------------------------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download CSV",
    data=csv,
    file_name=f"{selected_chart}.csv"
)
