"""Round 4 of the legibility exploration: structural fixes rather than colour
tweaks. The 17 selected Strategic Authorities get emphasis by separating them
from the rest of the LAD mosaic.

  Q_focus               LADs outside the selected authorities drawn in flat
                        light grey; only LADs inside carry the colour scale
  R_focus_gutter        + each authority shrunk inward (GUTTER_M) and its LADs
                        clipped to it, leaving a white gap between neighbours
  S_focus_gutter_bins   + banded (threshold) colour scale instead of continuous
  T_exploded            authorities pushed outward from England's centre over
                        a grey silhouette of the whole country
  U_gutter_fullcolor    R's gutter, but every LAD keeps its colour (no grey
                        context), house heatmap range
  V_gutter_fullcolor_bins  U with the banded scale

Blue house palette, domain capped at 120, navy + white-halo outline throughout.
Not wired into the main pipeline - purely a comparison aid.
"""

import json
from pathlib import Path

import altair as alt
import geopandas as gpd
import pandas as pd
import vl_convert as vlc
from shapely.affinity import translate

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

GUTTER_M = 1_800          # inward shrink per authority, metres
EXPLODE_K = 0.10          # outward push as a share of distance from centre
OUTSIDE_GREY = "#e6e6e6"
DOMAIN_CAP = 120

# Light-blue start instead of the heatmap's grey, so low-productivity LADs
# inside an authority can't be mistaken for the grey "outside" context.
CONT_RANGE = ["#DCEAF5", "#179FDB", "#0063AF", "#122B39"]
BIN_EDGES = [80, 90, 100, 120]
BIN_RANGE = ["#DCEAF5", "#8CC8EC", "#179FDB", "#0063AF", "#122B39"]


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
    alt.themes.register("report_contrast_r4", report_local)
    alt.themes.enable("report_contrast_r4")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_contrast_r4", enable=True)(report_local)

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
# Data: assign each LAD to a selected authority (or none)
# ---------------------------------------------------------------------------

lads = gpd.read_file("geo/lad_productivity.geojson")[["LAD24CD", "LAD24NM", "productivity", "geometry"]]
lads["geometry"] = lads.geometry.buffer(0)  # a few ONS BGC polygons self-intersect; clipping needs valid input
sa_all = gpd.read_file("geo/sa_areas.geojson")
sa = sa_all[sa_all.short_name.isin(SELECTED)][["short_name", "official_name", "mayor", "geometry"]].copy()
assert set(sa.short_name) == SELECTED

pts = lads.copy()
pts["geometry"] = lads.geometry.representative_point()
joined = gpd.sjoin(pts, sa[["short_name", "geometry"]], predicate="within", how="left")
lads["short_name"] = joined["short_name"].values

inside = lads[lads.short_name.notna()].copy()
outside = lads[lads.short_name.isna()].copy()
print(f"LADs inside selected authorities: {len(inside)}, outside: {len(outside)}")
print(inside.groupby("short_name").size().to_string())

PROD_MIN = float(inside.productivity.min())

# ---------------------------------------------------------------------------
# Geometry variants
# ---------------------------------------------------------------------------


def with_gutter(sa_gdf, inside_gdf):
    shrunk = sa_gdf.copy()
    shrunk["geometry"] = sa_gdf.geometry.buffer(-GUTTER_M)
    lookup = shrunk.set_index("short_name").geometry
    clipped = inside_gdf.copy()
    clipped["geometry"] = [
        geom.intersection(lookup[name]) for geom, name in zip(clipped.geometry, clipped.short_name)
    ]
    clipped = clipped[~clipped.geometry.is_empty]
    return shrunk, clipped


def exploded(sa_gdf, inside_gdf):
    centre = lads.geometry.union_all().centroid
    offsets = {}
    for name, geom in zip(sa_gdf.short_name, sa_gdf.geometry):
        c = geom.centroid
        offsets[name] = ((c.x - centre.x) * EXPLODE_K, (c.y - centre.y) * EXPLODE_K)
    moved_sa = sa_gdf.copy()
    moved_sa["geometry"] = [translate(g, *offsets[n]) for g, n in zip(sa_gdf.geometry, sa_gdf.short_name)]
    moved_in = inside_gdf.copy()
    moved_in["geometry"] = [translate(g, *offsets[n]) for g, n in zip(inside_gdf.geometry, inside_gdf.short_name)]
    return moved_sa, moved_in


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------


def color_encoding(binned, cont_range=CONT_RANGE, domain_min=None):
    if binned:
        scale = alt.Scale(type="threshold", domain=BIN_EDGES, range=BIN_RANGE)
        legend = alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"])
    else:
        lo = PROD_MIN if domain_min is None else domain_min
        scale = alt.Scale(range=cont_range, domain=[lo, DOMAIN_CAP], clamp=True)
        legend = alt.Legend(title=["GVA per hour worked,", "UK=100, 2023 (capped 120+)"])
    return alt.Color("productivity:Q", scale=scale, legend=legend)


def fill_layer(gdf, binned, stroke_width=0.3, cont_range=CONT_RANGE, domain_min=None):
    return alt.Chart(gdf).mark_geoshape(stroke="#ffffff", strokeWidth=stroke_width).encode(
        color=color_encoding(binned, cont_range, domain_min),
        tooltip=[alt.Tooltip("LAD24NM:N", title="Local authority"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )


def context_layer(gdf):
    return alt.Chart(gdf).mark_geoshape(fill=OUTSIDE_GREY, stroke="#ffffff", strokeWidth=0.3)


def outline_layers(sa_gdf, stroke_width=1.2):
    feats = json.loads(sa_gdf[["short_name", "official_name", "mayor", "geometry"]].to_json())["features"]
    base = alt.Chart(alt.Data(values=feats, format=alt.DataFormat(type="json")))
    casing = base.mark_geoshape(fill=None, stroke="#ffffff", strokeWidth=stroke_width + 1.8)
    main = base.mark_geoshape(fill=None, stroke=P["domain"], strokeWidth=stroke_width).encode(
        tooltip=[alt.Tooltip("properties.official_name:N", title="Strategic authority"),
                 alt.Tooltip("properties.mayor:N", title="Mayor")])
    return [casing, main]


def biggest_part(geom):
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom


def label_layers(sa_gdf):
    lab = sa_gdf[["short_name"]].copy()
    anchor = sa_gdf.geometry.map(biggest_part).representative_point()
    lab["anchor_x"] = anchor.x.values
    lab["anchor_y"] = anchor.y.values
    lab["label_x"] = lab.short_name.map(lambda s: ALL_LABELS[s][0])
    lab["label_y"] = lab.short_name.map(lambda s: ALL_LABELS[s][1])
    lab["align"] = lab.short_name.map(lambda s: ALL_LABELS[s][2])
    dx = {"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0}
    dy = {"right": 0, "left": 0, "center": 13_000}
    lab["lx"] = lab.label_x + lab["align"].map(dx)
    lab["ly"] = lab.label_y + lab["align"].map(dy)
    lab = pd.DataFrame(lab)

    layers = [
        alt.Chart(lab).mark_rule(color="#9aa8b2", strokeWidth=0.7).encode(
            longitude="lx:Q", latitude="ly:Q", longitude2="anchor_x:Q", latitude2="anchor_y:Q"),
        alt.Chart(lab).mark_circle(size=22, color=P["domain"], opacity=1).encode(
            longitude="anchor_x:Q", latitude="anchor_y:Q"),
    ]
    for align in ("right", "left", "center"):
        sub = lab[lab["align"] == align]
        if not sub.empty:
            layers.append(alt.Chart(sub).mark_text(
                font=FONT, fontSize=11, color=P["domain"], align=align, baseline="middle",
            ).encode(longitude="label_x:Q", latitude="label_y:Q", text="short_name:N"))
    return layers


def render(name, layers):
    chart = (
        alt.layer(*layers)
        .project(**PROJECTION)
        .properties(width=WIDTH, height=HEIGHT)
        .configure_view(stroke=None)
    )
    (OUT / f"{name}.png").write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    print(f"wrote outputs/contrast_alternatives/{name}.png")


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------

render("Q_focus", [
    context_layer(outside), fill_layer(inside, binned=False),
    *outline_layers(sa), *label_layers(sa),
])

sa_g, inside_g = with_gutter(sa, inside)
render("R_focus_gutter", [
    context_layer(outside), fill_layer(inside_g, binned=False),
    *outline_layers(sa_g), *label_layers(sa_g),
])

render("S_focus_gutter_bins", [
    context_layer(outside), fill_layer(inside_g, binned=True),
    *outline_layers(sa_g), *label_layers(sa_g),
])

sa_x, inside_x = exploded(sa_g, inside_g)
render("T_exploded", [
    context_layer(lads), fill_layer(inside_x, binned=True),
    *outline_layers(sa_x), *label_layers(sa_x),
])

# Full-colour gutter: outside LADs keep their data colour; only the selected
# authorities are shrunk, so each is ringed by a white gap.
full = pd.concat([outside, inside_g], ignore_index=True)
full = gpd.GeoDataFrame(full, geometry="geometry", crs=lads.crs)
HEATMAP = eco_style.report()["config"]["range"]["heatmap"]
ALL_MIN = float(lads.productivity.min())

render("U_gutter_fullcolor", [
    fill_layer(full, binned=False, cont_range=HEATMAP, domain_min=ALL_MIN),
    *outline_layers(sa_g), *label_layers(sa_g),
])

render("V_gutter_fullcolor_bins", [
    fill_layer(full, binned=True),
    *outline_layers(sa_g), *label_layers(sa_g),
])
