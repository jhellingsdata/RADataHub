"""UK healthy life expectancy map for the health-inequalities article:
HLE at birth by local area, 2022-2024, one map per sex. Same frame, London
inset, YlGnBu scale and North of England / Greater Manchester outlines as the
annotated productivity map (productivity_map_itl3_uk.py), so the two pair.

Data
    sources/11_ONS_HLE_UK_local_areas_2011-2024.xlsx
        ONS "Healthy life expectancy, UK: between 2011 to 2013 and 2022 to
        2024", released 19 February 2026. Sheet 1, header row starting
        "Period": Period, Country, Area type, Area code, Area name, Sex, Sex
        code, Age group, Age code, HLE, LCI, UCI, Proportion (%). Filtered to
        Area type "Local Areas" (England upper-tier authorities, Scottish
        council areas, Welsh unitary authorities, NI districts), Age group "<1".
        ONS excludes Isles of Scilly and City of London (small populations).
    geo/ctyua_dec2025_uk_bgc.geojson
        ONS Open Geography Portal, Counties and Unitary Authorities (December
        2025) Boundaries UK BGC, fetched from the ArcGIS FeatureServer. All
        216 HLE local-area codes join (incl. the 2025 Barnsley/Sheffield codes).
    sources/International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson
        Only for the North of England and Greater Manchester outlines, built
        from ITL3 areas exactly as in the productivity map.

Pipeline
    health_map_uk.py -> outputs/health_article/hle_map_uk_{female,male}.{png,vl.json}
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

PERIOD = "2022 to 2024"
PALETTE = ["#C7E9B4", "#7FCDBB", "#41B6C4", "#2C7FB8", "#253494"]  # YlGnBu, low -> high
NO_DATA = P["Other_3"]
BREAKS = [55, 58, 61, 64]
BAND_LABELS = (
    [f"Under {BREAKS[0]}"]
    + [f"{lo}–{hi}" for lo, hi in zip(BREAKS[:-1], BREAKS[1:])]
    + [f"{BREAKS[-1]} and over"]
)
LEGEND_DOMAIN = BAND_LABELS[::-1] + ["No data"]
LEGEND_RANGE = PALETTE[::-1] + [NO_DATA]

# Line weights as in productivity_map_itl3_uk.py
LINE_WIDTH = 1.0
LEADER_COLOR, LEADER_WIDTH = "#9aa8b2", 0.7


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
    alt.themes.register("report_health_map", report_local)
    alt.themes.enable("report_health_map")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_health_map", enable=True)(report_local)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

raw = pd.read_excel("sources/11_ONS_HLE_UK_local_areas_2011-2024.xlsx", "1", header=None)
header_row = raw.index[raw[0].astype(str).str.strip().eq("Period")][0]
hle = raw.iloc[header_row + 1:].copy()
hle.columns = raw.iloc[header_row].astype(str).str.strip()
hle = hle[(hle.Period == PERIOD) & (hle["Age group"].astype(str) == "<1") & (hle["Area type"] == "Local Areas")]
hle = hle[["Area code", "Area name", "Sex", "HLE", "LCI", "UCI"]].copy()
hle["HLE"] = pd.to_numeric(hle.HLE)

areas = gpd.read_file("geo/ctyua_dec2025_uk_bgc.geojson")[["CTYUA25CD", "CTYUA25NM", "geometry"]].to_crs("EPSG:27700")
areas["geometry"] = areas.geometry.buffer(0).simplify(200)
missing = set(hle["Area code"]) - set(areas.CTYUA25CD)
assert not missing, sorted(missing)

itl3 = gpd.read_file("sources/International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson")
itl3 = itl3[["ITL325CD", "geometry"]].to_crs("EPSG:27700")
itl3["geometry"] = itl3.geometry.buffer(0).simplify(200)

# ---------------------------------------------------------------------------
# Frame: same extent as the productivity map (ITL3 bounds), so the two match
# ---------------------------------------------------------------------------

minx, miny, maxx, maxy = itl3.total_bounds
PAD = 15_000
DOMAIN_X = (minx - PAD, maxx + PAD + 170_000)  # extra room on the right for the legend
DOMAIN_Y = (miny - PAD, maxy + PAD)
WIDTH = 620
SCALE = WIDTH / (DOMAIN_X[1] - DOMAIN_X[0])
HEIGHT = round((DOMAIN_Y[1] - DOMAIN_Y[0]) * SCALE)
PROJECTION = dict(type="identity", reflectY=True, scale=SCALE,
                  translate=[-DOMAIN_X[0] * SCALE, DOMAIN_Y[1] * SCALE])

# London inset: London boroughs (codes E09) scaled up into the North Sea.
INSET_SCALE = 3.5
INSET_ORIGIN = (590_000, 760_000)
INSET_PAD = 4_000
london_idx = areas.CTYUA25CD.str.startswith("E09")
lx0, ly0, lx1, ly1 = areas[london_idx].total_bounds
lx0, ly0, lx1, ly1 = lx0 - INSET_PAD, ly0 - INSET_PAD, lx1 + INSET_PAD, ly1 + INSET_PAD
ix1 = INSET_ORIGIN[0] + (lx1 - lx0) * INSET_SCALE
iy1 = INSET_ORIGIN[1] + (ly1 - ly0) * INSET_SCALE
frame_lines = pd.DataFrame(
    [(x, y, x2, y2) for (x, y, x2, y2) in [(lx0, ly0, lx1, ly1), (INSET_ORIGIN[0], INSET_ORIGIN[1], ix1, iy1)]
     for (x, y, x2, y2) in [(x, y, x2, y), (x, y, x, y2), (x2, y2, x2, y), (x2, y2, x, y2)]],
    columns=["x", "y", "x2", "y2"],
)
inset_label = pd.DataFrame({"x": [INSET_ORIGIN[0]], "y": [iy1 + 12_000], "text": ["London"]})


def to_inset(gdf):
    out = gdf.copy()
    out["geometry"] = out.geometry.translate(-lx0, -ly0).scale(
        INSET_SCALE, INSET_SCALE, origin=(0, 0)).translate(*INSET_ORIGIN)
    return out


# North of England and Greater Manchester outlines, as in the productivity map.
def outline(gdf):
    merged = gdf.geometry.buffer(600).union_all().buffer(-600)
    parts = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
    return MultiPolygon([Polygon(g.exterior) for g in parts])


north = outline(itl3[itl3.ITL325CD.str[:3].isin(["TLC", "TLD", "TLE"])])
gm = outline(itl3[itl3.ITL325CD.str.startswith("TLD3")])
outlines = gpd.GeoDataFrame({"name": ["North of England", "Greater Manchester"]},
                            geometry=[north, gm], crs="EPSG:27700")

LEADER_GAP = 7_000
ann = pd.DataFrame([
    ("North of England", 520_000, 575_000, 415_000, 545_000, "left"),
    ("Greater Manchester", 285_000, 430_000, *gm.representative_point().coords[0], "right"),
], columns=["text", "x", "y", "ax", "ay", "align"])
ann["lx"] = ann.x + ann["align"].map({"right": LEADER_GAP, "left": -LEADER_GAP})
ann["ly"] = ann.y

# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------


def fill_layer(data, stroke_width=0.3):
    return alt.Chart(data).mark_geoshape(stroke="#ffffff", strokeWidth=stroke_width).encode(
        color=alt.Color("band:N", scale=alt.Scale(domain=LEGEND_DOMAIN, range=LEGEND_RANGE),
                        legend=alt.Legend(title=["Healthy life expectancy", "at birth (years)"],
                                          orient="top-right")),
        tooltip=[alt.Tooltip("CTYUA25NM:N", title="Local area"),
                 alt.Tooltip("HLE:Q", title="Healthy life expectancy (years)", format=".1f")],
    )


def build(sex):
    d = areas.merge(hle[hle.Sex == sex], left_on="CTYUA25CD", right_on="Area code", how="left")
    d["band"] = pd.cut(d.HLE, bins=[-1e9, *BREAKS, 1e9], labels=BAND_LABELS, right=False).astype(str)
    d.loc[d.HLE.isna(), "band"] = "No data"
    d = d[["CTYUA25CD", "CTYUA25NM", "HLE", "band", "geometry"]]

    layers = [
        fill_layer(d),
        fill_layer(to_inset(d[d.CTYUA25CD.str.startswith("E09")])),
        alt.Chart(frame_lines).mark_rule(color=P["domain"], strokeWidth=0.8).encode(
            longitude="x:Q", latitude="y:Q", longitude2="x2:Q", latitude2="y2:Q"),
        alt.Chart(inset_label).mark_text(
            font=FONT, fontSize=11, fontWeight=600, color=P["domain"], align="left", baseline="bottom",
        ).encode(longitude="x:Q", latitude="y:Q", text="text:N"),
        alt.Chart(outlines).mark_geoshape(fill=None, stroke=P["domain"], strokeWidth=LINE_WIDTH),
        alt.Chart(ann).mark_rule(color=LEADER_COLOR, strokeWidth=LEADER_WIDTH).encode(
            longitude="lx:Q", latitude="ly:Q", longitude2="ax:Q", latitude2="ay:Q"),
    ]
    for align in ("right", "left"):
        layers.append(alt.Chart(ann[ann["align"] == align]).mark_text(
            font=FONT, fontSize=11, color=P["domain"], align=align, baseline="middle",
        ).encode(longitude="x:Q", latitude="y:Q", text="text:N"))

    m = alt.layer(*layers).project(**PROJECTION).properties(width=WIDTH, height=HEIGHT)
    who = {"Male": "males", "Female": "females"}[sex]
    return framed(
        m,
        "Healthy life expectancy varies by more than 20 years across the UK",
        f"Healthy life expectancy at birth, {who}, by local area, 2022–2024 (years)",
        "Source: ONS, Healthy life expectancy, UK: between 2011 to 2013 and 2022 to 2024 (February 2026).\n"
        "Boundaries: ONS Counties and Unitary Authorities, December 2025. Isles of Scilly and\n"
        "City of London not published by ONS (small populations).",
        source_width=WIDTH,
    ).configure_view(stroke=None)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

for sex in ["Female", "Male"]:
    chart = build(sex)
    stem = OUT / f"hle_map_uk_{sex.lower()}"
    stem.with_suffix(".png").write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    stem.with_suffix(".vl.json").write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {stem}.png / .vl.json")
