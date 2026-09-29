"""Round 2 of the legibility exploration (see
productivity_map_contrast_alternatives.py for round 1, which established the
white-halo + navy-stroke technique as the fix for boundary/fill contrast).

This round explores two further, independent questions:

  1. Domain-max exploration (halo + navy boundary held fixed): lower the
     color scale's max below the dataset's true max (200.9) so more LADs
     get clamped into the darkest colour band, i.e. more "very dark" area
     on the map. Renders cap=150 (8 LADs clamped), cap=120 (35 clamped),
     cap=100 (87 clamped) alongside the uncapped baseline for comparison.

  2. Boundary-colour exploration (domain cap held fixed at 120, the
     middle option above): halo technique kept, but the outer stroke
     colour is swapped between navy (baseline), orange, red and gold.

Not wired into the main pipeline - purely a comparison aid.
"""

import json
from pathlib import Path

import altair as alt
import geopandas as gpd
import vl_convert as vlc

import eco_style

OUT = Path("outputs/contrast_alternatives")
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
    alt.themes.register("report_contrast_r2", report_local)
    alt.themes.enable("report_contrast_r2")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_contrast_r2", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Labels (verbatim, filtered to SELECTED)
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

lab = anchors.copy()
lab["label_x"] = lab.short_name.map(lambda s: LABELS[s][0])
lab["label_y"] = lab.short_name.map(lambda s: LABELS[s][1])
lab["align"] = lab.short_name.map(lambda s: LABELS[s][2])
_dx = {"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0}
_dy = {"right": 0, "left": 0, "center": 13_000}
lab["lx"] = lab.label_x + lab["align"].map(_dx)
lab["ly"] = lab.label_y + lab["align"].map(_dy)

HEATMAP_FULL = eco_style.report()["config"]["range"]["heatmap"]
PROD_MIN = float(lads.productivity.min())
PROD_MAX = float(lads.productivity.max())


def leaders_dots_labels(dot_color):
    leaders = alt.Chart(lab).mark_rule(
        color="#9aa8b2", strokeWidth=0.7
    ).encode(
        longitude="lx:Q", latitude="ly:Q",
        longitude2="anchor_x:Q", latitude2="anchor_y:Q",
    )
    dots = alt.Chart(lab).mark_circle(
        size=22, color=dot_color, opacity=1
    ).encode(longitude="anchor_x:Q", latitude="anchor_y:Q")

    def label_layer(align):
        return alt.Chart(
            lab[lab["align"] == align]
        ).mark_text(
            font=FONT, fontSize=11, color=P["domain"],
            align=align, baseline="middle",
        ).encode(longitude="label_x:Q", latitude="label_y:Q", text="short_name:N")

    layers = [leaders, dots]
    for align in ("right", "left", "center"):
        layer = label_layer(align)
        if not layer.data.empty:
            layers.append(layer)
    return layers


def lad_fill_layer(domain_max, legend_title):
    return alt.Chart(lads).mark_geoshape(
        stroke="#ffffff", strokeWidth=0.3
    ).encode(
        color=alt.Color(
            "productivity:Q",
            scale=alt.Scale(range=HEATMAP_FULL, domain=[PROD_MIN, domain_max], clamp=True),
            legend=alt.Legend(title=legend_title),
        ),
        tooltip=[alt.Tooltip("LAD24NM:N", title="Local authority"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )


def sa_outline_halo(stroke_color, stroke_width=1.2):
    base = alt.Chart(
        alt.Data(values=sa_geo_features, format=alt.DataFormat(type="json"))
    )
    tooltip = [alt.Tooltip("properties.official_name:N", title="Strategic authority"),
               alt.Tooltip("properties.mayor:N", title="Mayor")]
    casing = base.mark_geoshape(fill=None, stroke="#ffffff", strokeWidth=stroke_width + 1.8)
    main = base.mark_geoshape(fill=None, stroke=stroke_color, strokeWidth=stroke_width).encode(tooltip=tooltip)
    return [casing, main]


def build_chart(fill_layer, stroke_color):
    layers = [fill_layer, *sa_outline_halo(stroke_color), *leaders_dots_labels(stroke_color)]
    return (
        alt.layer(*layers)
        .project(**PROJECTION)
        .properties(width=WIDTH, height=HEIGHT)
        .configure_view(stroke=None)
    )


def render(name, chart):
    spec = chart.to_json()
    (OUT / f"{name}.png").write_bytes(vlc.vegalite_to_png(spec, scale=2.5))
    print(f"wrote outputs/contrast_alternatives/{name}.png")


# ---------------------------------------------------------------------------
# 1. Domain-max exploration (navy halo boundary held fixed)
# ---------------------------------------------------------------------------

for cap, label in [(PROD_MAX, "E_cap_none"), (150, "F_cap150"), (120, "G_cap120"), (100, "H_cap100")]:
    title = [f"GVA per hour worked,", f"UK=100, 2023 (capped {round(cap)}+)" if cap != PROD_MAX else "UK=100, 2023"]
    fill = lad_fill_layer(cap, title)
    render(label, build_chart(fill, P["domain"]))

# ---------------------------------------------------------------------------
# 2. Boundary-colour exploration (domain capped at 120, the "few more dark
#    places" middle option)
# ---------------------------------------------------------------------------

COLOR_OPTIONS = {
    "I_color_navy":   P["domain"],
    "J_color_orange": P["bar"]["accent_2"],
    "K_color_red":    P["nominal_2"],
    "L_color_gold":   P["nominal_3"],
}
fixed_fill = lad_fill_layer(120, ["GVA per hour worked,", "UK=100, 2023 (capped 120+)"])
for name, color in COLOR_OPTIONS.items():
    render(name, build_chart(fixed_fill, color))
