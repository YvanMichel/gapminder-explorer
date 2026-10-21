# Gapminder Explorer

An interactive [Streamlit](https://streamlit.io) app for exploring the Gapminder dataset: life expectancy, GDP per capita and population for 142 countries, every 5 years from 1952 to 2007.

The data ships with [Plotly Express](https://plotly.com/python/plotly-express/), so no download or internet connection is needed to run the app.

## Features

Sidebar filters (continent, country, year range) apply to every tab.

| Tab | What it shows |
|---|---|
| Overview | Headline numbers, continent table, population share, summary statistics, missing-value check |
| Animated bubbles | The classic Gapminder chart with a play button, choice of axes, log scales and bubble size |
| Trends | Lines by continent, median and quartile band, stacked area, growth per period, country-by-year heatmap |
| Country profile | One country's key figures, time series, path through income and life expectancy, world rank, comparison with its continent |
| Compare countries | Several countries side by side, raw or indexed to 100, with bar and radar charts |
| Distributions | Histogram (optionally population-weighted), ECDF, box and violin plots, distribution over time |
| Relationships | Scatter with trendlines, correlation matrix, correlation over time, scatter matrix |
| Maps | World choropleth for any metric and year, with animation and several projections |
| Rankings & movers | Top and bottom N, bump chart, biggest gains and declines between two years, slope chart, treemap |
| Inequality & convergence | Gaps between countries over time, beta-convergence, GDP share vs population share |
| Data | Filtered table with CSV download |

Life expectancy and GDP per capita for continents and the world are population-weighted averages. Total GDP is derived as `gdpPercap × pop`.

## Getting started

```bash
git clone https://github.com/YvanMichel/gapminder-explorer.git
cd gapminder-explorer

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

streamlit run gapminder_app.py
```

Streamlit prints a local URL (usually http://localhost:8501) to open in your browser.

## Data columns

- `country`, `continent`, `iso_alpha`, `iso_num`: identifiers
- `year`: 1952 to 2007, in steps of 5
- `lifeExp`: life expectancy at birth, in years
- `pop`: population
- `gdpPercap`: GDP per capita, in US$ adjusted for inflation and purchasing power parity

## Source

[Gapminder](https://www.gapminder.org/data/), as bundled with Plotly Express.
