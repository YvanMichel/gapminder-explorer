"""Streamlit app to explore the Gapminder dataset (1952-2007, 142 countries).

Run with:  streamlit run gapminder_app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="Gapminder Explorer", page_icon="🌍", layout="wide")

METRICS = {
    "lifeExp": "Life expectancy (years)",
    "gdpPercap": "GDP per capita (US$, PPP)",
    "pop": "Population",
}
LOG_BY_DEFAULT = {"lifeExp": False, "gdpPercap": True, "pop": True}
CONTINENT_COLORS = px.colors.qualitative.Set2


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@st.cache_data
def load_data() -> pd.DataFrame:
    df = px.data.gapminder()
    df["gdp"] = df["gdpPercap"] * df["pop"]  # total GDP
    return df.sort_values(["year", "country"]).reset_index(drop=True)


def aggregate(df: pd.DataFrame, by) -> pd.DataFrame:
    """Population-weighted life expectancy / GDP per capita for groups."""
    t = (
        df.assign(le_w=df["lifeExp"] * df["pop"])
        .groupby(by, as_index=False)
        .agg(
            pop=("pop", "sum"),
            gdp=("gdp", "sum"),
            le_w=("le_w", "sum"),
            countries=("country", "nunique"),
        )
    )
    t["lifeExp"] = t["le_w"] / t["pop"]
    t["gdpPercap"] = t["gdp"] / t["pop"]
    return t.drop(columns="le_w")


def show(fig, **kwargs):
    st.plotly_chart(fig, width="stretch", **kwargs)


def metric_select(label, key, default="lifeExp"):
    return st.selectbox(
        label,
        list(METRICS),
        index=list(METRICS).index(default),
        format_func=METRICS.get,
        key=key,
    )


def year_select(label, years, key, default=None):
    return st.select_slider(
        label, options=years, value=default if default is not None else years[-1], key=key
    )


df_all = load_data()

# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
st.sidebar.title("🌍 Filters")
all_continents = sorted(df_all["continent"].unique())
continents = st.sidebar.multiselect("Continents", all_continents, default=all_continents)

country_options = sorted(df_all[df_all["continent"].isin(continents)]["country"].unique())
countries_sel = st.sidebar.multiselect(
    "Restrict to countries (empty = all)", country_options, default=[]
)

all_years = sorted(df_all["year"].unique().tolist())
year_min, year_max = st.sidebar.select_slider(
    "Year range", options=all_years, value=(all_years[0], all_years[-1])
)

df = df_all[
    df_all["continent"].isin(continents)
    & df_all["year"].between(year_min, year_max)
    & (df_all["country"].isin(countries_sel) if countries_sel else True)
]

st.sidebar.caption(
    f"{df['country'].nunique()} countries · {df['year'].nunique()} years · {len(df):,} rows"
)
st.sidebar.caption("Source: Gapminder, bundled with Plotly Express.")

st.title("Gapminder Explorer")
st.caption(
    "Life expectancy, GDP per capita and population for 142 countries, "
    "every 5 years from 1952 to 2007."
)

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

years = sorted(df["year"].unique().tolist())
first_year, last_year = years[0], years[-1]

tabs = st.tabs(
    [
        "📋 Overview",
        "🎞️ Animated bubbles",
        "📈 Trends",
        "🏳️ Country profile",
        "⚖️ Compare countries",
        "📊 Distributions",
        "🔗 Relationships",
        "🗺️ Maps",
        "🏆 Rankings & movers",
        "🌐 Inequality & convergence",
        "🗃️ Data",
    ]
)

# --------------------------------------------------------------------------- #
# 1. Overview
# --------------------------------------------------------------------------- #
with tabs[0]:
    st.subheader(f"Snapshot: {first_year} → {last_year}")
    w_first = aggregate(df[df["year"] == first_year], "year").iloc[0]
    w_last = aggregate(df[df["year"] == last_year], "year").iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", df["country"].nunique())
    c2.metric(
        f"Population ({last_year})",
        f"{w_last['pop'] / 1e9:.2f} bn",
        f"{(w_last['pop'] / w_first['pop'] - 1) * 100:+.0f}% vs {first_year}",
    )
    c3.metric(
        f"Life expectancy ({last_year})",
        f"{w_last['lifeExp']:.1f} yrs",
        f"{w_last['lifeExp'] - w_first['lifeExp']:+.1f} yrs vs {first_year}",
    )
    c4.metric(
        f"GDP per capita ({last_year})",
        f"${w_last['gdpPercap']:,.0f}",
        f"{(w_last['gdpPercap'] / w_first['gdpPercap'] - 1) * 100:+.0f}% vs {first_year}",
    )
    st.caption("Life expectancy and GDP per capita are population-weighted averages.")

    left, right = st.columns(2)
    with left:
        st.markdown(f"**Continents in {last_year}**")
        cont = aggregate(df[df["year"] == last_year], "continent").sort_values(
            "pop", ascending=False
        )
        st.dataframe(
            cont.rename(
                columns={
                    "continent": "Continent",
                    "pop": "Population",
                    "gdp": "Total GDP",
                    "countries": "Countries",
                    "lifeExp": "Life exp.",
                    "gdpPercap": "GDP/capita",
                }
            ).style.format(
                {
                    "Population": "{:,.0f}",
                    "Total GDP": "{:,.0f}",
                    "Life exp.": "{:.1f}",
                    "GDP/capita": "{:,.0f}",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    with right:
        st.markdown(f"**Population share by continent, {last_year}**")
        show(
            px.pie(
                cont,
                names="continent",
                values="pop",
                hole=0.45,
                color="continent",
                color_discrete_sequence=CONTINENT_COLORS,
            )
        )

    st.markdown("**Descriptive statistics (filtered rows)**")
    st.dataframe(
        df[["lifeExp", "pop", "gdpPercap"]].describe().T.style.format("{:,.2f}"),
        width="stretch",
    )

    st.markdown("**Data quality**")
    q1, q2 = st.columns(2)
    q1.dataframe(
        df.isna().sum().rename("missing values").to_frame().T, hide_index=True, width="stretch"
    )
    q2.dataframe(
        df.dtypes.astype(str).rename("dtype").to_frame().T, hide_index=True, width="stretch"
    )

# --------------------------------------------------------------------------- #
# 2. Animated bubbles
# --------------------------------------------------------------------------- #
with tabs[1]:
    st.subheader("The classic Gapminder bubble chart")
    c1, c2, c3, c4 = st.columns(4)
    bx = c1.selectbox("X axis", list(METRICS), index=1, format_func=METRICS.get, key="bub_x")
    by = c2.selectbox("Y axis", list(METRICS), index=0, format_func=METRICS.get, key="bub_y")
    bsize = c3.selectbox("Bubble size", list(METRICS), index=2, format_func=METRICS.get, key="bub_s")
    size_max = c4.slider("Max bubble size", 10, 100, 55)
    c5, c6 = st.columns(2)
    log_x = c5.checkbox("Log X axis", value=LOG_BY_DEFAULT[bx], key=f"bub_logx_{bx}")
    log_y = c6.checkbox("Log Y axis", value=LOG_BY_DEFAULT[by], key=f"bub_logy_{by}")

    def axis_range(col, log):
        lo, hi = df[col].min(), df[col].max()
        return [lo * 0.8, hi * 1.25] if log else [lo - (hi - lo) * 0.05, hi + (hi - lo) * 0.05]

    fig = px.scatter(
        df,
        x=bx,
        y=by,
        size=bsize,
        color="continent",
        hover_name="country",
        animation_frame="year",
        animation_group="country",
        log_x=log_x,
        log_y=log_y,
        size_max=size_max,
        range_x=axis_range(bx, log_x),
        range_y=axis_range(by, log_y),
        labels=METRICS,
        color_discrete_sequence=CONTINENT_COLORS,
        height=650,
    )
    show(fig)
    st.caption("Press ▶ to animate, or drag the slider to jump to a year.")

# --------------------------------------------------------------------------- #
# 3. Trends
# --------------------------------------------------------------------------- #
with tabs[2]:
    st.subheader("How the world and its continents evolve")
    metric = metric_select("Metric", "trend_metric")
    by_cont = aggregate(df, ["continent", "year"])
    world = aggregate(df, "year")

    left, right = st.columns(2)
    with left:
        st.markdown("**By continent (population-weighted)**")
        fig = px.line(
            by_cont,
            x="year",
            y=metric,
            color="continent",
            markers=True,
            labels={**METRICS, "year": "Year"},
            color_discrete_sequence=CONTINENT_COLORS,
        )
        fig.add_trace(
            go.Scatter(
                x=world["year"],
                y=world[metric],
                name="World",
                mode="lines+markers",
                line=dict(color="black", dash="dash"),
            )
        )
        show(fig)
    with right:
        st.markdown("**Unweighted country distribution (median & quartiles)**")
        q = df.groupby("year")[metric].quantile([0.25, 0.5, 0.75]).unstack()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=q.index, y=q[0.75], line=dict(width=0), showlegend=False))
        fig.add_trace(
            go.Scatter(
                x=q.index,
                y=q[0.25],
                fill="tonexty",
                line=dict(width=0),
                name="Interquartile range",
                fillcolor="rgba(99,110,250,0.25)",
            )
        )
        fig.add_trace(
            go.Scatter(x=q.index, y=q[0.5], name="Median", line=dict(color="rgb(99,110,250)"))
        )
        fig.update_layout(xaxis_title="Year", yaxis_title=METRICS[metric])
        show(fig)

    st.markdown("**Stacked composition over time**")
    stack_metric = st.radio(
        "Stack",
        ["pop", "gdp"],
        format_func={"pop": "Population", "gdp": "Total GDP"}.get,
        horizontal=True,
    )
    normalize = st.checkbox("Show as % share", value=False)
    fig = px.area(
        by_cont,
        x="year",
        y=stack_metric,
        color="continent",
        groupnorm="percent" if normalize else None,
        color_discrete_sequence=CONTINENT_COLORS,
        labels={"year": "Year", "pop": "Population", "gdp": "Total GDP (US$)"},
    )
    show(fig)

    st.markdown("**Decade-over-decade growth by continent**")
    g = by_cont.sort_values(["continent", "year"]).copy()
    g["growth_%"] = g.groupby("continent")[metric].pct_change() * 100
    fig = px.bar(
        g.dropna(subset=["growth_%"]),
        x="year",
        y="growth_%",
        color="continent",
        barmode="group",
        color_discrete_sequence=CONTINENT_COLORS,
        labels={"growth_%": "Change vs previous period (%)", "year": "Year"},
    )
    show(fig)

    st.markdown("**Heatmap: every country over time**")
    max_rows = st.slider("Number of countries to show (top by latest value)", 10, 142, 40)
    piv = df.pivot(index="country", columns="year", values=metric)
    piv = piv.sort_values(piv.columns[-1], ascending=False).head(max_rows)
    fig = px.imshow(
        piv,
        aspect="auto",
        color_continuous_scale="Viridis",
        labels=dict(color=METRICS[metric], x="Year", y=""),
        height=max(400, 14 * len(piv)),
    )
    show(fig)

# --------------------------------------------------------------------------- #
# 4. Country profile
# --------------------------------------------------------------------------- #
with tabs[3]:
    st.subheader("Single-country deep dive")
    country_list = sorted(df["country"].unique())
    default_idx = country_list.index("France") if "France" in country_list else 0
    country = st.selectbox("Country", country_list, index=default_idx)
    cdf = df[df["country"] == country].sort_values("year")
    row0, row1 = cdf.iloc[0], cdf.iloc[-1]
    n_years = row1["year"] - row0["year"]

    st.markdown(f"**{country}** · {row1['continent']}")
    c1, c2, c3 = st.columns(3)
    c1.metric(
        f"Life expectancy ({int(row1['year'])})",
        f"{row1['lifeExp']:.1f}",
        f"{row1['lifeExp'] - row0['lifeExp']:+.1f} yrs since {int(row0['year'])}",
    )
    c2.metric(
        f"GDP per capita ({int(row1['year'])})",
        f"${row1['gdpPercap']:,.0f}",
        f"{(row1['gdpPercap'] / row0['gdpPercap'] - 1) * 100:+.0f}% since {int(row0['year'])}",
    )
    c3.metric(
        f"Population ({int(row1['year'])})",
        f"{row1['pop'] / 1e6:,.1f} M",
        f"{(row1['pop'] / row0['pop'] - 1) * 100:+.0f}% since {int(row0['year'])}",
    )
    if n_years > 0:
        cagr_g = (row1["gdpPercap"] / row0["gdpPercap"]) ** (1 / n_years) - 1
        cagr_p = (row1["pop"] / row0["pop"]) ** (1 / n_years) - 1
        st.caption(
            f"Average annual growth: GDP per capita {cagr_g * 100:.2f}% · "
            f"population {cagr_p * 100:.2f}%"
        )

    fig = make_subplots(
        rows=1, cols=3, subplot_titles=[METRICS[m] for m in METRICS], horizontal_spacing=0.08
    )
    for i, m in enumerate(METRICS, start=1):
        fig.add_trace(
            go.Scatter(x=cdf["year"], y=cdf[m], mode="lines+markers", name=METRICS[m]),
            row=1,
            col=i,
        )
    fig.update_layout(showlegend=False, height=350)
    show(fig)

    left, right = st.columns(2)
    with left:
        st.markdown("**Path through income / health space**")
        fig = px.line(
            cdf,
            x="gdpPercap",
            y="lifeExp",
            text="year",
            markers=True,
            log_x=True,
            labels=METRICS,
        )
        fig.update_traces(textposition="top center")
        show(fig)
    with right:
        st.markdown("**World rank over time (1 = best)**")
        ranks = df.copy()
        for m in METRICS:
            ranks[f"rank_{m}"] = ranks.groupby("year")[m].rank(ascending=False, method="min")
        r = ranks[ranks["country"] == country].melt(
            id_vars="year",
            value_vars=[f"rank_{m}" for m in METRICS],
            var_name="metric",
            value_name="rank",
        )
        r["metric"] = r["metric"].str.replace("rank_", "").map(METRICS)
        fig = px.line(r, x="year", y="rank", color="metric", markers=True)
        fig.update_yaxes(autorange="reversed", title="Rank among filtered countries")
        show(fig)

    st.markdown("**Compared with its continent (unweighted median)**")
    cont_med = (
        df[df["continent"] == row1["continent"]].groupby("year")[list(METRICS)].median().reset_index()
    )
    m = metric_select("Metric", "profile_metric")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cdf["year"], y=cdf[m], name=country, mode="lines+markers"))
    fig.add_trace(
        go.Scatter(
            x=cont_med["year"],
            y=cont_med[m],
            name=f"{row1['continent']} median",
            mode="lines",
            line=dict(dash="dash"),
        )
    )
    fig.update_layout(xaxis_title="Year", yaxis_title=METRICS[m])
    show(fig)

# --------------------------------------------------------------------------- #
# 5. Compare countries
# --------------------------------------------------------------------------- #
with tabs[4]:
    st.subheader("Side-by-side comparison")
    wanted = ["France", "China", "United States", "Nigeria", "Brazil"]
    default_cmp = [c for c in wanted if c in country_list]
    chosen = st.multiselect("Countries", country_list, default=default_cmp, key="cmp_countries")
    if not chosen:
        st.info("Pick at least one country.")
    else:
        c1, c2 = st.columns(2)
        cmp_metric = c1.selectbox(
            "Metric", list(METRICS), format_func=METRICS.get, key="cmp_metric"
        )
        mode = c2.radio(
            "Display", ["Raw values", f"Indexed ({first_year} = 100)"], horizontal=True
        )
        cmp = df[df["country"].isin(chosen)].sort_values("year").copy()
        if mode.startswith("Indexed"):
            base = cmp.groupby("country")[cmp_metric].transform("first")
            cmp["value"] = cmp[cmp_metric] / base * 100
            ylab = f"{METRICS[cmp_metric]} (index)"
        else:
            cmp["value"] = cmp[cmp_metric]
            ylab = METRICS[cmp_metric]
        logy = st.checkbox("Log Y axis", value=False, key="cmp_log")
        fig = px.line(
            cmp, x="year", y="value", color="country", markers=True, log_y=logy,
            labels={"value": ylab, "year": "Year"},
        )
        show(fig)

        cmp_year = year_select("Year for the radar / bar comparison", years, "cmp_year")
        snap = df[(df["year"] == cmp_year) & (df["country"].isin(chosen))]
        left, right = st.columns(2)
        with left:
            fig = px.bar(
                snap.sort_values(cmp_metric),
                x=cmp_metric,
                y="country",
                orientation="h",
                color="continent",
                labels=METRICS,
                color_discrete_sequence=CONTINENT_COLORS,
            )
            show(fig)
        with right:
            # radar: each metric scaled 0-1 against all filtered countries in that year
            year_all = df[df["year"] == cmp_year]
            scaled = pd.DataFrame(
                {
                    "lifeExp": year_all["lifeExp"],
                    "gdpPercap": np.log10(year_all["gdpPercap"]),
                    "pop": np.log10(year_all["pop"]),
                }
            )
            scaled = (scaled - scaled.min()) / (scaled.max() - scaled.min())
            scaled["country"] = year_all["country"].values
            fig = go.Figure()
            for _, r in scaled[scaled["country"].isin(chosen)].iterrows():
                vals = [r["lifeExp"], r["gdpPercap"], r["pop"]]
                fig.add_trace(
                    go.Scatterpolar(
                        r=vals + vals[:1],
                        theta=["Life exp.", "GDP/capita (log)", "Population (log)", "Life exp."],
                        name=r["country"],
                        fill="toself",
                        opacity=0.5,
                    )
                )
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
            show(fig)
            st.caption("Each axis is min-max scaled across the filtered countries for that year.")

        st.markdown("**Table**")
        tbl = cmp.pivot(index="year", columns="country", values=cmp_metric)
        st.dataframe(tbl.style.format("{:,.1f}"), width="stretch")

# --------------------------------------------------------------------------- #
# 6. Distributions
# --------------------------------------------------------------------------- #
with tabs[5]:
    st.subheader("How are countries distributed?")
    c1, c2, c3 = st.columns(3)
    with c1:
        d_metric = metric_select("Metric", "dist_metric")
    with c2:
        d_year = year_select("Year", years, "dist_year")
    with c3:
        d_log = st.checkbox("Log scale", value=LOG_BY_DEFAULT[d_metric], key=f"dist_log_{d_metric}")
    dsnap = df[df["year"] == d_year]

    left, right = st.columns(2)
    with left:
        st.markdown("**Histogram**")
        nbins = st.slider("Bins", 5, 60, 25)
        weight = st.checkbox("Weight by population (people, not countries)", value=False)
        fig = px.histogram(
            dsnap,
            x=d_metric,
            y="pop" if weight else None,
            histfunc="sum" if weight else "count",
            color="continent",
            nbins=nbins,
            log_x=d_log,
            marginal="rug",
            labels={**METRICS, "pop": "Population"},
            color_discrete_sequence=CONTINENT_COLORS,
        )
        fig.update_layout(barmode="stack")
        show(fig)
    with right:
        st.markdown("**Cumulative distribution (ECDF)**")
        fig = px.ecdf(
            dsnap, x=d_metric, color="continent", log_x=d_log, labels=METRICS,
            color_discrete_sequence=CONTINENT_COLORS,
        )
        show(fig)

    left, right = st.columns(2)
    with left:
        st.markdown("**Box plot by continent**")
        fig = px.box(
            dsnap, x="continent", y=d_metric, color="continent", points="all",
            hover_name="country", log_y=d_log, labels=METRICS,
            color_discrete_sequence=CONTINENT_COLORS,
        )
        fig.update_layout(showlegend=False)
        show(fig)
    with right:
        st.markdown("**Violin plot by continent**")
        fig = px.violin(
            dsnap, x="continent", y=d_metric, color="continent", box=True,
            hover_name="country", log_y=d_log, labels=METRICS,
            color_discrete_sequence=CONTINENT_COLORS,
        )
        fig.update_layout(showlegend=False)
        show(fig)

    st.markdown("**Distribution over time**")
    fig = px.box(
        df, x="year", y=d_metric, color="continent", log_y=d_log, labels=METRICS,
        color_discrete_sequence=CONTINENT_COLORS,
    )
    fig.update_xaxes(type="category")
    show(fig)

    st.markdown("**Summary statistics by continent**")
    st.dataframe(
        dsnap.groupby("continent")[d_metric].describe().style.format("{:,.2f}"),
        width="stretch",
    )

# --------------------------------------------------------------------------- #
# 7. Relationships
# --------------------------------------------------------------------------- #
with tabs[6]:
    st.subheader("How do the variables relate?")
    c1, c2, c3, c4 = st.columns(4)
    rx = c1.selectbox("X", list(METRICS), index=1, format_func=METRICS.get, key="rel_x")
    ry = c2.selectbox("Y", list(METRICS), index=0, format_func=METRICS.get, key="rel_y")
    r_year = c3.select_slider("Year", options=years, value=last_year, key="rel_year")
    r_log = c4.checkbox("Log X", value=LOG_BY_DEFAULT[rx], key=f"rel_log_{rx}")
    rsnap = df[df["year"] == r_year]

    c1, c2 = st.columns(2)
    trend = c1.selectbox(
        "Trendline", ["None", "OLS (per continent)", "OLS (overall)", "LOWESS"], index=2
    )
    size_by_pop = c2.checkbox("Size bubbles by population", value=True)
    trend_kwargs = {}
    if trend == "OLS (per continent)":
        trend_kwargs = dict(trendline="ols")
    elif trend == "OLS (overall)":
        trend_kwargs = dict(trendline="ols", trendline_scope="overall")
    elif trend == "LOWESS":
        trend_kwargs = dict(trendline="lowess", trendline_scope="overall")
    if trend_kwargs and r_log:
        trend_kwargs["trendline_options"] = dict(log_x=True)
    fig = px.scatter(
        rsnap, x=rx, y=ry, color="continent", size="pop" if size_by_pop else None,
        hover_name="country", log_x=r_log, size_max=45, labels=METRICS, height=550,
        color_discrete_sequence=CONTINENT_COLORS, **trend_kwargs,
    )
    show(fig)

    left, right = st.columns(2)
    with left:
        st.markdown("**Correlation matrix**")
        method = st.radio("Method", ["pearson", "spearman"], horizontal=True)
        log_vars = st.checkbox("Use log of population and GDP per capita", value=True)
        cdat = rsnap[list(METRICS)].copy()
        if log_vars:
            cdat["pop"] = np.log10(cdat["pop"])
            cdat["gdpPercap"] = np.log10(cdat["gdpPercap"])
        corr = cdat.corr(method=method)
        corr.index = corr.columns = [METRICS[c] for c in corr.columns]
        fig = px.imshow(
            corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r"
        )
        show(fig)
    with right:
        st.markdown("**Correlation over time**")
        pairs = [("gdpPercap", "lifeExp"), ("pop", "lifeExp"), ("pop", "gdpPercap")]
        rows = []
        for yr, g in df.groupby("year"):
            for a, b in pairs:
                aa = np.log10(g[a]) if a != "lifeExp" else g[a]
                bb = np.log10(g[b]) if b != "lifeExp" else g[b]
                if len(g) > 2:
                    rows.append(
                        {"year": yr, "pair": f"{METRICS[a]} ↔ {METRICS[b]}", "r": aa.corr(bb)}
                    )
        fig = px.line(pd.DataFrame(rows), x="year", y="r", color="pair", markers=True)
        fig.update_yaxes(range=[-1, 1], title="Correlation (log scale for GDP/pop)")
        show(fig)

    st.markdown("**Scatter matrix**")
    fig = px.scatter_matrix(
        rsnap, dimensions=list(METRICS), color="continent", hover_name="country",
        labels={k: v.split(" (")[0] for k, v in METRICS.items()},
        color_discrete_sequence=CONTINENT_COLORS, height=650,
    )
    fig.update_traces(diagonal_visible=False, marker=dict(size=5))
    show(fig)

    st.markdown("**Preston curve across decades** (life expectancy vs income, one line per year)")
    fig = px.scatter(
        df, x="gdpPercap", y="lifeExp", color="year", log_x=True, hover_name="country",
        color_continuous_scale="Turbo", opacity=0.7, labels=METRICS,
    )
    show(fig)

# --------------------------------------------------------------------------- #
# 8. Maps
# --------------------------------------------------------------------------- #
with tabs[7]:
    st.subheader("World maps")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        m_metric = metric_select("Metric", "map_metric")
    with c2:
        m_year = year_select("Year", years, "map_year")
    with c3:
        m_log = st.checkbox("Log colour scale", value=LOG_BY_DEFAULT[m_metric], key=f"map_log_{m_metric}")
    with c4:
        proj = st.selectbox(
            "Projection", ["natural earth", "orthographic", "equirectangular", "mercator"]
        )
    animate = st.checkbox("Animate through years", value=False)

    mdf = df.copy()
    color_col = m_metric
    if m_log:
        color_col = f"log10_{m_metric}"
        mdf[color_col] = np.log10(mdf[m_metric])
    df_color = mdf  # fixed colour range across years so frames are comparable
    mdf = mdf if animate else mdf[mdf["year"] == m_year]
    fig = px.choropleth(
        mdf,
        locations="iso_alpha",
        color=color_col,
        hover_name="country",
        hover_data={"iso_alpha": False, m_metric: ":,.1f", color_col: False},
        animation_frame="year" if animate else None,
        color_continuous_scale="Viridis",
        range_color=[df_color[color_col].min(), df_color[color_col].max()],
        projection=proj,
        labels={color_col: ("log10 " if m_log else "") + METRICS[m_metric]},
        height=600,
    )
    show(fig)
    if not set(df["continent"].unique()) == set(all_continents):
        st.caption("Countries outside the selected continents are not coloured.")

# --------------------------------------------------------------------------- #
# 9. Rankings & movers
# --------------------------------------------------------------------------- #
with tabs[8]:
    st.subheader("Who leads, who lags, who moved most?")
    c1, c2, c3 = st.columns(3)
    with c1:
        k_metric = metric_select("Metric", "rank_metric")
    with c2:
        k_year = year_select("Year", years, "rank_year")
    with c3:
        top_n = st.slider("Top / bottom N", 3, 25, 10)
    ksnap = df[df["year"] == k_year].sort_values(k_metric, ascending=False)

    left, right = st.columns(2)
    with left:
        st.markdown(f"**Top {top_n}**")
        fig = px.bar(
            ksnap.head(top_n).iloc[::-1], x=k_metric, y="country", color="continent",
            orientation="h", labels=METRICS, color_discrete_sequence=CONTINENT_COLORS,
        )
        show(fig)
    with right:
        st.markdown(f"**Bottom {top_n}**")
        fig = px.bar(
            ksnap.tail(top_n), x=k_metric, y="country", color="continent",
            orientation="h", labels=METRICS, color_discrete_sequence=CONTINENT_COLORS,
        )
        show(fig)

    st.markdown("**Bump chart: rank of the current top countries over time**")
    top_names = ksnap.head(top_n)["country"].tolist()
    bump = df.copy()
    bump["rank"] = bump.groupby("year")[k_metric].rank(ascending=False, method="min")
    bump = bump[bump["country"].isin(top_names)]
    fig = px.line(bump, x="year", y="rank", color="country", markers=True)
    fig.update_yaxes(autorange="reversed", title="Rank")
    show(fig)

    st.markdown("**Biggest movers between two years**")
    c1, c2, c3 = st.columns(3)
    if len(years) < 2:
        st.info("Select a wider year range to compare two different years.")
    else:
        y_from = c1.select_slider("From", options=years, value=first_year, key="mv_from")
        y_to = c2.select_slider("To", options=years, value=last_year, key="mv_to")
        rel = c3.checkbox("Relative change (%)", value=True)
        if y_from >= y_to:
            st.info("Choose a 'From' year earlier than the 'To' year.")
        else:
            a = df[df["year"] == y_from].set_index("country")[k_metric]
            b = df[df["year"] == y_to].set_index("country")[k_metric]
            chg = pd.DataFrame({"from": a, "to": b}).dropna()
            chg["change"] = (chg["to"] / chg["from"] - 1) * 100 if rel else chg["to"] - chg["from"]
            chg = chg.join(df.drop_duplicates("country").set_index("country")["continent"])
            chg = chg.sort_values("change", ascending=False).reset_index()
            label = "Change (%)" if rel else "Change"
            left, right = st.columns(2)
            with left:
                st.markdown("*Largest gains*")
                fig = px.bar(
                    chg.head(top_n).iloc[::-1], x="change", y="country", color="continent",
                    orientation="h", labels={"change": label},
                    color_discrete_sequence=CONTINENT_COLORS,
                )
                show(fig)
            with right:
                st.markdown("*Largest declines / smallest gains*")
                fig = px.bar(
                    chg.tail(top_n), x="change", y="country", color="continent",
                    orientation="h", labels={"change": label},
                    color_discrete_sequence=CONTINENT_COLORS,
                )
                show(fig)

            st.markdown("**Slope chart (every country)**")
            slope = chg.melt(
                id_vars=["country", "continent"], value_vars=["from", "to"],
                var_name="when", value_name="value",
            )
            slope["year"] = slope["when"].map({"from": y_from, "to": y_to})
            fig = px.line(
                slope, x="year", y="value", color="continent", line_group="country",
                hover_name="country", markers=True, labels={"value": METRICS[k_metric]},
                color_discrete_sequence=CONTINENT_COLORS, height=550,
            )
            fig.update_xaxes(type="category")
            show(fig)

    st.markdown("**Treemap of the world population**")
    fig = px.treemap(
        ksnap, path=[px.Constant("World"), "continent", "country"], values="pop",
        color=k_metric, color_continuous_scale="RdYlGn", hover_name="country",
        labels=METRICS, height=550,
    )
    show(fig)
    st.caption(f"Area = population in {k_year}; colour = {METRICS[k_metric]}.")

# --------------------------------------------------------------------------- #
# 10. Inequality & convergence
# --------------------------------------------------------------------------- #
with tabs[9]:
    st.subheader("Is the world converging?")
    rows = []
    for yr, g in df.groupby("year"):
        rows.append(
            {
                "year": yr,
                "Life exp. gap (max − min)": g["lifeExp"].max() - g["lifeExp"].min(),
                "Life exp. std dev": g["lifeExp"].std(),
                "Std dev of log10 GDP/capita": np.log10(g["gdpPercap"]).std(),
                "Richest / poorest GDP ratio": g["gdpPercap"].max() / g["gdpPercap"].min(),
                "Top-10% / bottom-10% GDP ratio": g["gdpPercap"].quantile(0.9)
                / g["gdpPercap"].quantile(0.1),
            }
        )
    conv = pd.DataFrame(rows)
    cols = [c for c in conv.columns if c != "year"]
    left, right = st.columns(2)
    for i, col in enumerate(cols):
        with (left if i % 2 == 0 else right):
            st.markdown(f"**{col}**")
            fig = px.line(conv, x="year", y=col, markers=True)
            fig.update_layout(yaxis_title=None, height=300)
            show(fig)
    st.caption(
        "Falling standard deviation = convergence between countries (sigma-convergence)."
    )

    st.markdown("**Beta-convergence: do poorer countries grow faster?**")
    if len(years) >= 2:
        a = df[df["year"] == first_year].set_index("country")
        b = df[df["year"] == last_year].set_index("country")
        bc = pd.DataFrame(
            {
                "start": a["gdpPercap"],
                "growth": ((b["gdpPercap"] / a["gdpPercap"]) ** (1 / (last_year - first_year)) - 1)
                * 100,
                "continent": a["continent"],
                "pop": a["pop"],
            }
        ).dropna()
        fig = px.scatter(
            bc.reset_index(), x="start", y="growth", color="continent", size="pop",
            hover_name="country", log_x=True, trendline="ols", trendline_scope="overall",
            trendline_options=dict(log_x=True), size_max=40,
            labels={"start": f"GDP per capita in {first_year}", "growth": "Average annual growth (%)"},
            color_discrete_sequence=CONTINENT_COLORS,
        )
        show(fig)
        st.caption(
            "A downward-sloping line suggests catch-up growth by initially poorer countries."
        )

    st.markdown("**Share of the world's GDP vs share of its population**")
    sh = aggregate(df[df["year"] == last_year], "continent")
    sh["Population share"] = sh["pop"] / sh["pop"].sum() * 100
    sh["GDP share"] = sh["gdp"] / sh["gdp"].sum() * 100
    fig = px.bar(
        sh.melt(id_vars="continent", value_vars=["Population share", "GDP share"]),
        x="continent", y="value", color="variable", barmode="group",
        labels={"value": "% of total", "variable": ""},
    )
    show(fig)
    st.caption(f"Year {last_year} (end of the selected range).")

# --------------------------------------------------------------------------- #
# 11. Data
# --------------------------------------------------------------------------- #
with tabs[10]:
    st.subheader("Filtered data")
    st.dataframe(
        df.drop(columns=["iso_num"]),
        hide_index=True,
        width="stretch",
        column_config={
            "lifeExp": st.column_config.NumberColumn("Life exp.", format="%.1f"),
            "gdpPercap": st.column_config.NumberColumn("GDP/capita", format="$%.0f"),
            "pop": st.column_config.NumberColumn("Population", format="%d"),
            "gdp": st.column_config.NumberColumn("Total GDP", format="$%.3e"),
        },
    )
    st.download_button(
        "⬇️ Download as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="gapminder_filtered.csv",
        mime="text/csv",
    )
    st.markdown(
        """
**Columns**
- `country`, `continent`, `iso_alpha`, `iso_num`: identifiers
- `year`: 1952 – 2007 in steps of 5
- `lifeExp`: life expectancy at birth, years
- `pop`: population
- `gdpPercap`: GDP per capita, US$ adjusted for inflation and PPP
- `gdp`: derived here as `gdpPercap × pop`
"""
    )
