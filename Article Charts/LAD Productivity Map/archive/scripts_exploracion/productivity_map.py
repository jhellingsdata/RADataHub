"""England labour productivity by Local Authority District, with Strategic
Authority ("MSA") boundaries overlaid for context.

Altair choropleth built on the eco_style report theme.

Pipeline
    build_productivity_geometry.py -> geo/lad_productivity.geojson
    productivity_map.py            -> outputs/lad_productivity_map.{png,svg,html,vl.json}

Design notes
    Coordinates are British National Grid (EPSG:27700) and the chart uses
    d3's identity projection with an explicit scale and translate, following
    the same approach as RADataHub/msa_map/update_map_15sept/msa_map.py, so
    the map is pixel-stable rather than relying on Vega-Lite's auto-fit.

    Strategic Authorities have no productivity figure published at their own
    aggregate level, so they are drawn as an outline-only layer (no fill, no
    color encoding) on top of the LAD choropleth, which carries the real,
    granular data.
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


def report_local():
    """eco_style.report() with map-specific title/legend styling, mirroring
    RADataHub/msa_map/update_map_15sept/msa_map.py's report_local()."""
    spec = eco_style.report()
    cfg = spec["config"]
    cfg["title"] = {
        "font": FONT, "subtitleFont": FONT,
        "fontSize": 17, "fontWeight": 600,
        "subtitleFontSize": 11.5, "subtitleLineHeight": 15,
        "color": P["domain"], "subtitleColor": "#5b6b76",
        "anchor": "start", "offset": 14, "subtitlePadding": 8,
    }
    cfg["legend"] = {
        "labelFont": FONT, "titleFont": FONT,
        "labelFontSize": 11.5, "titleFontSize": 11.5,
        "titleColor": P["domain"], "labelColor": P["domain"],
        "titleFontWeight": 600, "gradientLength": 140,
    }
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_productivity", report_local)
    alt.themes.enable("report_productivity")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_productivity", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

lads = gpd.read_file("geo/lad_productivity.geojson")
sa = json.load(open("geo/sa_areas.geojson"))

# ---------------------------------------------------------------------------
# Projection: identity + explicit BNG scale/translate, computed from the
# England LAD layer's own bounds (this map has no side label columns, so
# padding can be tighter than msa_map.py's hand-tuned domain).
# ---------------------------------------------------------------------------

minx, miny, maxx, maxy = lads.total_bounds
pad = 15_000  # metres
DOMAIN_X = (minx - pad, maxx + pad)
DOMAIN_Y = (miny - pad, maxy + pad)
WIDTH = 700

SCALE = WIDTH / (DOMAIN_X[1] - DOMAIN_X[0])
HEIGHT = round((DOMAIN_Y[1] - DOMAIN_Y[0]) * SCALE)
TRANSLATE = [-DOMAIN_X[0] * SCALE, DOMAIN_Y[1] * SCALE]

PROJECTION = dict(type="identity", reflectY=True, scale=SCALE, translate=TRANSLATE)

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
    alt.Data(values=sa["features"], format=alt.DataFormat(type="json"))
).mark_geoshape(
    fill=None, stroke=P["domain"], strokeWidth=1.3
).encode(
    tooltip=[alt.Tooltip("properties.official_name:N", title="Strategic authority"),
             alt.Tooltip("properties.mayor:N", title="Mayor")],
)

subtitle = [
    "Local authority district productivity (colour); Strategic/Combined",
    "Authority boundaries overlaid for context - these authorities have no",
    "productivity figure published at their own aggregate level.",
    "Source: ONS, Subregional productivity: labour productivity indices by",
    "local authority district, released 19 June 2025.",
]

chart = (
    alt.layer(lad_fill, sa_outline)
    .project(**PROJECTION)
    .properties(
        width=WIDTH, height=HEIGHT,
        title=alt.Title("England productivity by local authority", subtitle=subtitle),
    )
    .configure_view(stroke=None)
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

spec = chart.to_json()
(OUT / "lad_productivity_map.png").write_bytes(vlc.vegalite_to_png(spec, scale=2.5))
(OUT / "lad_productivity_map.svg").write_text(vlc.vegalite_to_svg(spec))
chart.save(OUT / "lad_productivity_map.html")

spec_path = OUT / "lad_productivity_map.vl.json"
spec_path.write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
vlc.vegalite_to_svg(spec_path.read_text())  # validity round-trip

print(f"projection scale {SCALE:.7f}  canvas {WIDTH}x{HEIGHT}")
print(f"vega-lite spec: {spec_path.stat().st_size / 1024:.0f} KB, validated")
print("wrote outputs/lad_productivity_map.png / .svg / .html / .vl.json")
