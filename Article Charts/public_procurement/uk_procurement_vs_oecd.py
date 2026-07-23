"""
Chart of the Day — UK public procurement spending vs the OECD
Economics Observatory / LSE Growth Lab

Data: OECD, Government at a Glance 2025 (Size of public procurement),
      via Our World in Data. General government procurement (intermediate
      consumption + gross fixed capital formation + social transfers in
      kind via market producers) as a % of GDP. Public corporations
      excluded. Latest available year: 2024.

Chile has no 2024 observation in this release and is not shown.
Turkiye's latest available observation is 2020 and is excluded to keep
the comparison to a single year.
"""

import altair as alt
import pandas as pd
import eco_style

alt.themes.enable("report")

# ── Load data ──────────────────────────────────────────────────────────
raw = pd.read_csv("government-procurement-share-gdp.csv")
raw = raw.rename(columns={"Government procurement spending (% of GDP)": "value"})

# True OECD member countries with a 2024 observation (Chile: no data;
# Turkiye: latest observation is 2020, excluded for year consistency)
OECD_MEMBERS_2024 = [
    "Australia", "Austria", "Belgium", "Canada", "Colombia", "Costa Rica",
    "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany",
    "Greece", "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan",
    "Latvia", "Lithuania", "Luxembourg", "Mexico", "Netherlands",
    "New Zealand", "Norway", "Poland", "Portugal", "Slovakia", "Slovenia",
    "South Korea", "Spain", "Sweden", "Switzerland", "United Kingdom",
    "United States",
]

df = raw[(raw["Year"] == 2024) & (raw["Entity"].isin(OECD_MEMBERS_2024))].copy()
df = df.sort_values("value", ascending=False).reset_index(drop=True)
df["highlight"] = df["Entity"] == "United Kingdom"
df["label"] = df["value"].map(lambda v: f"{v:.1f}%")

oecd_avg = raw.loc[
    (raw["Year"] == 2024) & (raw["Entity"] == "OECD countries"), "value"
].iloc[0]

country_order = df["Entity"].tolist()
n = len(df)

# ── Layout constants ─────────────────────────────────────────────────
STEP = 15          # px per bar (band height)
CHART_WIDTH = 330   # plot-area width; country labels sit in left padding
LABEL_COLOR = eco_style.pallete["domain"]

# ── Base encoding shared across layers ──────────────────────────────
y_enc = alt.Y(
    "Entity:N",
    sort=country_order,
    axis=None,  # country names are drawn as a text layer instead (avoids
                # a vl-convert label-clipping bug in wide category axes)
)

# ── Bars ──────────────────────────────────────────────────────────────
bars = (
    alt.Chart(df)
    .mark_bar(size=STEP - 4, cornerRadiusEnd=1)
    .encode(
        y=y_enc,
        x=alt.X(
            "value:Q",
            title=None,
            scale=alt.Scale(domain=[0, 22]),
            axis=alt.Axis(
                values=[0, 5, 10, 15, 20],
                labelExpr="datum.value + '%'",
            ),
        ),
        color=alt.condition(
            "datum.highlight",
            alt.value(eco_style.pallete["UK"]),
            alt.value(eco_style.pallete["bar"]["other"]),
        ),
    )
)

# ── Country name + value labels ────────────────────────────────────────
# Altair/Vega-Lite has no conditional fontWeight encoding channel, so the
# bold (UK) vs normal (rest) label styling is split into separate mark
# layers per subset rather than a single conditional encode().
df_uk = df[df["highlight"]]
df_other = df[~df["highlight"]]

def name_layer(data, weight):
    return (
        alt.Chart(data)
        .mark_text(align="right", baseline="middle", dx=-8, fontWeight=weight)
        .encode(y=y_enc, x=alt.value(0), text="Entity:N", color=alt.value(LABEL_COLOR))
    )

def value_layer(data, weight, color):
    return (
        alt.Chart(data)
        .mark_text(align="left", baseline="middle", dx=6, fontWeight=weight)
        .encode(y=y_enc, x="value:Q", text="label:N", color=alt.value(color))
    )

names_other = name_layer(df_other, "normal")
names_uk = name_layer(df_uk, "bold")
values_other = value_layer(df_other, "normal", LABEL_COLOR)
values_uk = value_layer(df_uk, "bold", eco_style.pallete["UK"])

# ── OECD average reference line ───────────────────────────────────────
avg_df = pd.DataFrame([{"value": oecd_avg}])

avg_rule = (
    alt.Chart(avg_df)
    .mark_rule(strokeDash=[4, 3], opacity=0.6)
    .encode(x="value:Q", color=alt.value(LABEL_COLOR))
)

avg_label = (
    alt.Chart(avg_df)
    .mark_text(align="center", baseline="bottom", dy=-4, fontSize=10)
    .encode(x="value:Q", y=alt.value(0), text=alt.value(f"OECD average, {oecd_avg:.1f}%"), color=alt.value(LABEL_COLOR))
)

# ── Assemble main chart ────────────────────────────────────────────────
main = (
    (bars + values_other + values_uk + names_other + names_uk + avg_rule + avg_label)
    .properties(
        width=CHART_WIDTH,
        height=alt.Step(STEP),
        title=alt.Title(
            text="The UK is a bigger public buyer than most of the OECD",
            subtitle="General government procurement, % of GDP, OECD countries, 2024",
            anchor="start",
            fontSize=16,
            fontWeight="bold",
            color=LABEL_COLOR,
            subtitleFontSize=11,
            subtitleColor=LABEL_COLOR,
            offset=14,
        ),
    )
)

# ── Source caption ──────────────────────────────────────────────────────
caption_text = (
    "Source: OECD, Government at a Glance 2025, via Our World in Data. "
    "Chile: no 2024 data. Turkiye: latest data is 2020, excluded."
)

caption = (
    alt.Chart(pd.DataFrame([{"text": caption_text}]))
    .mark_text(align="left", fontSize=9, color=LABEL_COLOR)
    .encode(x=alt.value(0), text="text:N")
    .properties(width=CHART_WIDTH, height=14)
)

chart = (
    alt.vconcat(main, caption, spacing=10)
    .configure_view(stroke="transparent")
    .properties(padding={"left": 96, "right": 28, "top": 20, "bottom": 4})
)

if __name__ == "__main__":
    chart.save("uk_procurement_vs_oecd.png", scale_factor=3)
    chart.save("uk_procurement_vs_oecd.json")
    print("Saved PNG and JSON")
