import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

# Read data, skipping metadata rows
df = pd.read_csv("../data/Qualifications.csv", skiprows=8)
df.columns = [
    "Date", "N4_num", "N4_den", "pct_nvq4", "conf4",
    "N3_num", "N3_den", "pct_nvq3_only", "conf3",
    "N2_num", "N2_den", "pct_nvq2_only", "conf2",
    "N1_num", "N1_den", "pct_nvq1_only", "conf1",
    "N0_num", "N0_den", "pct_no_qual", "conf0",
]

df = df.dropna(subset=["Date"])
df = df[df["Date"].str.strip() != ""]

# Extract year from "Jan YYYY-Dec YYYY"
df["year"] = df["Date"].str.extract(r"Jan (\d{4})").astype(int)

# Filter 2008–2020
df = df[(df["year"] >= 2008) & (df["year"] <= 2020)].copy()

for col in ["pct_nvq4", "pct_nvq3_only", "pct_nvq2_only", "pct_no_qual"]:
    df[col] = df[col].astype(float)

# Compute cumulative proportions (as 0–1 for % formatting)
df["NQF level 4 or above"] = df["pct_nvq4"] / 100
df["NQF level 3 or above"] = (df["pct_nvq4"] + df["pct_nvq3_only"]) / 100
df["NQF level 2 or above"] = (df["pct_nvq4"] + df["pct_nvq3_only"] + df["pct_nvq2_only"]) / 100
df["No qualifications"]    = df["pct_no_qual"] / 100

long_df = df[
    ["year", "NQF level 4 or above", "NQF level 3 or above",
     "NQF level 2 or above", "No qualifications"]
].melt(id_vars="year", var_name="Series", value_name="Proportion")

# Ordered so legend matches original chart
series_order = [
    "NQF level 2 or above",
    "NQF level 3 or above",
    "NQF level 4 or above",
    "No qualifications",
]

chart = (
    alt.Chart(long_df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(
            "year:Q",
            title="Year",
            axis=alt.Axis(format="d", tickCount=13, tickMinStep=1),
        ),
        y=alt.Y(
            "Proportion:Q",
            title="Proportion",
            axis=alt.Axis(format=".0%"),
            scale=alt.Scale(domain=[0, 0.9]),
        ),
        color=alt.Color(
            "Series:N",
            title=None,
            sort=series_order,
        ),
        order=alt.Order("Series:N", sort="ascending"),
        tooltip=[
            alt.Tooltip("year:Q", title="Year", format="d"),
            alt.Tooltip("Series:N", title="Series"),
            alt.Tooltip("Proportion:Q", title="Proportion", format=".1%"),
        ],
    )
    .properties(
        width=750,
        height=420,
        title=alt.TitleParams(
            text="Highest level of qualification held by adults of working age, 2008 to 2020",
            subtitle="Proportion of adults aged 16–64, United Kingdom | Source: Annual Population Survey (ONS)",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save("qualifications.png", scale_factor=2)
