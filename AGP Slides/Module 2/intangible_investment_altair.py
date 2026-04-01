import altair as alt
import pandas as pd
from ecostyles import EcoStyles
import os

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv(
    "https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/AGP%20Slides/Module%202/Intangible_investment.csv",
    skiprows=6
)
df["Year"] = df["Year"].astype(str)
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
        x=alt.X("Year:T").axis(tickCount=8),
        y=alt.Y("Investment:Q").axis(labelExpr="'£' + datum.value + 'bn'").title(
            'Investment, current prices'
        ),

        color=alt.Color("Asset Type:N").legend(None),
        tooltip=[
            alt.Tooltip("Asset Type:N", title="Asset Type"),
            alt.Tooltip("Year:T", title="Year"),
            alt.Tooltip("Investment:Q", title="Investment (£bn)", format=",.1f"),
        ],
    )
    .properties(
        width=550,
        height=380,
        title=alt.TitleParams(
            text="Total investment in intangible vs tangible assets, UK, 1997\u20132023, \u00a3 billion (current prices)",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart += (
    alt.Chart(df)
    .mark_text(strokeWidth=2.5)
    .encode(
        x=alt.X("Year:T").aggregate("max"),
        y=alt.Y("Investment:Q").aggregate({'argmax': 'Year'}),
        text=alt.Text("Asset Type:N").aggregate({'argmax': 'Year'}),
        color=alt.Color("Asset Type:N")
    )
)
chart = chart.configure_axis(labelFontSize=13, titleFontSize=13).configure_text(fontSize=13)

chart = styles.add_source(chart, 'Source: ONS; total investment (purchased and own production combined)')

# chart.configure_axis(labelFontSize=13).save("intangible_investment_v2.png", scale_factor=2)

# Find our current working directory, so save the chart to the same location as this script
current_dir = os.path.dirname(os.path.abspath(__file__))

styles.save(chart, current_dir, "intangible_investment_v2", width=550, height=380)
