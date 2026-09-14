"""


Automotive Fuel Spending Insights (ONS real-time indicators, 4 Sep 2026)
Source series: ONS calculations and DESNZ.

Every series in this workbook is a year-on-year index: 100 = the equivalent week
in the previous year. So 123 means "23% higher than the same week last year",
not "23% above some fixed base". Every title and axis label below says so.

  F1  Pump prices vs fuel bought per transaction, weekly
  F2  Price against quantity, week by week (scatter)
  F3  Pump price index by week of year, one line per year
  F4  Fuel bought per transaction, deviation from a year earlier (diverging area)
"""

import pandas as pd
import altair as alt

import eco_style
from eco_style import pallete
from eco_charts import (WIDTH, HEIGHT, LABEL_SIZE, LABEL_WEIGHT, MINUS,
                        figure, yq, xq, xt, hline, annotate, end_labels,
                        signed, save, read_ons)

try:
    alt.theme.enable("report")
except Exception:
    alt.themes.enable("report")

F = "data/automotivefuelinsightsdataset040926.xlsx"
SRC = ("Source: ONS real-time indicators, ONS calculations and Department for Energy "
       "Security and Net Zero, published 4 September 2026")
BASE = "Note: 100 = the equivalent week in the previous year. Data are not seasonally adjusted."


def weekly():
    w = read_ons(F, "1.Weekly Fuel Insights")
    w.columns = ["date", "price", "qty", "sales"]
    return w


# ------------------------------------------------------------------ F1
def f1():
    w = weekly()
    d = w[["date", "price", "qty"]].melt("date", var_name="k", value_name="v")
    names = {"price": "Pump price", "qty": "Fuel per transaction"}
    d["series"] = d.k.map(names)

    scale = alt.Scale(domain=list(names.values()),
                      range=[pallete["nominal_2"], pallete["nominal_1"]])
    X = xt(values=[f"{y}-01-01" for y in range(2021, 2027)])
    Y = yq("v:Q", "Index, 100 = same week a year earlier",
           values=[80, 100, 120, 140], domain=[72, 150])

    lines = alt.Chart(d).mark_line(strokeWidth=2).encode(
        x=X, y=Y, color=alt.Color("series:N", scale=scale, legend=None))
    labs = end_labels(d[d.date == d.date.max()], X, Y, "series:N", scale=scale)

    ann = pd.DataFrame({
        "date": [pd.Timestamp("2022-08-20"), pd.Timestamp("2023-11-01"),
                 pd.Timestamp("2025-09-01")],
        "v": [143, 82, 133],
        "t": ["2022 oil shock", "Prices fell back through 2023", "Prices climbing again"]})

    plot = (hline(100, Y, dash=(4, 3), opacity=0.5)
            + lines + labs + annotate(ann, X, Y)
            ).properties(width=WIDTH - 90, height=HEIGHT - 105)

    return figure(
        "As pump prices climb, drivers are putting less in the tank",
        ["UK average pump price and estimated fuel demanded per transaction, weekly",
         "January 2021 to 23 August 2026"],
        plot,
        [SRC, BASE])




# ------------------------------------------------------------------ F2
def f2():
    w = weekly().dropna(subset=["price", "qty"])
    w["yr"] = w.date.dt.year.astype(str)
    w["grp"] = w.yr.where(w.yr.isin(["2022", "2026"]), "2021, 2023\u20132025")

    order = ["2021, 2023\u20132025", "2022", "2026"]
    scale = alt.Scale(domain=order,
                      range=[pallete["Other_3"], pallete["nominal_5"], pallete["nominal_2"]])
    X = xq("price:Q", "Pump price index", values=[80, 100, 120, 140], domain=[70, 152])
    Y = yq("qty:Q", "Fuel per transaction, index", values=[80, 90, 100, 110],
           domain=[78, 116])

    pts = alt.Chart(w).mark_point(filled=True, size=38, opacity=0.85).encode(
        x=X, y=Y, color=alt.Color("grp:N", scale=scale, legend=None, sort=order),
        order=alt.Order("grp:N", sort="ascending"))

    guide = (hline(100, Y, dash=(3, 3), opacity=0.35))
    ann = pd.DataFrame({
        "price": [137, 78, 127],
        "qty": [104, 114, 87],
        "t": ["2022", "2021 and 2023\u20132025", "2026"]})
    lbl = alt.Chart(ann).mark_text(align="left", fontSize=11.5, fontWeight=700).encode(
        x=X, y=Y, text="t:N",
        color=alt.Color("t:N", legend=None,
                        scale=alt.Scale(domain=["2022", "2021 and 2023\u20132025", "2026"],
                                        range=[pallete["nominal_5"],
                                               pallete["Deemphasize_Other"],
                                               pallete["nominal_2"]])))
    note = pd.DataFrame({"price": [73], "qty": [82], "t": ["Each dot is one week"]})

    plot = (guide + pts + lbl + annotate(note, X, Y)
            ).properties(width=WIDTH - 90, height=HEIGHT - 105)

    return figure(
        "Higher pump prices go with smaller fill-ups, week after week",
        ["Estimated fuel demanded per transaction against the average UK pump price",
         "Weekly, January 2021 to 23 August 2026"],
        plot,
        [SRC, BASE])


# ------------------------------------------------------------------ F3
def f3():
    w = weekly()
    iso = w.date.dt.isocalendar()          # ISO year, not calendar year: a week-ending
    w["yr"] = iso.year.astype(str)          # date in early January belongs to the old year
    w["week"] = iso.week.astype(int)
    w = w[(w.week <= 52) & (w.yr != "2020")]

    order = ["2021", "2022", "2023", "2024", "2025", "2026"]
    scale = alt.Scale(domain=order,
                      range=[pallete["Other_3"], pallete["nominal_5"], pallete["Other_3"],
                             pallete["Other_3"], pallete["Other_3"], pallete["nominal_2"]])
    X = xq("week:Q", "Week of year", values=[1, 10, 20, 30, 40, 52], domain=[1, 52])
    Y = yq("price:Q", "Index, 100 = same week a year earlier",
           values=[80, 100, 120, 140], domain=[72, 150])

    lines = alt.Chart(w).mark_line(strokeWidth=2).encode(
        x=X, y=Y, color=alt.Color("yr:N", scale=scale, legend=None, sort=order),
        detail="yr:N")
    tips = w.sort_values("week").groupby("yr").tail(1)
    labs = end_labels(tips[tips.yr.isin(["2022", "2026"])], X, Y, "yr:N", scale=scale)
    grey = end_labels(tips[~tips.yr.isin(["2022", "2026"])], X, Y, "yr:N",
                      color=pallete["Deemphasize_Other"], size=10, weight=400, dx=9)

    plot = (hline(100, Y, dash=(4, 3), opacity=0.5) + lines + labs + grey
            ).properties(width=WIDTH - 90, height=HEIGHT - 105)

    return figure(
        "Pump price inflation is back above 20% for the first time since 2022",
        ["UK average pump price by week of year, weekly",
         "Grey lines: 2021, 2023, 2024 and 2025"],
        plot,
        [SRC, BASE])


# ------------------------------------------------------------------ F4
def f4():
    w = weekly()[["date", "qty"]].dropna().copy()
    # plotted values are the published index itself, clipped at the 100 baseline,
    # so nothing on this chart is a newly calculated statistic
    w["above"] = w.qty.clip(lower=100)
    w["below"] = w.qty.clip(upper=100)

    X = xt(values=[f"{y}-01-01" for y in range(2021, 2027)])
    AX = dict(values=[80, 90, 100, 110], domain=[78, 118])
    Y = yq("above:Q", "Index, 100 = same week a year earlier", **AX)
    YB = yq("below:Q", "Index, 100 = same week a year earlier", **AX)

    up = alt.Chart(w).mark_area(color=pallete["nominal_1"], opacity=0.9).encode(
        x=X, y=Y, y2=alt.datum(100))
    dn = alt.Chart(w).mark_area(color=pallete["nominal_2"], opacity=0.9).encode(
        x=X, y=YB, y2=alt.datum(100))

    ann = pd.DataFrame({
        "date": [pd.Timestamp("2024-05-01"), pd.Timestamp("2021-05-01"),
                 pd.Timestamp("2025-11-01")],
        "above": [114, 84, 86],
        "t": ["Bigger fill-ups than a year earlier", "Smaller fill-ups",
              "21 straight weeks below"]})

    plot = (up + dn + hline(100, Y, opacity=0.55) + annotate(ann, X, Y)
            ).properties(width=WIDTH - 90, height=HEIGHT - 105)

    return figure(
        "Fuel bought per fill-up has been below year-earlier levels since April",
        ["Estimated fuel demanded per transaction, weekly",
         "Blue: above the level of a year earlier.  Red: below"],
        plot,
        [SRC, BASE])


if __name__ == "__main__":
    chart_1 = f1()
    print(chart_1)
    chart_1.show()
    print(save(chart_1, "fuel_1_price_vs_demand", outdir="outputs"))


    chart_2 = f2()
    print(chart_2)
    chart_2.show()
    print(save(chart_2, "fuel_2_scatter", outdir="outputs"))

    chart_3 = f3()
    print(chart_3)
    chart_3.show()
    print(save(chart_3, "fuel_3_cycle", outdir="outputs"))

    chart_4 = f4()
    print(chart_4)
    chart_4.show()
    print(save(chart_4, "fuel_4_deviation", outdir="outputs"))

            


