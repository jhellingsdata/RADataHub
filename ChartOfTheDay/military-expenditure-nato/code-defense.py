"""
Chart of the Day: Recent defence spending increases have been large
Dumbbell chart of military spending as % of GDP, 2016 vs 2025.
Source: SIPRI Military Expenditure Database, Apr. 2026.
UK highlighted; new NATO 3.5% core target line marked.
"""

import altair as alt
import pandas as pd
import vl_convert as vlc
import sys
import os

import eco_style
from eco_style import pallete

alt.themes.enable("report")

# -----------------------------------------------------------------------------
# Data: SIPRI Fact Sheet, Trends in World Military Expenditure 2025 (Apr. 2026)
# Table 1, "Spending as a share of GDP (%)" columns for 2016 and 2025.
# Selection: NATO members + Russia for context. UK highlighted.
# Ukraine excluded (40% of GDP wartime outlier compresses the rest of the chart).
# Figures with [] in the SIPRI table are SIPRI estimates; central value used.
# -----------------------------------------------------------------------------

data = pd.DataFrame([
    # country,         share_2016, share_2025, spending_bn_2025
    ("Russia",                 5.4,       7.5,             190.0),
    ("Poland",                 1.9,       4.5,              46.8),
    ("Norway",                 1.6,       3.3,              17.0),
    ("Denmark",                1.2,       3.3,              14.9),
    ("United States",          3.4,       3.1,             954.0),
    ("Greece",                 2.6,       3.0,               8.4),
    ("Finland",                1.4,       2.6,               8.1),
    ("Sweden",                 1.1,       2.5,              16.5),
    ("United Kingdom",         2.0,       2.4,              89.0),
    ("Germany",                1.1,       2.3,             114.0),
    ("Romania",                1.4,       2.3,               9.7),
    ("Netherlands",            1.1,       2.2,              28.9),
    ("Spain",                  1.1,       2.1,              40.2),
    ("France",                 1.9,       2.0,              68.0),
    ("Belgium",                0.9,       2.0,              14.5),
    ("Italy",                  1.3,       1.9,              48.1),
    ("Czechia",                1.0,       1.8,               7.1),
    ("Canada",                 1.1,       1.6,              37.5),
], columns=["country", "share_2016", "share_2025", "spending_bn_2025"])

data["change_pp"] = data["share_2025"] - data["share_2016"]

# Long format for the dumbbell points
data_long = data.melt(
    id_vars=["country", "change_pp", "spending_bn_2025"],
    value_vars=["share_2016", "share_2025"],
    var_name="year",
    value_name="share",
)
data_long["year"] = data_long["year"].str.replace("share_", "").astype(int)

# Highlight UK
HIGHLIGHT = "United Kingdom"
data["highlight"] = data["country"] == HIGHLIGHT
data_long["highlight"] = data_long["country"] == HIGHLIGHT

# Sort by 2025 share — highest at top
country_order = data.sort_values("share_2025", ascending=False)["country"].tolist()

# Colours
UK_COLOR = pallete["United Kingdom"]
OTHER_COLOR_2025 = pallete["domain"]
OTHER_COLOR_2016 = pallete["Other_3"]
DARK = pallete["domain"]

X_MAX = 8

y_enc = alt.Y(
    "country:N",
    sort=country_order,
    axis=alt.Axis(title=None, labelLimit=140, labelPadding=8),
)

# Chart components
rule = (
    alt.Chart(data)
    .mark_rule(strokeWidth=2)
    .encode(
        y=y_enc,
        x=alt.X("share_2016:Q"),
        x2="share_2025:Q",
        color=alt.condition(
            alt.datum.highlight,
            alt.value(UK_COLOR),
            alt.value(OTHER_COLOR_2016),
        ),
    )
)

points_2016 = (
    alt.Chart(data_long[data_long["year"] == 2016])
    .mark_circle(size=90, opacity=1)
    .encode(
        y=y_enc,
        x=alt.X("share:Q"),
        color=alt.condition(
            alt.datum.highlight,
            alt.value(UK_COLOR),
            alt.value(OTHER_COLOR_2016),
        ),
    )
)

points_2025 = (
    alt.Chart(data_long[data_long["year"] == 2025])
    .mark_point(size=140, filled=True, opacity=1, shape="diamond")
    .encode(
        y=y_enc,
        x=alt.X(
            "share:Q",
            scale=alt.Scale(domain=[0, X_MAX]),
            axis=alt.Axis(format=".0f", titlePadding=10, title="% of GDP",
                          values=[0, 2, 4, 6, 8],
                          labelExpr="datum.value + '%'"),
        ),
        color=alt.condition(
            alt.datum.highlight,
            alt.value(UK_COLOR),
            alt.value(OTHER_COLOR_2025),
        ),
    )
)

labels_2025 = (
    alt.Chart(data_long[data_long["year"] == 2025])
    .mark_text(align="left", dx=10, fontSize=10, fontWeight=500)
    .encode(
        y=y_enc,
        x=alt.X("share:Q"),
        text=alt.Text("share:Q", format=".1f"),
        color=alt.condition(
            alt.datum.highlight,
            alt.value(UK_COLOR),
            alt.value(DARK),
        ),
    )
)


# Inline legend: positioned at x=6 (% of GDP space), y=Italy (country space)
# Layered directly into the dumbbell so it shares the chart's scales.
legend_anchor = "Italy"

legend_data = pd.DataFrame([
    {"x": 6.0, "country": legend_anchor, "label": "2016", "shape": "circle"},
    {"x": 6.9, "country": legend_anchor, "label": "2025", "shape": "diamond"},
])

legend_circle = (
    alt.Chart(legend_data[legend_data["shape"] == "circle"])
    .mark_circle(size=90, color=OTHER_COLOR_2016)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("country:N", sort=country_order),
    )
)
legend_diamond = (
    alt.Chart(legend_data[legend_data["shape"] == "diamond"])
    .mark_point(size=140, filled=True, color=OTHER_COLOR_2025, opacity = 1, shape="diamond")
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("country:N", sort=country_order),
    )
)
legend_labels = (
    alt.Chart(legend_data)
    .mark_text(align="left", dx=10, fontSize=10, color=DARK)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("country:N", sort=country_order),
        text="label:N",
    )
)
legend = legend_circle + legend_diamond + legend_labels

# Compose main dumbbell panel
dumbbell = (
    (rule + points_2016 + points_2025 + labels_2025 + legend)
    .properties(
        width=380,
        height=440,
        title=alt.TitleParams(
            text="Military expenditure as a share of GDP, 2016 vs 2025",
            anchor="start",
            fontSize=11,
            fontWeight="normal",
            color=DARK,
        ),
    )
)

# Right panel: horizontal bars of $ bn spending in 2025
# Cap the visible scale and annotate the US which exceeds the cap.
BAR_X_MAX = 200
data["spending_capped"] = data["spending_bn_2025"].clip(upper=BAR_X_MAX)
data["spending_label"] = data["spending_bn_2025"].apply(
    lambda v: f"{v:,.0f}" if v >= 100 else f"{v:.0f}"
)

bars = (
    alt.Chart(data)
    .mark_bar(height=10)
    .encode(
        y=alt.Y("country:N", sort=country_order, axis=None),
        x=alt.X(
            "spending_capped:Q",
            scale=alt.Scale(domain=[0, BAR_X_MAX]),
            axis=alt.Axis(
                title="Expenditure ($ bn)",
                titlePadding=10,
                values=[0, 50, 100, 150, 200],
                format=",.0f",
                labelExpr="'$' + datum.value",
            ),
        ),
        color=alt.condition(
            alt.datum.highlight,
            alt.value(UK_COLOR),
            alt.value(OTHER_COLOR_2025),
        ),
    )
)

bar_labels = (
    alt.Chart(data)
    .mark_text(align="left", dx=4, fontSize=10, fontWeight=500)
    .encode(
        y=alt.Y("country:N", sort=country_order, axis=None),
        x=alt.X("spending_capped:Q"),
        text="spending_label:N",
        color=alt.condition(
            alt.datum.highlight,
            alt.value(UK_COLOR),
            alt.value(DARK),
        ),
    )
)

bar_panel = (bars + bar_labels).properties(
    width=180,
    height=440,
    title=alt.TitleParams(
        text="Military expenditure, 2025 ($ bn)",
        anchor="start",
        fontSize=11,
        fontWeight="normal",
        color=DARK,
    ),
)

# Stitch panels horizontally with a shared title
main = (
    alt.hconcat(dumbbell, bar_panel, spacing=20)
    .properties(
        title=alt.TitleParams(
            text="NATO's military burden is climbing across the alliance",
            subtitle="",
            anchor="start",
            fontSize=15,
            subtitleFontSize=10,
            subtitleColor=DARK,
            offset=10,
        ),
    )
)

# Source caption
source_caption = alt.vconcat(
    alt.Chart(pd.DataFrame({"text": [
        "Source: SIPRI Military Expenditure Database, April 2026."
    ]}))
    .mark_text(align="left", fontSize=9, color=DARK, opacity=0.7, x=0)
    .encode(text="text:N")
    .properties(width=580, height=12),
    alt.Chart(pd.DataFrame({"text": [
        "Note: US bar capped at $200bn; full value $954bn."
    ]}))
    .mark_text(align="left", fontSize=9, color=DARK, opacity=0.7, x=0)
    .encode(text="text:N")
    .properties(width=580, height=12),
    spacing=2,
)

chart = alt.vconcat(main, source_caption, spacing=4).configure_view(strokeWidth=0)

#Save chart as svg
chart.save("chart-defense.svg")
