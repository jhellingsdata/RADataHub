"""
OECD Average Annual Wages — Altair Chart via SDMX API
======================================================
Data: Average annual wages in USD PPP (constant prices)
Source: OECD.ELS.SAE, DSD_EARNINGS@AV_AN_WAGE
API docs: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html
"""

import requests
import pandas as pd
from io import StringIO
import altair as alt

import eco_style

# ─── Register and enable the ECO theme ───
alt.themes.enable('report')

# ── 1. Configuration ─────────────────────────────────────────────────────────

# Data query URL (CSV with labels for readability)
DATA_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.ELS.SAE,DSD_EARNINGS@AV_AN_WAGE,/"
    "..USD_PPP..Q.."
    "?startPeriod=2000"
    "&dimensionAtObservation=AllDimensions"
    "&format=csvfilewithlabels"
)

# Countries to highlight (ISO-3166-1 alpha-3 codes)
HIGHLIGHT = ["POL", "CHL", "GBR", "USA", "KOR", "IRL", "LUX"]

# Friendly labels
COUNTRY_LABELS = {
    "MEX": "Mexico",
    "POL": "Poland",
    "LUX": "Luxembourg",
    "GBR": "United Kingdom",
    "USA": "United States",
    "KOR": "South Korea",
    "IRL": "Ireland",
}

# Colour palette — uses eco_style.pallete keys
color_map = {
    "Luxembourg":     eco_style.pallete["nominal_6"],   # teal
    "United States":  eco_style.pallete["nominal_2"],   # red → mapped to USA
    "United Kingdom": eco_style.pallete["nominal_1"],   # blue → mapped to GBR
    "Ireland":        eco_style.pallete["nominal_5"],   # orange
    "South Korea":    eco_style.pallete["nominal_3"],   # yellow
    "Poland":         eco_style.pallete["Other_2"],     # teal alt
}

BASE_YEAR = 2000
END_YEAR  = 2024

# ── 2. Fetch data from OECD SDMX API ─────────────────────────────────────────

print("Fetching data from OECD API...")
response = requests.get(DATA_URL, timeout=60)
response.raise_for_status()

df = pd.read_csv(StringIO(response.text))

# ── 3. Inspect & clean ───────────────────────────────────────────────────────

# Standardise column names
col_map = {}
for c in df.columns:
    cl = c.lower()
    if "ref_area" == cl:
        col_map[c] = "country_code"
    elif "reference area" in cl:
        col_map[c] = "country_name"
    elif "time_period" == cl:
        col_map[c] = "year"
    elif "obs_value" == cl or "obsvalue" == cl:
        col_map[c] = "value"

df = df.rename(columns=col_map)

if "country_name" not in df.columns and "country_code" in df.columns:
    df["country_name"] = df["country_code"].map(COUNTRY_LABELS).fillna(df["country_code"])

df["year"]  = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df[(df["year"] >= BASE_YEAR) & (df["year"] <= END_YEAR)].copy()
df = df.dropna(subset=["value"])

print(f"\nAfter filtering: {len(df)} observations, "
      f"{df['year'].min():.0f}–{df['year'].max():.0f}")
print(f"Countries available: {sorted(df['country_code'].unique())}")

# ── 4. Prepare chart data ────────────────────────────────────────────────────

df["highlight"] = df["country_code"].isin(HIGHLIGHT)
df["label"] = df["country_code"].map(COUNTRY_LABELS).fillna("")

# Compute OECD average (unweighted mean across all countries per year)
oecd_avg = (
    df.groupby("year")["value"]
      .mean()
      .reset_index()
      .assign(label="OECD")
)

# Background lines (non-highlighted countries)
bg = df[~df["highlight"]].copy()
bg["label"] = bg["country_code"]

# Foreground lines (highlighted countries)
fg = df[df["highlight"]].copy()

# End-of-line labels
fg_labels = (
    fg.sort_values("year")
      .groupby("country_code")
      .last()
      .reset_index()
)

# OECD average end label
oecd_avg_label = oecd_avg.sort_values("year").tail(1).copy()

# ── 5. Build Altair chart ────────────────────────────────────────────────────

# Colour scale from eco_style
line_order = list(color_map.keys())
colour_range = [color_map[k] for k in line_order]

# Background: all other OECD countries
bg_lines = (
    alt.Chart(bg)
    .mark_line(strokeWidth=0.7, opacity=0.35)
    .encode(
        x=alt.X("year:O", title="",
                 axis=alt.Axis(values=list(range(BASE_YEAR, END_YEAR + 1, 2)))),
        y=alt.Y("value:Q", title="Average annual wage (USD, PPP)",
                 scale=alt.Scale(zero=False)),
        detail="country_code:N",
        color=alt.value(eco_style.pallete["Other_3"]),
    )
)

# Foreground: highlighted countries
fg_lines = (
    alt.Chart(fg)
    .mark_line(strokeWidth=2.5)
    .encode(
        x="year:O",
        y="value:Q",
        color=alt.Color(
            "label:N",
            scale=alt.Scale(domain=line_order, range=colour_range),
            legend=None,
        ),
        tooltip=["label:N", "year:O", alt.Tooltip("value:Q", format=",.0f")],
    )
)

# End-of-line labels
end_labels = (
    alt.Chart(fg_labels)
    .mark_text(align="left", dx=6, fontSize=11, fontWeight=500)
    .encode(
        x="year:O",
        y="value:Q",
        text="label:N",
        color=alt.Color(
            "label:N",
            scale=alt.Scale(domain=line_order, range=colour_range),
            legend=None,
        ),
    )
)

# OECD average — dashed line
oecd_line = (
    alt.Chart(oecd_avg)
    .mark_line(strokeWidth=2, strokeDash=[6, 4],
               color=eco_style.pallete["domain"])
    .encode(
        x="year:O",
        y="value:Q",
        tooltip=["label:N", "year:O", alt.Tooltip("value:Q", format=",.0f")],
    )
)

oecd_label = (
    alt.Chart(oecd_avg_label.assign(label_y=58000))
    .mark_text(align="left", dx=6, fontSize=11, fontWeight=500,
               color=eco_style.pallete["domain"])
    .encode(
        x="year:O",
        y="label_y:Q",
        text="label:N",
    )
)

# Source caption — bottom-right
source_df = pd.DataFrame([{"text": "Source: OECD."}])

source_caption = (
    alt.Chart(source_df)
    .mark_text(
        align="right",
        baseline="middle",
        fontSize=10,
        color=eco_style.pallete["domain"],
        opacity=0.5,
    )
    .encode(
        x=alt.value(700),
        y=alt.value(20),
        text="text:N",
    )
    .properties(width=700, height=16)
)

# Assemble chart
main_chart = (
    (bg_lines + fg_lines + oecd_line + end_labels + oecd_label)
    .properties(
        width=700,
        height=420,
        title={
            "text": "UK wages have barely grown in two decades"
        }
    )
)

chart = (
    alt.vconcat(main_chart, source_caption)
    .configure_concat(spacing=0)
    .configure_axisY(grid=False) # remove horizontal grid lines

)

chart 
# ── 6. Save outputs ──────────────────────────────────────────────────────────

chart.save("oecd_wages_chart.png", scale=3, ppi=300)
chart.save("oecd_wages_chart.svg", scale=3, ppi=300)


# Save highlighted dataset
fg.to_csv("oecd_wages_highlight.csv", index=False)


print("\nDone!")