"""
Chart of the Day — PISA 2025: UK science turned back up while the OECD kept falling.

Economics Observatory house style. Retrieval only: every value plotted is a mean
score published by OECD. Nothing here is computed.

SOURCE
    OECD (2026), PISA 2025 Results (Volume I): Future-Ready Students,
    OECD Publishing, Paris. https://doi.org/10.1787/73451bc5-en
    Annex B1, Table I.B1.2, sub-table 'Table I.B1.2a.36' —
    Mean science performance, 2006 through 2025.
    StatLink: https://stat.link/mrq53f  (version 1, 08-Sep-2026)

    Layout: title rows 1-2, three-deep header ending row 9, then 'OECD average',
    'OECD average-23', 'OECD average-35', 'OECD total' and economies. Column A
    is the economy; then Mean/S.E. pairs for PISA 2006, 2009, 2012, 2015, 2018,
    2022, 2025, followed by published change columns. Missing values are 'm'.

THE COMPARATOR MATTERS
    The plain 'OECD average' row is mostly 'm' in this table: it only carries
    2012, 2015 and 2025, because OECD membership and participation changed
    across cycles. 'OECD average-23' is the 23 countries with valid data in
    every science cycle since 2006, and is the row OECD itself uses for trend
    comparison. That is the row plotted here, and the subtitle says so.

WHAT THIS CHART DELIBERATELY DOES NOT DO
    No computed changes. OECD prints a 'PISA 2025 - PISA 2006' difference
    column; those published values are asserted below and may be quoted, but
    nothing is subtracted here.
    No trend line, no interpolation across the 'm' gaps.
    The x-axis is ordinal, one slot per cycle, so the 2018-2022 gap (four years,
    PISA 2021 having been postponed) is drawn the same width as the three-year
    gaps. Cycles are the unit of comparison, which is how OECD presents trends.
    The y-axis is cropped to 478-520; PISA scales have no meaningful zero, so a
    cropped window is standard, but it does make the 2025 upturn look steeper
    than a full-scale view would.

OUTPUTS (written to <route>/charts/)
    pisa_2025_science_trend.png   (scale_factor=3)
    pisa_2025_science_trend.svg
    pisa_2025_science_trend.json  (Vega-Lite, data inlined)
    pisa_2025_science_trend_data.csv
"""

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
STEM = os.path.join(OUT_DIR, "pisa_2025_science_trend")

SHEET = "Table I.B1.2a.36"
SKIPROWS = 9
CYCLES = [2006, 2009, 2012, 2015, 2018, 2022, 2025]
MEAN_COLS = {yr: 1 + 2 * i for i, yr in enumerate(CYCLES)}   # A=0, then Mean/S.E.

SERIES = {"United Kingdom": "UK", "OECD average-23": "OECD average"}

# Published values, asserted so a column shift or a sheet reshuffle crashes
# rather than plotting the wrong series.
EXPECT = {
    "UK": {2006: 515, 2022: 500, 2025: 511},
    "OECD average": {2006: 503, 2022: 491, 2025: 486},
}


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
C_OECD = eco_style.pallete["nominal_4"]         # #122b39
SUBTITLE = tint(INK, 0.70)
NOTE = tint(INK, 0.65)


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
raw[0] = (raw[0].astype(str).str.strip()
          .str.replace(r"\s*\*+$", "", regex=True))

rows = []
for name, label in SERIES.items():
    hit = raw[raw[0].eq(name)]
    assert not hit.empty, f"Row '{name}' not found in {SHEET}."
    r = hit.iloc[0]
    for yr, col in MEAN_COLS.items():
        val = pd.to_numeric(r[col], errors="coerce")   # 'm' -> NaN
        if pd.notna(val):
            rows.append({"series": label, "cycle": yr, "score": float(val)})

df = pd.DataFrame(rows)

for label, checks in EXPECT.items():
    for yr, want in checks.items():
        got = df.loc[(df.series == label) & (df.cycle == yr), "score"]
        assert not got.empty, f"{label} {yr} missing after parse."
        assert round(float(got.iloc[0])) == want, (
            f"{label} {yr} parsed as {round(float(got.iloc[0]))}, expected {want}."
        )

# Every cycle must be present for both series, or the line would silently jump.
for label in SERIES.values():
    have = sorted(df.loc[df.series == label, "cycle"])
    assert have == CYCLES, f"{label} has cycles {have}, expected {CYCLES}."

print("  " + " | ".join(
    f"{lab}: {int(round(df.loc[(df.series == lab) & (df.cycle == 2022), 'score'].iloc[0]))}"
    f" (2022) -> {int(round(df.loc[(df.series == lab) & (df.cycle == 2025), 'score'].iloc[0]))} (2025)"
    for lab in SERIES.values()))


# ----------------------------------------------------------------------------
# Chart
# ----------------------------------------------------------------------------
W, H = 600, 380
ends = df[df.cycle == df.cycle.max()]

enc_x = alt.X(
    "cycle:O",
    axis=alt.Axis(title=None, labelAngle=0, labelFontSize=11, format="d"),
)
enc_y = alt.Y(
    "score:Q",
    scale=alt.Scale(domain=[478, 520], nice=False),
    axis=alt.Axis(title="Mean science score", titleFontSize=12, titleColor=INK,
                  titleAlign="left", titleAngle=0, titleBaseline="bottom",
                  titleX=0, titleY=-10, format="d", tickCount=5),
)
scale_colour = alt.Scale(domain=list(SERIES.values()), range=[C_UK, C_OECD])

lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.4)
    .encode(x=enc_x, y=enc_y,
            color=alt.Color("series:N", scale=scale_colour, legend=None))
    .properties(width=W, height=H)
)
dots = (
    alt.Chart(df)
    .mark_point(filled=True, size=52)
    .encode(x=enc_x, y=enc_y,
            color=alt.Color("series:N", scale=scale_colour, legend=None),
            tooltip=["series:N", "cycle:O", "score:Q"])
)
# Direct end labels instead of a legend.
end_labels = (
    alt.Chart(ends)
    .mark_text(align="left", baseline="middle", dx=12, fontSize=12,
               fontWeight=700)
    .encode(x=enc_x, y=enc_y, text="series:N",
            color=alt.Color("series:N", scale=scale_colour, legend=None))
)
end_values = (
    alt.Chart(ends)
    .mark_text(align="left", baseline="middle", dx=12, dy=15, fontSize=11)
    .encode(x=enc_x, y=enc_y, text=alt.Text("score:Q", format=".0f"),
            color=alt.Color("series:N", scale=scale_colour, legend=None))
)

chart = (
    alt.layer(lines, dots, end_labels, end_values)
    .properties(
        width=W,
        height=H,
        title=alt.TitleParams(
            "UK science scores turned back up in 2025",
            subtitle=[
                "Mean PISA science score by cycle. The OECD comparator is the "
                "23 countries with data in every cycle since 2006.",
            ],
            fontSize=18,
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
        "Plotted against 'OECD average-23', the consistent set OECD uses for "
        "trend comparison; the all-member average is not published for every "
        "cycle.",
        "Figures cover the whole United Kingdom; the four UK nations also "
        "report separately.",
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
df.to_csv(f"{STEM}_data.csv", index=False)

print(f"\nWrote 4 files to {OUT_DIR}")
