"""
Rightmove Housing Market Insights (ONS real-time indicators, 4 Sep 2026)
Four figures, ECO house style.

  H1  Rental vs sales listings, Great Britain, monthly index (SA)
  H2  Average days on market by region, 2023 vs 2026 (dumbbell)
  H3  Change in days on market by region (choropleth)
  H4  Spread between the fastest and slowest regional markets (range band)
"""

import json
import pandas as pd
import altair as alt

import eco_style                      # registers the 'report' theme + pallete
from eco_style import pallete
from eco_charts import (WIDTH, HEIGHT, LABEL_SIZE, LABEL_WEIGHT, MINUS,
                        figure, yq, yn, xq, xt, hline, annotate, end_labels,
                        signed, save, read_ons)

try:
    alt.theme.enable("report")
except Exception:
    alt.themes.enable("report")

F = "/mnt/user-data/uploads/housingmarketinsightsdataset040926.xlsx"
SRC = "Source: ONS real-time indicators, Rightmove data, published 4 September 2026"

REGIONS = ["Scotland", "Wales", "East Midlands", "East of England", "London",
           "North East", "North West", "South East", "South West",
           "West Midlands", "Yorkshire and The Humber"]

# label anchor per region, nudged off the representative point where a region is
# too small or too crowded to hold text. Short names so the map reads without a key.
LABEL = {
    "Scotland":                 ("Scotland",      -4.30, 56.90),
    "North East":               ("North East",    -1.85, 55.10),
    "North West":               ("North West",    -2.85, 54.20),
    "Yorkshire and The Humber": ("Yorks & Humber", -1.05, 53.95),
    "East Midlands":            ("E Midlands",    -0.55, 52.95),
    "West Midlands":            ("W Midlands",    -2.55, 52.45),
    "Wales":                    ("Wales",         -3.85, 52.25),
    "East of England":          ("E of England",   0.75, 52.30),
    "South West":               ("South West",    -3.55, 50.95),
    "South East":               ("South East",    -1.15, 51.05),
    "London":                   ("London",         2.05, 51.75),
}


def _tom():
    m = read_ons(F, "6.Monthly Time on Market SA")
    return m.rename(columns={c: c.replace(" Sales", "") for c in m.columns if c != "date"})


# ------------------------------------------------------------------ H1
def h1():
    m = read_ons(F, "5.Monthly New Listings SA")
    d = m[["date", "Great Britain Rentals", "Great Britain Sales"]].melt(
        "date", var_name="series", value_name="index")
    d["series"] = d["series"].str.replace("Great Britain ", "", regex=False)

    scale = alt.Scale(domain=["Rentals", "Sales"],
                      range=[pallete["nominal_1"], pallete["nominal_2"]])
    X = xt(values=[f"{y}-01-01" for y in (2023, 2024, 2025, 2026)])
    Y = yq("index:Q", "Index, 2023 average = 100",
           values=[90, 100, 110, 120, 130], domain=[88, 130])

    lines = alt.Chart(d).mark_line(strokeWidth=2.4).encode(
        x=X, y=Y, color=alt.Color("series:N", scale=scale, legend=None))
    labs = end_labels(d[d.date == d.date.max()], X, Y, "series:N", scale=scale)

    ann = pd.DataFrame({"date": [pd.Timestamp("2024-11-01")], "index": [96.4],
                        "t": ["2023 average"]})
    plot = (hline(100, Y, dash=(4, 3), opacity=0.45)
            + lines + labs + annotate(ann, X, Y)
            ).properties(width=WIDTH - 62, height=HEIGHT - 105)

    return figure(
        "Great Britain: rental listings sit 19% above their 2023 average, sales listings 6%",
        ["New listings on Rightmove, monthly, seasonally adjusted",
         "January 2023 to July 2026"],
        plot,
        [SRC, "Note: excludes new-build, auction and retirement properties. One property may generate several listings."])


# ------------------------------------------------------------------ H2
def h2():
    m = _tom()
    d = pd.DataFrame({"region": REGIONS,
                      "start": [m.iloc[0][r] for r in REGIONS],
                      "end": [m.iloc[-1][r] for r in REGIONS]})
    d["chg"] = d["end"] - d["start"]
    d = d.sort_values("chg", ascending=False).reset_index(drop=True)
    d["label"] = d["chg"].map(lambda v: "no change" if abs(v) < 1 else signed(v, "{:.0f}"))
    order = d["region"].tolist()

    Y = yn("region:N", sort=order, padding=0.45)
    XD = dict(values=[30, 40, 50, 60, 70, 80], domain=[28, 84])
    X, XE = xq("start:Q", **XD), xq("end:Q", **XD)

    conn = alt.Chart(d).mark_rule(color=pallete["Other_3"], strokeWidth=6,
                                  strokeCap="round").encode(y=Y, x=X, x2=alt.X2("end:Q"))
    p23 = alt.Chart(d).mark_point(filled=True, size=95, opacity=1,
                                  color=pallete["Deemphasize_Other"]).encode(y=Y, x=X)
    p26 = alt.Chart(d).mark_point(filled=True, size=115, opacity=1,
                                  color=pallete["nominal_2"]).encode(y=Y, x=XE)
    val = alt.Chart(d).mark_text(align="left", dx=11, fontSize=10.5, fontWeight=600,
                                 color=pallete["Deemphasize_Other"], baseline="middle"
                                 ).encode(y=Y, x=XE, text="label:N")

    plot = (conn + p23 + p26 + val).properties(width=WIDTH - 230, height=HEIGHT - 118)

    return figure(
        "Homes take a third longer to sell than in 2023 \u2014 except in Scotland",
        ["Average days a sales listing spends on the market, seasonally adjusted",
         "Grey marker: January 2023.  Red marker: July 2026"],
        plot, [SRC])


# ------------------------------------------------------------------ H3
def h3():
    m = _tom()
    d = pd.DataFrame({"region": REGIONS,
                      "start": [m.iloc[0][r] for r in REGIONS],
                      "end": [m.iloc[-1][r] for r in REGIONS]})
    d["pct"] = 100 * (d["end"] - d["start"]) / d["start"]





    gj = json.load(open("/home/claude/gb_regions_small.json"))
    geo = alt.Data(values=gj, format=alt.DataFormat(property="features", type="json"))

    bands = ["Up to +10%", "+10% to +25%", "+25% to +40%", "More than +40%"]
    d["band"] = pd.cut(d.pct, [-99, 10, 25, 40, 999], labels=bands).astype(str)

    colour = alt.Color(
        "band:N", title="Change in days on market",
        scale=alt.Scale(domain=bands, range=[pallete["Other_3"], pallete["nominal_3"],
                                             pallete["nominal_5"], pallete["nominal_2"]]),
        legend=alt.Legend(orient="none", legendX=2, legendY=138, symbolType="square",
                          symbolSize=170, labelFontSize=10.5, titleFontSize=11,
                          titlePadding=8, rowPadding=5))

    shapes = (alt.Chart(geo).mark_geoshape(stroke="white", strokeWidth=1.2)
              .encode(color=colour)
              .transform_lookup(lookup="properties.region",
                                from_=alt.LookupData(d, "region", ["band"])))

    # only the two extremes are called out on the map; the rest is in the key
    calls = pd.DataFrame({
        "lon": [-4.30, 1.90], "lat": [56.90, 52.55],
        "lon2": [-4.30, -0.45], "lat2": [56.90, 52.88],
        "t": ["Scotland: no change", "East Midlands: +55%"]})
    lead = (alt.Chart(calls.iloc[[1]]).mark_rule(color=pallete["Deemphasize_Other"],
                                                strokeWidth=0.9)
            .encode(longitude="lon:Q", latitude="lat:Q",
                    longitude2="lon2:Q", latitude2="lat2:Q"))
    calltxt = (alt.Chart(calls).mark_text(fontSize=11, fontWeight=600, align="left", dx=4,
                                          color=pallete["domain"])
               .encode(longitude="lon:Q", latitude="lat:Q", text="t:N"))

    themap = (shapes + lead + calltxt).project(type="mercator").properties(
        width=WIDTH - 30, height=HEIGHT - 55)

    return figure(
        "The slowdown in selling times is deepest in the Midlands and the South West",
        ["Change in the average number of days a sales listing spends on the market,",
         "January 2023 to July 2026, seasonally adjusted"],
        themap,
        [SRC, "Note: Scotland is a single reporting region. Northern Ireland is not covered by this dataset."])


# ------------------------------------------------------------------ H4
def h4():
    m = _tom()
    long = m.melt("date", var_name="region", value_name="days")
    reg = long[long.region.isin(REGIONS)]
    band = reg.groupby("date")["days"].agg(lo="min", hi="max").reset_index()

    X = xt(values=[f"{y}-01-01" for y in (2023, 2024, 2025, 2026)])
    Y = yq("days:Q", "Average days on market", values=[30, 45, 60, 75, 90], domain=[28, 90])
    YLO = yq("lo:Q", "Average days on market", values=[30, 45, 60, 75, 90], domain=[28, 90])

    area = alt.Chart(band).mark_area(color=pallete["Other_3"], opacity=0.55).encode(
        x=X, y=YLO, y2=alt.Y2("hi:Q"))

    show = {"London": pallete["nominal_2"], "Great Britain": pallete["domain"],
            "Scotland": pallete["nominal_1"]}
    sub = long[long.region.isin(show)]
    scale = alt.Scale(domain=list(show), range=list(show.values()))
    lines = alt.Chart(sub).mark_line(strokeWidth=2.2).encode(
        x=X, y=Y, color=alt.Color("region:N", scale=scale, legend=None))
    labs = end_labels(sub[sub.date == sub.date.max()], X, Y, "region:N", scale=scale)

    ann = pd.DataFrame({"date": [pd.Timestamp("2024-03-01"), pd.Timestamp("2025-03-01")],
                        "days": [52.0, 42.0],
                        "t": ["Shaded band: fastest to slowest region",
                              "Scotland has not slowed at all"]})
    plot = (area + lines + labs + annotate(ann, X, Y)
            ).properties(width=WIDTH - 105, height=HEIGHT - 105)

    return figure(
        "It now takes 42 days longer to sell a home in London than in Scotland",
        ["Average days a sales listing spends on the market, by country and English region",
         "Monthly, seasonally adjusted, January 2023 to July 2026"],
        plot, [SRC])


if __name__ == "__main__":
    for name, fn in [("housing_1_listings", h1), ("housing_2_days_dumbbell", h2),
                     ("housing_3_days_map", h3), ("housing_4_spread", h4)]:
        try:
            print(save(fn(), name))
        except Exception as e:
            print("FAIL", name, type(e).__name__, e)
