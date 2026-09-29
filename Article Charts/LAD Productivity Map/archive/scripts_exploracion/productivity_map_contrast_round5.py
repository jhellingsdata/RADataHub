"""Round 5 of the legibility exploration, built on the user's preferred
round-4 layout (V_gutter_fullcolor_bins): every LAD coloured, the 17 selected
Strategic Authorities ringed by a white gutter + navy halo outline, banded
(threshold) colour scale.

Varies palette and band breaks. Every palette's lightest band is kept
visibly tinted so it never reads as the white gutter/background (the flaw in
round-4 V). Legend switched to square swatches with range labels.

Outputs go to outputs/contrast_alternatives/round5/, plus a contact sheet
comparing all variants side by side.
"""

import argparse
import json
from pathlib import Path

import altair as alt
import geopandas as gpd
import pandas as pd
import vl_convert as vlc
from PIL import Image, ImageDraw, ImageFont

import eco_style

parser = argparse.ArgumentParser()
parser.add_argument("--gutter", type=int, default=1_800, help="inward shrink per authority, metres")
parser.add_argument("--only", nargs="*", help="render only these variant names")
parser.add_argument("--tag", default="", help="suffix appended to output filenames")
parser.add_argument("--no-sheet", action="store_true", help="skip the contact sheet")
args = parser.parse_args()

OUT = Path("outputs/contrast_alternatives/round5")
OUT.mkdir(parents=True, exist_ok=True)

FONT = "Circular Std"
P = eco_style.pallete
GUTTER_M = args.gutter

SELECTED = {
    "West Yorkshire", "Greater Manchester", "Liverpool City Region",
    "West Midlands", "West of England", "North East",
    "York & North Yorkshire", "South Yorkshire", "East Midlands",
    "Cambridgeshire & Peterborough", "Tees Valley", "Hull & East Yorkshire",
    "Cumbria", "Cheshire & Warrington", "Hampshire & the Solent",
    "Sussex & Brighton", "Greater Essex",
}

# ---------------------------------------------------------------------------
# Palettes (light -> dark) and band breaks
# ---------------------------------------------------------------------------

PALETTES = {
    "blue5":   ["#C6E0F2", "#8CC8EC", "#179FDB", "#0063AF", "#122B39"],
    "teal5":   ["#C4EAE8", "#7FD1CD", P["nominal_6"], "#1F7F7C", "#0F4C4A"],
    "orange5": ["#FAD3BA", "#F2A876", P["bar"]["accent_2"], "#B23E18", "#6E2410"],
    "ylgnbu5": ["#C7E9B4", "#7FCDBB", "#41B6C4", "#2C7FB8", "#253494"],
    "teal6":   ["#C4EAE8", "#94DAD6", "#5FC6C2", P["nominal_6"], "#1F7F7C", "#0F4C4A"],
    # below UK average in reds, around average neutral, above in blues
    "redblue5": [P["nominal_2"], "#F29AAB", "#D6D4D4", "#7CC3E9", "#0063AF"],
}

BREAKS = {
    "fixed":     [80, 90, 100, 120],           # round-4 V
    "quintile":  [80, 86, 95, 108],            # ~59 LADs per band
    "six":       [75, 85, 95, 105, 120],
    "ukcentred": [80, 95, 105, 120],           # 95-105 = roughly UK average
}

VARIANTS = [
    # name,                   palette,    breaks
    ("01_blue_fixed",         "blue5",    "fixed"),
    ("02_teal_fixed",         "teal5",    "fixed"),
    ("03_orange_fixed",       "orange5",  "fixed"),
    ("04_ylgnbu_fixed",       "ylgnbu5",  "fixed"),
    ("05_blue_quintile",      "blue5",    "quintile"),
    ("06_teal_quintile",      "teal5",    "quintile"),
    ("07_teal_six",           "teal6",    "six"),
    ("08_redblue_ukcentred",  "redblue5", "ukcentred"),
]


def band_labels(breaks):
    labels = [f"Under {breaks[0]}"]
    labels += [f"{lo}–{hi}" for lo, hi in zip(breaks[:-1], breaks[1:])]
    labels.append(f"{breaks[-1]} and over")
    return labels


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
    alt.themes.register("report_contrast_r5", report_local)
    alt.themes.enable("report_contrast_r5")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_contrast_r5", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Labels / projection (same layout as the other subset maps)
# ---------------------------------------------------------------------------

LEFT_X, RIGHT_X = 262_000, 680_000
ALL_LABELS = {
    "North East":                    (LEFT_X, 600_000, "right"),
    "Cumbria":                       (LEFT_X, 548_000, "right"),
    "West Yorkshire":                (LEFT_X, 440_000, "right"),
    "Greater Manchester":            (LEFT_X, 412_000, "right"),
    "Liverpool City Region":         (LEFT_X, 384_000, "right"),
    "Cheshire & Warrington":         (LEFT_X, 356_000, "right"),
    "West Midlands":                 (LEFT_X, 290_000, "right"),
    "West of England":               (LEFT_X, 210_000, "right"),
    "Tees Valley":                   (RIGHT_X, 545_000, "left"),
    "York & North Yorkshire":        (RIGHT_X, 505_000, "left"),
    "Hull & East Yorkshire":         (RIGHT_X, 465_000, "left"),
    "South Yorkshire":               (RIGHT_X, 425_000, "left"),
    "East Midlands":                 (RIGHT_X, 345_000, "left"),
    "Cambridgeshire & Peterborough": (RIGHT_X, 250_000, "left"),
    "Greater Essex":                 (RIGHT_X, 205_000, "left"),
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
# Geometry: assign LADs to authorities, shrink authorities, clip their LADs
# ---------------------------------------------------------------------------

lads = gpd.read_file("geo/lad_productivity.geojson")[["LAD24CD", "LAD24NM", "productivity", "geometry"]]
lads["geometry"] = lads.geometry.buffer(0)  # a few ONS BGC polygons self-intersect
sa_all = gpd.read_file("geo/sa_areas.geojson")
sa = sa_all[sa_all.short_name.isin(SELECTED)][["short_name", "official_name", "mayor", "geometry"]].copy()
assert set(sa.short_name) == SELECTED

pts = lads.copy()
pts["geometry"] = lads.geometry.representative_point()
joined = gpd.sjoin(pts, sa[["short_name", "geometry"]], predicate="within", how="left")
lads["short_name"] = joined["short_name"].values

sa_g = sa.copy()
sa_g["geometry"] = sa.geometry.buffer(-GUTTER_M)
shrunk = sa_g.set_index("short_name").geometry

inside = lads[lads.short_name.notna()].copy()
inside["geometry"] = [g.intersection(shrunk[n]) for g, n in zip(inside.geometry, inside.short_name)]
inside = inside[~inside.geometry.is_empty]
outside = lads[lads.short_name.isna()]
full = gpd.GeoDataFrame(pd.concat([outside, inside], ignore_index=True), geometry="geometry", crs=lads.crs)


def biggest_part(geom):
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom


lab = sa_g[["short_name"]].copy()
anchor = sa_g.geometry.map(biggest_part).representative_point()
lab["anchor_x"] = anchor.x.values
lab["anchor_y"] = anchor.y.values
lab["label_x"] = lab.short_name.map(lambda s: ALL_LABELS[s][0])
lab["label_y"] = lab.short_name.map(lambda s: ALL_LABELS[s][1])
lab["align"] = lab.short_name.map(lambda s: ALL_LABELS[s][2])
lab["lx"] = lab.label_x + lab["align"].map({"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0})
lab["ly"] = lab.label_y + lab["align"].map({"right": 0, "left": 0, "center": 13_000})
lab = pd.DataFrame(lab)

sa_feats = json.loads(sa_g.to_json())["features"]

# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------


def fill_layer(palette, breaks):
    labels = band_labels(breaks)
    # Band label as its own field so the legend shows readable ranges in order.
    data = full.copy()
    data["band"] = pd.cut(data.productivity, bins=[-1e9, *breaks, 1e9], labels=labels, right=False).astype(str)
    return alt.Chart(data).mark_geoshape(stroke="#ffffff", strokeWidth=0.3).encode(
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=labels[::-1], range=palette[::-1]),
            legend=alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"]),
        ),
        tooltip=[alt.Tooltip("LAD24NM:N", title="Local authority"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )


def outline_layers():
    base = alt.Chart(alt.Data(values=sa_feats, format=alt.DataFormat(type="json")))
    casing = base.mark_geoshape(fill=None, stroke="#ffffff", strokeWidth=3.0)
    main = base.mark_geoshape(fill=None, stroke=P["domain"], strokeWidth=1.2).encode(
        tooltip=[alt.Tooltip("properties.official_name:N", title="Strategic authority"),
                 alt.Tooltip("properties.mayor:N", title="Mayor")])
    return [casing, main]


def label_layers():
    layers = [
        alt.Chart(lab).mark_rule(color="#9aa8b2", strokeWidth=0.7).encode(
            longitude="lx:Q", latitude="ly:Q", longitude2="anchor_x:Q", latitude2="anchor_y:Q"),
        alt.Chart(lab).mark_circle(size=22, color=P["domain"], opacity=1).encode(
            longitude="anchor_x:Q", latitude="anchor_y:Q"),
    ]
    for align in ("right", "left", "center"):
        sub = lab[lab["align"] == align]
        layers.append(alt.Chart(sub).mark_text(
            font=FONT, fontSize=11, color=P["domain"], align=align, baseline="middle",
        ).encode(longitude="label_x:Q", latitude="label_y:Q", text="short_name:N"))
    return layers


written = []
for name, pal_key, brk_key in VARIANTS:
    if args.only and name not in args.only:
        continue
    name = f"{name}{args.tag}"
    palette, breaks = PALETTES[pal_key], BREAKS[brk_key]
    assert len(palette) == len(breaks) + 1, name
    chart = (
        alt.layer(fill_layer(palette, breaks), *outline_layers(), *label_layers())
        .project(**PROJECTION)
        .properties(width=WIDTH, height=HEIGHT)
        .configure_view(stroke=None)
    )
    path = OUT / f"{name}.png"
    path.write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    written.append((name, path))
    print(f"wrote {path}")

# ---------------------------------------------------------------------------
# Contact sheet: all variants side by side, 2 columns
# ---------------------------------------------------------------------------

if args.no_sheet:
    raise SystemExit

THUMB_W = 1100
thumbs = []
for name, path in written:
    im = Image.open(path).convert("RGB")
    im = im.resize((THUMB_W, round(im.height * THUMB_W / im.width)))
    thumbs.append((name, im))

cell_h = max(im.height for _, im in thumbs) + 60
cols = 2
rows = -(-len(thumbs) // cols)
sheet = Image.new("RGB", (cols * THUMB_W, rows * cell_h), "white")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.load_default(size=36)
except TypeError:
    font = ImageFont.load_default()
for i, (name, im) in enumerate(thumbs):
    x, y = (i % cols) * THUMB_W, (i // cols) * cell_h
    draw.text((x + 20, y + 10), name, fill=P["domain"], font=font)
    sheet.paste(im, (x, y + 60))
sheet.save(OUT / "00_contact_sheet.png")
print(f"wrote {OUT / '00_contact_sheet.png'}")
