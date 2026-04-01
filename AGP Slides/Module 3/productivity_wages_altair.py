import altair as alt
import pandas as pd
import requests
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

COLOR_WAGES = "#f4134d"   # red  – left axis (weekly wage)
COLOR_PROD  = "#1a85ff"   # blue – right axis (productivity index)


def fetch_eco_series(series_code: str) -> pd.DataFrame:
    url = f"https://api.economicsobservatory.com/gbr/{series_code}?vega"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year >= 2005].copy()
    return df


df_wages = fetch_eco_series("wage_r")
df_prod  = fetch_eco_series("prod")

wages_layer = (
    alt.Chart(df_wages)
    .mark_line(strokeWidth=2.5, color=COLOR_WAGES)
    .encode(
        x=alt.X(
            "date:T",
            title="",
            axis=alt.Axis(grid=False),
        ),
        y=alt.Y(
            "value:Q",
            title="Weekly Wage (£)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(titleColor=COLOR_WAGES, grid=False),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %Y"),
            alt.Tooltip("value:Q", title="Weekly Wage (£)", format=",.0f"),
        ],
    )
)

prod_layer = (
    alt.Chart(df_prod)
    .mark_line(strokeWidth=2.5, color=COLOR_PROD)
    .encode(
        x=alt.X(
            "date:T",
            title="",
            axis=alt.Axis(grid=False),
        ),
        y=alt.Y(
            "value:Q",
            title="Productivity Index",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                titleColor=COLOR_PROD,
                orient="right",
                grid=False,
            ),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %Y"),
            alt.Tooltip("value:Q", title="Productivity Index", format=".1f"),
        ],
    )
)

chart = (
    alt.layer(wages_layer, prod_layer)
    .resolve_scale(y="independent")
    .properties(
        width=750,
        height=420,
        title=alt.TitleParams(
            text="Real Weekly Wages & Productivity",
            subtitle="Average weekly wage, constant prices, £ (left) | Productivity index (right) | Source: ONS through ECO API",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save("productivity_wages_chart.png", scale_factor=2)
