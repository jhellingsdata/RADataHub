"""
Chart of the Day — UK youth unemployment (16-24, not in full-time education)
Source: ONS, Labour Force Survey, Table A06 SA (May 2026 release), series AIXT.

Production script. Run locally where Circular Std is installed.
The `report` theme in eco_style.py supplies all fonts and colours; nothing
font- or colour-related is hardcoded here.
"""

import datetime
import pandas as pd
import altair as alt
import vl_convert as vlc

import eco_style  # registers the 'report' theme and exposes `pallete`
from eco_style import pallete

alt.theme.enable("report")

# ---------------------------------------------------------------- load data
# ---------------------------------------------------------------- load data
XLS = "/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/youth-unemployment/a06samay2026.xls"  # local path; ONS A06 SA workbook
RATE_COL = 62  # AIXT: 16-24 not in full-time education, unemployed, rate (%)

raw = pd.read_excel(XLS, sheet_name="People", engine="xlrd", header=None)
periods = raw.iloc[9:, 0].astype(str).str.strip()
rates = pd.to_numeric(raw.iloc[9:, RATE_COL], errors="coerce")

df = pd.DataFrame({"period": periods.values, "rate": rates.values}).dropna()
# ONS workbook contains a typo in one label
df["period"] = df["period"].replace({"Jan-Mar 20194": "Jan-Mar 2019"})

_MON = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

def _end_date(label):
    p = label.replace("-", " ").split()
    return datetime.date(int(p[2]), _MON[p[1]], 1)


df["date"] = pd.to_datetime(df["period"].apply(_end_date))
df = df.reset_index(drop=True)

latest = df.iloc[-1]
latest_label = f"{latest['rate']:.1f}%"
# "Jan-Mar 2026" -> "Jan–Mar 2026" with an en-dash between the months
_ENDASH = "\u2013"
_p = latest["period"].split()
_months = _p[0].replace("-", _ENDASH)
latest_period = f"{_months} {_p[1]}"

# ---------------------------------------------------------------- main chart
WIDTH = 480
HEIGHT = 300

line = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5, color=pallete["accent"])
    .encode(
        x=alt.X(
            "date:T",
            axis=alt.Axis(format="%Y", tickCount=8),
            scale=alt.Scale(nice=False, padding=6),
        ),
        y=alt.Y(
            "rate:Q",
            scale=alt.Scale(domain=[0, 22]),
            axis=alt.Axis(
                labelExpr="datum.value + '%'",
                values=[0, 5, 10, 15, 20],
            ),
        ),
    )
)

# end-point marker + label so the current value reads in under 10 seconds
end_dot = (
    alt.Chart(df.iloc[[-1]])
    .mark_circle(size=70, color=pallete["accent"])
    .encode(x="date:T", y="rate:Q")
)

end_label = (
    alt.Chart(df.iloc[[-1]])
    .mark_text(
        align="right", dx=-8, dy=-14, fontSize=13, fontWeight="bold",
        lineHeight=13, color=pallete["accent"],
    )
    .encode(
        x="date:T", y="rate:Q",
        text=alt.value([latest_label, latest_period]),
    )
)

main = (
    (line + end_dot + end_label)
    .properties(
        width=WIDTH,
        height=HEIGHT,
        title=alt.TitleParams(
            text="Youth unemployment is back at its highest since 2014",
            subtitle=[
                "Unemployment rate, 16- to 24-year-olds not in full-time "
                "education, UK, seasonally adjusted (%)",
            ],
            anchor="start",
            fontSize=16,
            subtitleFontSize=12,
            subtitleColor=pallete["Deemphasize_Other"],
            offset=14,
        ),
    )
)

# ---------------------------------------------------------------- source line
source = (
    alt.Chart(df.iloc[[0]])
    .mark_text(
        align="left", color=pallete["Deemphasize_Other"], fontSize=10,
    )
    .encode(
        x=alt.value(0),
        y=alt.value(0),
        text=alt.value(
            "Source: ONS, Labour Force Survey, May 2026."
        ),
    )
    .properties(width=WIDTH, height=12)
)

chart = (
    alt.vconcat(main, source, spacing=5)
    .configure_view(strokeWidth=0)
)

chart

# ---------------------------------------------------------------- export

png = vlc.vegalite_to_png(chart.to_json(), scale=3)
with open("youth_unemployment.png", "wb") as f:
    f.write(png)

svg = vlc.vegalite_to_svg(chart.to_json())
with open("youth_unemployment.svg", "w") as f:
    f.write(svg)

print("wrote youth_unemployment.{json,png,svg}; latest =", latest_label)
