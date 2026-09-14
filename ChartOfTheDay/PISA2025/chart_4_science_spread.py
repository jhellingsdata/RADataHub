"""
Chart of the Day — PISA 2025: the UK's high science average hides a wide gap.

For each economy, the 10th percentile, the mean and the 90th percentile science
score on one row. The bar length is the distance between the weakest and
strongest tenth of students.

Economics Observatory house style. Retrieval only: every value plotted is a
score published by OECD. Nothing here is computed.

SOURCE
    OECD (2026), PISA 2025 Results (Volume I): Future-Ready Students,
    OECD Publishing, Paris. https://doi.org/10.1787/73451bc5-en
    Annex B1, Table I.B1.2, sub-table 'Table I.B1.2a.1' —
    Mean score and variation in science performance.
    StatLink: https://stat.link/mrq53f  (version 1, 08-Sep-2026)

    Layout: title rows 1-2, three-deep header ending row 9, then 'OECD average',
    'OECD total' and economies. Column A is the economy, then Mean/S.E.,
    S.D./S.E., and Score/S.E. pairs for the 10th, 25th, 50th, 75th and 90th
    percentiles. The 10th percentile is column 5, the 90th is column 13.

WHY THIS CHART
    A mean tells you where a system sits. It says nothing about how far apart
    its students are. OECD reports that the gap between the highest- and
    lowest-achieving students in science widened between 2022 and 2025. The
    published percentiles show that directly, and they show that two systems
    with similar averages can have very different floors.

WHAT THIS CHART DELIBERATELY DOES NOT DO
    No computed spread. The P90-minus-P10 distance is shown as bar length, not
    stated as a number, because subtracting two published percentiles is
    arithmetic. Only the published P10, mean and P90 values are labelled.
    No standard deviations, even though the table carries them; mixing an SD
    with percentiles in one chart invites a comparison the chart cannot support.

TRAP
    Do NOT describe the UK spread as one of the widest. Checked against all 91
    economies with percentile data, the UK sits 17th, above the median but well
    behind Luxembourg, the United States, Israel and Germany. The finding this
    chart actually supports is about the floor: Estonia posts a higher mean than
    the UK with a LOWER 90th percentile, because its 10th percentile is far
    higher. The UK's strength in science sits at the top end.

OUTPUTS (written to <route>/charts/)
    pisa_2025_science_spread.png   (scale_factor=3)
    pisa_2025_science_spread.svg
    pisa_2025_science_spread.json  (Vega-Lite, data inlined)
    pisa_2025_science_spread_data.csv
"""

import copy
import json
import os
import re

import altair as alt
import pandas as pd
import vl_convert as vlc

import eco_style  # registers the 'report' theme and exposes `pallete`

alt.theme.enable("report")
alt.data_transformers.disable_max_rows()

# Single editable route. The dataset is read from here and every output
# is written to the charts/ folder beside it, created on first run.
SOURCE_FILE = "/Users/alonso/Documents/GitHub/RADataHub/ChartOfTheDay/PISA2025/mrq53f.xlsx"
OUT_DIR = os.path.join(os.path.dirname(SOURCE_FILE), "charts")
os.makedirs(OUT_DIR, exist_ok=True)
STEM = os.path.join(OUT_DIR, "pisa_2025_science_spread")

SHEET = "Table I.B1.2a.1"
SKIPROWS = 9
COL_ECONOMY, COL_MEAN, COL_P10, COL_P90 = 0, 1, 5, 13
AVERAGE_ROW = "OECD average"

HIGHLIGHT = "United Kingdom"
PEERS = {
    "Singapore": "SGP",
    "Japan": "JPN",
    "Estonia": "EST",
    "Korea": "KOR",
    "United Kingdom": "UK",
    "Canada": "CAN",
    "United States": "USA",
    "Germany": "DEU",
    "France": "FRA",
    "Italy": "ITA",
    "Denmark": "DNK",
}

# Published values, asserted so a column shift crashes rather than plotting the
# wrong percentile out of a 15-column table.
EXPECT = {
    "UK": {"mean": 511, "p10": 374, "p90": 646},
    "EST": {"mean": 527, "p10": 410, "p90": 640},
}
EXPECT_AVERAGE = {"mean": 482, "p10": 351, "p90": 610}


def tint(colour, alpha=None, over=(255, 255, 255)):
    """Composite an eco_style palette colour onto `over` at `alpha`.

    Needed because some palette entries are rgba() and vl-convert silently
    drops the alpha on a mark colour property, rendering them solid.
    """
    m = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)",
        str(colour),
    )
    if m:
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
    else:
        h = str(colour).lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = 1.0
    if alpha is not None:
        a = alpha
    mix = [round(a * c + (1 - a) * o) for c, o in zip((r, g, b), over)]
    return "#{:02x}{:02x}{:02x}".format(*mix)


INK = eco_style.pallete["domain"]
C_UK = eco_style.pallete["United Kingdom"]      # #179fdb
C_BAR = eco_style.pallete["Other_3"]            # #d6d4d4
C_BAR_UK = eco_style.pallete["bar"]["other"]    # #a8c0de
C_DOT = eco_style.pallete["nominal_4"]          # #122b39
MUTED = tint(INK, 0.75)
SUBTITLE = tint(INK, 0.70)
NOTE = tint(INK, 0.65)


def refit(enc, field):
    """Copy an X/Y encoding, changing only the field it points at.

    A helper layer that builds its own alt.X/alt.Y (or passes axis=None) drops
    the shared axis for the whole layered view, so the scale and axis objects
    have to be carried over intact.
    """
    out = copy.deepcopy(enc)
    out.shorthand = field
    return out


# ----------------------------------------------------------------------------
# Load
# ----------------------------------------------------------------------------
if not os.path.exists(SOURCE_FILE):
    raise FileNotFoundError(
        f"{SOURCE_FILE} not found. Download Table I.B1.2 from "
        "https://stat.link/mrq53f and save it to that path."
    )

print(f"Reading {SHEET} …")
raw = pd.read_excel(SOURCE_FILE, sheet_name=SHEET, header=None,
                    skiprows=SKIPROWS, dtype=object)
economy = raw[COL_ECONOMY].astype(str).str.strip()
tbl = pd.DataFrame({
    "economy": economy.str.replace(r"\s*\*+$", "", regex=True),
    "flagged": economy.str.endswith("*"),
    "mean": pd.to_numeric(raw[COL_MEAN], errors="coerce"),
    "p10": pd.to_numeric(raw[COL_P10], errors="coerce"),
    "p90": pd.to_numeric(raw[COL_P90], errors="coerce"),
}).dropna(subset=["mean", "p10", "p90"])

avg = tbl.loc[tbl["economy"].eq(AVERAGE_ROW)]
assert not avg.empty, f"'{AVERAGE_ROW}' row missing from {SHEET}."
for key, want in EXPECT_AVERAGE.items():
    got = float(avg.iloc[0][key])
    assert abs(got - want) <= 1.0, (
        f"OECD average {key} parsed as {got:.1f}, expected about {want}. "
        "Wrong column."
    )

N_ECONOMIES = int((~tbl["economy"].str.startswith("OECD")).sum())

df = tbl[tbl["economy"].isin(PEERS)].copy()
df["code"] = df["economy"].map(PEERS)
df["is_uk"] = df["economy"].eq(HIGHLIGHT)

for name in PEERS:
    assert name in set(tbl["economy"]), f"Peer '{name}' not in {SHEET}."
# Tolerance of 1 point rather than exact equality: several published values sit
# on a .5 boundary (UK P90 is 646.5) where Python rounds to even. The check
# exists to catch a column shift, which would be wrong by tens of points.
for code, checks in EXPECT.items():
    row = df.loc[df["code"].eq(code)].iloc[0]
    for key, want in checks.items():
        got = float(row[key])
        assert abs(got - want) <= 1.0, (
            f"{code} {key} parsed as {got:.1f}, expected about {want}. "
            "Wrong column."
        )

# Altair's sort="-x" is unreliable in layered charts, so pass an explicit list.
ORDER = df.sort_values("mean", ascending=False)["code"].tolist()
uk = df.loc[df["is_uk"]].iloc[0]
print(f"  UK science  P10 {uk['p10']:.0f} | mean {uk['mean']:.0f} | "
      f"P90 {uk['p90']:.0f}   ({N_ECONOMIES} economies in the table)")


# ----------------------------------------------------------------------------
# Chart
# ----------------------------------------------------------------------------
W, H = 560, 400

enc_x = alt.X(
    "p10:Q",
    # Left edge held back from the lowest P10 (342) so its outboard
    # label clears the row codes on the axis.
    scale=alt.Scale(domain=[310, 710], nice=False),
    axis=alt.Axis(title="Science score", titleFontSize=12, titleColor=INK,
                  titlePadding=10, format="d", tickCount=5),
)
enc_y = alt.Y("code:N", sort=ORDER, axis=alt.Axis(title=None, labelFontSize=12))

# Bar spans P10 to P90. x2 carries no axis of its own so it inherits the scale.
spread = (
    alt.Chart(df)
    .mark_bar(height=11, cornerRadius=5.5)
    .encode(x=enc_x, x2=alt.X2("p90:Q"), y=enc_y,
            color=alt.condition(alt.datum.is_uk, alt.value(C_BAR_UK),
                                alt.value(C_BAR)),
            tooltip=["economy:N", "p10:Q", "mean:Q", "p90:Q"])
    .properties(width=W, height=H)
)
mean_dot = (
    alt.Chart(df)
    .mark_point(filled=True, size=90, shape="diamond")
    .encode(x=refit(enc_x, "mean:Q"), y=enc_y,
            color=alt.condition(alt.datum.is_uk, alt.value(C_UK),
                                alt.value(C_DOT)))
)
p10_label = (
    alt.Chart(df)
    .mark_text(align="right", baseline="middle", dx=-8, fontSize=10,
               color=MUTED)
    .encode(x=enc_x, y=enc_y, text=alt.Text("p10:Q", format=".0f"))
)
p90_label = (
    alt.Chart(df)
    .mark_text(align="left", baseline="middle", dx=8, fontSize=10, color=MUTED)
    .encode(x=refit(enc_x, "p90:Q"), y=enc_y,
            text=alt.Text("p90:Q", format=".0f"))
)
mean_label = (
    alt.Chart(df[df["is_uk"]])
    .mark_text(align="center", baseline="bottom", dy=-11, fontSize=11,
               fontWeight=700, color=C_UK)
    .encode(x=refit(enc_x, "mean:Q"), y=enc_y,
            text=alt.Text("mean:Q", format=".0f"))
)

chart = (
    alt.layer(spread, mean_dot, p10_label, p90_label, mean_label)
    .properties(
        width=W,
        height=H,
        title=alt.TitleParams(
            "Where UK science students sit, from the weakest tenth to the "
            "strongest",
            subtitle=[
                "Science score at the 10th and 90th percentile, with the mean "
                "marked as a diamond, 2025. Sorted by mean score.",
            ],
            fontSize=17,
            subtitleFontSize=12,
            subtitleColor=SUBTITLE,
            anchor="start",
            offset=14,
            subtitlePadding=7,
        ),
    )
)

note = alt.TitleParams(
    [
        "Source: OECD (2026), PISA 2025 Results (Volume I), Table I.B1.2 "
        "(stat.link/mrq53f), published 8 September 2026.",
        "Bar ends are the published 10th and 90th percentile scores; the "
        "distance between them is not a figure OECD publishes.",
        f"Selected economies shown, of {N_ECONOMIES} in the table. Labels are "
        "ISO three-letter codes. Figures cover the whole United Kingdom.",
    ],
    fontSize=10,
    fontWeight=400,
    color=NOTE,
    anchor="start",
    orient="bottom",
    offset=18,
    lineHeight=13,
)

final = (
    alt.vconcat(chart, title=note)
    .configure_view(strokeWidth=0, stroke=None)
    .configure_axis(labelFontSize=11)
)

spec = final.to_dict()
with open(f"{STEM}.png", "wb") as f:
    f.write(vlc.vegalite_to_png(spec, scale=3))
with open(f"{STEM}.svg", "w", encoding="utf-8") as f:
    f.write(vlc.vegalite_to_svg(spec))
with open(f"{STEM}.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
df.drop(columns=["is_uk"]).to_csv(f"{STEM}_data.csv", index=False)

print(f"\nWrote 4 files to {OUT_DIR}")
