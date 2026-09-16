"""
Chart of the Day — PISA 2025: the UK held its ground while OECD scores fell away.

Three panels, one per domain: UK mean score against the OECD average-23
comparator, from each domain's first cycle to 2025.

Economics Observatory house style. Retrieval only: every value plotted is a mean
score published by OECD. Nothing here is computed.

SOURCE
    OECD (2026), PISA 2025 Results (Volume I): Future-Ready Students,
    OECD Publishing, Paris. https://doi.org/10.1787/73451bc5-en
    Annex B1, Table I.B1.2, sub-tables:
        Table I.B1.2a.37  reading,     PISA 2000-2025
        Table I.B1.2a.38  mathematics, PISA 2003-2025
        Table I.B1.2a.36  science,     PISA 2006-2025
    StatLink: https://stat.link/mrq53f  (version 1, 08-Sep-2026)

    Layout: title rows 1-2, three-deep header ending row 9, then 'OECD average',
    'OECD average-23', 'OECD average-35', 'OECD total' and economies. Column A
    is the economy, then Mean/S.E. pairs, one pair per cycle, then published
    change columns. Missing values are 'm'.

WHY 'OECD average-23' AND NOT 'OECD average'
    The plain OECD average row carries only a handful of cycles in these tables
    (membership and participation changed), so it cannot be drawn as a line.
    OECD average-23 is the arithmetic mean across OECD members excluding
    Austria, Chile, Colombia, Costa Rica, Estonia, Israel, Lithuania,
    Luxembourg, the Netherlands, the Slovak Republic, Slovenia, Spain, Türkiye,
    the United Kingdom and the United States. It is the same 23 countries in all
    three domains and every cycle from 2000, which is what makes it comparable.

    Note that it EXCLUDES the United Kingdom. The UK is being plotted against a
    benchmark it does not sit inside, which is the honest comparison and worth
    saying in the copy.

    It is NOT the same series as the 463 / 461 all-member averages used on the
    maths-reading scatter. Do not mix the two across charts without saying so.

WHAT THIS CHART DELIBERATELY DOES NOT DO
    No computed changes. OECD prints its own difference columns; the values
    below are read from them, never subtracted here.
    No interpolation across missing cycles.

OUTPUTS (written to <route>/charts/)
    pisa_2025_uk_three_domains.png   (scale_factor=3)
    pisa_2025_uk_three_domains.svg
    pisa_2025_uk_three_domains.json  (Vega-Lite, data inlined)
    pisa_2025_uk_three_domains_data.csv
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
STEM = os.path.join(OUT_DIR, "pisa_2025_uk_three_domains")

# Panel order left to right. Science last: it is the focal domain of the cycle
# and the only one where the UK rose, so it carries the payoff.
SHEETS = [("Reading", "Table I.B1.2a.37"),
          ("Mathematics", "Table I.B1.2a.38"),
          ("Science", "Table I.B1.2a.36")]
HEADER_ROW = 7          # 0-indexed row holding 'PISA 2000', 'PISA 2003', …
SKIPROWS = 9
SERIES = {"United Kingdom": "UK", "OECD average-23": "OECD-23"}

EXPECT_CYCLES = {
    "Reading": [2000, 2003, 2006, 2009, 2012, 2015, 2018, 2022, 2025],
    "Mathematics": [2003, 2006, 2009, 2012, 2015, 2018, 2022, 2025],
    "Science": [2006, 2009, 2012, 2015, 2018, 2022, 2025],
}
# Published 2025 values, asserted so a column shift crashes rather than
# plotting the wrong cycle.
EXPECT_2025 = {
    "Reading": {"UK": 494, "OECD-23": 466},
    "Mathematics": {"UK": 488, "OECD-23": 469},
    "Science": {"UK": 511, "OECD-23": 486},
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
C_UK = eco_style.pallete["United Kingdom"]     # #179fdb
C_OECD = eco_style.pallete["nominal_4"]        # #122b39
PANEL = tint(INK, 0.85)
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


def read_domain(domain, sheet):
    """Return tidy rows for one domain, with cycle columns detected from the header."""
    head = pd.read_excel(SOURCE_FILE, sheet_name=sheet, header=None,
                         skiprows=HEADER_ROW, nrows=1, dtype=object)
    # Cycle columns read 'PISA 2006'. Change columns read 'PISA 2006\n(2025 - 2006)'
    # and must be excluded, or the last cycles silently become differences.
    cycles = {}
    for i, v in enumerate(head.iloc[0]):
        s = str(v).strip()
        if s.startswith("PISA ") and "(" not in s:
            cycles[int(s.split()[1])] = i
    assert list(cycles) == EXPECT_CYCLES[domain], (
        f"{domain}: detected cycles {list(cycles)}, "
        f"expected {EXPECT_CYCLES[domain]}."
    )

    raw = pd.read_excel(SOURCE_FILE, sheet_name=sheet, header=None,
                        skiprows=SKIPROWS, dtype=object)
    raw[0] = raw[0].astype(str).str.strip().str.replace(r"\s*\*+$", "", regex=True)

    rows = []
    for name, label in SERIES.items():
        hit = raw[raw[0].eq(name)]
        assert not hit.empty, f"Row '{name}' not found in {sheet}."
        r = hit.iloc[0]
        for yr, col in cycles.items():
            val = pd.to_numeric(r[col], errors="coerce")   # 'm' -> NaN
            if pd.notna(val):
                rows.append({"domain": domain, "series": label,
                             "cycle": yr, "score": float(val)})
    return rows


print("Reading Table I.B1.2 trend sub-tables …")
df = pd.DataFrame([r for d, s in SHEETS for r in read_domain(d, s)])

for domain, checks in EXPECT_2025.items():
    for label, want in checks.items():
        got = df[(df.domain == domain) & (df.series == label) & (df.cycle == 2025)]
        assert not got.empty, f"{domain} {label} 2025 missing after parse."
        assert round(float(got.score.iloc[0])) == want, (
            f"{domain} {label} 2025 parsed as {round(float(got.score.iloc[0]))}, "
            f"expected {want}."
        )
for domain in EXPECT_CYCLES:
    have = sorted(df.loc[(df.domain == domain) & (df.series == "OECD-23"), "cycle"])
    assert have == EXPECT_CYCLES[domain], (
        f"{domain}: OECD-23 has cycles {have}, a gap would break the line."
    )

for domain in EXPECT_CYCLES:
    vals = {s: int(round(df[(df.domain == domain) & (df.series == s)
                            & (df.cycle == 2025)].score.iloc[0]))
            for s in SERIES.values()}
    print(f"  {domain:12s} 2025  UK {vals['UK']}  |  OECD-23 {vals['OECD-23']}")


# ----------------------------------------------------------------------------
# Panels
# ----------------------------------------------------------------------------
PW, PH = 215, 300
X_DOMAIN = [1998, 2038]     # right-hand headroom for the end labels;
# widened so "OECD-23" fits inside every panel, not just the last one
Y_DOMAIN = [460, 520]
SCALE_COLOUR = alt.Scale(domain=["UK", "OECD-23"], range=[C_UK, C_OECD])


def make_panel(domain, show_y, show_names):
    sub = df[df.domain == domain]
    ends = sub[sub.cycle == sub.cycle.max()]

    enc_x = alt.X(
        "cycle:Q",
        scale=alt.Scale(domain=X_DOMAIN, nice=False),
        axis=alt.Axis(title=None, values=[2005, 2015, 2025], format="d",
                      labelAngle=0, labelFontSize=11),
    )
    # Panels are separate views, not layers, so hiding the axis on panels 2 and
    # 3 does not suppress it on panel 1. Within a panel every layer reuses the
    # identical encoding object, which is what keeps the shared axis alive.
    enc_y = alt.Y(
        "score:Q",
        scale=alt.Scale(domain=Y_DOMAIN, nice=False),
        # axis=None would drop the gridlines too, leaving panels 2 and 3
        # without the horizontal rules panel 1 has. Hide labels instead.
        axis=alt.Axis(title=None, format="d", tickCount=4, labelFontSize=11,
                      labels=show_y, ticks=False, domain=show_y),
    )
    colour = alt.Color("series:N", scale=SCALE_COLOUR, legend=None)

    lines = (alt.Chart(sub).mark_line(strokeWidth=2.2)
             .encode(x=enc_x, y=enc_y, color=colour)
             .properties(width=PW, height=PH))
    dots = (alt.Chart(ends).mark_point(filled=True, size=48)
            .encode(x=enc_x, y=enc_y, color=colour))
    values = (alt.Chart(ends)
              .mark_text(align="left", baseline="middle", dx=8,
                         fontSize=11, fontWeight=700)
              .encode(x=enc_x, y=enc_y, color=colour,
                      text=alt.Text("score:Q", format=".0f")))
    layers = [lines, dots, values]
    if show_names:
        layers.append(
            alt.Chart(ends)
            .mark_text(align="left", baseline="middle", dx=8, dy=14,
                       fontSize=11)
            .encode(x=enc_x, y=enc_y, color=colour, text="series:N"))

    return (alt.layer(*layers)
            .properties(width=PW, height=PH,
                        title=alt.TitleParams(domain, anchor="start",
                                              fontSize=13, color=PANEL,
                                              offset=8)))


panels = alt.hconcat(
    make_panel("Reading", show_y=True, show_names=True),
    make_panel("Mathematics", show_y=False, show_names=True),
    make_panel("Science", show_y=False, show_names=True),
    spacing=18,
).resolve_scale(y="shared", color="shared")

note = alt.TitleParams(
    [
        "Source: OECD (2026), PISA 2025 Results (Volume I).",
    ],
    fontSize=10, fontWeight=400, color=NOTE, anchor="start",
    orient="bottom", offset=18, lineHeight=13,
)

# Two TitleParams cannot sit on one object, so the heading goes on an inner
# vconcat and the note on the outer one; both anchor to the same canvas edge.
titled = alt.vconcat(panels).properties(
    title=alt.TitleParams(
        "The UK held its ground as OECD scores fell away",
        subtitle=["Mean PISA score by cycle, UK and the OECD-23 comparator"],
        fontSize=19, subtitleFontSize=12, subtitleColor=SUBTITLE,
        anchor="start", offset=12, subtitlePadding=7,
    )
)
final = (alt.vconcat(titled, title=note)
         .configure_view(strokeWidth=0, stroke=None)
         .configure_axis(labelFontSize=11))

spec = final.to_dict()
with open(f"{STEM}.png", "wb") as f:
    f.write(vlc.vegalite_to_png(spec, scale=3))
with open(f"{STEM}.svg", "w", encoding="utf-8") as f:
    f.write(vlc.vegalite_to_svg(spec))
with open(f"{STEM}.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
df.to_csv(f"{STEM}_data.csv", index=False)

print(f"\nWrote 4 files to {OUT_DIR}")
