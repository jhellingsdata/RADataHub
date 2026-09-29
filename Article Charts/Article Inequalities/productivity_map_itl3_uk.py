"""UK productivity map for the health-inequalities article: ITL3 labour
productivity, YlGnBu colour scale as in the LAD productivity map
(GROWTH LAB/LAD Productivity Map/code/productivity_map_final.py).

Data
    sources/03_ONS_SRPROD01_subregional_productivity_current2025.xlsx
        ONS "Subregional productivity: labour productivity indices by UK ITL2
        and ITL3 subregions", released 19 June 2025. Sheet A1 = current-price
        (smoothed) GVA per hour worked index, UK=100, 2004-2023. Header row at
        index 4: ITL_level, ITL_code, Region_name, Index_2004 ... Index_2023.
    sources/International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson
        ONS Open Geography Portal, ITL3 January 2025, BGC. Same ITL 2025
        vintage as the data: all 182 ITL3 codes join, zero mismatches.
    geo/lad_may2024.geojson
        Annotated version only: Powys is not an ITL3 area in the 2025 vintage
        (it sits inside Mid Wales), so its outline comes from the LAD May 2024
        boundaries. Labels carry names only; the values are given in the text.

Pipeline
    productivity_map_itl3_uk.py -> outputs/health_article/itl3_productivity_map_uk_ylgnbu_annotated.{png,vl.json}
    (the unannotated drafts were dropped; the final copy lives in outputs/final_article_figures)
"""

import json
from pathlib import Path

import altair as alt
import geopandas as gpd
import pandas as pd
import vl_convert as vlc
from shapely.geometry import MultiPolygon, Polygon

import eco_style
from figure_frame import framed

OUT = Path("outputs/health_article")
OUT.mkdir(parents=True, exist_ok=True)

FONT = "Circular Std"
P = eco_style.pallete

YEAR = "Index_2023"  # most recent year in the current ONS edition
# Two colour versions of the same map, low -> high:
#   eco_style  eco_style's 5-step scale (house default)
#   ylgnbu     YlGnBu, the scale used for the earlier England LAD maps
PALETTES = {
    "": eco_style.report()["config"]["range"]["ordinal"],
    "_ylgnbu": ["#C7E9B4", "#7FCDBB", "#41B6C4", "#2C7FB8", "#253494"],
}
BREAKS = [80, 90, 100, 120]
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
        "labelFontSize": 11, "titleFontSize": 11,
        "titleColor": P["domain"], "labelColor": P["domain"],
        "titleFontWeight": 600, "symbolType": "square", "symbolSize": 180,
        "symbolStrokeWidth": 0, "rowPadding": 4,
    }
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_productivity_itl3", report_local)
    alt.themes.enable("report_productivity_itl3")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_productivity_itl3", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

prod = pd.read_excel("sources/03_ONS_SRPROD01_subregional_productivity_current2025.xlsx", "A1", header=4)
prod = prod[prod.ITL_level == "ITL3"][["ITL_code", "Region_name", YEAR]].rename(columns={YEAR: "productivity"})
prod["productivity"] = pd.to_numeric(prod.productivity)

itl3 = gpd.read_file("sources/International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson")
itl3 = itl3[["ITL325CD", "ITL325NM", "geometry"]].to_crs("EPSG:27700")
itl3["geometry"] = itl3.geometry.buffer(0)  # a few ONS BGC polygons self-intersect
itl3["geometry"] = itl3.geometry.simplify(200)  # 200 m keeps outlines, cuts file size

missing = set(prod.ITL_code) ^ set(itl3.ITL325CD)
assert not missing, sorted(missing)
itl3 = itl3.merge(prod, left_on="ITL325CD", right_on="ITL_code")
itl3["band"] = pd.cut(itl3.productivity, bins=[-1e9, *BREAKS, 1e9], labels=BAND_LABELS, right=False).astype(str)
print(f"ITL3 areas: {len(itl3)}; bands: {itl3.band.value_counts().to_dict()}")

# London inset: London's ITL3 areas (codes TLI..) scaled up and moved into the
# empty North Sea, framed, with a matching frame drawn round London itself.
INSET_SCALE = 3.5
INSET_ORIGIN = (590_000, 760_000)  # lower-left corner of the inset frame (BNG)
INSET_PAD = 4_000
london = itl3[itl3.ITL_code.str.startswith("TLI")].copy()
lx0, ly0, lx1, ly1 = london.total_bounds
lx0, ly0, lx1, ly1 = lx0 - INSET_PAD, ly0 - INSET_PAD, lx1 + INSET_PAD, ly1 + INSET_PAD
london["geometry"] = london.geometry.translate(-lx0, -ly0).scale(
    INSET_SCALE, INSET_SCALE, origin=(0, 0)).translate(*INSET_ORIGIN)
ix1 = INSET_ORIGIN[0] + (lx1 - lx0) * INSET_SCALE
iy1 = INSET_ORIGIN[1] + (ly1 - ly0) * INSET_SCALE
frames = pd.DataFrame({
    "x": [lx0, INSET_ORIGIN[0]], "y": [ly0, INSET_ORIGIN[1]],
    "x2": [lx1, ix1], "y2": [ly1, iy1],
})
frame_lines = pd.DataFrame(
    [(r.x, r.y, a, b) for r in frames.itertuples() for a, b in
     [(r.x2, r.y), (r.x, r.y2)]]
    + [(r.x2, r.y2, a, b) for r in frames.itertuples() for a, b in
       [(r.x2, r.y), (r.x, r.y2)]],
    columns=["x", "y", "x2", "y2"],
)
inset_label = pd.DataFrame({"x": [INSET_ORIGIN[0]], "y": [iy1 + 12_000], "text": ["London"]})

# ---------------------------------------------------------------------------
# Annotations: the places named in the productivity paragraph, plus the North
# (annotated version only)
# ---------------------------------------------------------------------------


# Line weights as in the LAD productivity map (productivity_map_final.py): thin navy outlines, no halo,
# grey leader lines, regular-weight labels, 0.3 white area borders.
LINE_WIDTH = 1.0
LEADER_COLOR, LEADER_WIDTH = "#9aa8b2", 0.7


def outline(gdf):
    # close the gaps the 200 m simplify leaves between neighbours, then keep
    # only outer rings so no internal slivers are drawn
    merged = gdf.geometry.buffer(600).union_all().buffer(-600)
    parts = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
    return MultiPolygon([Polygon(g.exterior) for g in parts])


north = outline(itl3[itl3.ITL_code.str[:3].isin(["TLC", "TLD", "TLE"])])  # NE, NW, Yorkshire and The Humber
powys = gpd.read_file("geo/lad_may2024.geojson").query("LAD24NM == 'Powys'").to_crs("EPSG:27700").geometry.iloc[0]
tower_hamlets = london.loc[london.ITL_code == "TLI42"].geometry.iloc[0]  # already moved into the inset

outlines = gpd.GeoDataFrame(
    {"name": ["North of England", "Powys", "Tower Hamlets"],
     "width": [LINE_WIDTH] * 3},
    geometry=[north, powys, tower_hamlets], crs="EPSG:27700",
)

# Label position (BNG metres), anchor point for the leader line, alignment.
th_pt = tower_hamlets.representative_point()
ANNOTATIONS = [
    ("North of England", 520_000, 575_000, (415_000, 545_000), "left"),
    ("Powys", 215_000, 280_000, tuple(powys.representative_point().coords[0]), "right"),
    ("Tower Hamlets", th_pt.x, INSET_ORIGIN[1] - 22_000, (th_pt.x, th_pt.y), "center"),
]
ann = pd.DataFrame(ANNOTATIONS, columns=["text", "x", "y", "anchor", "align"])
ann["ax"] = ann.anchor.map(lambda a: a[0])
ann["ay"] = ann.anchor.map(lambda a: a[1])
ann = ann.drop(columns="anchor")
LEADER_GAP = 7_000
ann["lx"] = ann.x + ann["align"].map({"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0})
ann["ly"] = ann.y + ann["align"].map({"right": 0, "left": 0, "center": 9_000})

# ---------------------------------------------------------------------------
# Projection: British National Grid metres, identity projection
# ---------------------------------------------------------------------------

minx, miny, maxx, maxy = itl3.total_bounds
PAD = 15_000
DOMAIN_X = (minx - PAD, maxx + PAD + 170_000)  # extra room on the right for the legend
DOMAIN_Y = (miny - PAD, maxy + PAD)
WIDTH = 620
SCALE = WIDTH / (DOMAIN_X[1] - DOMAIN_X[0])
HEIGHT = round((DOMAIN_Y[1] - DOMAIN_Y[0]) * SCALE)


def projection(scale):
    return dict(type="identity", reflectY=True, scale=scale,
                translate=[-DOMAIN_X[0] * scale, DOMAIN_Y[1] * scale])


def fill_layer(data, palette, stroke_width=0.3, legend_orient="top-right"):
    return alt.Chart(data).mark_geoshape(stroke="#ffffff", strokeWidth=stroke_width).encode(
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=BAND_LABELS[::-1], range=palette[::-1]),
            legend=alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"], orient=legend_orient),
        ),
        tooltip=[alt.Tooltip("ITL325NM:N", title="ITL3 area"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )


def inset_layers(palette, stroke_width=0.3, frame_width=0.8, font_size=11):
    return [
        fill_layer(london, palette, stroke_width=stroke_width),
        alt.Chart(frame_lines).mark_rule(color=P["domain"], strokeWidth=frame_width).encode(
            longitude="x:Q", latitude="y:Q", longitude2="x2:Q", latitude2="y2:Q"),
        alt.Chart(inset_label).mark_text(
            font=FONT, fontSize=font_size, fontWeight=600, color=P["domain"], align="left", baseline="bottom",
        ).encode(longitude="x:Q", latitude="y:Q", text="text:N"),
    ]


def annotation_layers():
    layers = [
        alt.Chart(outlines).mark_geoshape(fill=None, stroke=P["domain"]).encode(
            strokeWidth=alt.StrokeWidth("width:Q", scale=None)),
        alt.Chart(ann).mark_rule(color=LEADER_COLOR, strokeWidth=LEADER_WIDTH).encode(
            longitude="lx:Q", latitude="ly:Q", longitude2="ax:Q", latitude2="ay:Q"),
    ]
    for align in ("right", "left", "center"):
        layers.append(alt.Chart(ann[ann["align"] == align]).mark_text(
            font=FONT, fontSize=11, color=P["domain"], align=align,
            baseline="top" if align == "center" else "middle",
        ).encode(longitude="x:Q", latitude="y:Q", text="text:N"))
    return layers


def build(palette, annotated=False):
    m = (
        alt.layer(fill_layer(itl3, palette), *inset_layers(palette), *(annotation_layers() if annotated else []))
        .project(**projection(SCALE))
        .properties(width=WIDTH, height=HEIGHT)
    )
    return framed(
        m,
        "Labour productivity varies widely across the UK",
        "GVA per hour worked by ITL3 subregion, current prices, 2023 (UK=100)",
        "Source: ONS, Subregional productivity: labour productivity indices by UK ITL2 and ITL3\n"
        "subregions (June 2025), Table A1. Boundaries: ONS ITL3 January 2025."
        + ("\nPowys outline: ONS local authority districts, May 2024."
           if annotated else ""),
        source_width=WIDTH,
    ).configure_view(stroke=None)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

VERSIONS = [("_ylgnbu_annotated", PALETTES["_ylgnbu"], True)]  # the article version only

for suffix, palette, annotated in VERSIONS:
    chart = build(palette, annotated)
    stem = OUT / f"itl3_productivity_map_uk{suffix}"
    stem.with_suffix(".png").write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    stem.with_suffix(".vl.json").write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {stem}.png / .vl.json")

