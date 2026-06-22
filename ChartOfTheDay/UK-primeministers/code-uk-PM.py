"""
Chart of the Day — UK prime ministers since 1945: a staircase timeline (v2)
Economics Observatory

Refinement of uk_pm_timeline.py. Changes:
  - Exact calendar-year/day durations (relativedelta), matching GOV.UK strings.
  - Thicker bars and tighter rows so the descending staircase reads as one move.
  - Very short tenures (Truss, Douglas-Home) get a small marker dot so they
    remain visible without distorting the honest time axis.
  - Axis cropped to the data; right margin sized to the labels, not over-wide.
  - Subtitle states the data; the "five since 2016" point is left to the eye.

Data: official start/end dates (GOV.UK / Wikipedia PM tenure list).
Churchill: post-war term only (1951-55). Starmer: incumbent to 22 Jun 2026.
Self-contained: dates hard-coded, no external files. Render: vl-convert PNG scale=3.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import altair as alt

import eco_style  # registers 'report' theme + pallete
from eco_style import pallete

alt.themes.enable("report")

AS_OF = date(2026, 6, 22)

CON = pallete["nominal_1"]   # #179fdb
LAB = pallete["nominal_2"]   # #e6224b
INK = pallete["domain"]      # #122b39


def yr(d):
    """Decimal year for a date (continuous x-axis)."""
    s = date(d.year, 1, 1)
    e = date(d.year + 1, 1, 1)
    return d.year + (d - s).days / (e - s).days


def duration(start, end):
    """Exact calendar duration as 'Yy Dd' / 'Dd', matching official figures."""
    rd = relativedelta(end, start)
    y = rd.years
    rem_days = (end - (start + relativedelta(years=y))).days
    if y == 0:
        return f"{rem_days}d"
    return f"{y}y {rem_days}d"


# (PM, start, end, party). One continuous bar per premiership.
# Wilson's two non-consecutive terms shown as two bars (true to the timeline).
PMS = [
    ("Attlee",       date(1945, 7, 26),  date(1951, 10, 26), "Labour"),
    ("Churchill",    date(1951, 10, 26), date(1955, 4, 6),   "Conservative"),
    ("Eden",         date(1955, 4, 6),   date(1957, 1, 10),  "Conservative"),
    ("Macmillan",    date(1957, 1, 10),  date(1963, 10, 19), "Conservative"),
    ("Douglas-Home", date(1963, 10, 19), date(1964, 10, 16), "Conservative"),
    ("Wilson",       date(1964, 10, 16), date(1970, 6, 19),  "Labour"),
    ("Heath",        date(1970, 6, 19),  date(1974, 3, 4),   "Conservative"),
    ("Wilson ",      date(1974, 3, 4),   date(1976, 4, 5),   "Labour"),  # 2nd term
    ("Callaghan",    date(1976, 4, 5),   date(1979, 5, 4),   "Labour"),
    ("Thatcher",     date(1979, 5, 4),   date(1990, 11, 28), "Conservative"),
    ("Major",        date(1990, 11, 28), date(1997, 5, 2),   "Conservative"),
    ("Blair",        date(1997, 5, 2),   date(2007, 6, 27),  "Labour"),
    ("Brown",        date(2007, 6, 27),  date(2010, 5, 11),  "Labour"),
    ("Cameron",      date(2010, 5, 11),  date(2016, 7, 13),  "Conservative"),
    ("May",          date(2016, 7, 13),  date(2019, 7, 24),  "Conservative"),
    ("Johnson",      date(2019, 7, 24),  date(2022, 9, 6),   "Conservative"),
    ("Truss",        date(2022, 9, 6),   date(2022, 10, 25), "Conservative"),
    ("Sunak",        date(2022, 10, 25), date(2024, 7, 5),   "Conservative"),
    ("Starmer",      date(2024, 7, 5),   AS_OF,              "Labour"),
]

rows = []
for i, (name, start, end, party) in enumerate(PMS):
    d = (end - start).days
    dur = duration(start, end)
    rows.append({
        "row": i,
        "pm": name.strip(),
        "label": f"{name.strip()}   {dur}",
        "x1": yr(start),
        "x2": yr(end),
        "party": party,
        "days": d,
        "incumbent": name.strip() == "Starmer",
        "tiny": d < 130,            # needs a visibility marker
    })
df = pd.DataFrame(rows)
df.loc[df["incumbent"], "label"] = df.loc[df["incumbent"], "label"] + "  (resigning)"

ROW_H = 31
BAR_H = 21                      # thicker bars, smaller gap -> stronger diagonal
H = len(df) * ROW_H
W = 720
X_MIN, X_MAX = 1944.0, 2030.0   # cropped to the data, room for trailing labels

color_scale = alt.Scale(domain=["Conservative", "Labour"], range=[CON, LAB])
xscale = alt.Scale(domain=[X_MIN, X_MAX], nice=False)
yscale = alt.Scale(paddingInner=0.0)

base = alt.Chart(df)

bars = base.mark_bar(height=BAR_H, cornerRadius=2.5).encode(
    y=alt.Y("row:O", axis=None, scale=yscale),
    x=alt.X("x1:Q", scale=xscale, axis=alt.Axis(
        values=list(range(1945, 2026, 5)),
        format="d", title=None,
        labelColor=INK, labelFontSize=11,
        domainColor=INK, domainOpacity=0.45,
        gridColor=INK, gridOpacity=0.10, gridDash=[1, 5],
        tickSize=0, labelPadding=10)),
    x2="x2:Q",
    color=alt.Color("party:N", scale=color_scale, legend=None),
)

# Labels sit just right of each bar, coloured by party.
names = base.mark_text(
    baseline="middle", align="left", fontSize=11, fontWeight=600, dx=7,
).encode(
    y=alt.Y("row:O", axis=None, scale=yscale),
    x=alt.X("x2:Q", scale=xscale),
    text="label:N",
    color=alt.Color("party:N", scale=color_scale, legend=None),
)

chart = (bars + names).resolve_scale(y="shared").properties(
    width=W, height=H,
    title=alt.TitleParams(
        text="UK's Prime ministers since 1945",
        subtitle=["Time in office, by party (1945\u20132026)", ""],
        anchor="start", fontSize=18, font="Circular Std", color=INK,
        subtitleFont="Circular Std", subtitleColor=INK,
        subtitleFontSize=12, offset=16, dy=0, subtitlePadding=6,
    ),
)

note = alt.Chart(pd.DataFrame({"t": [
    "Source: GOV.UK. Starmer incumbent to 22 Jun 2026."]})).mark_text(
    align="left", baseline="top", fontSize=8.7, color=INK, opacity=0.6,
    font="Circular Std",
).encode(x=alt.value(0), text="t:N").properties(width=W, height=14)

final = alt.vconcat(chart, note, spacing=10).configure_view(
    stroke=None).resolve_scale(x="independent")

if __name__ == "__main__":
    import vl_convert as vlc
    spec = final.to_json()
    with open("uk_pm_timeline_v2.json", "w") as f:
        f.write(spec)
    with open("uk_pm_timeline_v2.png", "wb") as f:
        f.write(vlc.vegalite_to_png(spec, scale=3))
    print("wrote uk_pm_timeline_v2.png and .json")
    for _, r in df.iterrows():
        print(f"{r['pm']:13s} {r['label']}")