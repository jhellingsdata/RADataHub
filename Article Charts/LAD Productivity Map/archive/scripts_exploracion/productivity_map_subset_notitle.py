"""England labour productivity by Local Authority District, selected
Strategic Authority ("MSA") subset, labeled - no title/subtitle/source text.

Fourth version: identical map to productivity_map_subset.py (same 17
authorities, same labels/leaders/dots/legend), with the title block removed
so only the map and legend are shown.

Pipeline
    build_productivity_geometry.py       -> geo/lad_productivity.geojson
    productivity_map_subset_notitle.py   -> outputs/lad_productivity_map_subset_notitle.{png,svg,html,vl.json}
"""

import json
from pathlib import Path

import altair as alt
import geopandas as gpd
import vl_convert as vlc

import eco_style

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

FONT = "Circular Std"
P = eco_style.pallete

SELECTED = {
    "West Yorkshire",
    "Greater Manchester",
    "Liverpool City Region",
    "West Midlands",
    "West of England",
    "North East",
    "York & North Yorkshire",
    "South Yorkshire",
    "East Midlands",
    "Cambridgeshire & Peterborough",
    "Tees Valley",
    "Hull & East Yorkshire",
    "Cumbria",
    "Cheshire & Warrington",
    "Hampshire & the Solent",
    "Sussex & Brighton",
    "Greater Essex",
}


def report_local():
    spec = eco_style.report()
    cfg = spec["config"]
    cfg["legend"] = {
        "labelFont": FONT, "titleFont": FONT,
        "labelFontSize": 11.5, "titleFontSize": 11.5,
        "titleColor": P["domain"], "labelColor": P["domain"],
        "titleFontWeight": 600, "gradientLength": 140,
    }
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_productivity_subset_notitle", report_local)
    alt.themes.enable("report_productivity_subset_notitle")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_productivity_subset_notitle", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Label layout, in British National Grid metres (verbatim from msa_map.py,
# filtered to SELECTED)
# ---------------------------------------------------------------------------

LEFT_X, RIGHT_X = 262_000, 680_000

ALL_LABELS = {
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
LABELS = {k: v for k, v in ALL_LABELS.items() if k in SELECTED}

LEADER_GAP = 9_000

# ---------------------------------------------------------------------------
# Projection: identity + explicit BNG scale/translate (same domain as the
# other subset version, so all charts stay pixel-comparable)
# ---------------------------------------------------------------------------

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

lads = gpd.read_file("geo/lad_productivity.geojson")
sa_gdf_full = gpd.read_file("geo/sa_areas.geojson")
sa_gdf = sa_gdf_full[sa_gdf_full.short_name.isin(SELECTED)].copy()

missing = SELECTED - set(sa_gdf_full.short_name)
assert not missing, f"requested authorities not found in sa_areas.geojson: {sorted(missing)}"

sa_geo_features = json.loads(sa_gdf.to_json())["features"]


def biggest_part(geom):
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom


anchors = sa_gdf.copy()
anchors["geometry"] = anchors.geometry.map(biggest_part).representative_point()
anchors["anchor_x"] = anchors.geometry.x
anchors["anchor_y"] = anchors.geometry.y
anchors = anchors[["short_name", "official_name", "anchor_x", "anchor_y"]]

missing_labels = set(anchors.short_name) - set(LABELS)
assert not missing_labels, f"selected authorities with no label position: {sorted(missing_labels)}"

lab = anchors.copy()
lab["label_x"] = lab.short_name.map(lambda s: LABELS[s][0])
lab["label_y"] = lab.short_name.map(lambda s: LABELS[s][1])
lab["align"] = lab.short_name.map(lambda s: LABELS[s][2])

_dx = {"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0}
_dy = {"right": 0, "left": 0, "center": 13_000}
lab["lx"] = lab.label_x + lab["align"].map(_dx)
lab["ly"] = lab.label_y + lab["align"].map(_dy)

# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

heatmap_range = eco_style.report()["config"]["range"]["heatmap"]

lad_fill = alt.Chart(lads).mark_geoshape(
    stroke="#ffffff", strokeWidth=0.3
).encode(
    color=alt.Color(
        "productivity:Q",
        scale=alt.Scale(range=heatmap_range),
        legend=alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"]),
    ),
    tooltip=[alt.Tooltip("LAD24NM:N", title="Local authority"),
             alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
)

sa_outline = alt.Chart(
    alt.Data(values=sa_geo_features, format=alt.DataFormat(type="json"))
).mark_geoshape(
    fill=None, stroke=P["domain"], strokeWidth=1.3
).encode(
    tooltip=[alt.Tooltip("properties.official_name:N", title="Strategic authority"),
             alt.Tooltip("properties.mayor:N", title="Mayor")],
)

leaders = alt.Chart(lab).mark_rule(
    color="#9aa8b2", strokeWidth=0.7
).encode(
    longitude="lx:Q", latitude="ly:Q",
    longitude2="anchor_x:Q", latitude2="anchor_y:Q",
)

dots = alt.Chart(lab).mark_circle(
    size=22, color=P["domain"], opacity=1
).encode(longitude="anchor_x:Q", latitude="anchor_y:Q")


def label_layer(align):
    return alt.Chart(
        lab[lab["align"] == align]
    ).mark_text(
        font=FONT, fontSize=11, color=P["domain"],
        align=align, baseline="middle",
    ).encode(
        longitude="label_x:Q", latitude="label_y:Q", text="short_name:N",
    )


labels_left = label_layer("right")
labels_right = label_layer("left")
labels_bottom = label_layer("center")

layers = [lad_fill, sa_outline, leaders, dots]
if not labels_left.data.empty:
    layers.append(labels_left)
if not labels_right.data.empty:
    layers.append(labels_right)
if not labels_bottom.data.empty:
    layers.append(labels_bottom)

chart = (
    alt.layer(*layers)
    .project(**PROJECTION)
    .properties(width=WIDTH, height=HEIGHT)
    .configure_view(stroke=None)
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

spec = chart.to_json()
(OUT / "lad_productivity_map_subset_notitle.png").write_bytes(vlc.vegalite_to_png(spec, scale=2.5))
(OUT / "lad_productivity_map_subset_notitle.svg").write_text(vlc.vegalite_to_svg(spec))
chart.save(OUT / "lad_productivity_map_subset_notitle.html")

spec_path = OUT / "lad_productivity_map_subset_notitle.vl.json"
spec_path.write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
vlc.vegalite_to_svg(spec_path.read_text())  # validity round-trip

print(f"selected authorities: {len(sa_gdf)} / {len(sa_gdf_full)}")
print(f"labelled: {len(lab)}")
print(f"vega-lite spec: {spec_path.stat().st_size / 1024:.0f} KB, validated")
print("wrote outputs/lad_productivity_map_subset_notitle.png / .svg / .html / .vl.json")
