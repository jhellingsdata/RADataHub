"""COTD variant - every July that set a new low for England, 1836 to 2026.

A record-progression staircase. Each point is a July value read off the Met Office
file that was lower than every July before it in the series. No value is calculated;
the selection is a comparison of published observations. England, not the UK.
"""
import os
import json
import altair as alt
import pandas as pd
import eco_style  # noqa: F401  - registers 'report', sets Circular Std

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()

alt.theme.enable("report")
pal = eco_style.pallete

# Fixed-width is required: whitespace parsing shifts the incomplete 2026 row and
# reports win/spr as aug/sep.
COLS = ["year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "win", "spr", "sum", "aut", "ann"]
SPECS = [(0, 4)] + [(4 + 7 * i, 11 + 7 * i) for i in range(12)] + \
        [(88 + 8 * i, 96 + 8 * i) for i in range(5)]
RAW = pd.read_fwf(os.path.join(HERE, "Rainfall_England.txt"), colspecs=SPECS,
                  skiprows=6, names=COLS, na_values=["---"])


def save(chart, stem):
    p = os.path.join(HERE, stem)
    chart.save(f"{p}.png", scale_factor=3)
    chart.save(f"{p}.svg")
    with open(f"{p}.json", "w") as fh:
        json.dump(chart.to_dict(), fh, indent=2)
    print("wrote", stem + ".{png,svg,json}")

j = RAW[["year", "jul"]].dropna().sort_values("year")
best, keep = float("inf"), []
for _, r in j.iterrows():
    if r.jul < best:
        best = r.jul
        keep.append({"year": int(r.year), "jul": float(r.jul)})
rec = pd.DataFrame(keep)
rec["is_last"] = rec.year == rec.year.max()
rec["show"] = rec.year.isin([1836, 1847, 1868, 1911, 2026])
rec["lab"] = rec.apply(lambda r: f"{r.year}|{r.jul:.1f}mm", axis=1)

# The staircase has to reach the right-hand edge, so repeat the standing record.
tail = rec.tail(1).assign(year=2044)
path = pd.concat([rec, tail], ignore_index=True)

W, H = 700, 340
xs = alt.Scale(domain=[1830, 2044], nice=False)
ys = alt.Scale(domain=[0, 92], nice=False)

# A final tick at 2025 sits a pixel left of the 2026 mark and reads as though the
# record fell in 2025, so the record year carries the last tick. Styling stays
# uniform across the axis; the theme supplies the label colour.
TICKS = [1850, 1875, 1900, 1925, 1950, 1975, 2000, 2026]

x = alt.X("year:Q", title=None, scale=xs,
          axis=alt.Axis(format="d", labelFontSize=11.5, labelPadding=8,
                        values=TICKS))
# The theme sets axisY title to None, so the title has to be passed inside
# alt.Axis to override it. Unit lives in the title, so labels stay plain.
YTITLE = "Rainfall in millimetres (mm)"

y = alt.Y("jul:Q", scale=ys,
          axis=alt.Axis(title=YTITLE, values=[0, 20, 40, 60, 80],
                        labelFontSize=11.5, labelExpr="datum.label + 'mm'"))

step = alt.Chart(path).mark_line(
    interpolate="step-after", strokeWidth=2.4, color=pal["nominal_1"],
).encode(x=x, y=y)

dots = alt.Chart(rec[~rec.is_last]).mark_point(
    filled=True, size=80, color=pal["nominal_1"],
).encode(x=x, y=y)

dot_last = alt.Chart(rec[rec.is_last]).mark_point(
    filled=True, size=80, color=pal["nominal_2"],
).encode(x=x, y=y)

labs = alt.Chart(rec[rec.show & ~rec.is_last]).mark_text(
    align="left", dx=7, dy=-20, fontSize=11.5, fontWeight=500, lineBreak="|",
    color=pal["domain"], baseline="bottom",
).encode(x=x, y=y, text="lab:N")

lab_last = alt.Chart(rec[rec.is_last]).mark_text(
    align="right", dx=-12, dy=-8, fontSize=11.5, fontWeight=600, lineBreak="|",
    color=pal["nominal_2"], baseline="bottom",
).encode(x=x, y=y, text="lab:N")

plateau = alt.Chart(pd.DataFrame({"year": [1958], "jul": [13.4]})).mark_text(
    align="center", dy=-12, fontSize=11.5, fontWeight=500,
    color=pal["domain"], opacity=0.75, baseline="bottom",
).encode(x=x, y=y, text=alt.value("The 1911 record stood until 2026"))

note = alt.Chart(pd.DataFrame({"_": [0]})).mark_text(
    align="left", dx=-46, dy=46, fontSize=10, lineBreak="|",
    color=pal["domain"], opacity=0.65,
).encode(x=alt.value(0), y=alt.value(H), text=alt.value(
    "Source: Met Office, monthly total precipitation for England."))

chart = alt.layer(step, dots, dot_last, labs, lab_last, plateau, note).properties(
    width=W, height=H,
    title=alt.TitleParams(
        "England has just recorded its driest July on record",
        subtitle=["Total July rainfall, 1836 to 2026"],
        anchor="start", fontSize=19, fontWeight=600, color=pal["domain"],
        subtitleFontSize=12.5, subtitleColor="rgba(18, 43, 57, 0.7)", offset=20, dy=-6),
).configure_view(stroke=None, strokeWidth=0)

save(chart, "chart_july_records")
