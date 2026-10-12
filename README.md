# COVID-19 Analytics Dashboard

An interactive Streamlit dashboard for exploring global COVID-19 trends using the Johns Hopkins CSSE time-series dataset.

This project was built as a portfolio-ready data analytics application. It turns COVID-19 case data into a clean dashboard with KPI cards, country comparisons, daily trend charts, rankings, and an interactive summary table.

## Dashboard Features

- Global KPI cards for confirmed cases, deaths, recovered cases, active cases, and 7-day daily averages
- Interactive global trend chart for confirmed, recovered, active, and death counts
- Country deep-dive view with daily confirmed cases and deaths
- Country comparison chart for selected countries
- Ranking chart for top countries by confirmed cases, deaths, active cases, or recoveries
- Latest country summary table
- Automatic data loading from public Johns Hopkins CSSE CSV files
- Fallback support for local processed CSV files in `data/processed`

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- Johns Hopkins CSSE COVID-19 data

## Project Structure

```text
covid19-data-analysis/
├── dashboard.py              # Main Streamlit dashboard
├── requirements.txt          # Python dependencies
├── data/                     # Data download utilities
├── features/                 # Original data processing scripts
├── notebooks/                # Original exploratory analysis notebooks
├── visualizations/           # Original Matplotlib visualization class
└── tests/                    # Test files
```

## How To Run Locally

Clone the repository:

```bash
git clone https://github.com/Mikail-837737/covid19-data-analysis.git
cd covid19-data-analysis
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the dashboard:

```bash
streamlit run dashboard.py
```

Open the local URL in your browser:

```text
http://localhost:8501
```

## Data Source

The dashboard uses the public Johns Hopkins CSSE COVID-19 time-series dataset:

https://github.com/CSSEGISandData/COVID-19

If processed project CSV files are available in `data/processed`, the dashboard uses them. Otherwise, it loads the public Johns Hopkins CSV files directly.

## Deployment

This dashboard can be deployed with Streamlit Community Cloud.

1. Push this repository to GitHub.
2. Go to https://streamlit.io/cloud.
3. Create a new app.
4. Select this repository.
5. Set the main file path to `dashboard.py`.
6. Deploy the app.

## Portfolio Summary

This project demonstrates:

- Data cleaning and transformation with Pandas
- Interactive dashboard development with Streamlit
- Data visualization with Plotly
- Time-series analysis
- Country-level comparison and ranking
- Building a deployable analytics project for a real-world dataset

## Author

Mikail
