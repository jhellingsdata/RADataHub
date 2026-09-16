"""
Chart of the Day — PISA 2025: the UK's all-rounders.

Share of 15-year-olds who are top performers in science, reading AND mathematics
at the same time. UK against peers, with the OECD average as a reference rule.

Economics Observatory house style. Retrieval only: every value plotted is a
percentage published by OECD. Nothing here is computed.

SOURCE
    OECD (2026), PISA 2025 Results (Volume I): Future-Ready Students,
    OECD Publishing, Paris. https://doi.org/10.1787/73451bc5-en
    Annex B1, Table I.B1.2, sub-table 'Table I.B1.2a.21' —
    Overlap of top performers in science, reading and mathematics.
    StatLink: https://stat.link/mrq53f  (version 1, 08-Sep-2026)

    Layout: title rows 1-2, three-deep header ending row 9, then 'OECD average',
    'OECD total' and economies. Column A is the economy, then %/S.E. pairs for:
    col 1 not top in any, 3 top in any, 5 science only, 7 reading only,
    9 maths only, 11 science+reading, 13 science+maths, 15 reading+maths,
    17 all three.

WHY THIS TABLE
    Headline means say how a system does on average. This says something the
    means cannot: how many students clear the top-performer bar in all three
    subjects at once. It is published, so it needs no arithmetic, and it is
    rarely charted.

WHAT THIS CHART DELIBERATELY DOES NOT DO
    No ranks on the chart. OECD publishes ranks elsewhere; deriving one from a
    percentage table is arithmetic.
    No summing of the overlap categories, and no ratio of UK to OECD average.
    Both are arithmetic. The reference rule lets a reader see the gap instead:
    the UK reads 5.4% against an OECD average of 2.6%, and saying "twice as
    likely" would be a division neither figure supports on its own.

OUTPUTS (written to <route>/charts/)
    pisa_2025_top_performers.png   (scale_factor=3)
    pisa_2025_top_performers.svg
    pisa_2025_top_performers.json  (Vega-Lite, data inlined)
    pisa_2025_top_performers_data.csv
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
STEM = os.path.join(OUT_DIR, "pisa_2025_top_performers")

SHEET = "Table I.B1.2a.21"
SKIPROWS = 9
COL_ECONOMY = 0
COL_ALL_THREE = 17
AVERAGE_ROW = "OECD average"

HIGHLIGHT = "United Kingdom"
# Displayed by ISO three-letter code; B-S-J-Z has no ISO code so OECD's own
# abbreviation is used. Keys must match the OECD economy strings exactly.
PEERS = {
    "Singapore": "SGP",
    "B-S-J-Z (China)": "B-S-J-Z",
    "Japan": "JPN",
    "Korea": "KOR",
    "United States": "USA",
    "United Kingdom": "UK",
    "Estonia": "EST",
    "Canada": "CAN",
    "Germany": "DEU",
    "France": "FRA",
    "Italy": "ITA",
    "Denmark": "DNK",
}

# Published values, asserted so a column shift crashes rather than plotting the
# wrong column of a 19-column table.
EXPECT = {"UK": 5.4, "SGP": 15.3, "DNK": 1.3}
EXPECT_AVERAGE = 2.6


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
BAR_UK = eco_style.pallete["United Kingdom"]        # #179fdb
BAR_OTHER = eco_style.pallete["bar"]["other"]       # #a8c0de
RULE = tint(INK, 0.55)
MUTED = tint(INK, 0.75)
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
economy = raw[COL_ECONOMY].astype(str).str.strip()
tbl = pd.DataFrame({
    "economy": economy.str.replace(r"\s*\*+$", "", regex=True),
    "flagged": economy.str.endswith("*"),
    "share": pd.to_numeric(raw[COL_ALL_THREE], errors="coerce"),
}).dropna(subset=["share"])

avg = tbl.loc[tbl["economy"].eq(AVERAGE_ROW), "share"]
assert not avg.empty, f"'{AVERAGE_ROW}' row missing from {SHEET}."
OECD_AVERAGE = round(float(avg.iloc[0]), 1)
assert OECD_AVERAGE == EXPECT_AVERAGE, (
    f"OECD average parsed as {OECD_AVERAGE}, expected {EXPECT_AVERAGE}. "
    "Wrong column."
)

N_ECONOMIES = int((~tbl["economy"].str.startswith("OECD")).sum())

df = tbl[tbl["economy"].isin(PEERS)].copy()
df["code"] = df["economy"].map(PEERS)
df["is_uk"] = df["economy"].eq(HIGHLIGHT)

for name in PEERS:
    assert name in set(tbl["economy"]), f"Peer '{name}' not in {SHEET}."
for code, want in EXPECT.items():
    got = round(float(df.loc[df["code"].eq(code), "share"].iloc[0]), 1)
    assert got == want, f"{code} parsed as {got}, expected {want}."

# Altair's sort="-x" is unreliable in layered charts, so pass an explicit list.
ORDER = df.sort_values("share", ascending=False)["code"].tolist()
print(f"  UK {float(df.loc[df.is_uk, 'share'].iloc[0]):.1f}% vs OECD average "
      f"{OECD_AVERAGE}%   ({N_ECONOMIES} economies in the table)")


# ----------------------------------------------------------------------------
# Chart
# ----------------------------------------------------------------------------
W, H = 560, 400
rule_df = pd.DataFrame({"share": [OECD_AVERAGE]})

enc_x = alt.X(
    "share:Q",
    scale=alt.Scale(domain=[0, 17], nice=False),
    axis=alt.Axis(title="% of 15-year-olds", titleFontSize=12, titleColor=INK,
                  titlePadding=10, format="d", tickCount=5),
)
enc_y = alt.Y("code:N", sort=ORDER, axis=alt.Axis(title=None, labelFontSize=12))

bars = (
    alt.Chart(df)
    .mark_bar(height=16)
    .encode(x=enc_x, y=enc_y,
            color=alt.condition(alt.datum.is_uk, alt.value(BAR_UK),
                                alt.value(BAR_OTHER)),
            tooltip=["economy:N", "share:Q"])
    .properties(width=W, height=H)
)
values = (
    alt.Chart(df)
    .mark_text(align="left", baseline="middle", dx=6, fontSize=11)
    .encode(x=enc_x, y=enc_y, text=alt.Text("share:Q", format=".1f"),
            color=alt.condition(alt.datum.is_uk, alt.value(BAR_UK),
                                alt.value(MUTED)))
)
# Reference rule reuses the identical X encoding so the shared axis survives.
avg_rule = (
    alt.Chart(rule_df)
    .mark_rule(color=RULE, strokeDash=[3, 4], strokeWidth=1)
    .encode(x=enc_x)
)
avg_label = (
    alt.Chart(rule_df)
    .mark_text(align="left", baseline="bottom", dx=5, fontSize=11, color=MUTED,
               text=f"OECD average: {OECD_AVERAGE}%")
    # Anchored to the bottom of the plot: the top row is the longest bar, so a
    # top-anchored label would sit inside it.
    .encode(x=enc_x, y=alt.value(H - 6))
)

chart = (
    alt.layer(bars, values, avg_rule, avg_label)
    .properties(
        width=W,
        height=H,
        title=alt.TitleParams(
            "How many UK teenagers excel in science, reading and maths at "
            "once",
            subtitle=[
                "Share of 15-year-olds who are top performers in science, "
                "reading and mathematics at the same time, 2025.",
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
        "Top performer means proficiency Level 5 or 6. Labels are ISO "
        "three-letter codes; B-S-J-Z is Beijing, Shanghai, Jiangsu and "
        "Zhejiang (China).",
        f"Selected economies shown, of {N_ECONOMIES} in the table. Figures "
        "cover the whole United Kingdom; the four UK nations report separately.",
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
