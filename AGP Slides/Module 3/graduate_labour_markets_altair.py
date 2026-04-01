import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv("../data/data-graduate-labour-markets.csv")

# Keep only national-level data (already filtered, but be explicit)
df = df[df["geographic_level"] == "National"].copy()

type_order = ["Graduate", "Postgraduate", "Non-graduate"]

base = alt.Chart(df).encode(
    x=alt.X(
        "time_period:Q",
        title="Year",
        axis=alt.Axis(format="d", tickMinStep=1, tickCount=10),
    ),
    color=alt.Color(
        "graduate_type:N",
        title=None,
        sort=type_order,
    ),
    tooltip=[
        alt.Tooltip("time_period:Q", title="Year", format="d"),
        alt.Tooltip("graduate_type:N", title="Type"),
    ],
)

employment_chart = (
    base.mark_line(strokeWidth=2.5)
    .encode(
        y=alt.Y(
            "employment_rate:Q",
            title="Employment rate (%)",
            scale=alt.Scale(domain=[60, 95]),
            axis=alt.Axis(format=".0f"),
        ),
        tooltip=base.encoding.tooltip + [
            alt.Tooltip("employment_rate:Q", title="Employment rate (%)", format=".1f"),
        ],
    )
    .properties(
        width=370,
        height=320,
        title=alt.TitleParams(text="Employment rate", fontSize=13, anchor="start"),
    )
)

unemployment_chart = (
    base.mark_line(strokeWidth=2.5)
    .encode(
        y=alt.Y(
            "unemployment_rate:Q",
            title="Unemployment rate (%)",
            scale=alt.Scale(domain=[0, 12]),
            axis=alt.Axis(format=".0f"),
        ),
        tooltip=base.encoding.tooltip + [
            alt.Tooltip("unemployment_rate:Q", title="Unemployment rate (%)", format=".1f"),
        ],
    )
    .properties(
        width=370,
        height=320,
        title=alt.TitleParams(text="Unemployment rate", fontSize=13, anchor="start"),
    )
)

chart = (
    alt.hconcat(employment_chart, unemployment_chart, spacing=40)
    .properties(
        title=alt.TitleParams(
            text="Graduate labour market outcomes, 2007 to 2024",
            subtitle="Adults aged 16–64, England | Source: Annual Population Survey (ONS)",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        )
    )
    .resolve_scale(color="shared")
)

chart.save("graduate_labour_markets.png", scale_factor=2)
print("Saved graduate_labour_markets.png")
