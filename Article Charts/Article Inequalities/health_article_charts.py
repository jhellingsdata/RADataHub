"""Charts for the health-inequalities article, in the eco_style "report" theme.

Only the charts whose source data are in sources/ and match the article text.

  1  hle_by_deprivation_decile
       Healthy life expectancy at birth by IMD decile, England, 2022-2024.
       sources/01_ONS_HLE_by_deprivation_decile_England_timeseries.xlsx,
       sheet 4 (header row 6: Period, IMD decile, Sex, Sex code, Age group,
       Age code, HLE, LCI, UCI, Proportion (%)). Age group "<1" = at birth.
  2  health_inactivity_by_region
       Economic inactivity due to ill health, nine English regions.
       sources/02_HealthEquityNorth_HealthForWealth2025.pdf, Figure 25
       (values printed on the chart, transcribed below).
  3  ill_health_onset_north_vs_rest
       Effect of an onset of ill health on staying employed and on monthly
       pay: England, the North, rest of England.
       sources/02_HealthEquityNorth_HealthForWealth2025.pdf, Figures 22 and
       24 (values printed on the charts, transcribed below).

Every chart is written to outputs/health_article/ as .png and .vl.json, and
its data as .csv.
No titles or source lines on the charts: those go in the article caption.
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
NORTH = P["nominal_1"]  # eco_style main colour #179fdb (first colour of the report theme)


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
    alt.themes.register("report_health_article", report_local)
    alt.themes.enable("report_health_article")
except AttributeError:  # Altair 6 API
    alt.theme.register("report_health_article", enable=True)(report_local)


def export(chart, name):
    """PNG (2.5x) and Vega-Lite JSON."""
    stem = OUT / name
    stem.with_suffix(".png").write_bytes(vlc.vegalite_to_png(chart.to_json(), scale=2.5))
    stem.with_suffix(".vl.json").write_text(json.dumps(chart.to_dict(), separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {stem}.*")


# ---------------------------------------------------------------------------
# 1. Healthy life expectancy by deprivation decile (ONS, 15 April 2026)
# ---------------------------------------------------------------------------

raw = pd.read_excel("sources/01_ONS_HLE_by_deprivation_decile_England_timeseries.xlsx", "4", header=6)
hle = raw[(raw["Period"] == "2022 to 2024") & (raw["Age group"] == "<1")][
    ["IMD decile", "Sex", "HLE", "LCI", "UCI"]].rename(columns={"IMD decile": "decile"})
hle["decile"] = hle.decile.astype(int)
assert len(hle) == 20, len(hle)
hle.to_csv(DATA_OUT / "hle_by_deprivation_decile.csv", index=False)

SEX_DOMAIN = ["Male", "Female"]
SEX_RANGE = [P["nominal_1"], P["nominal_2"]]
x_dec = alt.X("decile:O", axis=alt.Axis(
    title="Deprivation decile (1 = most deprived, 10 = least deprived)"))
y_hle = alt.Y("HLE:Q", scale=alt.Scale(domain=[45, 72]),
              axis=alt.Axis(title="Healthy life expectancy at birth (years)", tickCount=6, titleFont=FONT))
colour = alt.Color("Sex:N", scale=alt.Scale(domain=SEX_DOMAIN, range=SEX_RANGE), legend=None)
tooltip = [alt.Tooltip("Sex:N"), alt.Tooltip("decile:O", title="IMD decile"),
           alt.Tooltip("HLE:Q", title="HLE (years)", format=".1f"),
           alt.Tooltip("LCI:Q", title="95% CI lower", format=".1f"),
           alt.Tooltip("UCI:Q", title="95% CI upper", format=".1f")]

base = alt.Chart(hle).encode(x=x_dec, y=y_hle, color=colour)
lines = base.mark_line(strokeWidth=2)
dots = base.mark_circle(size=70, opacity=1).encode(tooltip=tooltip)

# Start values on decile 1; series name + value at the last observation
# (decile 10) replaces the legend.
first = hle[hle.decile == 1].copy()
first["label"] = first.HLE.map("{:.1f}".format)
start_labels = [
    alt.Chart(first[first.Sex == s]).mark_text(
        font=FONT, fontSize=11, fontWeight=600, color=INK, dy=dy,
    ).encode(x=x_dec, y="HLE:Q", text="label:N")
    for s, dy in [("Male", -12), ("Female", 14)]
]
last = hle[hle.decile == 10].copy()
last["label"] = last.Sex + " " + last.HLE.map("{:.1f}".format)
end_labels = [
    alt.Chart(last[last.Sex == s]).mark_text(
        font=FONT, fontSize=11, fontWeight=600, color=INK, align="left", dx=10, dy=dy,
    ).encode(x=x_dec, y="HLE:Q", text="label:N")
    for s, dy in [("Male", -6), ("Female", 6)]
]

chart1 = framed(
    alt.layer(lines, dots, *start_labels, *end_labels).properties(width=560, height=340),
    "People in England's most deprived areas spend around 20 fewer years in good health",
    "Healthy life expectancy at birth by area deprivation decile (IMD 2019), England, 2022–2024",
    "Source: ONS, Healthy life expectancy by national area deprivation, England (April 2026).",
)
export(chart1, "hle_by_deprivation_decile")

# ---------------------------------------------------------------------------
# 2. Economic inactivity due to ill health, English regions
#    Health for Wealth 2025, Figure 25 (% of working-age population)
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
inact.to_csv(DATA_OUT / "health_inactivity_by_region.csv", index=False)

y_reg = alt.Y("region:N", sort=inact.sort_values("rate", ascending=False).region.tolist(), axis=alt.Axis(title="Region", labelPadding=8))
x_rate = alt.X("share:Q", scale=alt.Scale(domain=[0, 0.105]),
               axis=alt.Axis(title="Economically inactive due to ill health (% of working-age population)",
                             format=".0%", tickCount=6))
bars = alt.Chart(inact).mark_bar(height=18, cornerRadiusEnd=4).encode(
    y=y_reg, x=x_rate,
    color=alt.Color("group:N", scale=alt.Scale(domain=["North of England", "Rest of England"],
                                               range=[NORTH, MUTED])),
    tooltip=[alt.Tooltip("region:N", title="Region"),
             alt.Tooltip("share:Q", title="Inactive due to ill health", format=".1%")],
)
bar_labels = alt.Chart(inact).mark_text(
    font=FONT, fontSize=11, color=INK, align="left", dx=5,
).encode(y=y_reg, x=x_rate, text="label:N")

chart2 = framed(
    alt.layer(bars, bar_labels).properties(width=420, height=270),
    "Health-related economic inactivity is highest in the North of England",
    "Share of the working-age population economically inactive due to ill health, English regions, 2024",
    "Source: Simpson et al. (2025), Health for Wealth 2025, Figure 25; based on ONS Annual Population Survey.",
)
export(chart2, "health_inactivity_by_region")

# ---------------------------------------------------------------------------
# 3. After an onset of ill health: England, the North, rest of England
#    Health for Wealth 2025, Figure 22 (probability of staying employed,
#    percentage points) and Figure 24 (relative monthly pay, %).
#    The report marks every estimate significant (**) except the
#    rest-of-England pay effect (-2.4).
# ---------------------------------------------------------------------------

AREAS = ["England", "North", "Rest of England"]
M_EMP = "Change in probability of staying in work (pp)"
M_PAY = "Change in monthly pay (%)"
onset = pd.DataFrame({
    "measure": [M_EMP] * 3 + [M_PAY] * 3,
    "area": AREAS * 2,
    "effect": [-1.45, -2.4, -1.16, -2.3, -6.6, -2.4],
    "significant": [True, True, True, True, True, False],
})
# Labels exactly as printed in the report (Figure 22 uses two decimals).
onset["label"] = ["−1.45 pp", "−2.4 pp", "−1.16 pp", "−2.3%", "−6.6%", "−2.4% (n.s.)"]
# Pay effects as fractions so that axis can use a % format.
onset["value"] = onset.effect.where(onset.measure == M_EMP, onset.effect / 100)
onset.to_csv(DATA_OUT / "ill_health_onset_north_vs_rest.csv", index=False)
# North in the report accent; the rest (incl. the n.s. bar, flagged by its label) in report grey.
onset["colour"] = [NORTH if a == "North" else MUTED
                   for a, sig in zip(onset.area, onset.significant)]


def onset_panel(measure, domain_min, axis_format):
    d = onset[onset.measure == measure]
    x = alt.X("area:N", sort=AREAS, axis=alt.Axis(
        title="Area"))
    y = alt.Y("value:Q", scale=alt.Scale(domain=[domain_min, 0]),
              axis=alt.Axis(title=measure, tickCount=4, **axis_format))
    bar = alt.Chart(d).mark_bar(width=46, cornerRadiusEnd=4).encode(
        x=x, y=y,
        color=alt.Color("colour:N", scale=None),
        tooltip=[alt.Tooltip("area:N", title="Area"),
                 alt.Tooltip("label:N", title=measure),
                 alt.Tooltip("significant:N", title="Statistically significant")],
    )
    txt = alt.Chart(d).mark_text(font=FONT, fontSize=11, fontWeight=600, color=INK,
                                 baseline="top", dy=5).encode(x=x, y=y, text="label:N")
    zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color=INK, strokeWidth=1).encode(y="z:Q")
    return alt.layer(bar, txt, zero).properties(width=240, height=220)


chart3 = framed(
    alt.hconcat(
        onset_panel(M_EMP, -3, dict(labelExpr="replace(format(datum.value, '.0f'), '-', '−') + ' pp'")),
        onset_panel(M_PAY, -0.08, dict(format=".0%")),
        spacing=60,
    ).resolve_scale(y="independent"),
    "Falling ill costs workers in the North of England more",
    "Estimated effect of an onset of ill health on staying in work and on monthly pay, 2009–2023",
    "Source: Simpson et al. (2025), Health for Wealth 2025, Figures 22 and 24; Understanding Society (UKHLS).\n"
    "pp = percentage points. n.s. = not statistically significant.",
    source_width=560,
)
export(chart3, "ill_health_onset_north_vs_rest")
