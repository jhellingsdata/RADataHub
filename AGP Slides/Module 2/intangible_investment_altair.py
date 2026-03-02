import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv(
    "https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/AGP%20Slides/Module%202/Intangible_investment.csv"
)
df["Year"] = df["Year"].astype(int)
df = df.rename(columns={
    "Intangible assets total": "Intangible",
    "Tangible assets total": "Tangible",
})
df = df.melt("Year", var_name="Asset Type", value_name="Investment")
df["Investment"] = df["Investment"].astype(float)

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X("Year:Q",
                title="Year",
                axis=alt.Axis(format="d", tickCount=8)),
        y=alt.Y("Investment:Q",
                title="Investment (£ billion, current prices)",
                axis=alt.Axis(format="~s")),
        color=alt.Color("Asset Type:N"),
        tooltip=[
            alt.Tooltip("Asset Type:N", title="Asset Type"),
            alt.Tooltip("Year:Q", title="Year", format="d"),
            alt.Tooltip("Investment:Q", title="Investment (£bn)", format=",.1f"),
        ],
    )
    .properties(
        width=750,
        height=420,
        title=alt.TitleParams(
            text="Total investment in intangible vs tangible assets, UK, 1997\u20132023, \u00a3 billion (current prices)",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save("intangible_investment.png", scale_factor=2)
