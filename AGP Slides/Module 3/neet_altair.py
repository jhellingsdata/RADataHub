import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

DATA_FILE = (
    "../data/Figure_1__The_percentage_of_young_people_who_are_not_in_education,"
    "_employment_or_training_(NEET)_increased_over_the_quarter_(July_to_September_2025)_[Note_1].csv"
)

df = pd.read_csv(DATA_FILE, skiprows=6)
df.columns = ["Quarter", "NEET_pct"]
df = df.dropna(subset=["Quarter"])
df = df[df["Quarter"].str.strip() != ""]
df["NEET_pct"] = pd.to_numeric(df["NEET_pct"], errors="coerce")
df = df.dropna(subset=["NEET_pct"])

# Clean typo "Jul to -Sep" → "Jul to Sep"
df["Quarter"] = df["Quarter"].str.replace(r"\s*-\s*", " ", regex=True)

# Map quarter label to approximate mid-quarter month for temporal axis
quarter_month = {
    "Jan to Mar": 2,
    "Apr to Jun": 5,
    "Jul to Sep": 8,
    "Oct to Dec": 11,
}

def parse_quarter(label):
    label = label.strip()
    year = int(label[-4:])
    for prefix, month in quarter_month.items():
        if prefix in label:
            return pd.Timestamp(year=year, month=month, day=1)
    return pd.NaT

df["date"] = df["Quarter"].apply(parse_quarter)
df = df.dropna(subset=["date"])
df["NEET_pct_frac"] = df["NEET_pct"] / 100

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(
            "date:T",
            title="Quarter",
            axis=alt.Axis(format="%Y", tickCount="year"),
        ),
        y=alt.Y(
            "NEET_pct_frac:Q",
            title="% of 16–24 year olds who are NEET",
            axis=alt.Axis(format=".0%"),
            scale=alt.Scale(domain=[0.08, 0.15]),
        ),
        tooltip=[
            alt.Tooltip("Quarter:N", title="Quarter"),
            alt.Tooltip("NEET_pct:Q", title="NEET (%)", format=".1f"),
        ],
    )
    .properties(
        width=300,
        height=400,
        title=alt.TitleParams(
            text=["Percent of 16–24 year olds who are not in", "education, employment or training, 2019–2025"],
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save("neet.png", scale_factor=2)
