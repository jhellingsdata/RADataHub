"""Regional charts for the health-inequalities article, eco_style "report" theme,
title / subtitle / source on every chart (figure_frame.framed).

  1  employment_inactivity_by_region   sources/04_ONS_HI00_… (18 Aug 2026, Apr-Jun 2026)
       Sheets <region>_p; latest LFS row; col 16 = employment rate 16-64 (%),
       col 18 = economic inactivity rate 16-64 (%).
  1b employment_inactivity_by_region_table   same data, table layout (bar in each cell)
  2  hle_by_region                      sources/11_ONS_HLE_UK_local_areas_2011-2024.xlsx
       Sheet 1, Area type Region / Country, Age group "<1", 2022 to 2024.
  3  gm_hle_over_time                   same file, Combined Authority "Greater Manchester"
       and Country "England", every three-year period.
  4  gm_gdp_growth                      sources/12_ONS_regional_GDP_all_ITL_Sep2026.xlsx
       Table 9 (GDP chained volume index, 2023=100), ITL2; growth 2015-2024 is
       our own calculation from the index.
  5  gm_productivity_growth             sources/03_ONS_SRPROD01_… (current edition, incl.
       the 30 Oct 2025 correction) Table A5 (chained volume GVA per hour,
       unsmoothed), ITL2; average annual growth 2015-2023 is our own calculation.
  6  gdhi_by_region                     sources/13_ONS_regional_GDHI_all_ITL_Aug2026.xlsx
       Table 4 (GDHI per head, UK=100), ITL1, 2024.

Outputs: outputs/health_article/<name>.{png,vl.json}; data in outputs/health_article/data/<name>.csv
"""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import vl_convert as vlc

import eco_style
from figure_frame import framed

OUT = Path("outputs/health_article")
DATA_OUT = OUT / "data"
DATA_OUT.mkdir(parents=True, exist_ok=True)

FONT = "Circular Std"
P = eco_style.pallete
INK = P["domain"]
MUTED = eco_style.report()["config"]["range"]["heatmap"][0]  # report theme grey (#C9C9C9)
ACCENT = P["nominal_1"]  # eco_style main colour #179fdb (first colour of the report theme)
NORTH = ["North East", "North West", "Yorkshire and The Humber"]
ORDINAL = ["", "fastest", "second-fastest", "third-fastest", "fourth-fastest", "fifth-fastest"]


def report_local():
    spec = eco_style.report()
    cfg = spec["config"]
    cfg["legend"] = {
        "labelFont": FONT, "titleFont": FONT, "labelFontSize": 11,
        "labelColor": INK, "title": None, "symbolStrokeWidth": 0,
        "orient": "top", "direction": "horizontal", "offset": 16,
    }
    # x-axis titles styled like eco_style's y-axis titles
    cfg["axisX"].update(titleColor=INK, titleOpacity=cfg["axisY"]["titleOpacity"], titlePadding=10)
    cfg["view"] = {"stroke": "transparent"}
    return spec


try:
    alt.themes.register("report_health_regional", report_local)
    alt.themes.enable("report_health_regional")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_health_regional", enable=True)(report_local)


def export(chart, name, data):
    stem = OUT / name
    stem.with_suffix(".png").write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    stem.with_suffix(".vl.json").write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
    data.to_csv(DATA_OUT / f"{name}.csv", index=False)
    print(f"wrote {stem}.*")


def ons_sheet(path, sheet, first_col_value):
    """Read an ONS table whose header row starts with `first_col_value`."""
    raw = pd.read_excel(path, sheet, header=None)
    hr = raw.index[raw[0].astype(str).str.strip().eq(first_col_value)][0]
    df = raw.iloc[hr + 1:].copy()
    df.columns = [str(c).strip().removesuffix(".0") for c in raw.iloc[hr]]
    return df


def ranked_bars(d, value, label, x_title, y_title, fmt, domain, group_domain, group_range,
                ref=None, ref_label=None, width=300, bar_height=16, legend=True,
                order=None, y_axis=True, x_values=alt.Undefined):
    """Horizontal bars sorted by value (or a given `order`), direct value labels, optional reference rule."""
    if order is None:
        order = d.sort_values(value, ascending=False)[label].tolist()
    y = alt.Y(f"{label}:N", sort=order,
              axis=alt.Axis(title=y_title, labelPadding=8, labelLimit=340) if y_axis else None)
    if domain is None:  # pad the data range so no bar or label runs off the axis
        lo, hi = d[value].min(), d[value].max()
        pad = (hi - lo) * 0.08
        domain = [min(0, lo - pad), hi + pad]
    x = alt.X(f"{value}:Q", scale=alt.Scale(domain=domain), axis=alt.Axis(title=x_title, format=fmt, tickCount=6, values=x_values))
    colour = alt.Color("group:N", scale=alt.Scale(domain=group_domain, range=group_range),
                       legend=alt.Legend() if legend else None)
    bars = alt.Chart(d).mark_bar(height=bar_height, cornerRadiusEnd=4).encode(
        y=y, x=x, color=colour,
        tooltip=[alt.Tooltip(f"{label}:N", title=y_title), alt.Tooltip(f"{value}:Q", title=x_title, format=fmt)])
    txt = alt.Chart(d).mark_text(font=FONT, fontSize=11, color=INK, align="left", dx=5).encode(
        y=y, x=x, text="text:N")
    layers = [bars, txt]
    if ref is not None:
        r = pd.DataFrame({"v": [ref], "t": [ref_label]})
        layers.append(alt.Chart(r).mark_rule(color=INK, strokeDash=[3, 3], strokeWidth=1).encode(x="v:Q"))
        layers.append(alt.Chart(r).mark_text(font=FONT, fontSize=11, color=INK, align="left", dx=4, dy=-4,
                                             baseline="bottom").encode(x="v:Q", y=alt.value(0), text="t:N"))
    return alt.layer(*layers).properties(width=width, height=len(d) * (bar_height + 6))


# ---------------------------------------------------------------------------
# 1. Employment and inactivity by English region, Apr-Jun 2026 (HI00)
# ---------------------------------------------------------------------------

HI00 = "sources/04_ONS_HI00_labour_market_18Aug2026_AprJun2026data.xlsx"
SHEETS = {"North East": "neast", "North West": "nwest", "Yorkshire and The Humber": "ykhu",
          "East Midlands": "emids", "West Midlands": "wmids", "East of England": "east",
          "London": "lon", "South East": "seast", "South West": "swest"}
rows = []
for region, sh in SHEETS.items():
    s = pd.read_excel(HI00, f"{sh}_p", header=None)
    lfs = s[s[0].astype(str).str.match(r"^[A-Z][a-z]{2}-[A-Z][a-z]{2} \d{4}$")].iloc[-1]
    assert lfs[0] == "Apr-Jun 2026", lfs[0]
    rows.append({"region": region, "employment": round(lfs[16], 1) / 100, "inactivity": round(lfs[18], 1) / 100})
lm = pd.DataFrame(rows)
lm["group"] = lm.region.isin(NORTH).map({True: "North of England", False: "Rest of England"})

GROUPS_ENG = (["North of England", "Rest of England"], [ACCENT, MUTED])
# Both panels on a 0-100% axis and in one region order (by employment), so each
# row is the same region; region names shown once, on the left panel.
LM_ORDER = lm.sort_values("employment", ascending=False).region.tolist()
panels = []
for col, x_title, first in [("employment", "Employment rate, aged 16–64 (%)", True),
                            ("inactivity", "Economic inactivity rate, aged 16–64 (%)", False)]:
    d = lm[["region", "group", col]].copy()
    d["text"] = (d[col] * 100).map("{:.1f}%".format)
    panels.append(ranked_bars(d, col, "region", x_title, "Region", ".0%", [0, 1],
                              *GROUPS_ENG, width=260, legend=first, order=LM_ORDER, y_axis=first,
                              x_values=[0, .25, .5, .75, 1]))
chart1 = framed(
    alt.hconcat(*panels, spacing=24),
    "Employment is lowest and economic inactivity highest in the North East",
    "Employment and economic inactivity rates, people aged 16–64, English regions, April–June 2026",
    "Source: ONS, Labour market in the regions of the UK, dataset HI00 (18 August 2026). Labour Force Survey;\n"
    "official statistics in development.",
    source_width=640,
)
export(chart1, "employment_inactivity_by_region", lm)

# 1b. Same data as a table: one row per region, one column per rate, each cell a
# bar on a 0-100% track with its value. Column headers replace the x axes.
COLS = ["Employment rate (%)", "Economic inactivity rate (%)"]
tbl = lm.melt(id_vars=["region", "group"], value_vars=["employment", "inactivity"], var_name="k", value_name="rate")
tbl["metric"] = tbl.k.map({"employment": COLS[0], "inactivity": COLS[1]})
tbl["text"] = (tbl.rate * 100).map("{:.1f}%".format)
tbl["full"] = 1.0
ty = alt.Y("region:N", sort=LM_ORDER, axis=alt.Axis(title=None, labelPadding=10, labelLimit=340, domain=False, ticks=False))
tx = alt.X("rate:Q", scale=alt.Scale(domain=[0, 1.18]), axis=None)  # headroom for the value label
track = alt.Chart().mark_bar(height=16, color=INK, opacity=0.06, cornerRadiusEnd=4).encode(
    y=ty, x=alt.X("full:Q", scale=alt.Scale(domain=[0, 1.18]), axis=None))
cell_bar = alt.Chart().mark_bar(height=16, cornerRadiusEnd=4).encode(  # one colour per column; headers name them
    y=ty, x=tx, color=alt.Color("metric:N", scale=alt.Scale(domain=COLS, range=[ACCENT, P["nominal_2"]]), legend=None),
    tooltip=["region:N", "metric:N", alt.Tooltip("rate:Q", format=".1%")])
cell_txt = alt.Chart().mark_text(font=FONT, fontSize=11, color=INK, align="left", dx=5).encode(
    y=ty, x=alt.X("full:Q", scale=alt.Scale(domain=[0, 1.18]), axis=None), text="text:N")
table = alt.layer(track, cell_bar, cell_txt, data=tbl).properties(width=250, height=len(lm) * 30).facet(
    column=alt.Column("metric:N", sort=COLS, title=None,
                      header=alt.Header(labelFont=FONT, labelFontSize=11, labelColor=INK, labelAnchor="start",
                                        labelOrient="top", labelPadding=10)),
    spacing=24,
)
chart1b = framed(
    table,
    "Employment is lowest and economic inactivity highest in the North East",
    "Employment and economic inactivity rates, people aged 16–64, English regions, April–June 2026. "
    "Each bar is drawn on a 0–100% scale",
    "Source: ONS, Labour market in the regions of the UK, dataset HI00 (18 August 2026). Labour Force Survey;\n"
    "official statistics in development.",
    source_width=640,
)
export(chart1b, "employment_inactivity_by_region_table", lm)

# ---------------------------------------------------------------------------
# 2. Healthy life expectancy by English region and UK nation, 2022-2024
# ---------------------------------------------------------------------------

HLE = "sources/11_ONS_HLE_UK_local_areas_2011-2024.xlsx"
hle_all = ons_sheet(HLE, "1", "Period")
hle_all = hle_all[hle_all["Age group"].astype(str) == "<1"].copy()
hle_all["HLE"] = pd.to_numeric(hle_all.HLE)

reg = hle_all[(hle_all.Period == "2022 to 2024")
              & ((hle_all["Area type"] == "Region")
                 | ((hle_all["Area type"] == "Country") & hle_all["Area name"].isin(["Wales", "Scotland", "Northern Ireland"])))]
reg = reg[["Area name", "Sex", "HLE", "LCI", "UCI"]].rename(columns={"Area name": "area"})
order = reg[reg.Sex == "Female"].sort_values("HLE", ascending=False).area.tolist()

y = alt.Y("area:N", sort=order, axis=alt.Axis(title="English region / UK nation", labelPadding=8))
x = alt.X("HLE:Q", scale=alt.Scale(domain=[54, 66]),
          axis=alt.Axis(title="Healthy life expectancy at birth (years)", tickCount=6))
sex_colour = alt.Color("Sex:N", scale=alt.Scale(domain=["Male", "Female"], range=[P["nominal_1"], P["nominal_2"]]))
link = alt.Chart(reg).mark_rule(color=MUTED, strokeWidth=2).encode(
    y=y, x=alt.X("min(HLE):Q", scale=alt.Scale(domain=[54, 66])), x2="max(HLE):Q")
dots = alt.Chart(reg).mark_circle(size=80, opacity=1).encode(
    y=y, x=x, color=sex_colour,
    tooltip=[alt.Tooltip("area:N", title="Area"), alt.Tooltip("Sex:N"),
             alt.Tooltip("HLE:Q", title="HLE (years)", format=".1f")])
ne = reg[reg.area == "North East"].copy()
ne["label"] = ne.Sex + " " + ne.HLE.map("{:.1f}".format)
ne_labels = [
    alt.Chart(ne[ne.Sex == s]).mark_text(font=FONT, fontSize=11, fontWeight=600, color=INK, align=a, dx=dx).encode(
        y=y, x="HLE:Q", text="label:N")
    for s, a, dx in [("Male", "left", 10), ("Female", "right", -10)]
]
chart2 = framed(
    alt.layer(link, dots, *ne_labels).properties(width=480, height=len(order) * 26),
    "Healthy life expectancy is lowest in the North East",
    "Healthy life expectancy at birth by English region and UK nation, 2022–2024 (years)",
    "Source: ONS, Healthy life expectancy, UK: between 2011 to 2013 and 2022 to 2024 (February 2026).",
    source_width=560,
)
export(chart2, "hle_by_region", reg)

# ---------------------------------------------------------------------------
# 3. Greater Manchester vs England over time
# ---------------------------------------------------------------------------

gm = hle_all[((hle_all["Area type"] == "Combined Authority") & (hle_all["Area name"] == "Greater Manchester"))
             | ((hle_all["Area type"] == "Country") & (hle_all["Area name"] == "England"))]
gm = gm[["Period", "Area name", "Sex", "HLE"]].rename(columns={"Area name": "area"}).copy()
gm["year"] = gm.Period.str[-4:].astype(int)  # final year of the three-year period
AREA_COLOURS = alt.Scale(domain=["England", "Greater Manchester"], range=[P["bar"]["accent_1"], ACCENT])


def gm_panel(sex):
    d = gm[gm.Sex == sex]
    x = alt.X("year:Q", scale=alt.Scale(domain=[2013, 2024]),
              axis=alt.Axis(title="Three-year period (final year)", format="d", tickCount=6))
    y = alt.Y("HLE:Q", scale=alt.Scale(domain=[55, 66]),
              axis=alt.Axis(title=f"Healthy life expectancy at birth, {sex.lower()}s (years)", tickCount=6))
    colour = alt.Color("area:N", scale=AREA_COLOURS, legend=None)
    line = alt.Chart(d).mark_line(strokeWidth=2).encode(x=x, y=y, color=colour)
    pts = alt.Chart(d).mark_circle(size=40, opacity=1).encode(
        x=x, y=y, color=colour,
        tooltip=[alt.Tooltip("area:N", title="Area"), alt.Tooltip("Period:N"),
                 alt.Tooltip("HLE:Q", title="HLE (years)", format=".1f")])
    last = d[d.year == 2024].copy()
    last["label"] = last.area + " " + last.HLE.map("{:.1f}".format)
    end = alt.Chart(last).mark_text(font=FONT, fontSize=11, fontWeight=600, color=INK, align="left", dx=8).encode(
        x=x, y="HLE:Q", text="label:N")
    return alt.layer(line, pts, end).properties(width=260, height=260)


chart3 = framed(
    alt.hconcat(gm_panel("Female"), gm_panel("Male"), spacing=150),
    "Healthy life expectancy in Greater Manchester has stayed around three years below England's",
    "Healthy life expectancy at birth, Greater Manchester Combined Authority and England, 2011–2013 to 2022–2024",
    "Source: ONS, Healthy life expectancy, UK: between 2011 to 2013 and 2022 to 2024 (February 2026).\n"
    "Values are three-year averages, shown at the period's final year.",
    source_width=700,
)
export(chart3, "gm_hle_over_time", gm)

# ---------------------------------------------------------------------------
# 4. Real GDP growth by ITL2 area, 2015-2024 (own calculation from ONS index)
# ---------------------------------------------------------------------------

gdp = ons_sheet("sources/12_ONS_regional_GDP_all_ITL_Sep2026.xlsx", "Table 9", "ITL")
for c in ["2015", "2024"]:
    gdp[c] = pd.to_numeric(gdp[c], errors="coerce")  # "[u]" flags -> NaN (none at ITL2)
uk_gdp = gdp[gdp.ITL == "UK"].iloc[0]
uk_growth = uk_gdp["2024"] / uk_gdp["2015"] - 1
# ONS suppresses ("[u]") 8 ITL2 areas in this release because of an error
# converting old ITL2 areas to the ITL25 ones (see the workbook's Notice sheet).
# They are dropped here, and the same codes are dropped from the productivity
# chart, whose GVA inputs go through the same conversion.
itl2_gdp = gdp[gdp.ITL == "ITL2"]
SUPPRESSED = set(itl2_gdp.loc[itl2_gdp["2015"].isna() | itl2_gdp["2024"].isna(), "ITL code"])
assert len(SUPPRESSED) == 8, sorted(SUPPRESSED)
g2 = itl2_gdp[~itl2_gdp["ITL code"].isin(SUPPRESSED)][["Region name", "2015", "2024"]].copy()
g2["growth"] = g2["2024"] / g2["2015"] - 1
is_gm = g2["Region name"] == "Greater Manchester"
g2["group"] = is_gm.map({True: "Greater Manchester", False: "Other ITL2 areas"})
g2["text"] = [f"{v:.1%}" if gm_row else "" for v, gm_row in zip(g2.growth, is_gm)]
rank_gdp = int(g2.growth.rank(ascending=False)[is_gm].iloc[0])
print(f"GDP growth: GM {g2.growth[is_gm].iloc[0]:.1%}, rank {rank_gdp} of {len(g2)}, UK {uk_growth:.1%}")

GROUPS_GM = (["Greater Manchester", "Other ITL2 areas"], [ACCENT, MUTED])
chart4 = framed(
    ranked_bars(g2, "growth", "Region name", "Cumulative real GDP growth, 2015–2024 (%)", "ITL2 area",
                ".0%", None, *GROUPS_GM, ref=uk_growth, ref_label=f"UK {uk_growth:.1%}",
                width=380, bar_height=9, legend=False),
    f"Greater Manchester had the {ORDINAL[rank_gdp]} GDP growth of {len(g2)} UK areas with published data",
    "Cumulative real GDP growth by ITL2 area, 2015–2024 (%, chained volume measures)",
    "Source: ONS, Regional economic activity by gross domestic product, UK: 1998 to 2024 (September 2026),\n"
    "Table 9; growth calculated from the chained volume index. 8 ITL2 areas in south-west England, Wales\n"
    "and Scotland are excluded: ONS suppressed them because of an error in converting to the 2025 ITL areas.",
    source_width=640,
)
export(chart4, "gm_gdp_growth", g2.drop(columns="text"))

# ---------------------------------------------------------------------------
# 5. Productivity growth by ITL2 area, 2015-2023 (own calculation from ONS index)
# ---------------------------------------------------------------------------

a5 = ons_sheet("sources/03_ONS_SRPROD01_subregional_productivity_current2025.xlsx", "A5", "ITL_level")
for c in ["Index_2015", "Index_2023"]:
    a5[c] = pd.to_numeric(a5[c])
YEARS = 2023 - 2015


def cagr(r):
    return (r["Index_2023"] / r["Index_2015"]) ** (1 / YEARS) - 1


uk_prod = cagr(a5[a5.ITL_level == "UK"].iloc[0])
p2 = a5[(a5.ITL_level == "ITL2") & ~a5.ITL_code.isin(SUPPRESSED)][["Region_name", "Index_2015", "Index_2023"]].copy()
assert len(p2) == 38, len(p2)
p2["growth"] = p2.apply(cagr, axis=1)
is_gm = p2.Region_name == "Greater Manchester"
p2["group"] = is_gm.map({True: "Greater Manchester", False: "Other ITL2 areas"})
p2["text"] = [f"{v:.1%}" if gm_row else "" for v, gm_row in zip(p2.growth, is_gm)]
rank_prod = int(p2.growth.rank(ascending=False)[is_gm].iloc[0])
print(f"Productivity growth: GM {p2.growth[is_gm].iloc[0]:.2%} a year, rank {rank_prod} of {len(p2)}, UK {uk_prod:.2%}")

chart5 = framed(
    ranked_bars(p2, "growth", "Region_name", "Average annual growth in GVA per hour worked, 2015–2023 (%)",
                "ITL2 area", ".1%", None, *GROUPS_GM, ref=uk_prod, ref_label=f"UK {uk_prod:.1%}",
                width=380, bar_height=9, legend=False),
    f"Greater Manchester had the {ORDINAL[rank_prod]} productivity growth of {len(p2)} UK areas compared",
    "Average annual growth in real GVA per hour worked by ITL2 area, 2015–2023 (%)",
    "Source: ONS, Subregional productivity, Table A5 (chained volume, unsmoothed; June 2025 edition,\n"
    "corrected 30 October 2025); average annual growth calculated from the index. Excludes the 8 ITL2\n"
    "areas ONS suppressed in its September 2026 regional GDP release (error in converting to 2025 ITL areas).",
    source_width=640,
)
export(chart5, "gm_productivity_growth", p2.drop(columns="text"))

# ---------------------------------------------------------------------------
# 6. Household income per head by region, 2024 (UK = 100)
# ---------------------------------------------------------------------------

gdhi = ons_sheet("sources/13_ONS_regional_GDHI_all_ITL_Aug2026.xlsx", "Table 4", "ITL")
gd = gdhi[gdhi.ITL == "ITL1"][["Region name", "2024"]].rename(columns={"2024": "index"}).copy()
gd["index"] = pd.to_numeric(gd["index"])
gd["group"] = gd["Region name"].isin(NORTH).map({True: "North of England", False: "Rest of the UK"})
gd["text"] = gd["index"].map("{:.1f}".format)
chart6 = framed(
    ranked_bars(gd, "index", "Region name", "GDHI per head, index (UK = 100)", "English region / UK nation",
                ".0f", [0, 150], ["North of England", "Rest of the UK"], [ACCENT, MUTED],
                ref=100, ref_label="UK = 100", width=380),
    "Household income per head is lowest in the North East",
    "Gross disposable household income (GDHI) per head, index UK = 100, 2024",
    "Source: ONS, Regional gross disposable household income, UK: 1997 to 2024 (August 2026), Table 4.",
    source_width=600,
)
export(chart6, "gdhi_by_region", gd.drop(columns="text"))
