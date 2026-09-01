"""
Chart of the Day — Iceland EU accession referendum, 29 August 2026.

Votes for and against restarting EU accession negotiations, by constituency,
as a share of valid votes.

Data: final counts from the six constituency returning officers (yfirkjörstjórnir),
as published by RÚV on 30 August 2026 with all votes counted. Official results pending
declaration by Landskjörstjórn.
"""

import os
import json

import altair as alt
import pandas as pd

import eco_style
from eco_style import pallete

alt.theme.enable("report")

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # Positron / Jupyter
    HERE = os.getcwd()

# ---------------------------------------------------------------- data

raw = pd.read_csv(os.path.join(HERE, "iceland_eu_referendum_2026.csv"))

seats = (
    raw[raw["level"] == "constituency"]
    .sort_values("yes_pct", ascending=False)
    .reset_index(drop=True)
)
national = raw[raw["level"] == "national"]

SPACER = " "  # blank row separating the national result from the constituencies

# Row order: the national result, a gap, then the six constituencies
ORDER = national["constituency"].tolist() + [SPACER] + seats["constituency"].tolist()

plot = pd.concat([national, seats], ignore_index=True)

plot["yes_label"] = plot["yes_pct"].map(lambda v: f"{v:.1f}%")
plot["no_label"] = plot["no_pct"].map(lambda v: f"{v:.1f}%")
plot["left"] = 0.0
plot["right"] = 100.0

# ---------------------------------------------------------------- encodings

BLUE = pallete["nominal_1"]  # yes
NAVY = pallete["bar"]["accent_1"]  # no

SCALE = alt.Scale(domain=[0, 100], nice=False)

x_share = alt.X("yes_pct:Q", scale=SCALE, axis=None)
x_left = alt.X("left:Q", scale=SCALE, axis=None)
x_right = alt.X("right:Q", scale=SCALE, axis=None)

y_area = alt.Y(
    "constituency:N",
    sort=ORDER,
    scale=alt.Scale(domain=ORDER, paddingInner=0.42),
    axis=alt.Axis(
        title=None, labelFontSize=12, domain=False, ticks=False, labelPadding=10
    ),
)

# Yes segment, from 0 out to the yes share
yes_bar = alt.Chart(plot).mark_bar(color=BLUE).encode(x=x_share, x2="left:Q", y=y_area)

# No segment, from the yes share out to 100
no_bar = alt.Chart(plot).mark_bar(color=NAVY).encode(x=x_share, x2="right:Q", y=y_area)

yes_value = (
    alt.Chart(plot)
    .mark_text(align="left", dx=10, fontSize=12, fontWeight=500, color="white")
    .encode(x=x_left, y=y_area, text="yes_label:N")
)

no_value = (
    alt.Chart(plot)
    .mark_text(align="right", dx=-10, fontSize=12, fontWeight=500, color="white")
    .encode(x=x_right, y=y_area, text="no_label:N")
)

# 50% marker over the bars, so it is obvious which side crossed it
fifty = (
    alt.Chart(pd.DataFrame({"yes_pct": [50.0]}))
    .mark_rule(strokeWidth=1.2, color="white", opacity=0.9)
    .encode(x=x_share)
)

# Direct labels above the bars instead of a legend
head_yes = (
    alt.Chart(plot.head(1))
    .mark_text(align="left", fontSize=13, fontWeight=600, color=BLUE, baseline="bottom")
    .encode(x=x_left, y=alt.value(-10), text=alt.datum("Yes"))
)

head_no = (
    alt.Chart(plot.head(1))
    .mark_text(align="right", fontSize=13, fontWeight=600, color=NAVY, baseline="bottom")
    .encode(x=x_right, y=alt.value(-10), text=alt.datum("No"))
)

head_fifty = (
    alt.Chart(pd.DataFrame({"yes_pct": [50.0]}))
    .mark_text(
        align="center", fontSize=11, color="rgba(24, 42, 56, 0.6)", baseline="bottom"
    )
    .encode(x=x_share, y=alt.value(-10), text=alt.datum("50%"))
)

chart = (
    alt.layer(
        yes_bar,
        no_bar,
        fifty,
        yes_value,
        no_value,
        head_yes,
        head_no,
        head_fifty,
    )
    .properties(
        width=580,
        height=290,
        title=alt.TitleParams(
            text="Iceland says no to reopening EU talks",
            subtitle=[
                "Votes for and against restarting EU accession negotiations, nationally and by",
                "constituency, 29 August 2026. Share of valid votes.",
            ],
            fontSize=19,
            fontWeight=600,
            subtitleFontSize=13,
            subtitleColor="rgba(24, 42, 56, 0.75)",
            subtitleLineHeight=18,
            anchor="start",
            offset=32,
            dy=-6,
        ),
    )
)

note = (
    alt.Chart(plot.head(1))
    .mark_text(
        align="left",
        baseline="top",
        fontSize=10.5,
        lineBreak="\n",
        color="rgba(24, 42, 56, 0.6)",
        lineHeight=14,
        dy=18,
    )
    .encode(
        x=alt.value(0),
        y=alt.value("height"),
        text=alt.datum(
            "Source: RÚV, all votes counted, 30 August 2026. Yes 105,339 votes, no 118,040. Turnout 82.5%.\n"
            "Blank and invalid ballots, 1,652 or 0.7% of votes cast, are excluded. Southwest covers the suburban municipalities around Reykjavík.\n"
            "Official results pending declaration by Landskjörstjórn."
        ),
    )
)

final = (
    alt.layer(chart, note)
    .configure_view(stroke=None, strokeWidth=0)
    .configure_axis(grid=False)
    .properties(padding={"left": 6, "right": 18, "top": 6, "bottom": 10})
)

# ---------------------------------------------------------------- outputs

final.save(os.path.join(HERE, "chart_iceland_referendum.png"), scale_factor=3)
final.save(os.path.join(HERE, "chart_iceland_referendum.svg"))

with open(os.path.join(HERE, "chart_iceland_referendum.json"), "w") as f:
    json.dump(final.to_dict(), f, indent=2, ensure_ascii=False)

print("written to", HERE)
