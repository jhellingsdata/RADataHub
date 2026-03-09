import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv("../data/data-employer-skills-survey.csv")
df = df[(df["geographic_level"] == "National") & (df["sector"] == "Total") & (df["site_size"] == "Total")].copy()

# Melt to long format for grouped bars
df_long = df.melt(
    id_vars=["time_period"],
    value_vars=["twentyfour_prices_total_per_employee", "twentyfour_prices_total_per_trainee"],
    var_name="series",
    value_name="expenditure",
)

label_map = {
    "twentyfour_prices_total_per_employee": "Expenditure per employee",
    "twentyfour_prices_total_per_trainee": "Expenditure per trainee",
}
df_long["series"] = df_long["series"].map(label_map)

series_order = ["Expenditure per employee", "Expenditure per trainee"]

chart = (
    alt.Chart(df_long)
    .mark_bar()
    .encode(
        x=alt.X(
            "time_period:O",
            title="Year",
            axis=alt.Axis(labelAngle=0),
        ),
        xOffset=alt.XOffset("series:N", sort=series_order),
        y=alt.Y(
            "expenditure:Q",
            title="Expenditure per year (£, 2024 prices)",
            scale=alt.Scale(domain=[0, 5000]),
            axis=alt.Axis(tickCount=5, format=",.0f"),
        ),
        color=alt.Color(
            "series:N",
            title=None,
            sort=series_order,
        ),
        tooltip=[
            alt.Tooltip("time_period:O", title="Year"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("expenditure:Q", title="Expenditure (£)", format=","),
        ],
    )
    .properties(
        width=500,
        height=340,
        title=alt.TitleParams(
            text="Average investment in training per employee and per trainee in the last 12 months in England",
            fontSize=14,
            subtitleFontSize=11,
            anchor="start",
        ),
    )
)

chart.save("employer_training_investment.png", scale_factor=2)
print("Saved employer_training_investment.png")
