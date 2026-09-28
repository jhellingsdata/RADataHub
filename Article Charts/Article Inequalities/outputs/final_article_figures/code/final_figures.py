"""Final figures for the article "How do health inequalities shape regional
economic performance in the UK?", eco_style "report" theme.

Each figure is exported twice, as PNG (2.5x) and Vega-Lite JSON:
  <name>.png / .vl.json           with title, subtitle and source
  <name>_no_title.png / .vl.json  chart only (title and source go in the article text)
and its data is saved as data/<name>.xlsx (sheet "data" + sheet "notes").

  Figure 1  figure1_hle_by_deprivation_decile
            inputs/01_ONS_HLE_by_deprivation_decile_England_timeseries.xlsx
            Sheet 4, Period "2022 to 2024", Age group "<1" (at birth).
  Figure 2  figure2_productivity_map_itl3_uk
            inputs/03_ONS_SRPROD01_subregional_productivity_current2025.xlsx
            Sheet A1, ITL3 rows, Index_2023 (GVA per hour worked, UK=100).
            Boundaries: inputs/International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson
            Powys outline: inputs/lad_may2024.geojson (Powys is not an ITL3 area).
  Figure 3  figure3_health_inactivity_by_region
            inputs/02_HealthEquityNorth_HealthForWealth2025.pdf, Figure 25
            (values printed on the chart, transcribed below).

Self-contained: all inputs are in ../inputs, helpers (eco_style.py,
figure_frame.py) sit next to this script. From the folder root:
  pip install -r requirements.txt
  python3 code/final_figures.py
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

HERE = Path(__file__).resolve().parent
FINAL = HERE.parent                    # outputs/final_article_figures
INPUTS = FINAL / "inputs"             # every input file ships inside the folder
FIG_OUT = FINAL / "figures"
DATA_OUT = FINAL / "data"
FIG_OUT.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)

FONT = "Circular Std"
# Circular Std is a licensed font and is not shipped. Put its .ttf/.otf files in
# fonts/ (or install it on the system); otherwise text renders in a fallback font.
if any((FINAL / "fonts").glob("*.[ot]tf")):
    vlc.register_font_directory(str(FINAL / "fonts"))
P = eco_style.pallete
INK = P["domain"]
MUTED = eco_style.report()["config"]["range"]["heatmap"][0]  # report theme grey (#C9C9C9)
ACCENT = P["nominal_1"]  # eco_style main colour #179fdb


def report_local():
    spec = eco_style.report()
    cfg = spec["config"]
    cfg["legend"] = {
        "labelFont": FONT, "titleFont": FONT, "labelFontSize": 11, "titleFontSize": 11,
        "labelColor": INK, "titleColor": INK, "title": None, "symbolStrokeWidth": 0,
        "orient": "top", "direction": "horizontal", "offset": 16,
    }
    # x-axis titles styled like eco_style's y-axis titles
    cfg["axisX"].update(titleColor=INK, titleOpacity=cfg["axisY"]["titleOpacity"], titlePadding=10)
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_final_figures", report_local)
    alt.themes.enable("report_final_figures")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_final_figures", enable=True)(report_local)


def write(chart, stem):
    stem.with_suffix(".png").write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    stem.with_suffix(".vl.json").write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))


def export(inner, name, title, subtitle, source, data, notes, source_width=400, is_map=False):
    """Titled and untitled versions of `inner`, plus its data as .xlsx.

    The untitled version is wrapped in a one-item vconcat, like the titled one,
    so the legend sits above the axis title exactly as in the titled layout.
    """
    titled = framed(inner, title, subtitle, source, source_width=source_width)
    untitled = alt.vconcat(inner)
    if is_map:  # no frame round the map area
        titled, untitled = titled.configure_view(stroke=None), untitled.configure_view(stroke=None)
    write(titled, FIG_OUT / name)
    write(untitled, FIG_OUT / f"{name}_no_title")
    meta = pd.DataFrame({"field": ["Title", "Subtitle", "Source", *notes.keys()],
                         "value": [title, subtitle, source.replace("\n", " "), *notes.values()]})
    with pd.ExcelWriter(DATA_OUT / f"{name}.xlsx") as xw:
        data.to_excel(xw, sheet_name="data", index=False)
        meta.to_excel(xw, sheet_name="notes", index=False)
    print(f"wrote {name}: 2 figures (.png + .vl.json) and data .xlsx")


# ---------------------------------------------------------------------------
# Figure 1. Healthy life expectancy by deprivation decile (ONS, April 2026)
# ---------------------------------------------------------------------------

raw = pd.read_excel(INPUTS / "01_ONS_HLE_by_deprivation_decile_England_timeseries.xlsx", "4", header=6)
hle = raw[(raw["Period"] == "2022 to 2024") & (raw["Age group"] == "<1")][
    ["IMD decile", "Sex", "HLE", "LCI", "UCI"]].rename(columns={"IMD decile": "decile"})
hle["decile"] = hle.decile.astype(int)
assert len(hle) == 20, len(hle)

x_dec = alt.X("decile:O", axis=alt.Axis(title="Deprivation decile (1 = most deprived, 10 = least deprived)"))
y_hle = alt.Y("HLE:Q", scale=alt.Scale(domain=[45, 72]),
              axis=alt.Axis(title="Healthy life expectancy at birth (years)", tickCount=6, titleFont=FONT))
colour = alt.Color("Sex:N", scale=alt.Scale(domain=["Male", "Female"], range=[P["nominal_1"], P["nominal_2"]]),
                   legend=None)
tooltip = [alt.Tooltip("Sex:N"), alt.Tooltip("decile:O", title="IMD decile"),
           alt.Tooltip("HLE:Q", title="HLE (years)", format=".1f"),
           alt.Tooltip("LCI:Q", title="95% CI lower", format=".1f"),
           alt.Tooltip("UCI:Q", title="95% CI upper", format=".1f")]
base = alt.Chart(hle).encode(x=x_dec, y=y_hle, color=colour)
lines = base.mark_line(strokeWidth=2)
dots = base.mark_circle(size=70, opacity=1).encode(tooltip=tooltip)
# Start values on decile 1; series name + value at decile 10 replaces the legend.
first = hle[hle.decile == 1].assign(label=lambda d: d.HLE.map("{:.1f}".format))
start_labels = [
    alt.Chart(first[first.Sex == s]).mark_text(font=FONT, fontSize=11, fontWeight=600, color=INK, dy=dy)
    .encode(x=x_dec, y="HLE:Q", text="label:N")
    for s, dy in [("Male", -12), ("Female", 14)]
]
last = hle[hle.decile == 10].assign(label=lambda d: d.Sex + " " + d.HLE.map("{:.1f}".format))
end_labels = [
    alt.Chart(last[last.Sex == s]).mark_text(font=FONT, fontSize=11, fontWeight=600, color=INK,
                                             align="left", dx=10, dy=dy)
    .encode(x=x_dec, y="HLE:Q", text="label:N")
    for s, dy in [("Male", -6), ("Female", 6)]
]
export(
    alt.layer(lines, dots, *start_labels, *end_labels).properties(width=560, height=340),
    "figure1_hle_by_deprivation_decile",
    "People in England's most deprived areas spend around 20 fewer years in good health",
    "Healthy life expectancy at birth by area deprivation decile (IMD 2019), England, 2022–2024",
    "Source: ONS, Healthy life expectancy by national area deprivation, England (April 2026).",
    hle.rename(columns={"decile": "IMD decile (1 = most deprived)", "HLE": "HLE at birth (years)",
                        "LCI": "95% CI lower", "UCI": "95% CI upper"}),
    {"Source file": "01_ONS_HLE_by_deprivation_decile_England_timeseries.xlsx, sheet 4",
     "Filter": "Period = 2022 to 2024; Age group = <1 (at birth)"},
)

# ---------------------------------------------------------------------------
# Figure 2. Labour productivity by ITL3 subregion, UK, 2023 (annotated map)
# ---------------------------------------------------------------------------

YEAR = "Index_2023"
PALETTE = ["#C7E9B4", "#7FCDBB", "#41B6C4", "#2C7FB8", "#253494"]  # YlGnBu, low -> high
BREAKS = [80, 90, 100, 120]
BAND_LABELS = ([f"Under {BREAKS[0]}"] + [f"{lo}–{hi}" for lo, hi in zip(BREAKS[:-1], BREAKS[1:])]
               + [f"{BREAKS[-1]} and over"])

prod = pd.read_excel(INPUTS / "03_ONS_SRPROD01_subregional_productivity_current2025.xlsx", "A1", header=4)
prod = prod[prod.ITL_level == "ITL3"][["ITL_code", "Region_name", YEAR]].rename(columns={YEAR: "productivity"})
prod["productivity"] = pd.to_numeric(prod.productivity)

itl3 = gpd.read_file(INPUTS / "International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson")
itl3 = itl3[["ITL325CD", "ITL325NM", "geometry"]].to_crs("EPSG:27700")
itl3["geometry"] = itl3.geometry.buffer(0)  # a few ONS BGC polygons self-intersect
itl3["geometry"] = itl3.geometry.simplify(200)  # 200 m keeps outlines, cuts file size
missing = set(prod.ITL_code) ^ set(itl3.ITL325CD)
assert not missing, sorted(missing)
itl3 = itl3.merge(prod, left_on="ITL325CD", right_on="ITL_code")
itl3["band"] = pd.cut(itl3.productivity, bins=[-1e9, *BREAKS, 1e9], labels=BAND_LABELS, right=False).astype(str)

# London inset: London's ITL3 areas scaled up and moved into the empty North
# Sea, framed, with a matching frame drawn round London itself.
INSET_SCALE, INSET_ORIGIN, INSET_PAD = 3.5, (590_000, 760_000), 4_000
london = itl3[itl3.ITL_code.str.startswith("TLI")].copy()
lx0, ly0, lx1, ly1 = london.total_bounds
lx0, ly0, lx1, ly1 = lx0 - INSET_PAD, ly0 - INSET_PAD, lx1 + INSET_PAD, ly1 + INSET_PAD
london["geometry"] = london.geometry.translate(-lx0, -ly0).scale(
    INSET_SCALE, INSET_SCALE, origin=(0, 0)).translate(*INSET_ORIGIN)
ix1 = INSET_ORIGIN[0] + (lx1 - lx0) * INSET_SCALE
iy1 = INSET_ORIGIN[1] + (ly1 - ly0) * INSET_SCALE
frames = pd.DataFrame({"x": [lx0, INSET_ORIGIN[0]], "y": [ly0, INSET_ORIGIN[1]], "x2": [lx1, ix1], "y2": [ly1, iy1]})
frame_lines = pd.DataFrame(
    [(r.x, r.y, a, b) for r in frames.itertuples() for a, b in [(r.x2, r.y), (r.x, r.y2)]]
    + [(r.x2, r.y2, a, b) for r in frames.itertuples() for a, b in [(r.x2, r.y), (r.x, r.y2)]],
    columns=["x", "y", "x2", "y2"],
)
inset_label = pd.DataFrame({"x": [INSET_ORIGIN[0]], "y": [iy1 + 12_000], "text": ["London"]})

# Annotations: the places named in the productivity paragraph, plus the North.
LINE_WIDTH = 1.0
LEADER_COLOR, LEADER_WIDTH = "#9aa8b2", 0.7


def outline(gdf):
    # close the gaps the 200 m simplify leaves between neighbours, keep outer rings only
    merged = gdf.geometry.buffer(600).union_all().buffer(-600)
    parts = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
    return MultiPolygon([Polygon(g.exterior) for g in parts])


north = outline(itl3[itl3.ITL_code.str[:3].isin(["TLC", "TLD", "TLE"])])  # NE, NW, Yorkshire and The Humber
powys = gpd.read_file(INPUTS / "lad_may2024.geojson").query("LAD24NM == 'Powys'").to_crs("EPSG:27700").geometry.iloc[0]
tower_hamlets = london.loc[london.ITL_code == "TLI42"].geometry.iloc[0]  # already moved into the inset
outlines = gpd.GeoDataFrame({"name": ["North of England", "Powys", "Tower Hamlets"], "width": [LINE_WIDTH] * 3},
                            geometry=[north, powys, tower_hamlets], crs="EPSG:27700")
th_pt = tower_hamlets.representative_point()
# label text, label position (BNG metres), leader-line anchor, alignment
ann = pd.DataFrame([
    ("North of England", 520_000, 575_000, (415_000, 545_000), "left"),
    ("Powys", 215_000, 280_000, tuple(powys.representative_point().coords[0]), "right"),
    ("Tower Hamlets", th_pt.x, INSET_ORIGIN[1] - 22_000, (th_pt.x, th_pt.y), "center"),
], columns=["text", "x", "y", "anchor", "align"])
ann["ax"] = ann.anchor.map(lambda a: a[0])
ann["ay"] = ann.anchor.map(lambda a: a[1])
ann = ann.drop(columns="anchor")
LEADER_GAP = 7_000
ann["lx"] = ann.x + ann["align"].map({"right": LEADER_GAP, "left": -LEADER_GAP, "center": 0})
ann["ly"] = ann.y + ann["align"].map({"right": 0, "left": 0, "center": 9_000})

# Projection: British National Grid metres, identity projection
minx, miny, maxx, maxy = itl3.total_bounds
PAD = 15_000
DOMAIN_X = (minx - PAD, maxx + PAD + 170_000)  # extra room on the right for the legend
DOMAIN_Y = (miny - PAD, maxy + PAD)
WIDTH = 620
SCALE = WIDTH / (DOMAIN_X[1] - DOMAIN_X[0])
HEIGHT = round((DOMAIN_Y[1] - DOMAIN_Y[0]) * SCALE)
MAP_LEGEND = dict(titleFontWeight=600, symbolType="square", symbolSize=180, rowPadding=4,
                  orient="top-right", direction="vertical", offset=18)  # Vega default offset


def fill_layer(data):
    return alt.Chart(data).mark_geoshape(stroke="#ffffff", strokeWidth=0.3).encode(
        color=alt.Color("band:N", scale=alt.Scale(domain=BAND_LABELS[::-1], range=PALETTE[::-1]),
                        legend=alt.Legend(title=["GVA per hour worked,", "UK=100, 2023"], **MAP_LEGEND)),
        tooltip=[alt.Tooltip("ITL325NM:N", title="ITL3 area"),
                 alt.Tooltip("productivity:Q", title="Productivity (UK=100)", format=".1f")],
    )


layers = [
    fill_layer(itl3),
    fill_layer(london),
    alt.Chart(frame_lines).mark_rule(color=INK, strokeWidth=0.8).encode(
        longitude="x:Q", latitude="y:Q", longitude2="x2:Q", latitude2="y2:Q"),
    alt.Chart(inset_label).mark_text(font=FONT, fontSize=11, fontWeight=600, color=INK, align="left",
                                     baseline="bottom").encode(longitude="x:Q", latitude="y:Q", text="text:N"),
    alt.Chart(outlines).mark_geoshape(fill=None, stroke=INK).encode(strokeWidth=alt.StrokeWidth("width:Q", scale=None)),
    alt.Chart(ann).mark_rule(color=LEADER_COLOR, strokeWidth=LEADER_WIDTH).encode(
        longitude="lx:Q", latitude="ly:Q", longitude2="ax:Q", latitude2="ay:Q"),
]
for align in ("right", "left", "center"):
    layers.append(alt.Chart(ann[ann["align"] == align]).mark_text(
        font=FONT, fontSize=11, color=INK, align=align, baseline="top" if align == "center" else "middle",
    ).encode(longitude="x:Q", latitude="y:Q", text="text:N"))
productivity_map = (
    alt.layer(*layers)
    .project(type="identity", reflectY=True, scale=SCALE, translate=[-DOMAIN_X[0] * SCALE, DOMAIN_Y[1] * SCALE])
    .properties(width=WIDTH, height=HEIGHT)
)
export(
    productivity_map,
    "figure2_productivity_map_itl3_uk",
    "Labour productivity varies widely across the UK",
    "GVA per hour worked by ITL3 subregion, current prices, 2023 (UK=100)",
    "Source: ONS, Subregional productivity: labour productivity indices by UK ITL2 and ITL3\n"
    "subregions (June 2025), Table A1. Boundaries: ONS ITL3 January 2025.\n"
    "Powys outline: ONS local authority districts, May 2024.",
    itl3[["ITL_code", "Region_name", "productivity", "band"]].sort_values("productivity", ascending=False)
    .rename(columns={"ITL_code": "ITL3 code", "Region_name": "ITL3 area",
                     "productivity": "GVA per hour worked, UK=100, 2023", "band": "Map band"}),
    {"Source file": "03_ONS_SRPROD01_subregional_productivity_current2025.xlsx, sheet A1 (current price, "
                    "smoothed), column Index_2023",
     "Boundaries": "ONS ITL3 January 2025 BGC; Powys outline from ONS LAD May 2024",
     "Note": "The article text cites 2021 figures (ONS, 2023 edition); this map shows 2023"},
    source_width=WIDTH,
    is_map=True,
)

# ---------------------------------------------------------------------------
# Figure 3. Economic inactivity due to ill health, English regions
#           Health for Wealth 2025, Figure 25 (% of working-age population)
# ---------------------------------------------------------------------------

inact = pd.DataFrame({
    "region": ["North East", "North West", "Yorkshire and The Humber", "West Midlands",
               "East Midlands", "South West", "East of England", "London", "South East"],
    "rate": [9.5, 8.4, 7.3, 6.8, 6.7, 5.6, 5.2, 4.8, 4.5],
})
inact["group"] = inact.region.isin(["North East", "North West", "Yorkshire and The Humber"]).map(
    {True: "North of England", False: "Rest of England"})
inact["share"] = inact.rate / 100  # fraction, so the axis can use a % format
inact["label"] = inact.rate.map("{:.1f}%".format)

y_reg = alt.Y("region:N", sort=inact.sort_values("rate", ascending=False).region.tolist(),
              axis=alt.Axis(title="Region", labelPadding=8))
x_rate = alt.X("share:Q", scale=alt.Scale(domain=[0, 0.105]),
               axis=alt.Axis(title="Economically inactive due to ill health (% of working-age population)",
                             format=".0%", tickCount=6))
bars = alt.Chart(inact).mark_bar(height=18, cornerRadiusEnd=4).encode(
    y=y_reg, x=x_rate,
    color=alt.Color("group:N", scale=alt.Scale(domain=["North of England", "Rest of England"], range=[ACCENT, MUTED])),
    tooltip=[alt.Tooltip("region:N", title="Region"),
             alt.Tooltip("share:Q", title="Inactive due to ill health", format=".1%")],
)
bar_labels = alt.Chart(inact).mark_text(font=FONT, fontSize=11, color=INK, align="left", dx=5).encode(
    y=y_reg, x=x_rate, text="label:N")
export(
    alt.layer(bars, bar_labels).properties(width=420, height=270),
    "figure3_health_inactivity_by_region",
    "Health-related economic inactivity is highest in the North of England",
    "Share of the working-age population economically inactive due to ill health, English regions, 2024",
    "Source: Simpson et al. (2025), Health for Wealth 2025, Figure 25; based on ONS Annual Population Survey.",
    inact[["region", "group", "rate"]].rename(columns={
        "region": "Region", "group": "Group",
        "rate": "Economically inactive due to ill health (% of working-age population)"}),
    {"Source file": "02_HealthEquityNorth_HealthForWealth2025.pdf, Figure 25 (values transcribed from the chart)",
     "North vs rest": "Report: 8.4% North vs 5.6% rest of England in 2024, a 2.8 pp (50%) gap"},
)
