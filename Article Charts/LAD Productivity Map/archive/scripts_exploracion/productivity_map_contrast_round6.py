"""Round 6: boundary styling for the highlighted Strategic Authorities.

Palette/bands fixed to the user's pick from round 5 (04_ylgnbu_fixed).
The round-4/5 white gutter is dropped by default: a wide gap made areas
separated only by a river (e.g. Wirral/Liverpool across the Mersey,
Warrington) read as islands. Instead the boundary itself carries the
emphasis:

  A_halo_navy        navy line + white halo, no gap
  B_thick_navy       heavier navy line, no halo, no gap
  C_halo_magenta     magenta line (outside the YlGnBu hue range) + halo
  D_halo_orange      orange line + halo
  E_inner_band       translucent navy band just inside each authority edge
  F_dim_outside      LADs outside the 17 authorities faded, navy halo line
  G_gap400_navy      tiny 0.4 km gutter + navy halo (reference)

Outputs: outputs/contrast_alternatives/round6/ plus a contact sheet.
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

OUT = Path("outputs/contrast_alternatives/round6")
OUT.mkdir(parents=True, exist_ok=True)

FONT = "Circular Std"
P = eco_style.pallete

SELECTED = {
    "West Yorkshire", "Greater Manchester", "Liverpool City Region",
    "West Midlands", "West of England", "North East",
    "York & North Yorkshire", "South Yorkshire", "East Midlands",
    "Cambridgeshire & Peterborough", "Tees Valley", "Hull & East Yorkshire",
    "Cumbria", "Cheshire & Warrington", "Hampshire & the Solent",
    "Sussex & Brighton", "Greater Essex",
}

PALETTE = ["#C7E9B4", "#7FCDBB", "#41B6C4", "#2C7FB8", "#253494"]   # 04_ylgnbu
BREAKS = [80, 90, 100, 120]
INNER_BAND_M = 2_500
OUTSIDE_OPACITY = 0.35

VARIANTS = {
    #  name                        gutter_m  stroke                 width  halo   extra          dot
    "A_halo_navy":               (0,   P["domain"],            1.4,   True,  None,          True),
    "B_thick_navy":              (0,   P["domain"],            2.2,   False, None,          True),
    "C_halo_magenta":            (0,   P["nominal_2"],         1.6,   True,  None,          True),
    "D_halo_orange":             (0,   P["bar"]["accent_2"],   1.6,   True,  None,          True),
    "E_inner_band":              (0,   P["domain"],            1.0,   False, "inner_band",  True),
    "F_dim_outside":             (0,   P["domain"],            1.4,   True,  "dim_outside", True),
    "G_gap400_navy":             (400, P["domain"],            1.4,   True,  None,          True),
    "F2_dim_outside_nohalo_nodot": (0,   P["domain"],          1.4,   False, "dim_outside", False),
    "G2_gap400_nohalo_nodot":      (400, P["domain"],          1.4,   False, None,          False),
    "G3_gap400_nohalo_nodot_thin": (400, P["domain"],          1.0,   False, None,          False),
    # "outline_original": fills shrunk for the gap, but the line is drawn on the
    # original (unshrunk) boundary, so neighbours' lines overlap into one instead
    # of two parallel lines that merge into a heavy dark border.
    "I1_nogap_thin":               (0,   P["domain"],          1.0,   False, None,               False),
    "I2_gap400_line_on_border":    (400, P["domain"],          1.0,   False, "outline_original", False),
}


def band_labels(breaks):
    labels = [f"Under {breaks[0]}"]
    labels += [f"{lo}–{hi}" for lo, hi in zip(breaks[:-1], breaks[1:])]
    labels.append(f"{breaks[-1]} and over")
    return labels


LABELS_TXT = band_labels(BREAKS)


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
    alt.themes.register("report_contrast_r6", report_local)
    alt.themes.enable("report_contrast_r6")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_contrast_r6", enable=True)(report_local)

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
# Data
# ---------------------------------------------------------------------------

lads = gpd.read_file("geo/lad_productivity.geojson")[["LAD24CD", "LAD24NM", "productivity", "geometry"]]
lads["geometry"] = lads.geometry.buffer(0)  # a few ONS BGC polygons self-intersect
lads["band"] = pd.cut(lads.productivity, bins=[-1e9, *BREAKS, 1e9], labels=LABELS_TXT, right=False).astype(str)

sa_all = gpd.read_file("geo/sa_areas.geojson")
sa = sa_all[sa_all.short_name.isin(SELECTED)][["short_name", "official_name", "mayor", "geometry"]].copy()
assert set(sa.short_name) == SELECTED

pts = lads.copy()
pts["geometry"] = lads.geometry.representative_point()
joined = gpd.sjoin(pts, sa[["short_name", "geometry"]], predicate="within", how="left")
lads["short_name"] = joined["short_name"].values
lads["focus"] = lads.short_name.notna().astype(int)


def geometry_for_gutter(gutter_m, base=None):
    """Return (authority outlines, LAD fill layer data) for a given gutter."""
    base = sa if base is None else base
    if gutter_m == 0:
        return base, lads
    sa_g = base.copy()
    sa_g["geometry"] = base.geometry.buffer(-gutter_m)
    shrunk = sa_g.set_index("short_name").geometry
    inside = lads[lads.focus == 1].copy()
    inside["geometry"] = [g.intersection(shrunk[n]) for g, n in zip(inside.geometry, inside.short_name)]
    inside = inside[~inside.geometry.is_empty]
    full = pd.concat([lads[lads.focus == 0], inside], ignore_index=True)
    return sa_g, gpd.GeoDataFrame(full, geometry="geometry", crs=lads.crs)


def biggest_part(geom):
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom


def label_table(sa_gdf):
    lab = sa_gdf[["short_name"]].copy()
    anchor = sa_gdf.geometry.map(biggest_part).representative_point()
    lab["anchor_x"] = anchor.x.values
    lab["anchor_y"] = anchor.y.values
    lab["label_x"] = lab.short_name.map(lambda s: ALL_LABELS[s][0])
    lab["label_y"] = lab.short_name.map(lambda s: ALL_LABELS[s][1])
    lab["align"] = lab.short_name.map(lambda s: ALL_LABELS[s][2])
    lab["lx"] = lab.label_x + lab["align"].map({"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0})
    lab["ly"] = lab.label_y + lab["align"].map({"right": 0, "left": 0, "center": 13_000})
    return pd.DataFrame(lab)


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------


def fill_layer(data, dim_outside):
    enc = dict(
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=LABELS_TXT[::-1], range=PALETTE[::-1]),
            legend=alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"]),
        ),
        tooltip=[alt.Tooltip("LAD24NM:N", title="Local authority"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )
    if dim_outside:
        enc["opacity"] = alt.condition("datum.focus == 1", alt.value(1), alt.value(OUTSIDE_OPACITY))
    return alt.Chart(data).mark_geoshape(stroke="#ffffff", strokeWidth=0.3).encode(**enc)


def inner_band_layer(sa_gdf):
    band = sa_gdf.copy()
    band["geometry"] = sa_gdf.geometry.difference(sa_gdf.geometry.buffer(-INNER_BAND_M))
    feats = json.loads(band[["short_name", "geometry"]].to_json())["features"]
    return alt.Chart(alt.Data(values=feats, format=alt.DataFormat(type="json"))).mark_geoshape(
        fill=P["domain"], fillOpacity=0.45, stroke=None)


def outline_layers(sa_gdf, stroke, width, halo):
    feats = json.loads(sa_gdf[["short_name", "official_name", "mayor", "geometry"]].to_json())["features"]
    base = alt.Chart(alt.Data(values=feats, format=alt.DataFormat(type="json")))
    main = base.mark_geoshape(fill=None, stroke=stroke, strokeWidth=width).encode(
        tooltip=[alt.Tooltip("properties.official_name:N", title="Strategic authority"),
                 alt.Tooltip("properties.mayor:N", title="Mayor")])
    if not halo:
        return [main]
    casing = base.mark_geoshape(fill=None, stroke="#ffffff", strokeWidth=width + 1.8)
    return [casing, main]


def label_layers(lab, dot_color, show_dot=True):
    layers = [
        alt.Chart(lab).mark_rule(color="#9aa8b2", strokeWidth=0.7).encode(
            longitude="lx:Q", latitude="ly:Q", longitude2="anchor_x:Q", latitude2="anchor_y:Q"),
    ]
    if show_dot:
        layers.append(alt.Chart(lab).mark_circle(size=22, color=dot_color, opacity=1).encode(
            longitude="anchor_x:Q", latitude="anchor_y:Q"))
    for align in ("right", "left", "center"):
        sub = lab[lab["align"] == align]
        layers.append(alt.Chart(sub).mark_text(
            font=FONT, fontSize=11, color=P["domain"], align=align, baseline="middle",
        ).encode(longitude="label_x:Q", latitude="label_y:Q", text="short_name:N"))
    return layers


parser = argparse.ArgumentParser()
parser.add_argument("--only", nargs="*", help="render only these variant names")
parser.add_argument("--sheet", default="00_contact_sheet", help="contact sheet filename stem")
args = parser.parse_args()

written = []
for name, (gutter_m, stroke, width, halo, extra, dot) in VARIANTS.items():
    if args.only and name not in args.only:
        continue
    sa_draw, fill_data = geometry_for_gutter(gutter_m)
    layers = [fill_layer(fill_data, dim_outside=(extra == "dim_outside"))]
    if extra == "inner_band":
        layers.append(inner_band_layer(sa_draw))
    outline_geom = sa if extra == "outline_original" else sa_draw
    layers += outline_layers(outline_geom, stroke, width, halo)
    layers += label_layers(label_table(sa_draw), stroke, show_dot=dot)
    chart = (
        alt.layer(*layers)
        .project(**PROJECTION)
        .properties(width=WIDTH, height=HEIGHT)
        .configure_view(stroke=None)
    )
    path = OUT / f"{name}.png"
    path.write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    written.append((name, path))
    print(f"wrote {path}")

# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------

THUMB_W = 1100
thumbs = []
for name, path in written:
    im = Image.open(path).convert("RGB")
    thumbs.append((name, im.resize((THUMB_W, round(im.height * THUMB_W / im.width)))))

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
sheet.save(OUT / f"{args.sheet}.png")
print(f"wrote {OUT / f'{args.sheet}.png'}")
