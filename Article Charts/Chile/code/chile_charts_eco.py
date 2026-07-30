"""
Chile Chart of the Day - unified build (ECO house style)
========================================================
Built to the eco-altair-charts skill: registered 'report' theme, palette-only
colour, manual mark_text header, source note layered onto the plot, explicit
domain lines on both axes, hand-set tick values, direct labels with leaders,
and PNG(scale=3)/SVG/JSON export.

Figure 1  "Protests in Chile, 1990-2025"  -- The GDELT Project, Event Database.
          Annual count of CAMEO root-code-14 (protest) events in Chile
          (ActionGeo_CountryCode = 'CI'), from BigQuery `gdelt-bq.full.events`,
          saved as chile_protests.csv.
Figure 2  "Chileans' reported trust in institutions" -- LAPOP AmericasBarometer,
          Chile country-year files 2006-2023. Weighted mean trust (1-7):
          Police b18, Congress b13, Armed Forces b12, Political parties b21,
          President b21a, Courts b1. Weight = wt (2008 self-weighted). 2006 has
          no b21a (President starts 2008); the 2021 round dropped the battery and
          is skipped. The 2006 file breaks readstat, so pandas' reader is used.

Run: python chile_charts_eco.py
"""

import os, glob, re
import pandas as pd
import altair as alt
import vl_convert as vlc

from eco_style import pallete            # single source of truth
alt.themes.enable("report")

DATA_DIR = "/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/chile-protest"
OUTDIR   = "."

WIDTH, HEIGHT = 640, 380                 # house canvas; identical across the set
LABEL_SIZE, LABEL_WEIGHT = 11, 600       # direct series labels
MINUS = "\u2212"                         # typographic minus for rendered labels

# ----------------------------------------------------------- shared layout
def make_header(title_text, subtitle_text=None, width=WIDTH):
    base = alt.Chart(pd.DataFrame({"x": [0]})).encode(x=alt.value(0))
    title = base.mark_text(
        align="left", baseline="top", fontSize=16, fontWeight="bold",
        color=pallete["domain"], dy=-10,
    ).encode(text=alt.value(title_text)).properties(width=width, height=22)
    if not subtitle_text:
        return title
    subtitle = base.mark_text(
        align="left", baseline="top", fontSize=12,
        color=pallete["Deemphasize_Discrete"],
    ).encode(text=alt.value(subtitle_text)).properties(width=width, height=18)
    return alt.vconcat(title, subtitle, spacing=1)

def source_note(lines, width=WIDTH, dy0=30, step=13):
    """One or more source/caveat lines pinned to the plot's bottom-left."""
    layers = []
    for i, t in enumerate(lines):
        layers.append(alt.Chart(pd.DataFrame({"t": [t]})).mark_text(
            align="left", baseline="top", fontSize=9.5, dy=dy0 + i * step,
            color=pallete["Deemphasize_Discrete"],
        ).encode(x=alt.value(0), y=alt.value("height"), text="t:N"))
    return alt.layer(*layers).properties(width=width, height=HEIGHT)

def compose(header, main):
    return alt.vconcat(header, main, spacing=6).resolve_scale(
        color="independent"
    ).configure_view(strokeWidth=0).configure_concat(spacing=4)

def y_value_labels(values, y_scale, fmt=","):
    """Explicit y labels (axis labels off) to dodge the vl-convert top-label clip."""
    return alt.Chart(pd.DataFrame({"v": values})).mark_text(
        align="right", dx=-6, color=pallete["domain"], font="Circular Std", fontSize=11
    ).encode(y=alt.Y("v:Q", scale=y_scale, axis=None), x=alt.value(0),
             text=alt.Text("v:Q", format=fmt))

def domain_axis(values, fmt="d", grid=False):
    return alt.Axis(values=values, format=fmt, grid=grid, title=None, labels=False,
                    domain=True, domainColor=pallete["domain"], domainWidth=1,
                    domainOpacity=0.5, labelAngle=0)

def save_chart(chart, name):
    os.makedirs(OUTDIR, exist_ok=True)
    stem = os.path.join(OUTDIR, name)
    chart.save(stem + ".json")
    with open(stem + ".png", "wb") as f:
        f.write(vlc.vegalite_to_png(chart.to_json(), scale=3))
    with open(stem + ".svg", "w") as f:
        f.write(vlc.vegalite_to_svg(chart.to_json()))
    print(f"Saved {name} .png / .svg / .json")

# =============================================================== FIGURE 1
def figure1_protests():
    df = pd.read_csv(f"{DATA_DIR}/chile_protests.csv")
    X_DOMAIN, Y_DOMAIN = [1990, 2025], [0, 2500]
    X_TICKS = list(range(1990, 2026, 5))
    Y_TICKS = [0, 500, 1000, 1500, 2000, 2500]
    xs = alt.Scale(domain=X_DOMAIN, nice=False)
    ys = alt.Scale(domain=Y_DOMAIN, nice=False)

    x = alt.X("year:Q", scale=xs, axis=alt.Axis(
        values=X_TICKS, format="d", grid=False, title=None,
        domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5, labelAngle=0))
    y = alt.Y("protest_events:Q", scale=ys, axis=domain_axis(Y_TICKS, grid=True))

    line = alt.Chart(df).mark_line(color=pallete["accent"], strokeWidth=2.75).encode(x=x, y=y)

    # peak annotation (2019 estallido social) -- skill: endpoint dot + value label
    peak = df.loc[df["protest_events"].idxmax()]
    pk = pd.DataFrame({"year": [peak.year], "protest_events": [peak.protest_events],
                       "t": [f"{int(peak.protest_events):,} events, 2019"]})
    # axis=None on every secondary y-layer so resolve_axis(y="independent")
    # leaves exactly one y-axis (the `line` layer's), not a duplicate on the right.
    dot = alt.Chart(pk).mark_point(filled=True, size=55, opacity=1, color=pallete["accent"]).encode(
        x=alt.X("year:Q", scale=xs), y=alt.Y("protest_events:Q", scale=ys, axis=None))
    plab = alt.Chart(pk).mark_text(align="right", baseline="bottom", dx=-6, dy=-4,
        fontSize=LABEL_SIZE, fontWeight=LABEL_WEIGHT, color=pallete["accent"]).encode(
        x=alt.X("year:Q", scale=xs), y=alt.Y("protest_events:Q", scale=ys, axis=None), text="t:N")

    note = source_note([
        "Source: The GDELT Project.",
        "Counts reflect events in Chile as reported in global news media."])
    main = alt.layer(y_value_labels(Y_TICKS, ys, fmt=","), line, dot, plab, note
        ).resolve_axis(y="independent").properties(width=WIDTH, height=HEIGHT)
    header = make_header("Chile's protests peaked with the 2019 social uprising",
                         "Number of protest events recorded per year")
    save_chart(compose(header, main), "figure1_chile_protests_eco")

# =============================================================== FIGURE 2
VMAP = {"b18": "Police", "b13": "Congress", "b12": "Armed Forces",
        "b21": "Political parties", "b21a": "President", "b1": "Courts"}
ORDER  = ["Police", "Congress", "Armed Forces", "Political parties", "President", "Courts"]
FILL   = {"Police": pallete["nominal_1"], "Congress": pallete["nominal_2"],
          "Armed Forces": pallete["nominal_6"], "Political parties": pallete["nominal_3"],
          "President": pallete["nominal_4"], "Courts": pallete["nominal_5"]}

def trust_by_year():
    files = sorted(set(glob.glob(f"{DATA_DIR}/chl_*.dta") + glob.glob(f"{DATA_DIR}/CHL_*.dta")))
    rows = []
    for f in files:
        d = pd.read_stata(f, convert_categoricals=False); c = set(d.columns)
        if not any(v in c for v in VMAP):
            continue
        yr = int(d["year"].dropna().mode()[0]) if "year" in c else int(re.search(r"_(\d{4})_", f).group(1))
        w = d["wt"] if "wt" in c else pd.Series(1.0, index=d.index)
        for v, name in VMAP.items():
            if v not in c: continue
            x = pd.to_numeric(d[v], errors="coerce").where(lambda s: (s >= 1) & (s <= 7))
            rows.append((yr, name, float((x * w).sum() / w[x.notna()].sum())))
    df = pd.DataFrame(rows, columns=["year", "institution", "trust"])
    df["fill"] = df["institution"].map(FILL)
    return df

def figure2_trust():
    df = trust_by_year()
    df.pivot(index="year", columns="institution", values="trust")[ORDER].round(3).to_csv(
        os.path.join(OUTDIR, "chile_trust_by_year.csv"))

    X_TICKS = [2005, 2008, 2011, 2014, 2017, 2020, 2023]     # even 3-year grid
    Y_TICKS = [1, 2, 3, 4, 5, 6, 7]
    X_DOMAIN = [2005, 2032]                                  # headroom for labels
    Y_DOMAIN = [1, 7]
    xs = alt.Scale(domain=X_DOMAIN, nice=False)
    ys = alt.Scale(domain=Y_DOMAIN, nice=False)

    x = alt.X("year:Q", scale=xs, axis=alt.Axis(
        values=X_TICKS, format="d", grid=False, title=None,
        domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5, labelAngle=0))
    y = alt.Y("trust:Q", scale=ys, axis=domain_axis(Y_TICKS, grid=True))
    y_na = alt.Y("trust:Q", scale=ys, axis=None)     # for sibling y-layers
    col = alt.Color("fill:N", scale=None)

    lines  = alt.Chart(df).mark_line(strokeWidth=2).encode(x=x, y=y, color=col, detail="institution:N")
    points = alt.Chart(df).mark_point(filled=True, size=22, opacity=1).encode(x=x, y=y_na, color=col, detail="institution:N")

    # direct labels + leaders (skill: push apart ascending, clamp, connect)
    LABEL_X = 2023 + 0.6
    MIN_GAP = 0.30
    last = df[df.year == df.year.max()].sort_values("trust").reset_index(drop=True)
    ys_lab = last["trust"].tolist()
    for i in range(1, len(ys_lab)):
        if ys_lab[i] - ys_lab[i - 1] < MIN_GAP:
            ys_lab[i] = ys_lab[i - 1] + MIN_GAP
    over = (ys_lab[-1] if ys_lab else 0) - Y_DOMAIN[1]
    if over > 0:
        ys_lab = [v - over for v in ys_lab]
    last["ylab"], last["label_x"] = ys_lab, LABEL_X

    connectors = alt.Chart(last).mark_rule(strokeWidth=1, opacity=0.55).encode(
        x=alt.X("year:Q", scale=xs), y=alt.Y("trust:Q", scale=ys, axis=None),
        x2="label_x:Q", y2="ylab:Q", color=alt.Color("fill:N", scale=None))
    labels = alt.Chart(last).mark_text(align="left", baseline="middle", dx=4,
        fontSize=LABEL_SIZE, fontWeight=LABEL_WEIGHT).encode(
        x=alt.X("label_x:Q", scale=xs), y=alt.Y("ylab:Q", scale=ys, axis=None),
        text="institution:N", color=alt.Color("fill:N", scale=None))

    note = source_note([
        "Source: LAPOP AmericasBarometer (2006\u20132023). Population-weighted means.",
        "Trust in the President first recorded in 2008; the 2021 round omitted the trust battery."])
    main = alt.layer(y_value_labels(Y_TICKS, ys, fmt="d"),
                     lines, points, connectors, labels, note
        ).resolve_axis(y="independent").properties(width=WIDTH, height=HEIGHT)
    header = make_header("Trust in Chile's institutions has broadly fallen since 2010",
                         "Mean reported trust, 1 (not at all) to 7 (a lot)")
    save_chart(compose(header, main), "figure2_chile_trust_eco")

# =============================================================== main
if __name__ == "__main__":
    figure1_protests()
    figure2_trust()