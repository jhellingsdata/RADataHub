"""
Denmark's 20 highest net fiscal contributors by country of origin, 2017 vs 2019

Columns: country, residents, DKK per person (dots).

Source: Finansministeriet (2023), "Indvandreres nettobidrag til de offentlige
finanser i 2019 - revideret version (september 2023)", Table B2, pp. 57-58.
Immigrants and their descendants together.

Requires the FULL 37-row Table B2 extract in dk_country_netcontribution.csv.
The footnote counts the origin groups this top-20 cut removes, so a truncated
CSV cannot produce it. The script fails loudly rather than guessing.
"""

import os
import sys
import json

# ---------------------------------------------------------------- paths
# Repo layout:
#   taxes contribution/
#       eco_style.py            <- shared, one level up
#       denmark/                <- this script, the CSV, and the outputs
#       uk tax contributors/
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Positron / Jupyter cells run without __file__ defined
    HERE = ("/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/"
            "taxes contribution/denmark")

PROJECT = os.path.dirname(HERE)          # 'taxes contribution', holds eco_style.py
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import altair as alt                     # noqa: E402
import pandas as pd                      # noqa: E402
import eco_style                         # noqa: E402  registers the 'report' theme
from eco_style import pallete            # noqa: E402

DATA = os.path.join(HERE, "dk_country_netcontribution.csv")
OUT = HERE                               # write PNG/SVG/JSON beside the script

alt.theme.enable("report")


def ink(alpha=1.0, base="domain"):
    """Tint a palette colour, so every grey stays tied to eco_style."""
    value = pallete[base]
    if value.startswith("rgb"):
        return value
    h = value.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if alpha >= 1:
        return "rgb({}, {}, {})".format(r, g, b)
    return "rgba({}, {}, {}, {})".format(r, g, b, alpha)


INK = pallete["domain"]
MUTED = ink(0.55)
GREY = ink(0.30)
DOT17 = ink(0.42)
DOT19 = pallete["nominal_1"]

TOP_N = 20
HIGHLIGHT = "United Kingdom"

# ---------------------------------------------------------------- data
full = pd.read_csv(DATA)
d = full.nlargest(TOP_N, "v2019").sort_values("v2019", ascending=False).reset_index(drop=True)

excluded = full[~full["country"].isin(d["country"])]
if excluded.empty:
    raise SystemExit(
        "dk_country_netcontribution.csv holds only the {} plotted rows. The footnote "
        "counts the groups this cut removes, so it needs the full 37-row Table B2 "
        "extract. Restore the complete CSV.".format(len(full)))

N_OUT = len(excluded)
EXCL_HI = int(excluded["v2019"].max())
EXCL_LO = int(excluded["v2019"].min())

d["row"] = d.index.astype(float)
d["res_lab"] = d["n2019_k"].map(lambda n: "{:,.0f}".format(n * 1000))

d_uk = d[d["country"] == HIGHLIGHT]
d_rest = d[d["country"] != HIGHLIGHT]
UK_ROW = float(d_uk["row"].iloc[0])

N = len(d)
H = 440
HEAD_Y = -1.05
YS = alt.Scale(domain=[N + 0.35, -1.55], nice=False)
y_q = alt.Y("row:Q", scale=YS, axis=None)

X_DOM = [-30, 116]
XS = alt.Scale(domain=X_DOM, nice=False)


def band(w):
    return alt.Chart(pd.DataFrame({"y": [UK_ROW - 0.5], "y2": [UK_ROW + 0.5]})).mark_rect(
        fill=DOT19, fillOpacity=0.10, stroke=None
    ).encode(y=alt.Y("y:Q", scale=YS, axis=None), y2=alt.Y2("y2:Q"),
             x=alt.value(0), x2=alt.value(w))


def head(txt, align="left", x=0):
    return alt.Chart(pd.DataFrame({"row": [HEAD_Y], "t": [txt]})).mark_text(
        align=align, baseline="middle", fontSize=10, fontWeight=700, color=MUTED
    ).encode(x=alt.value(x), y=y_q, text="t:N")


def rule_at(w, r, op=0.18):
    return alt.Chart(pd.DataFrame({"row": [r]})).mark_rule(
        color=INK, opacity=op, strokeWidth=1
    ).encode(y=y_q, x=alt.value(0), x2=alt.value(w))


def text_col(w, field, header, align="left", size=12, weight=400, color=INK):
    x = 0 if align == "left" else w
    return alt.layer(
        band(w), rule_at(w, HEAD_Y + 0.40), head(header, align, x),
        alt.Chart(d_rest).mark_text(align=align, baseline="middle", fontSize=size,
                                    fontWeight=weight, color=color).encode(
            x=alt.value(x), y=y_q, text=field + ":N"),
        alt.Chart(d_uk).mark_text(align=align, baseline="middle", fontSize=size + 0.5,
                                  fontWeight=700, color=INK).encode(
            x=alt.value(x), y=y_q, text=field + ":N"),
    ).properties(width=w, height=H)


LW, RW, PW = 190, 68, 404

labels_col = text_col(LW, "country", "COUNTRY OF ORIGIN")
res_col = text_col(RW, "res_lab", "RESIDENTS", align="right", size=11, color=MUTED)

# ---------------------------------------------------------------- dot panel
TICKS = [-20, 0, 50, 100]
tk = pd.DataFrame({"x": [float(t) for t in TICKS]})
tk["lab"] = [("\u2212" if t < 0 else ("+" if t > 0 else ""))
             + "{:,.0f}".format(abs(t) * 1000) for t in TICKS]
GT, GB = 24, H - 20

grid = alt.Chart(tk[tk["x"] != 0]).mark_rule(
    color=INK, opacity=0.28, strokeWidth=1, strokeDash=[1, 5]
).encode(x=alt.X("x:Q", scale=XS, axis=None), y=alt.value(GT), y2=alt.value(GB))
zero = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(
    color=INK, strokeWidth=1, opacity=0.55
).encode(x=alt.X("x:Q", scale=XS, axis=None), y=alt.value(GT), y2=alt.value(GB))


def ticks_at(y_px):
    return alt.Chart(tk).mark_text(align="center", baseline="bottom", fontSize=10,
                                   color=MUTED).encode(
        x=alt.X("x:Q", scale=XS, axis=None), y=alt.value(y_px), text="lab:N")


connector = alt.Chart(d).mark_rule(color=GREY, strokeWidth=1.8).encode(
    x=alt.X("v2017:Q", scale=XS, axis=None), x2=alt.X2("v2019:Q"), y=y_q)
dot17 = alt.Chart(d).mark_point(filled=True, size=34, opacity=1, color=DOT17).encode(
    x=alt.X("v2017:Q", scale=XS, axis=None), y=y_q)
dot19 = alt.Chart(d).mark_point(filled=True, size=92, opacity=1, color=DOT19).encode(
    x=alt.X("v2019:Q", scale=XS, axis=None), y=y_q)
dot19_uk = alt.Chart(d_uk).mark_point(
    filled=True, size=140, opacity=1, color=DOT19, stroke=INK, strokeWidth=1.6
).encode(x=alt.X("v2019:Q", scale=XS, axis=None), y=y_q)

dot_col = alt.layer(
    band(PW), rule_at(PW, HEAD_Y + 0.40),
    ticks_at(15), ticks_at(H - 5),
    grid, zero, connector, dot17, dot19, dot19_uk,
).properties(width=PW, height=H)

row = alt.hconcat(labels_col, res_col, dot_col, spacing=14)
TW = LW + RW + PW + 14 * 2

# ---------------------------------------------------------------- legend
lg = pd.DataFrame({"x": [0.0, 66.0], "lab": ["2017", "2019"],
                   "sz": [34, 92], "c": [DOT17, DOT19]})
LXS = alt.Scale(domain=[0, TW], nice=False)
legend = alt.layer(
    alt.Chart(lg).mark_point(filled=True, opacity=1).encode(
        x=alt.X("x:Q", scale=LXS, axis=None), y=alt.value(10),
        size=alt.Size("sz:Q", scale=None), color=alt.Color("c:N", scale=None)),
    alt.Chart(lg).mark_text(align="left", dx=12, baseline="middle", fontSize=11,
                            color=MUTED).encode(
        x=alt.X("x:Q", scale=LXS, axis=None), y=alt.value(10), text="lab:N"),
).properties(width=TW, height=20)


def text_block(txt, size, weight, color, height):
    return alt.Chart(pd.DataFrame({"t": [txt]})).mark_text(
        align="left", baseline="top", fontSize=size, fontWeight=weight,
        color=color, lineBreak="\n",
    ).encode(x=alt.value(0), y=alt.value(0), text="t:N").properties(
        width=TW, height=height)


title = text_block("British migrants are Denmark's second-highest net contributors",
                   19, 700, INK, 26)
sub = text_block("Net fiscal contribution per person, DKK, 20 highest-ranked "
                 "countries of origin, 2017 and 2019",
                 12.5, 400, ink(0.75), 22)
note = text_block(
    "Source: Danish Ministry of Finance, September 2023 revision.".format(
        N_OUT, abs(EXCL_HI) * 1000, abs(EXCL_LO) * 1000),
    9.5, 400, ink(0.6), 30)

chart = (
    alt.vconcat(title, sub, legend, row, note, spacing=11)
    .configure_view(strokeWidth=0, stroke=None)
    .configure_concat(spacing=11)
    .properties(padding={"left": 24, "right": 24, "top": 22, "bottom": 16},
                background="white")
)

chart  # inline preview in Positron

stem = "dk_top20_dots"
chart.save(os.path.join(OUT, stem + ".png"), scale_factor=3)
chart.save(os.path.join(OUT, stem + ".svg"))
with open(os.path.join(OUT, stem + ".json"), "w") as f:
    json.dump(json.loads(chart.to_json()), f, indent=2)
print("wrote", stem, "->", OUT)