import altair as alt
import pandas as pd
from pathlib import Path
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

BASE_DIR = Path(__file__).resolve().parent
df = pd.read_csv(BASE_DIR.parent / "data" / "Flourish-data_data copy.csv")
df = df.rename(columns={"Column1": "Year"})


def normalize_year(value: str) -> str:
    value = str(value).strip()
    return value.replace("-", "–")


df["Year"] = df["Year"].apply(normalize_year)
year_order = df["Year"].tolist()

actual_cols = {
    "Classroom–based learning": "Classroom-based learning",
    "Work–based learning or apprenticeships": "Work-based learning or apprenticeships",
    "Advanced learner loans": "Advanced learner loans",
    "Total adult skills": "Total adult skills",
}

forecast_cols = {
    "Classroom–based learning (forecast)": "Classroom-based learning",
    "Work–based learning or apprenticeships (forecast)": "Work-based learning or apprenticeships",
    "Advanced learner loans (forecast)": "Advanced learner loans",
    "Total adult skills (forecast)": "Total adult skills",
}

actual = df.melt(
    id_vars="Year",
    value_vars=list(actual_cols.keys()),
    var_name="Series",
    value_name="Value",
).dropna(subset=["Value"])
actual["Series"] = actual["Series"].map(actual_cols)
actual["Segment"] = "Actual"

forecast = df.melt(
    id_vars="Year",
    value_vars=list(forecast_cols.keys()),
    var_name="Series",
    value_name="Value",
).dropna(subset=["Value"])
forecast["Series"] = forecast["Series"].map(forecast_cols)
forecast["Segment"] = "Forecast"

plot_df = pd.concat([actual, forecast], ignore_index=True)

series_order = [
    "Total adult skills",
    "Work-based learning or apprenticeships",
    "Classroom-based learning",
    "Advanced learner loans",
]

series_colors = alt.Scale(
    domain=series_order,
    range=["#2A4447", "#E7A407", "#32966C", "#2D74B9"],
)

line_layer = (
    alt.Chart(plot_df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(
            "Year:N",
            sort=year_order,
            title="Financial year (starting in April)",
            axis=alt.Axis(labelAngle=-60, tickSize=8),
        ),
        y=alt.Y(
            "Value:Q",
            title="£ billion, 2025–26 prices",
            scale=alt.Scale(domain=[0, 7]),
            axis=alt.Axis(values=[0, 1, 2, 3, 4, 5, 6, 7], labelExpr="'£' + datum.value + 'bn'"),
        ),
        color=alt.Color("Series:N", sort=series_order, scale=series_colors, legend=None),
        detail="Series:N",
        strokeDash=alt.StrokeDash(
            "Segment:N",
            scale=alt.Scale(domain=["Actual", "Forecast"], range=[[], [8, 4]]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("Year:N", title="Financial year"),
            alt.Tooltip("Series:N"),
            alt.Tooltip("Value:Q", title="£bn", format=".2f"),
            alt.Tooltip("Segment:N"),
        ],
    )
)

label_text = {
    "Total adult skills": "Total adult skills",
    "Work-based learning or apprenticeships": "Work-based learning or\napprenticeships",
    "Classroom-based learning": "Classroom-based learning",
    "Advanced learner loans": "Advanced learner loans",
}

label_df = forecast[forecast["Year"] == "2025–26"].copy()
label_df["Label"] = label_df["Series"].map(label_text)

labels = (
    alt.Chart(label_df)
    .mark_text(align="left", dx=8, fontWeight="bold", fontSize=11, clip=False)
    .encode(
        x=alt.X("Year:N", sort=year_order),
        y=alt.Y("Value:Q"),
        text=alt.Text("Label:N"),
        color=alt.Color("Series:N", sort=series_order, scale=series_colors, legend=None),
    )
)

chart = (
    (line_layer + labels)
    .properties(
        width=750,
        height=420,
        title=alt.TitleParams(
            text="Public spending on adult education and skills (projected for 2025–26)",
            fontSize=16,
            subtitleFontSize=12,
            anchor="start",
        ),
    )
)

chart.save(BASE_DIR / "public_spending_adult_skills.png", scale_factor=2)
print("Saved public_spending_adult_skills.png")
