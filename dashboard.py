from __future__ import annotations

from functools import reduce
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


RAW_DATA_URLS = {
    "Confirmed": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
    "csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",
    "Recovered": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
    "csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv",
    "Deaths": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
    "csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv",
}

PROCESSED_FILES = {
    "Confirmed": "confirmed_cases.csv",
    "Recovered": "recovered_cases.csv",
    "Deaths": "dead_cases.csv",
    "Active": "active_cases.csv",
}

METRIC_COLORS = {
    "Confirmed": "#2563eb",
    "Recovered": "#059669",
    "Deaths": "#dc2626",
    "Active": "#d97706",
    "Daily confirmed": "#2563eb",
    "Daily deaths": "#dc2626",
}


st.set_page_config(
    page_title="COVID-19 Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.4rem;
                padding-bottom: 2rem;
            }

            [data-testid="stSidebar"] {
                background: #f8fafc;
                border-right: 1px solid #e2e8f0;
            }

            h1, h2, h3 {
                letter-spacing: 0;
            }

            .hero-title {
                font-size: clamp(2rem, 4vw, 3.4rem);
                font-weight: 780;
                line-height: 1.03;
                margin: 0;
                color: #0f172a;
            }

            .hero-subtitle {
                color: #475569;
                font-size: 1.02rem;
                line-height: 1.55;
                max-width: 860px;
                margin-top: .75rem;
            }

            .metric-card {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 1rem;
                background: #ffffff;
                min-height: 126px;
            }

            .metric-label {
                color: #64748b;
                font-size: .82rem;
                font-weight: 700;
                text-transform: uppercase;
            }

            .metric-value {
                color: #0f172a;
                font-size: clamp(1.55rem, 3vw, 2.25rem);
                font-weight: 780;
                line-height: 1.05;
                margin-top: .35rem;
            }

            .metric-note {
                color: #64748b;
                font-size: .86rem;
                margin-top: .45rem;
            }

            .section-heading {
                color: #0f172a;
                font-size: 1.1rem;
                font-weight: 760;
                margin: 1.1rem 0 .35rem;
            }

            div[data-testid="stMetricValue"] {
                color: #0f172a;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_country_name(country: str) -> str:
    replacements = {
        "Korea, South": "South Korea",
        "Taiwan*": "Taiwan",
        "US": "United States",
        "Congo (Brazzaville)": "Congo",
        "Congo (Kinshasa)": "Democratic Republic of Congo",
        "Cote d'Ivoire": "Ivory Coast",
    }
    return replacements.get(country, country)


def process_raw_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["Province/State", "Lat", "Long"], errors="ignore").copy()
    df = df.rename(columns={"Country/Region": "Country"})
    df["Country"] = df["Country"].map(clean_country_name)
    df = df.groupby("Country", as_index=False).sum(numeric_only=True)
    df = df.set_index("Country").T
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")
    df.index.name = "Date"
    df = df.reset_index()
    df = df.drop(columns=["Diamond Princess", "MS Zaandam"], errors="ignore")
    return df


def read_processed_dataset(data_dir: Path) -> dict[str, pd.DataFrame] | None:
    if not all((data_dir / filename).exists() for filename in PROCESSED_FILES.values()):
        return None

    datasets = {}
    for metric, filename in PROCESSED_FILES.items():
        df = pd.read_csv(data_dir / filename)
        df["Date"] = pd.to_datetime(df["Date"])
        datasets[metric] = df

    return datasets


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_data() -> dict[str, pd.DataFrame]:
    processed = read_processed_dataset(Path("data/processed"))
    if processed is not None:
        return processed

    datasets = {}
    for metric, url in RAW_DATA_URLS.items():
        raw_df = pd.read_csv(url)
        datasets[metric] = process_raw_timeseries(raw_df)

    active = datasets["Confirmed"].drop(columns=["Date"])
    active = active.subtract(datasets["Recovered"].drop(columns=["Date"]), fill_value=0)
    active = active.subtract(datasets["Deaths"].drop(columns=["Date"]), fill_value=0)
    active = active.clip(lower=0)
    active["Date"] = datasets["Confirmed"]["Date"]
    datasets["Active"] = active[["Date"] + sorted(active.drop(columns=["Date"]).columns)]

    return datasets


def align_country_columns(datasets: dict[str, pd.DataFrame]) -> list[str]:
    country_sets = [
        set(df.columns) - {"Date"}
        for df in datasets.values()
    ]
    return sorted(set.intersection(*country_sets))


def world_timeseries(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    parts = []
    for metric, df in datasets.items():
        series = df.drop(columns=["Date"]).sum(axis=1).rename(metric)
        parts.append(pd.DataFrame({"Date": df["Date"], metric: series}))
    return reduce(lambda left, right: pd.merge(left, right, on="Date", how="outer"), parts)


def country_timeseries(datasets: dict[str, pd.DataFrame], country: str) -> pd.DataFrame:
    parts = []
    for metric, df in datasets.items():
        parts.append(pd.DataFrame({"Date": df["Date"], metric: df[country]}))
    return reduce(lambda left, right: pd.merge(left, right, on="Date", how="outer"), parts)


def summary_table(datasets: dict[str, pd.DataFrame], countries: list[str]) -> pd.DataFrame:
    rows = []
    latest_date = datasets["Confirmed"]["Date"].max()
    for country in countries:
        confirmed = int(datasets["Confirmed"].loc[datasets["Confirmed"]["Date"] == latest_date, country].iloc[0])
        recovered = int(datasets["Recovered"].loc[datasets["Recovered"]["Date"] == latest_date, country].iloc[0])
        deaths = int(datasets["Deaths"].loc[datasets["Deaths"]["Date"] == latest_date, country].iloc[0])
        active = max(confirmed - recovered - deaths, 0)
        fatality_rate = (deaths / confirmed * 100) if confirmed else 0
        rows.append(
            {
                "Country": country,
                "Confirmed": confirmed,
                "Recovered": recovered,
                "Deaths": deaths,
                "Active": active,
                "Fatality rate": fatality_rate,
            }
        )

    return pd.DataFrame(rows).sort_values("Confirmed", ascending=False)


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def number(value: float) -> str:
    return f"{value:,.0f}"


def build_line_chart(df: pd.DataFrame, columns: list[str], title: str) -> go.Figure:
    fig = go.Figure()
    for column in columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df[column],
                mode="lines",
                name=column,
                line={"color": METRIC_COLORS.get(column), "width": 3},
            )
        )
    fig.update_layout(
        title=title,
        height=430,
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        yaxis_title="Cases",
        xaxis_title="",
    )
    return fig


def build_daily_chart(df: pd.DataFrame, title: str) -> go.Figure:
    daily = df[["Date", "Confirmed", "Deaths"]].copy()
    daily["Daily confirmed"] = daily["Confirmed"].diff().clip(lower=0).rolling(7).mean()
    daily["Daily deaths"] = daily["Deaths"].diff().clip(lower=0).rolling(7).mean()
    fig = build_line_chart(daily, ["Daily confirmed", "Daily deaths"], title)
    fig.update_layout(yaxis_title="7-day average")
    return fig


def main() -> None:
    inject_styles()

    try:
        datasets = load_data()
    except Exception as exc:
        st.error(
            "The dashboard could not load COVID-19 data. Check your internet connection "
            "or generate `data/processed` with the project pipeline."
        )
        st.exception(exc)
        return

    countries = align_country_columns(datasets)
    world_df = world_timeseries(datasets)
    latest = world_df.sort_values("Date").iloc[-1]
    first_date = world_df["Date"].min().date()
    latest_date = world_df["Date"].max().date()

    with st.sidebar:
        st.title("Controls")
        default_countries = [country for country in ["United States", "India", "Brazil", "Turkey"] if country in countries]
        selected_country = st.selectbox("Country deep dive", countries, index=countries.index(default_countries[-1]) if default_countries else 0)
        comparison_countries = st.multiselect(
            "Compare countries",
            countries,
            default=default_countries[:4],
            max_selections=8,
        )
        ranking_metric = st.selectbox("Ranking metric", ["Confirmed", "Deaths", "Active", "Recovered"])
        top_n = st.slider("Top countries", 5, 25, 10)
        date_range = st.date_input(
            "Date window",
            value=(first_date, latest_date),
            min_value=first_date,
            max_value=latest_date,
        )

    st.markdown('<h1 class="hero-title">COVID-19 Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-subtitle">
            Interactive portfolio dashboard built on top of the existing COVID-19 analysis project.
            Explore global trends, compare countries, and surface the highest-impact regions from
            the Johns Hopkins CSSE time-series dataset.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(first_date), pd.to_datetime(latest_date)

    world_filtered = world_df[(world_df["Date"] >= start_date) & (world_df["Date"] <= end_date)]

    cols = st.columns(5)
    with cols[0]:
        metric_card("Confirmed", number(latest["Confirmed"]), f"Latest data: {latest_date}")
    with cols[1]:
        metric_card("Deaths", number(latest["Deaths"]), f"{latest['Deaths'] / latest['Confirmed'] * 100:.2f}% fatality rate")
    with cols[2]:
        metric_card("Recovered", number(latest["Recovered"]), "Reported recoveries")
    with cols[3]:
        metric_card("Active", number(latest["Active"]), "Confirmed - recovered - deaths")
    with cols[4]:
        latest_daily = world_df["Confirmed"].diff().clip(lower=0).rolling(7).mean().iloc[-1]
        metric_card("Daily Avg", number(latest_daily), "7-day confirmed cases")

    st.markdown('<div class="section-heading">Global Trend</div>', unsafe_allow_html=True)
    st.plotly_chart(
        build_line_chart(world_filtered, ["Confirmed", "Recovered", "Active", "Deaths"], "Global COVID-19 cases"),
        use_container_width=True,
    )

    left, right = st.columns([1.15, 1])

    with left:
        country_df = country_timeseries(datasets, selected_country)
        country_df = country_df[(country_df["Date"] >= start_date) & (country_df["Date"] <= end_date)]
        st.markdown(f'<div class="section-heading">{selected_country} Deep Dive</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_daily_chart(country_df, f"{selected_country}: daily confirmed cases and deaths"),
            use_container_width=True,
        )

    with right:
        latest_summary = summary_table(datasets, countries)
        top_df = latest_summary.head(top_n)
        st.markdown('<div class="section-heading">Country Rankings</div>', unsafe_allow_html=True)
        fig = px.bar(
            top_df.sort_values(ranking_metric),
            x=ranking_metric,
            y="Country",
            orientation="h",
            color=ranking_metric,
            color_continuous_scale="Blues",
            title=f"Top {top_n} countries by {ranking_metric.lower()}",
        )
        fig.update_layout(height=430, margin={"l": 10, "r": 10, "t": 60, "b": 10}, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-heading">Country Comparison</div>', unsafe_allow_html=True)
    if comparison_countries:
        comparison = pd.DataFrame({"Date": datasets["Confirmed"]["Date"]})
        for country in comparison_countries:
            comparison[country] = datasets["Confirmed"][country]
        comparison = comparison[(comparison["Date"] >= start_date) & (comparison["Date"] <= end_date)]
        fig = px.line(
            comparison,
            x="Date",
            y=comparison_countries,
            title="Confirmed cases by selected country",
            labels={"value": "Confirmed cases", "variable": "Country"},
        )
        fig.update_layout(height=420, hovermode="x unified", margin={"l": 10, "r": 10, "t": 60, "b": 10})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select at least one country in the sidebar to compare trends.")

    table = latest_summary.head(30).copy()
    table["Fatality rate"] = table["Fatality rate"].map(lambda value: f"{value:.2f}%")
    st.markdown('<div class="section-heading">Latest Country Summary</div>', unsafe_allow_html=True)
    st.dataframe(table, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
