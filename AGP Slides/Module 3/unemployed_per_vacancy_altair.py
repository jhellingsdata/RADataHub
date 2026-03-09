import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv(
    "../data/series-090326.csv",
    skiprows=8,
    header=None,
    names=["date", "value"],
)

df["date"] = pd.to_datetime(df["date"], format="%Y %b")
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df = df.dropna()

# Last 20 years
cutoff = df["date"].max() - pd.DateOffset(years=20)
df = df[df["date"] >= cutoff]

COLOR = "#17648D"

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5, color=COLOR)
    .encode(
        x=alt.X(
            "date:T",
            title="",
            axis=alt.Axis(format="%Y", tickCount=10),
        ),
        y=alt.Y(
            "value:Q",
            title="Unemployed people per vacancy",
            scale=alt.Scale(zero=True),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %Y"),
            alt.Tooltip("value:Q", title="Unemployed per vacancy", format=".1f"),
        ],
    )
    .properties(
        width=750,
        height=420,
        title=alt.TitleParams(
            text="Unemployed people per vacancy, UK (exc. Agriculture, Forestry & Fishing)",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save("unemployed_per_vacancy.png", scale_factor=2)
