"""England's Strategic Authorities by statutory tier, September 2026.

Altair choropleth built on the eco_style report theme.

Pipeline
    build_tables.py    -> msa_tiers.csv, msa_lad_crosswalk.csv  (validated)
    build_geometry.py  -> geo/england.geojson, geo/sa_areas.geojson, msa_anchors.csv
    msa_map.py         -> outputs/msa_tiers_map.{png,svg,html}

Design notes
    Coordinates are British National Grid (EPSG:27700) and the chart uses
    d3's identity projection with an explicit scale and translate. That makes
    every screen position predictable from a grid reference, so label
    positions can be set in metres and will not drift when the data changes.

    Label anchors sit in the sea and over Wales, neither of which is drawn,
    which is what keeps the label columns clear of the coastline.
"""

import json
import shutil
from pathlib import Path

import altair as alt
import geopandas as gpd
import pandas as pd
import vl_convert as vlc

import eco_style

OUT = Path("/mnt/user-data/outputs")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Theme: eco_style report, with the font resolved for static export
# ---------------------------------------------------------------------------

FONT = "Carlito"  # stand-in for Circular Std, which is not installed here
P = eco_style.pallete


def report_local():
    """eco_style.report() with a locally available font and title styling.

    Swap FONT back to "Circular Std" wherever the licensed font is installed;
    nothing else in the spec changes.
    """
    spec = eco_style.report()
    cfg = spec["config"]
    cfg["font"] = FONT
    cfg["axisX"]["labelFont"] = FONT
    cfg["axisY"]["labelFont"] = FONT
    cfg["title"] = {
        "font": FONT,
        "subtitleFont": FONT,
        "fontSize": 17,
        "fontWeight": 600,
        "subtitleFontSize": 11.5,
        "subtitleLineHeight": 15,
        "color": P["domain"],
        "subtitleColor": "#5b6b76",
        "anchor": "start",
        "offset": 14,
        "subtitlePadding": 8,
    }
    cfg["legend"] = {
        "labelFont": FONT,
        "titleFont": FONT,
        "labelFontSize": 11.5,
        "titleFontSize": 11.5,
        "titleColor": P["domain"],
        "labelColor": P["domain"],
        "titleFontWeight": 600,
        "symbolType": "square",
        "symbolSize": 150,
        "labelOffset": 7,
        "rowPadding": 5,
    }
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_local", report_local)
    alt.themes.enable("report_local")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_local", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Tier scale: a dark-to-light escalator, so tier reads off the page
# ---------------------------------------------------------------------------

NO_SA = "Not in a strategic authority"

TIER_DISPLAY = {
    "Established Mayoral": "Established Mayoral",
    "Mayoral": "Mayoral",
    "Foundation": "Foundation",
    "Planned": "Agreed, not yet established",
}

TIER_COLOURS = {
    "Established Mayoral": P["nominal_4"],   # #122b39
    "Mayoral": "#0063af",
    "Foundation": P["nominal_1"],            # #179fdb
    "Agreed, not yet established": "#a8c0de",
    NO_SA: "#e9edef",
}

DOMAIN = list(TIER_COLOURS)
RANGE = [TIER_COLOURS[k] for k in DOMAIN]

# Authorities in the Mayoral tier whose inaugural mayoral election has not
# yet been held. Flagged on the map rather than given a separate colour,
# because the tier is a legal fact and the vacancy is a timing fact.
NO_MAYOR_YET = {"Cheshire & Warrington", "Cumbria",
                "Sussex & Brighton", "Hampshire & the Solent"}

# ---------------------------------------------------------------------------
# Label layout, in British National Grid metres
#   x, y      text anchor
#   align     "right" -> left-hand column, "left" -> right-hand column
# ---------------------------------------------------------------------------

LEFT_X, RIGHT_X = 262_000, 680_000

LABELS = {
    # left column
    "North East":                    (LEFT_X, 600_000, "right"),
    "Cumbria":                       (LEFT_X, 548_000, "right"),
    "Lancashire":                    (LEFT_X, 468_000, "right"),
    "West Yorkshire":                (LEFT_X, 440_000, "right"),
    "Greater Manchester":            (LEFT_X, 412_000, "right"),
    "Liverpool City Region":         (LEFT_X, 384_000, "right"),
    "Cheshire & Warrington":         (LEFT_X, 356_000, "right"),
    "West Midlands":                 (LEFT_X, 290_000, "right"),
    "West of England":               (LEFT_X, 210_000, "right"),
    "Devon & Torbay":                (205_000, 128_000, "right"),
    # right column
    "Tees Valley":                   (RIGHT_X, 545_000, "left"),
    "York & North Yorkshire":        (RIGHT_X, 505_000, "left"),
    "Hull & East Yorkshire":         (RIGHT_X, 465_000, "left"),
    "South Yorkshire":               (RIGHT_X, 425_000, "left"),
    "Greater Lincolnshire":          (RIGHT_X, 385_000, "left"),
    "East Midlands":                 (RIGHT_X, 345_000, "left"),
    "Norfolk & Suffolk":             (RIGHT_X, 290_000, "left"),
    "Cambridgeshire & Peterborough": (RIGHT_X, 250_000, "left"),
    "Greater Essex":                 (RIGHT_X, 205_000, "left"),
    "Greater London":                (RIGHT_X, 160_000, "left"),
    "Sussex & Brighton":             (RIGHT_X, 105_000, "left"),
    # bottom
    "Hampshire & the Solent":        (400_000, 32_000, "center"),
}

LEADER_GAP = 9_000  # metres between text edge and the start of the leader line

# ---------------------------------------------------------------------------
# Projection: explicit scale and translate over a chosen data domain
# ---------------------------------------------------------------------------

DOMAIN_X = (-75_000, 840_000)   # room for both label columns
DOMAIN_Y = (-25_000, 685_000)
WIDTH = 940

SCALE = WIDTH / (DOMAIN_X[1] - DOMAIN_X[0])
HEIGHT = round((DOMAIN_Y[1] - DOMAIN_Y[0]) * SCALE)
TRANSLATE = [-DOMAIN_X[0] * SCALE, DOMAIN_Y[1] * SCALE]  # reflectY flips y

PROJECTION = dict(type="identity", reflectY=True,
                  scale=SCALE, translate=TRANSLATE)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

tiers = pd.read_csv("msa_tiers.csv")
anchors = pd.read_csv("msa_anchors.csv")

england = json.load(open("geo/england.geojson"))
for f in england["features"]:
    f["properties"]["tier_display"] = NO_SA

sa_geo = json.load(open("geo/sa_areas.geojson"))
for f in sa_geo["features"]:
    f["properties"]["tier_display"] = TIER_DISPLAY[f["properties"]["tier"]]

lab = anchors.merge(tiers[["short_name", "official_name", "mayor", "party"]],
                    on="short_name", how="left")
lab["label_x"] = lab.short_name.map(lambda s: LABELS[s][0])
lab["label_y"] = lab.short_name.map(lambda s: LABELS[s][1])
lab["align"] = lab.short_name.map(lambda s: LABELS[s][2])
lab["tier_display"] = lab.tier.map(TIER_DISPLAY)
lab["label"] = lab.short_name + lab.short_name.isin(NO_MAYOR_YET).map({True: "*", False: ""})

# Leader lines start at the edge of the text block, not its anchor point
_dx = {"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0}
_dy = {"right": 0, "left": 0, "center": 13_000}
lab["lx"] = lab.label_x + lab["align"].map(_dx)
lab["ly"] = lab.label_y + lab["align"].map(_dy)

missing = set(tiers.short_name) - set(LABELS)
assert not missing, f"authorities with no label position: {sorted(missing)}"

# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

colour = alt.Color(
    "properties.tier_display:N",
    scale=alt.Scale(domain=DOMAIN, range=RANGE),
    legend=alt.Legend(title="Statutory tier", orient="none",
                      legendX=6, legendY=4, direction="vertical"),
)

base = alt.Chart(alt.Data(values=england["features"],
                          format=alt.DataFormat(type="json")))

england_fill = base.mark_geoshape(
    stroke="#d4dbdf", strokeWidth=0.7
).encode(color=colour)

sa_fill = alt.Chart(
    alt.Data(values=sa_geo["features"], format=alt.DataFormat(type="json"))
).mark_geoshape(
    stroke="white", strokeWidth=1.0
).encode(
    color=colour,
    tooltip=[alt.Tooltip("properties.official_name:N", title="Authority"),
             alt.Tooltip("properties.tier:N", title="Tier"),
             alt.Tooltip("properties.mayor:N", title="Mayor"),
             alt.Tooltip("properties.party:N", title="Party"),
             alt.Tooltip("properties.next_election:N", title="Next election"),
             alt.Tooltip("properties.date_established:N", title="Established"),
             alt.Tooltip("properties.instrument:N", title="Instrument")],
)

leaders = alt.Chart(lab).mark_rule(
    color="#9aa8b2", strokeWidth=0.7
).encode(
    longitude="lx:Q", latitude="ly:Q",
    longitude2="anchor_x:Q", latitude2="anchor_y:Q",
)

dots = alt.Chart(lab).mark_circle(
    size=22, color="#4a5b66", opacity=1
).encode(longitude="anchor_x:Q", latitude="anchor_y:Q")

def label_layer(align):
    """One text layer per alignment: align is a Vega-Lite mark property,
    so it cannot be driven from a data column."""
    return alt.Chart(
        lab[lab["align"] == align]
    ).mark_text(
        font=FONT, fontSize=11.5, color=P["domain"],
        align=align, baseline="middle",
    ).encode(
        longitude="label_x:Q", latitude="label_y:Q", text="label:N",
    )


labels_left = label_layer("right")    # left-hand column, text ends at anchor
labels_right = label_layer("left")    # right-hand column, text starts at anchor
labels_bottom = label_layer("center")

counts = tiers.tier.value_counts()
subtitle = [
    f"{counts['Established Mayoral']} Established Mayoral, {counts['Mayoral']} Mayoral "
    f"and {counts['Foundation']} Foundation authorities, plus "
    f"{counts['Planned']} areas agreed but not yet established.",
    "* Mayoral tier; inaugural mayoral election not yet held.",
    "Sources: English Devolution and Community Empowerment Act 2026; NAO HC 263 (1 July 2026); "
    "Rewiring the State Cabinet Statement (31 July 2026).",
    "Boundaries: ONS 2013 local authority districts dissolved to authority footprints.",
]

chart = (
    alt.layer(england_fill, sa_fill, leaders, dots,
              labels_left, labels_right, labels_bottom)
    .project(**PROJECTION)
    .properties(
        width=WIDTH, height=HEIGHT,
        title=alt.Title(
            "England's Strategic Authorities by statutory tier",
            subtitle=subtitle,
        ),
    )
    .configure_view(stroke=None)
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

spec = chart.to_json()
(OUT / "msa_tiers_map.png").write_bytes(vlc.vegalite_to_png(spec, scale=2.5))
(OUT / "msa_tiers_map.svg").write_text(vlc.vegalite_to_svg(spec))
chart.save(OUT / "msa_tiers_map.html")

# Vega-Lite spec. Geometry and attributes are inlined, so this file is
# self-contained: drop it into vega-embed with no data fetch, and the tooltips
# come with it. Written compact because indenting puts every coordinate on its
# own line and inflates it several times over; run it through `jq .` or
# `python -m json.tool` to read it. Round-tripped through vl-convert as a
# validity check, since an unparseable spec would otherwise only fail in the
# browser.
spec_path = OUT / "msa_tiers_map.vl.json"
spec_path.write_text(json.dumps(chart.to_dict(), separators=(",", ":"),
                                ensure_ascii=False))
vlc.vegalite_to_svg(spec_path.read_text())

# Geometry on its own, for anything that needs the boundaries without the chart
DATA = OUT / "data"
DATA.mkdir(exist_ok=True)
for name in ("england.geojson", "sa_areas.geojson"):
    shutil.copy(Path("geo") / name, DATA / name)

print(f"projection scale {SCALE:.7f}  canvas {WIDTH}x{HEIGHT}")
print(f"labelled authorities: {len(lab)}")
print(f"vega-lite spec: {spec_path.stat().st_size / 1024:.0f} KB, validated")
print("wrote msa_tiers_map.png / .svg / .html / .vl.json + data/*.geojson")
