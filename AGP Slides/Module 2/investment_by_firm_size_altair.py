import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv(
    "https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/AGP%20Slides/Module%202/Investment_by_firm_size.csv"
)
df["Year"] = df["Year"].astype(int)
df["Median Investment Share of GVA"] = (
    df["Median Investment Share of GVA"].str.rstrip("%").astype(float)
)

SIZE_ORDER = ["Micro", "Small", "Medium-small", "Medium-large", "Large", "Very large"]

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5)
    .transform_calculate(firm_size_short="split(datum['Firm Size'], ', ')[0]")
    .encode(
        x=alt.X("Year:Q",
                title="Year",
                axis=alt.Axis(format="d", tickCount=6)),
        y=alt.Y("Median Investment Share of GVA:Q",
                title="Median investment share of GVA (%)",
                axis=alt.Axis(format=".1f")),
        color=alt.Color(
            "firm_size_short:N",
            legend=alt.Legend(title="Firm size"),
            sort=SIZE_ORDER,
        ),
        tooltip=[
            alt.Tooltip("firm_size_short:N", title="Firm size"),
            alt.Tooltip("Year:Q", title="Year", format="d"),
            alt.Tooltip("Median Investment Share of GVA:Q", title="Investment Share (%)", format=".2f"),
        ],
    )
    .properties(
        width=750,
        height=420,
        title=alt.TitleParams(
            text="Median investment share of GVA (%), by firm size band, UK, 2008-2019",
            subtitle="",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save("investment_by_firm_size.png", scale_factor=2)
