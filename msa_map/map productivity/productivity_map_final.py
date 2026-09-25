"""Final England productivity maps: LAD labour productivity with selected
Strategic Authorities ("MSAs") outlined and labelled.

Authority set chosen with --msa-set:
  17  (default) the article's 17 selected authorities
  21  every authority except Greater London; outputs carry a "_21msa" suffix
  22  all 22 authorities including Greater London; "_22msa" suffix

Design settled through the legibility rounds in productivity_map_contrast_*.py:
  - colour: YlGnBu, 5 bands (under 80 / 80-90 / 90-100 / 100-120 / 120+, UK=100)
  - boundaries: thin navy line, no halo, no gap (a gap made areas split only by
    a river, e.g. Wirral/Liverpool, read as islands, and doubled shared borders)
  - labels: leader lines, no anchor dots; no title/subtitle/source block

Two versions:
  fullcolor   every LAD coloured
  dimoutside  LADs outside the 17 authorities faded

Pipeline
    build_productivity_geometry.py -> geo/lad_productivity.geojson
    productivity_map_final.py      -> outputs/final/lad_productivity_map_{fullcolor,dimoutside}.{png,svg,html,vl.json}
"""

import argparse
import json
from pathlib import Path

import altair as alt
import geopandas as gpd
import pandas as pd
import vl_convert as vlc

import eco_style

OUT = Path("outputs/final")
OUT.mkdir(parents=True, exist_ok=True)

FONT = "Circular Std"
P = eco_style.pallete

MSA_17 = {
    "West Yorkshire", "Greater Manchester", "Liverpool City Region",
    "West Midlands", "West of England", "North East",
    "York & North Yorkshire", "South Yorkshire", "East Midlands",
    "Cambridgeshire & Peterborough", "Tees Valley", "Hull & East Yorkshire",
    "Cumbria", "Cheshire & Warrington", "Hampshire & the Solent",
    "Sussex & Brighton", "Greater Essex",
}
MSA_21 = MSA_17 | {"Lancashire", "Devon & Torbay", "Greater Lincolnshire", "Norfolk & Suffolk"}
MSA_22 = MSA_21 | {"Greater London"}

# Change this to "21" or "22" when running inside an IDE console (Positron,
# Jupyter, VS Code); from a terminal, use --msa-set instead.
DEFAULT_MSA_SET = "17"

parser = argparse.ArgumentParser()
parser.add_argument("--msa-set", choices=["17", "21", "22"], default=DEFAULT_MSA_SET)
# parse_known_args: IDE kernels pass their own arguments (-f, --logfile, ...),
# which would make parse_args() abort.
args, _ = parser.parse_known_args()
SELECTED = {"17": MSA_17, "21": MSA_21, "22": MSA_22}[args.msa_set]
SET_TAG = "" if args.msa_set == "17" else f"_{args.msa_set}msa"

PALETTE = ["#C7E9B4", "#7FCDBB", "#41B6C4", "#2C7FB8", "#253494"]  # YlGnBu, light -> dark
BREAKS = [80, 90, 100, 120]
LINE_COLOR = P["domain"]
LINE_WIDTH = 1.0
OUTSIDE_OPACITY = 0.35

BAND_LABELS = (
    [f"Under {BREAKS[0]}"]
    + [f"{lo}–{hi}" for lo, hi in zip(BREAKS[:-1], BREAKS[1:])]
    + [f"{BREAKS[-1]} and over"]
)


def report_local():
    spec = eco_style.report()
    cfg = spec["config"]
    cfg["legend"] = {
        "labelFont": FONT, "titleFont": FONT,
        "labelFontSize": 11.5, "titleFontSize": 11.5,
        "titleColor": P["domain"], "labelColor": P["domain"],
        "titleFontWeight": 600, "symbolType": "square", "symbolSize": 180,
        "symbolStrokeWidth": 0, "rowPadding": 4,
    }
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_productivity_final", report_local)
    alt.themes.enable("report_productivity_final")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_productivity_final", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Label layout (British National Grid metres) and projection
# ---------------------------------------------------------------------------

LEFT_X, RIGHT_X = 262_000, 680_000
LABELS = {
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
    "Hampshire & the Solent":        (400_000, 32_000, "center"),
}
LEADER_GAP = 9_000

DOMAIN_X = (-75_000, 840_000)
DOMAIN_Y = (-25_000, 685_000)
WIDTH = 940
SCALE = WIDTH / (DOMAIN_X[1] - DOMAIN_X[0])
HEIGHT = round((DOMAIN_Y[1] - DOMAIN_Y[0]) * SCALE)
TRANSLATE = [-DOMAIN_X[0] * SCALE, DOMAIN_Y[1] * SCALE]
PROJECTION = dict(type="identity", reflectY=True, scale=SCALE, translate=TRANSLATE)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

lads = gpd.read_file("geo/lad_productivity.geojson")[["LAD24CD", "LAD24NM", "productivity", "geometry"]]
lads["geometry"] = lads.geometry.buffer(0)  # a few ONS BGC polygons self-intersect
lads["band"] = pd.cut(lads.productivity, bins=[-1e9, *BREAKS, 1e9], labels=BAND_LABELS, right=False).astype(str)

sa_all = gpd.read_file("geo/sa_areas.geojson")
sa = sa_all[sa_all.short_name.isin(SELECTED)][["short_name", "official_name", "mayor", "geometry"]].copy()
assert set(sa.short_name) == SELECTED, sorted(SELECTED - set(sa.short_name))

# Which LADs fall inside a selected authority (for the faded-outside version)
pts = lads.copy()
pts["geometry"] = lads.geometry.representative_point()
joined = gpd.sjoin(pts, sa[["short_name", "geometry"]], predicate="within", how="left")
lads["focus"] = joined["short_name"].notna().astype(int).values
print(f"LADs inside the {len(SELECTED)} authorities: {lads.focus.sum()}, outside: {(lads.focus == 0).sum()}")


def biggest_part(geom):
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom


lab = sa[["short_name"]].copy()
anchor = sa.geometry.map(biggest_part).representative_point()
lab["anchor_x"] = anchor.x.values
lab["anchor_y"] = anchor.y.values
lab["label_x"] = lab.short_name.map(lambda s: LABELS[s][0])
lab["label_y"] = lab.short_name.map(lambda s: LABELS[s][1])
lab["align"] = lab.short_name.map(lambda s: LABELS[s][2])
lab["lx"] = lab.label_x + lab["align"].map({"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0})
lab["ly"] = lab.label_y + lab["align"].map({"right": 0, "left": 0, "center": 13_000})
lab = pd.DataFrame(lab)

sa_feats = json.loads(sa.to_json())["features"]

# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------


def fill_layer(dim_outside, lad_stroke=0.3, legend_orient="right"):
    enc = dict(
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=BAND_LABELS[::-1], range=PALETTE[::-1]),
            legend=alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"], orient=legend_orient),
        ),
        tooltip=[alt.Tooltip("LAD24NM:N", title="Local authority"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )
    if dim_outside:
        enc["opacity"] = alt.condition("datum.focus == 1", alt.value(1), alt.value(OUTSIDE_OPACITY))
    return alt.Chart(lads).mark_geoshape(stroke="#ffffff", strokeWidth=lad_stroke).encode(**enc)


def outline_layer(width=LINE_WIDTH):
    return alt.Chart(alt.Data(values=sa_feats, format=alt.DataFormat(type="json"))).mark_geoshape(
        fill=None, stroke=LINE_COLOR, strokeWidth=width,
    ).encode(tooltip=[alt.Tooltip("properties.official_name:N", title="Strategic authority"),
                      alt.Tooltip("properties.mayor:N", title="Mayor")])


def label_layers(font_size=11, leader_width=0.7):
    layers = [alt.Chart(lab).mark_rule(color="#9aa8b2", strokeWidth=leader_width).encode(
        longitude="lx:Q", latitude="ly:Q", longitude2="anchor_x:Q", latitude2="anchor_y:Q")]
    for align in ("right", "left", "center"):
        layers.append(alt.Chart(lab[lab["align"] == align]).mark_text(
            font=FONT, fontSize=font_size, color=P["domain"], align=align, baseline="middle",
        ).encode(longitude="label_x:Q", latitude="label_y:Q", text="short_name:N"))
    return layers


def build(dim_outside):
    return (
        alt.layer(fill_layer(dim_outside), outline_layer(), *label_layers())
        .project(**PROJECTION)
        .properties(width=WIDTH, height=HEIGHT)
        .configure_view(stroke=None)
    )


# ---------------------------------------------------------------------------
# Print version: exactly PRINT_W_CM x PRINT_H_CM at PRINT_DPI, for Word.
# Vega-Lite units are points (72 per inch); with padding 0, autosize "none"
# and the legend placed inside the view, the canvas is exactly width x height,
# and vl_convert's ppi both sets the pixel count and tags the PNG's dpi.
# ---------------------------------------------------------------------------

PRINT_W_CM, PRINT_H_CM, PRINT_DPI = 17.5, 15.5, 300
# Round to whole output pixels, plus a hair, because the renderer floors the
# pixel size and float error would otherwise drop the last pixel.
PRINT_W_PT = (round(PRINT_W_CM / 2.54 * PRINT_DPI) + 0.01) * 72 / PRINT_DPI
PRINT_H_PT = (round(PRINT_H_CM / 2.54 * PRINT_DPI) + 0.01) * 72 / PRINT_DPI

# Frame: x runs from west of Cornwall to past the right-hand label column; the
# y extent follows from the page aspect ratio, centred on England.
P_DOMAIN_X = (70_000, 895_000)
P_SCALE = PRINT_W_PT / (P_DOMAIN_X[1] - P_DOMAIN_X[0])
_y_span = PRINT_H_PT / P_SCALE
_y_mid = (5_000 + 658_000) / 2
P_DOMAIN_Y = (_y_mid - _y_span / 2, _y_mid + _y_span / 2)
P_PROJECTION = dict(type="identity", reflectY=True, scale=P_SCALE,
                    translate=[-P_DOMAIN_X[0] * P_SCALE, P_DOMAIN_Y[1] * P_SCALE])

# Line weights scaled with the canvas so the look matches the approved
# screen version; text sized for a printed page (the screen version's 11px
# labels would print at under 6pt at this size).
K = PRINT_W_PT / WIDTH
PRINT_FONT_PT = 7.5


def build_print(dim_outside):
    return (
        alt.layer(
            fill_layer(dim_outside, lad_stroke=0.3 * K, legend_orient="top-right"),
            outline_layer(width=LINE_WIDTH * K),
            *label_layers(font_size=PRINT_FONT_PT, leader_width=0.7 * K),
        )
        .project(**P_PROJECTION)
        .properties(width=PRINT_W_PT, height=PRINT_H_PT, padding=0,
                    autosize=alt.AutoSizeParams(type="none"))
        .configure_view(stroke=None)
        .configure_legend(labelFontSize=PRINT_FONT_PT, titleFontSize=PRINT_FONT_PT,
                          symbolSize=60, rowPadding=2, offset=4)
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

for suffix, dim in [("fullcolor", False), ("dimoutside", True)]:
    chart = build(dim)
    stem = OUT / f"lad_productivity_map_{suffix}{SET_TAG}"
    spec = chart.to_json()
    stem.with_suffix(".png").write_bytes(vlc.vegalite_to_png(spec, scale=2.5))
    stem.with_suffix(".svg").write_text(vlc.vegalite_to_svg(spec))
    chart.save(str(stem.with_suffix(".html")))
    vl_path = stem.with_suffix(".vl.json")
    vl_path.write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
    vlc.vegalite_to_svg(vl_path.read_text())  # validity round-trip
    print(f"wrote {stem}.png / .svg / .html / .vl.json")

    print_path = OUT / f"lad_productivity_map_{suffix}{SET_TAG}_{PRINT_W_CM}x{PRINT_H_CM}cm_{PRINT_DPI}dpi.png"
    print_path.write_bytes(vlc.vegalite_to_png(build_print(dim).to_json(), scale=1, ppi=PRINT_DPI))
    print(f"wrote {print_path}")
