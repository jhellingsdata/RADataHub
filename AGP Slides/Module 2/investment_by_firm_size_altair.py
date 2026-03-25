import altair as alt
import pandas as pd
from ecostyles import EcoStyles
import os

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv(
    "https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/AGP%20Slides/Module%202/Investment_by_firm_size.csv"
)
df["Year"] = df["Year"].astype(str)
df["Median Investment Share of GVA"] = (
    df["Median Investment Share of GVA"].str.rstrip("%").astype(float)
)

SIZE_ORDER = ["Micro", "Small", "Medium-small", "Medium-large", "Large", "Very large"]

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5)
    .transform_calculate(firm_size_short="split(datum['Firm Size'], ', ')[0]")
    .encode(
        x=alt.X("Year:T").axis(tickCount=6),
        y=alt.Y("Median Investment Share of GVA:Q").axis(format=".1f").title("Median investment share of GVA (%)"),
        color=alt.Color("firm_size_short:N").legend(None).sort(SIZE_ORDER)
    )
    .properties(
        width=520,
        height=400
    )
)

chart += (
    chart.mark_text()
    .encode(
        x=alt.X("Year:T").aggregate("max"),
        y=alt.Y("Median Investment Share of GVA:Q").aggregate({'argmax': 'Year'}),
        text=alt.Text("Firm Size:N").aggregate({'argmax': 'Year'}),
        color=alt.Color("firm_size_short:N")
    )
)

chart = chart.configure_axis(labelFontSize=13, titleFontSize=13).configure_text(fontSize=13)

chart = styles.add_source(chart, 'Source: DBT analysis of ONS data.')

# chart.configure_axis(labelFontSize=13).save("intangible_investment_v2.png", scale_factor=2)
# chart.save("investment_by_firm_size_V2.png", scale_factor=2)

# Find our current working directory, so save the chart to the same location as this script
current_dir = os.path.dirname(os.path.abspath(__file__))

styles.save(chart, current_dir, "investment_by_firm_size_v2", width=500, height=400)
