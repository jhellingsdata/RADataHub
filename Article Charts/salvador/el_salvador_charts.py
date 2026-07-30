"""
El Salvador COTD -- unified chart builder
=========================================

One file that rebuilds all eight figures in the ECO house style.

Run everything:
    python el_salvador_charts.py

Run one (or several) by key:
    python el_salvador_charts.py fig3_exports_per_capita
    python el_salvador_charts.py fig6_investment fig8_fdi

Each figure lives in its own build_* function, so you can edit one without
touching the others. Shared boilerplate (header, footer, y-axis labels,
World Bank fetch, save-to-json/png/svg) is factored into helpers at the top.

STYLE CONTRACT (homogenised across all eight figures):
  - Canvas          : 640 x 380 for every figure.
  - Header          : title 16px bold (domain); subtitle 12px (Deemphasize_Discrete).
  - Footer          : 9.5px, height 14.
  - Direct labels   : 11px, weight 600.
  - Bukele marker   : dashed rule + "Bukele first term begins", 10.5px.
  - Negative sign   : Unicode minus (U+2212) in every rendered label.
  - Titles          : descriptive "El Salvador: <subject>"; subtitle states the data.
  - Colour          : palette keys only (eco_style.pallete); no inline hex.

------------------------------------------------------------------------------
THINGS TO CHECK BEFORE RUNNING (flagged, not silently assumed):

1. PATHS. Edit the CONFIG block below if your repo lives elsewhere. Outputs
   go to <REPO_DIR>/output.

2. DATA SOURCES.
     - figs 1, 5, 6, 7, 8  pull live from the World Bank API (worldbank.org).
     - fig 9               pulls live from freedomhouse.org.
     - figs 2, 3           read the two local CSVs you supplied.
   Each live fetch falls back to a cache under <REPO_DIR>/data ONLY if that
   cache file exists locally. The caches were built in the previous sandbox
   session, so if you don't have them, the live pull must succeed.

3. fig3 COLUMN NAME. The exports CSV is read expecting a value column named
   EXPORTS_VALUE_COL (set in build_fig3). The old file called it
   "Per Capita Constant (2024 USD) gross exports". If
   'What-did-El-Salvador-export-1995-2024.csv' names it differently, change
   that one constant.

4. YEAR RANGES for figs 6 and 8 are set to 2015-2024 to match your current
   scripts. The live World Bank pull returns 2010-2024, so if you want the
   full range the original report used, widen START_YEAR / X_DOMAIN in those
   two functions.
------------------------------------------------------------------------------
"""

import os
import sys
import time
import math

import pandas as pd
import altair as alt
import vl_convert as vlc
from io import BytesIO
import requests

# =============================================================================
# CONFIG -- edit these
# =============================================================================
REPO_DIR = "/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/el_salvador"
DATA_DIR = REPO_DIR                          # the two supplied CSVs live here
CACHE_DIR = os.path.join(REPO_DIR, "data")  # optional live-fetch fallbacks
OUTPUT_DIR = os.path.join(REPO_DIR, "output")

# Local CSVs you provided
MARKET_SHARE_CSV = os.path.join(DATA_DIR, "El-Salvador-s-global-market-share-1995-2024.csv")
EXPORTS_CSV = os.path.join(DATA_DIR, "What-did-El-Salvador-export-1995-2024.csv")

# Where eco_style.py lives. REPO_DIR is tried first, then this script's own
# folder, so it works whether eco_style sits in the repo or next to this file.
# __file__ is undefined in a notebook, so fall back to the working directory.
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.insert(0, os.getcwd())
sys.path.insert(0, REPO_DIR)
from eco_style import pallete  # noqa: E402

alt.themes.enable("report")

# =============================================================================
# SHARED STYLE CONSTANTS -- one canvas, one label size, one Bukele marker
# =============================================================================
WIDTH, HEIGHT = 640, 380
LABEL_SIZE, LABEL_WEIGHT = 11, 600          # direct line-end / sector labels
BUKELE_TEXT = "Bukele first term begins"
BUKELE_SIZE = 10.5
MINUS = "\u2212"                            # rendered negative sign
SQ = "'"                                    # single quote for Vega format() args
                                            # (keeps backslashes out of f-strings)


def _sign(expr):
    """Vega expression wrapper: swap the ASCII hyphen a JS format() emits for a
    typographic minus, so every rendered label matches the axis glyphs."""
    return f'replace({expr}, "-", "{MINUS}")'


def nice_upper(data_max, target_ticks=4, headroom=1.06):
    """Round a data maximum up to a clean axis ceiling with round-number ticks.

    Returns (ceiling, ticks). Sizes the axis to the data plus a little headroom
    instead of a fixed domain, so the panel doesn't carry dead whitespace above
    the series. Steps are chosen from the 1/2/2.5/5 x 10^n family."""
    if data_max <= 0:
        return 1.0, [0, 1]
    rough = data_max * headroom / target_ticks
    mag = 10 ** math.floor(math.log10(rough))
    step = 10 * mag
    for m in (1, 2, 2.5, 5, 10):
        if rough <= m * mag:
            step = m * mag
            break
    ceiling = math.ceil(data_max * headroom / step) * step
    n = int(round(ceiling / step))
    ticks = [round(step * i, 6) for i in range(n + 1)]
    return ceiling, ticks


# =============================================================================
# SHARED HELPERS
# =============================================================================
def make_header(title_text, subtitle_text=None, width=WIDTH, title_size=16, subtitle_color=None):
    """Title (+ optional subtitle) as manual mark_text (house style).
    Added offset to the title to provide top padding.

    Pass subtitle_text=None (or omit it) for a title-only header: the measure
    and unit then live on the y-axis title instead. Any range/caveat the
    subtitle used to carry must move to the footer note or the y-axis title."""
    subtitle_color = subtitle_color or pallete["Deemphasize_Discrete"]
    base = alt.Chart(pd.DataFrame({"x": [0]})).encode(x=alt.value(0))
    
    # Adding a small dy (offset) to the title provides the needed top padding
    title = base.mark_text(
        align="left", baseline="top", fontSize=title_size, fontWeight="bold",
        color=pallete["domain"], dy=-10 
    ).encode(text=alt.value(title_text)).properties(width=width, height=22)

    # Title-only header: return the single mark. compose() accepts it fine.
    if not subtitle_text:
        return title

    subtitle = base.mark_text(
        align="left", baseline="top", fontSize=12, color=subtitle_color,
    ).encode(text=alt.value(subtitle_text)).properties(width=width, height=18)
    return alt.vconcat(title, subtitle, spacing=1)

def compose(header, main, footer):
    # Removed .configure_padding({"top": 10}) which caused the crash
    return alt.vconcat(header, main, footer, spacing=6).resolve_scale(
        color="independent"
    ).configure_view(strokeWidth=0).configure_concat(spacing=4)
def save_chart(chart, name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stem = os.path.join(OUTPUT_DIR, name)
    chart.save(stem + ".json")
    with open(stem + ".png", "wb") as f:
        f.write(vlc.vegalite_to_png(chart.to_json(), scale=3))
    with open(stem + ".svg", "w") as f:
        f.write(vlc.vegalite_to_svg(chart.to_json()))
    print(f"[saved] {name}  ->  .json .png .svg")


def make_footer(text, width=WIDTH):
    """Source/notes line as manual mark_text (house style: 9.5px, height 14)."""
    base = alt.Chart(pd.DataFrame({"x": [0]})).encode(x=alt.value(0))
    return base.mark_text(
        align="left", baseline="top", fontSize=9.5,
        color=pallete["Deemphasize_Discrete"],
    ).encode(text=alt.value(text)).properties(width=width, height=14)


def ref_rule(years, x_scale, color=None, dash=(4, 3), opacity=0.45, stroke_width=1):
    """Thin dashed vertical reference rule(s) at the given x positions."""
    color = color or pallete["Deemphasize_Discrete"]
    d = pd.DataFrame({"x": list(years)})
    return alt.Chart(d).mark_rule(
        strokeDash=list(dash), strokeWidth=stroke_width, opacity=opacity, color=color,
    ).encode(x=alt.X("x:Q", scale=x_scale))


def bukele_annotation(x_scale, y_scale, y_pos, year=2019, text=BUKELE_TEXT):
    """Dashed vertical rule at Bukele's first term (2019) plus a text label at
    y_pos. Returns (rule, label) so callers can layer them where they choose."""
    rule = alt.Chart(pd.DataFrame({"x": [year]})).mark_rule(
        color=pallete["domain"], strokeDash=[4, 3], strokeWidth=1, opacity=0.55,
    ).encode(x=alt.X("x:Q", scale=x_scale))
    label = alt.Chart(pd.DataFrame({"x": [year], "y": [y_pos], "t": [text]})).mark_text(
        align="left", baseline="middle", dx=5, fontSize=BUKELE_SIZE,
        color=pallete["Deemphasize_Discrete"],
    ).encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="t:N")
    return rule, label


def endpoint(year, value, x_scale, y_scale, fmt=".1f", suffix="%", color=None):
    """Filled dot + bold value label at a series endpoint (percentage series)."""
    color = color or pallete["accent"]
    txt = ("{:" + fmt + "}").format(value).replace("-", MINUS) + suffix
    d = pd.DataFrame({"x": [year], "y": [value], "t": [txt]})
    dot = alt.Chart(d).mark_point(filled=True, size=60, opacity=1, color=color).encode(
        x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
    label = alt.Chart(d).mark_text(
        align="left", baseline="middle", dx=8, fontSize=LABEL_SIZE,
        fontWeight=LABEL_WEIGHT, color=color,
    ).encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="t:N")
    return dot + label


def wb_fetch(countries, indicator, start, end, per_page=500, retries=4):
    """Tidy (country, year, value) frame from the live World Bank API."""
    url = f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
    params = {"format": "json", "per_page": per_page, "date": f"{start}:{end}"}
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
                raise RuntimeError(f"World Bank API returned no data for {indicator} / {countries}.")
            records = payload[1]
            df = pd.DataFrame.from_records(
                [{"country": r["countryiso3code"], "year": int(r["date"]), "value": r["value"]}
                 for r in records if r["value"] is not None]
            )
            if df.empty:
                raise RuntimeError(f"Parsed zero observations for {indicator}.")
            return df.sort_values(["country", "year"]).reset_index(drop=True)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                wait = 2 ** (attempt - 1)
                print(f"[retry] {indicator}: attempt {attempt}/{retries} failed ({e}); "
                      f"waiting {wait}s.", file=sys.stderr)
                time.sleep(wait)
    raise last_err


def load_wb(countries, indicator, start, end, cache_path=None, cache_value_col="value"):
    """Live World Bank fetch, falling back to a local cache if one exists."""
    try:
        df = wb_fetch(countries, indicator, start, end)
        print(f"[live] {indicator}: {len(df)} rows from the World Bank API.")
        return df
    except Exception as e:  # noqa: BLE001
        if cache_path and os.path.exists(cache_path):
            print(f"[warn] live fetch failed ({e}); using cache {cache_path}.", file=sys.stderr)
            c = pd.read_csv(cache_path, comment="#")
            if cache_value_col != "value" and cache_value_col in c.columns:
                c = c.rename(columns={cache_value_col: "value"})
            return c
        raise


# Common colour set-up for the 4-country panels (figs 6 & 8)
PEER_DOMAIN = ["El Salvador", "Honduras", "Nicaragua", "Guatemala"]
PEER_RANGE = [pallete["accent"], pallete["nominal_5"], pallete["nominal_6"], pallete["nominal_3"]]
PEER_NAMES = {"SLV": "El Salvador", "HND": "Honduras", "NIC": "Nicaragua", "GTM": "Guatemala"}

SECTOR_TEXTILES = pallete["nominal_1"]
SECTOR_AGRICULTURE = pallete["nominal_2"]


# =============================================================================
# FIGURE 1 -- GDP per capita relative to the US
# =============================================================================
def build_fig1():
    raw = load_wb(["SLV", "USA"], "NY.GDP.PCAP.KD", 1965, 2024,
                  cache_path=os.path.join(CACHE_DIR, "wdi_gdp_per_capita_cache.csv"))
    wide = raw.pivot(index="year", columns="country", values="value").reset_index()
    wide["ratio"] = wide["SLV"] / wide["USA"] * 100
    wide = wide.sort_values("year").reset_index(drop=True)

    latest_year = int(wide["year"].max())
    latest_ratio = wide.loc[wide["year"] == latest_year, "ratio"].iloc[0]

    Y_DOMAIN, Y_TICKS = [0, 13], [0, 2, 4, 6, 8, 10, 12]
    X_DOMAIN = [1963, 2029]
    X_TICKS = [1970, 1985, 2000, 2015]
    y_scale = alt.Scale(domain=Y_DOMAIN, nice=False)
    x_scale = alt.Scale(domain=X_DOMAIN, nice=False)

    header = make_header(
        "El Salvador: GDP per capita relative to the United States",
        width=WIDTH,
    )

    line = alt.Chart(wide).mark_line(color=pallete["accent"], strokeWidth=2.75).encode(
        x=alt.X("year:Q", scale=x_scale, axis=alt.Axis(
            values=X_TICKS, format="d", grid=False, title=None, 
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        # Native Y axis matching Fig 2 & 3 looks
        y=alt.Y("ratio:Q", scale=y_scale, axis=alt.Axis(
            values=Y_TICKS, labelExpr="datum.value + '%'", title="GDP per capita, % of US level", grid=True,
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
    )
    civil_war_rule = ref_rule([1979, 1992], x_scale)
    bukele_rule, bukele_label = bukele_annotation(x_scale, y_scale, y_pos=3.0)

    civil_war = alt.Chart(pd.DataFrame({"x": [1985.5], "y": [12.6], "label": ["Civil war"]})).mark_text(
        align="center", baseline="middle", fontSize=10.5, color=pallete["Deemphasize_Discrete"],
    ).encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="label")

    end = endpoint(latest_year, latest_ratio, x_scale, y_scale, fmt=".1f")

    main = alt.layer(civil_war_rule, bukele_rule, line,
                     civil_war, bukele_label, end).properties(width=WIDTH, height=HEIGHT)
    footer = make_footer("Source: World Bank, World Development Indicators.", WIDTH)
    print(f"[fig1] latest_year={latest_year} latest_ratio={latest_ratio:.2f}%")
    return compose(header, main, footer)


# =============================================================================
# FIGURE 2 -- global market share by sector (log scale)
# =============================================================================
def build_fig2():
    df = pd.read_csv(MARKET_SHARE_CSV).rename(columns={"Market Share": "share"})
    df["pct"] = df["share"] * 100

    HIGHLIGHT = {"Textiles": SECTOR_TEXTILES, "Agriculture": SECTOR_AGRICULTURE}
    GREY_LINE = pallete["Other_3"]           
    GREY_LABEL = pallete["Deemphasize_Other"]
    df["lcol"] = df["Sector"].map(lambda s: HIGHLIGHT.get(s, GREY_LINE))
    df["tcol"] = df["Sector"].map(lambda s: HIGHLIGHT.get(s, GREY_LABEL))
    df["order"] = df["Sector"].map(lambda s: 1 if s in HIGHLIGHT else 0)  

    last = df[df.Year == 2024].copy()
    NUDGE = {}  
    last["label_y"] = last.apply(lambda r: r["pct"] * NUDGE.get(r["Sector"], 1.0), axis=1)

    X_DOMAIN, Y_DOMAIN = [1994, 2031], [0.0003, 0.35]
    x = alt.X("Year:Q", scale=alt.Scale(domain=X_DOMAIN, nice=False),
              axis=alt.Axis(
                  values=[1995, 2005, 2015, 2024], format="d", 
                  domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5))
    
    # Native Y axis
    y = alt.Y("pct:Q", scale=alt.Scale(type="log", domain=Y_DOMAIN, nice=False),
              axis=alt.Axis(
                  values=[0.001, 0.01, 0.1], labelExpr="format(datum.value, '~r') + '%'",
                  title="Share of world exports (%)", grid=True,
                  domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5))

    lines = alt.Chart(df).mark_line(strokeWidth=2.25).encode(
        x=x, y=y, detail="Sector:N", order="order:Q", color=alt.Color("lcol:N", scale=None))
    labels = alt.Chart(last).mark_text(
        align="left", dx=6, fontWeight=LABEL_WEIGHT, fontSize=LABEL_SIZE).encode(
        x=alt.X("Year:Q", scale=alt.Scale(domain=X_DOMAIN, nice=False)),
        y=alt.Y("label_y:Q", scale=alt.Scale(type="log", domain=Y_DOMAIN, nice=False)),
        text="Sector:N", color=alt.Color("tcol:N", scale=None))
    main = (lines + labels).properties(width=WIDTH, height=HEIGHT)

    header = make_header(
        "El Salvador: global export market share by sector",
        width=WIDTH,
    )
    footer = make_footer(
        "Source: Atlas of Economic Complexity. Note: log scale.", WIDTH)
    return compose(header, main, footer)


# =============================================================================
# FIGURE 3 -- real per-capita exports by sector (stacked area)
# =============================================================================
def build_fig3():
    """Stacked area of per-capita gross exports by sector, 1995-2024.

    Y axis is fixed by hand (data peaks near $176/person), so the panel never
    depends on nice_upper. All eleven sectors are shown, stacked largest-at-
    bottom by their latest-year size and labelled directly at the right edge
    with leader lines (fig9 pattern). Set GROUP_TAIL=True to collapse the eight
    small sectors into one muted "Other" band for a cleaner four-band cut."""
    VALUE_COL = "Per Capita Constant (2024 USD) gross exports"

    # --- fig3-local style (kept here, like the other figures' local domains) --
    Y_DOMAIN, Y_TICKS = [0, 200], [0, 50, 100, 150, 200]
    X_DOMAIN, X_TICKS = [1995, 2031], [1995, 2005, 2015, 2024]
    LABEL_X = 2024.6
    LABEL_MIN_GAP = 9.0                       # min vertical gap between labels
    GROUP_TAIL = False
    STORY_SECTORS = ["Services", "Textiles", "Agriculture"]
    OTHER_LABEL = "Other"

    _DARK = pallete["Deemphasize_Other"]
    # fill + label colour + stack rank (0 = bottom), ordered by 2024 size.
    # Eleven sectors exceed the palette's distinct colours, so the smallest
    # bands take muted tones and rely on their leader-line labels.
    SECTOR_STYLE = {
        "Services":    {"fill": pallete["nominal_1"],              "text": pallete["nominal_1"], "rank": 0},
        "Textiles":    {"fill": pallete["nominal_2"],              "text": pallete["nominal_2"], "rank": 1},
        "Agriculture": {"fill": pallete["nominal_3"],              "text": pallete["nominal_3"], "rank": 2},
        "Chemicals":   {"fill": pallete["nominal_5"],              "text": pallete["nominal_5"], "rank": 3},
        "Electronics": {"fill": pallete["nominal_6"],              "text": pallete["nominal_6"], "rank": 4},
        "Metals":      {"fill": pallete["nominal_4"],              "text": pallete["nominal_4"], "rank": 5},
        "Minerals":    {"fill": pallete["bar"]["other"],           "text": _DARK,                "rank": 6},
        "Machinery":   {"fill": _DARK,                             "text": _DARK,                "rank": 7},
        "Other":       {"fill": pallete["Other_3"],                "text": _DARK,                "rank": 8},
        "Stone":       {"fill": pallete["Deemphasize_Continuous"], "text": _DARK,                "rank": 9},
        "Vehicles":    {"fill": pallete["shadow"],                 "text": _DARK,                "rank": 10},
    }

    df = pd.read_csv(EXPORTS_CSV)
    if VALUE_COL not in df.columns:
        raise KeyError(f"fig3: expected value column {VALUE_COL!r}; found {df.columns.tolist()}")
    df = df.rename(columns={VALUE_COL: "value"})[["year", "Sector", "value"]]

    # Optionally collapse the small tail into one band.
    if GROUP_TAIL:
        df["band"] = df["Sector"].where(df["Sector"].isin(STORY_SECTORS), OTHER_LABEL)
    else:
        df["band"] = df["Sector"]
    df = df.groupby(["year", "band"], as_index=False)["value"].sum()
    df["rank"] = df["band"].map(lambda b: SECTOR_STYLE[b]["rank"])
    df["fill"] = df["band"].map(lambda b: SECTOR_STYLE[b]["fill"])

    tot = df.groupby("year")["value"].sum()
    print(f"[fig3] bands={df['band'].nunique()} peak=${tot.max():.0f}/cap in {int(tot.idxmax())}")

    y_scale = alt.Scale(domain=Y_DOMAIN, nice=False)
    x_scale = alt.Scale(domain=X_DOMAIN, nice=False)

    x = alt.X("year:Q", scale=x_scale, axis=alt.Axis(
        values=X_TICKS, format="d", grid=False, title=None,
        domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5))
    y = alt.Y("value:Q", stack="zero", scale=y_scale, axis=alt.Axis(
        values=Y_TICKS, format="$,.0f", grid=True, title=None,
        domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5))

    areas = alt.Chart(df).mark_area(opacity=0.95).encode(
        x=x, y=y,
        color=alt.Color("fill:N", scale=None),
        order=alt.Order("rank:Q", sort="ascending"),
    )

    # Direct labels at each band's latest-year midpoint, nudged apart by
    # LABEL_MIN_GAP and connected back to their band with leader lines.
    last = df[df["year"] == df["year"].max()].sort_values("rank").reset_index(drop=True)
    last["ymid"] = last["value"].cumsum() - last["value"] / 2
    last = last.sort_values("ymid").reset_index(drop=True)

    ys = last["ymid"].tolist()
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < LABEL_MIN_GAP:
            ys[i] = ys[i - 1] + LABEL_MIN_GAP
    over = (ys[-1] if ys else 0) - Y_DOMAIN[1]
    if over > 0:
        ys = [v - over for v in ys]
    last["ylab"] = ys
    last["label_x"] = LABEL_X
    last["tcol"] = last["band"].map(lambda b: SECTOR_STYLE[b]["text"])

    connectors = alt.Chart(last).mark_rule(strokeWidth=1, opacity=0.55).encode(
        x=alt.X("year:Q", scale=x_scale), y=alt.Y("ymid:Q", scale=y_scale),
        x2=alt.X2("label_x:Q"), y2=alt.Y2("ylab:Q"),
        color=alt.Color("tcol:N", scale=None))
    labels = alt.Chart(last).mark_text(
        align="left", baseline="middle", dx=4, fontSize=LABEL_SIZE, fontWeight=LABEL_WEIGHT,
    ).encode(
        x=alt.X("label_x:Q", scale=x_scale), y=alt.Y("ylab:Q", scale=y_scale),
        text="band:N", color=alt.Color("tcol:N", scale=None))

    main = alt.layer(areas, connectors, labels).properties(width=WIDTH, height=HEIGHT)

    header = make_header(
        "El Salvador: real per-capita exports by sector",
        "Gross exports per person, constant 2024 US$",
    )
    footer = make_footer(
        "Source: Atlas of Economic Complexity, Harvard Growth Lab.", WIDTH)
    return compose(header, main, footer)


# =============================================================================
# FIGURE 5 -- net migration as a share of population
# =============================================================================
def build_fig5():
    def load_netm():
        try:
            d = wb_fetch(["SLV"], "SM.POP.NETM", 1960, 2024)
            return d[["year", "value"]].rename(columns={"value": "net_migration"})
        except Exception as e:  # noqa: BLE001
            p = os.path.join(CACHE_DIR, "wdi_net_migration_5yr_cache.csv")
            if os.path.exists(p):
                print(f"[warn] live SM.POP.NETM failed ({e}); using 5yr cache.", file=sys.stderr)
                c = pd.read_csv(p, comment="#")
                ycol = "period_end_year" if "period_end_year" in c.columns else "year"
                vcol = "five_year_total" if "five_year_total" in c.columns else "value"
                return c.rename(columns={ycol: "year", vcol: "net_migration"})[["year", "net_migration"]]
            raise

    def load_pop():
        try:
            d = wb_fetch(["SLV"], "SP.POP.TOTL", 1960, 2024)
            return d[["year", "value"]].rename(columns={"value": "population"})
        except Exception as e:  # noqa: BLE001
            p = os.path.join(CACHE_DIR, "wdi_population_slv_cache.csv")
            if os.path.exists(p):
                print(f"[warn] live SP.POP.TOTL failed ({e}); using cache.", file=sys.stderr)
                return pd.read_csv(p, comment="#")[["year", "population"]]
            raise

    netm = load_netm().dropna().sort_values("year")
    pop = load_pop().dropna().sort_values("year")

    span = int(netm["year"].max()) - int(netm["year"].min()) + 1
    if len(netm) < 0.4 * span:
        rows = []
        for _, r in netm.iterrows():
            end = int(r["year"])
            rate = r["net_migration"] / 5.0
            for yv in range(end - 4, end + 1):
                rows.append({"year": yv, "net_migration": rate})
        netm = pd.DataFrame(rows).drop_duplicates(subset="year", keep="last")

    df = netm.merge(pop, on="year", how="inner")
    df["ratio"] = df["net_migration"] / df["population"] * 100
    df = df[(df["year"] >= 1960) & (df["year"] <= 2024)].sort_values("year").reset_index(drop=True)

    latest_year = int(df["year"].max())
    latest_ratio = df.loc[df["year"] == latest_year, "ratio"].iloc[0]

    Y_DOMAIN = [-2.5, 0.25]
    Y_TICKS = [-2.5, -2.0, -1.5, -1.0, -0.5, 0.0]
    X_DOMAIN = [1958, 2029]
    X_TICKS = [1970, 1985, 2000, 2015]
    y_scale = alt.Scale(domain=Y_DOMAIN, nice=False)
    x_scale = alt.Scale(domain=X_DOMAIN, nice=False)

    header = make_header(
        "El Salvador: net migration as a share of population",
        width=WIDTH,
    )
    line = alt.Chart(df).mark_line(color=pallete["accent"], strokeWidth=2.75).encode(
        x=alt.X("year:Q", scale=x_scale, axis=alt.Axis(
            values=X_TICKS, format="d", grid=False, title=None, 
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        # Native Y axis replacing negative with typographical minus correctly
        y=alt.Y("ratio:Q", scale=y_scale, axis=alt.Axis(
            values=Y_TICKS, labelExpr="replace(format(datum.value, '.1f') + '%', '-', '\u2212')", 
            title="Net migration, % of population", grid=True,
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
    )
    civil_war_rule = ref_rule([1979, 1992], x_scale)
    bukele_rule, bukele_label = bukele_annotation(x_scale, y_scale, y_pos=-2.35)

    civil_war = alt.Chart(pd.DataFrame({"x": [1985.5], "y": [0.15], "label": ["Civil war"]})).mark_text(
        align="center", baseline="middle", fontSize=10.5, color=pallete["Deemphasize_Discrete"],
    ).encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="label")

    end = endpoint(latest_year, latest_ratio, x_scale, y_scale, fmt=".2f")

    main = alt.layer(civil_war_rule, bukele_rule, line,
                     civil_war, bukele_label, end).properties(width=WIDTH, height=HEIGHT)
    footer = make_footer("Source: World Bank, World Development Indicators. "
                         "Note: negative values indicate net emigration.", WIDTH)
    print(f"[fig5] latest_year={latest_year} latest_ratio={latest_ratio:.3f}%")
    return compose(header, main, footer)


# =============================================================================
# Shared builder for the two 4-country line panels (figs 6 & 8)
# =============================================================================
def _peer_panel(indicator, cache_name, cache_col, title, subtitle=None, footer_text="",
                y_domain=None, y_ticks=None, start_year=2015, end_year=2024, zero_line=False,
                bukele_label_y_offset=1.5, label_nudge=None, right_pad=3.0, x_ticks=None,
                y_title="", label_min_gap=None):
    df = load_wb(list(PEER_NAMES.keys()), indicator, start_year, end_year,
                 cache_path=os.path.join(CACHE_DIR, cache_name), cache_value_col=cache_col)
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
    df["country_name"] = df["country"].map(PEER_NAMES)

    latest_year = int(df["year"].max())
    for code, name in PEER_NAMES.items():
        vals = df[(df.country == code) & (df.year == latest_year)]["value"]
        if not vals.empty:
            print(f"[{indicator}] {name} ({latest_year}): {vals.iloc[0]:.1f}%")

    X_DOMAIN = [start_year - 0.7, end_year + right_pad]
    X_TICKS = x_ticks if x_ticks is not None else list(range(start_year, end_year + 1))
    y_scale = alt.Scale(domain=y_domain, nice=False)
    x_scale = alt.Scale(domain=X_DOMAIN, nice=False)
    color_scale = alt.Scale(domain=PEER_DOMAIN, range=PEER_RANGE)

    header = make_header(title, subtitle, WIDTH)
    peers = df[df["country"] != "SLV"]
    slv = df[df["country"] == "SLV"]

    lines_peers = alt.Chart(peers).mark_line(strokeWidth=1.75, opacity=0.85).encode(
        x=alt.X("year:Q", scale=x_scale, axis=alt.Axis(
            values=X_TICKS, format="d", grid=False, title=None, 
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        # Native Y axis
        y=alt.Y("value:Q", scale=y_scale, axis=alt.Axis(
            values=y_ticks, labelExpr="datum.value + '%'", title=y_title, grid=True,
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        color=alt.Color("country_name:N", scale=color_scale, legend=None),
    )
    line_slv = alt.Chart(slv).mark_line(strokeWidth=3).encode(
        x=alt.X("year:Q", scale=x_scale), y=alt.Y("value:Q", scale=y_scale),
        color=alt.Color("country_name:N", scale=color_scale, legend=None),
    )
    # Endpoint country labels with leader lines (same treatment as fig9).
    # Placement is owned here rather than delegated to end_labels(), so the
    # connector can be drawn to the exact nudged label position.
    latest = int(df["year"].max())
    last = df[df["year"] == latest].copy().sort_values("value").reset_index(drop=True)

    min_gap = label_min_gap if label_min_gap is not None else 0.0
    ys = last["value"].tolist()
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < min_gap:
            ys[i] = ys[i - 1] + min_gap
    over = (ys[-1] if ys else 0) - y_domain[1]
    if over > 0:
        ys = [y - over for y in ys]
    last["ylab"] = ys

    LABEL_X = latest + 0.35                    # anchor just right of the last point
    last["label_x"] = LABEL_X

    connectors = alt.Chart(last).mark_rule(strokeWidth=1, opacity=0.55).encode(
        x=alt.X("year:Q", scale=x_scale),
        y=alt.Y("value:Q", scale=y_scale),
        x2=alt.X2("label_x:Q"),
        y2=alt.Y2("ylab:Q"),
        color=alt.Color("country_name:N", scale=color_scale, legend=None))

    country_labels = alt.Chart(last).mark_text(
        align="left", baseline="middle", dx=4, fontSize=LABEL_SIZE, fontWeight=LABEL_WEIGHT).encode(
        x=alt.X("label_x:Q", scale=x_scale),
        y=alt.Y("ylab:Q", scale=y_scale),
        text="country_name:N",
        color=alt.Color("country_name:N", scale=color_scale, legend=None))

    bukele_rule, bukele_label = bukele_annotation(
        x_scale, y_scale, y_pos=y_domain[1] - bukele_label_y_offset)

    layers = [bukele_rule]
    if zero_line:
        layers.append(alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
            color=pallete["domain"], opacity=0.5, strokeWidth=1).encode(y=alt.Y("y:Q", scale=y_scale)))
    layers += [lines_peers, line_slv, connectors, country_labels, bukele_label]
    main = alt.layer(*layers).properties(width=WIDTH, height=HEIGHT)

    footer = make_footer(footer_text, WIDTH)
    return compose(header, main, footer)


def build_fig6():
    return _peer_panel(
        "NE.GDI.FTOT.ZS", "gfcf_4country_cache.csv", "gfcf_pct_gdp",
        "El Salvador: fixed investment as a share of GDP",
        footer_text="Source: World Bank, World Development Indicators.",
        y_domain=[0, 30], y_ticks=[0, 10, 20, 30], zero_line=False,
        x_ticks=[2015, 2018, 2021, 2024],
        y_title="Gross fixed capital formation, % of GDP",
        label_min_gap=1.6,
        label_nudge=None,
    )


def build_fig8():
    return _peer_panel(
        "BX.KLT.DINV.WD.GD.ZS", "fdi_4country_cache.csv", "fdi_pct_gdp",
        "El Salvador: foreign direct investment as a share of GDP",
        footer_text="Source: World Bank, World Development Indicators.",
        y_domain=[-1, 9], y_ticks=[0, 2, 4, 6, 8], zero_line=False, bukele_label_y_offset=0.5,
        x_ticks=[2015, 2018, 2021, 2024],
        y_title="FDI net inflows, % of GDP",
        label_min_gap=0.7,
        label_nudge=None,
    )


# =============================================================================
# FIGURE 7 -- real GDP per capita growth (bars, with 2025 estimate)
# =============================================================================
def build_fig7():
    raw = load_wb(["SLV"], "NY.GDP.PCAP.KD", 2010, 2024,
                  cache_path=os.path.join(CACHE_DIR, "wdi_gdp_per_capita_cache.csv"))
    levels = raw[raw["country"] == "SLV"].sort_values("year").reset_index(drop=True)
    levels["growth"] = levels["value"].pct_change() * 100
    levels["estimated"] = False

    est_2025 = 3.8 - 0.4  
    levels = pd.concat([levels, pd.DataFrame(
        {"country": ["SLV"], "year": [2025], "value": [None], "growth": [est_2025], "estimated": [True]}
    )], ignore_index=True)

    df = levels[(levels["year"] >= 2015) & (levels["year"] <= 2025)].reset_index(drop=True)
    df_chart = df.drop(columns=["value", "country"])

    def cagr(start_year, end_year):
        start_val = df.loc[df.year == start_year, "value"].iloc[0]
        if end_year == 2025:
            end_val = df.loc[df.year == 2024, "value"].iloc[0] * (1 + est_2025 / 100)
        else:
            end_val = df.loc[df.year == end_year, "value"].iloc[0]
        return ((end_val / start_val) ** (1 / (end_year - start_year)) - 1) * 100

    cagr_pre, cagr_post = cagr(2015, 2019), cagr(2022, 2025)
    print(f"[fig7] CAGR 2015-19: {cagr_pre:.2f}% | 2022-25: {cagr_post:.2f}%")

    Y_DOMAIN = [-9, 14]
    Y_TICKS = [-8, -4, 0, 4, 8, 12]
    X_ORDER = list(range(2015, 2026))
    y_scale = alt.Scale(domain=Y_DOMAIN)

    header = make_header(
        "El Salvador: real GDP per capita growth",
        width=WIDTH,
    )
    df_chart["highlight"] = df["year"].apply(
        lambda y: "covid" if y == 2020 else ("estimate" if y == 2025 else "normal"))
    color_scale = alt.Scale(domain=["normal", "covid", "estimate"],
                            range=[pallete["bar"]["accent_1"], pallete["bar"]["accent_2"], pallete["Other_3"]])

    bars = alt.Chart(df_chart).mark_bar(size=32).encode(
        x=alt.X("year:O", sort=X_ORDER, axis=alt.Axis(
            labelAngle=0, title=None, grid=False, 
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        # Native Y axis properly replacing negative numbers
        y=alt.Y("growth:Q", scale=y_scale, axis=alt.Axis(
            values=Y_TICKS, labelExpr="replace(datum.value + '%', '-', '\u2212')", title="Real GDP per capita, annual % change", grid=True,
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        color=alt.Color("highlight:N", scale=color_scale, legend=None),
    )
    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color=pallete["domain"], opacity=0.5, strokeWidth=1).encode(y=alt.Y("y:Q", scale=y_scale))

    growth_num = f"format(datum.growth, {SQ}.1f{SQ})"
    value_labels = alt.Chart(df_chart).mark_text(
        baseline="bottom", fontSize=9.5, color=pallete["domain"], dy=-3).transform_calculate(
        label=f'{_sign(growth_num)} + "%"',
        ypos="datum.growth >= 0 ? datum.growth : 0").encode(
        x=alt.X("year:O", sort=X_ORDER), y=alt.Y("ypos:Q", scale=y_scale), text="label:N")

    covid_label = alt.Chart(pd.DataFrame({"year": [2020], "y": [-8.2], "label": ["COVID shock"]})).mark_text(
        baseline="top", fontSize=10, color=pallete["Deemphasize_Discrete"]).encode(
        x=alt.X("year:O", sort=X_ORDER), y=alt.Y("y:Q", scale=y_scale), text="label")
    est_label = alt.Chart(pd.DataFrame({"year": [2025], "y": [12.5], "label": ["est."]})).mark_text(
        baseline="middle", fontSize=9, fontStyle="italic", color=pallete["Deemphasize_Discrete"]).encode(
        x=alt.X("year:O", sort=X_ORDER), y=alt.Y("y:Q", scale=y_scale), text="label")

    main = alt.layer(bars, zero_line, value_labels,
                     covid_label, est_label).properties(width=WIDTH, height=HEIGHT)
    footer = make_footer("Source: World Bank, World Development Indicators.", WIDTH)
    return compose(header, main, footer)


# =============================================================================
# FIGURE 9 -- Freedom House A-G subcategory scores (% of maximum)
# =============================================================================
def build_fig9():
    CACHE_PATH = os.path.join(CACHE_DIR, "freedom_house_subcategories_cache.csv")
    PRIMARY_URL = "https://freedomhouse.org/sites/default/files/2025-02/All_data_FIW_2013-2024.xlsx"
    FALLBACK_URL = ("https://freedomhouse.org/sites/default/files/2024-02/"
                    "Aggregate_Category_and_Subcategory_Scores_FIW_2003-2024.xlsx")

    SUBCATS = ["A", "B", "C", "D", "E", "F", "G"]
    MAXIMA = {"A": 12, "B": 16, "C": 12, "D": 16, "E": 12, "F": 16, "G": 16}
    LABELS = {
        "A": "A. Electoral Process", "B": "B. Political Pluralism & Participation",
        "C": "C. Functioning of Government", "D": "D. Freedom of Expression & Belief",
        "E": "E. Associational & Organizational Rights", "F": "F. Rule of Law",
        "G": "G. Personal Autonomy & Individual Rights",
    }
    SHORT_LABELS = {
        "A": "Electoral process", "B": "Political pluralism",
        "C": "Functioning of gov't", "D": "Expression & belief",
        "E": "Associational rights", "F": "Rule of law",
        "G": "Personal autonomy",
    }

    def from_bulk(url):
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        xls = pd.ExcelFile(BytesIO(resp.content))
        country_names = ("country", "fh_country", "country/territory", "country/ territory")
        for sheet in xls.sheet_names:
            for hdr in (0, 1, 2):
                try:
                    d = xls.parse(sheet, header=hdr)
                except Exception:  # noqa: BLE001
                    continue
                d.columns = [str(c).strip() for c in d.columns]
                ccol = next((c for c in d.columns if c.lower() in country_names), None)
                ycol = next((c for c in d.columns if c.lower() in ("year", "edition")), None)
                if ccol is None or ycol is None or not all(s in d.columns for s in SUBCATS):
                    continue
                sel = d[d[ccol].astype(str).str.strip().str.lower() == "el salvador"].copy()
                if sel.empty:
                    continue
                sel = sel.rename(columns={ycol: "year"})
                sel["year"] = pd.to_numeric(sel["year"], errors="coerce")
                if ycol.lower() == "edition":
                    sel["year"] = sel["year"] - 1   
                sel = sel.dropna(subset=["year"])
                sel["year"] = sel["year"].astype(int)
                print(f"[fig9] parsed sheet='{sheet}' header_row={hdr} year_col='{ycol}'")
                return sel[["year"] + SUBCATS].sort_values("year")
        raise RuntimeError(f"Could not locate El Salvador A-G subcategory rows in {url}")

    raw = None
    for url in (PRIMARY_URL, FALLBACK_URL):
        try:
            raw = from_bulk(url)
            print(f"[fig9] loaded from {url}")
            break
        except Exception as e:  # noqa: BLE001
            print(f"[warn] {url} failed: {e}", file=sys.stderr)
    if raw is None:
        print("[warn] using manually verified 2017-2024 cache.", file=sys.stderr)
        raw = pd.read_csv(CACHE_PATH, comment="#")

    raw = raw[(raw["year"] >= 2017) & (raw["year"] <= 2024)].copy()
    df = raw.melt(id_vars="year", value_vars=SUBCATS, var_name="subcat", value_name="score")
    df["max_score"] = df["subcat"].map(MAXIMA)
    df["pct"] = df["score"] / df["max_score"] * 100
    df["label"] = df["subcat"].map(LABELS)
    df["short"] = df["subcat"].map(SHORT_LABELS)

    Y_DOMAIN, Y_TICKS = [0, 100], [0, 20, 40, 60, 80, 100]
    X_DOMAIN, X_TICKS = [2016.5, 2028], [2018, 2020, 2022, 2024]
    y_scale = alt.Scale(domain=Y_DOMAIN, nice=False)
    x_scale = alt.Scale(domain=X_DOMAIN, nice=False)

    color_scale = alt.Scale(domain=[LABELS[s] for s in SUBCATS], range=[
        pallete["nominal_1"], pallete["nominal_2"], pallete["nominal_3"], pallete["nominal_4"],
        pallete["nominal_5"], pallete["nominal_6"], pallete["Deemphasize_Other"]])

    header = make_header(
        "El Salvador: Freedom House subcategory scores",
        width=WIDTH,
    )
    lines = alt.Chart(df).mark_line(strokeWidth=2.25).encode(
        x=alt.X("year:Q", scale=x_scale, axis=alt.Axis(
            values=X_TICKS, format="d", grid=False, title=None, 
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        # Native Y axis
        y=alt.Y("pct:Q", scale=y_scale, axis=alt.Axis(
            values=Y_TICKS, labelExpr="datum.value + '%'", title="Subcategory score, % of maximum", grid=True,
            domain=True, domainColor=pallete["domain"], domainWidth=1, domainOpacity=0.5)),
        color=alt.Color("label:N", scale=color_scale, legend=None),
    )

    last = df[df["year"] == int(df["year"].max())].copy().sort_values("pct").reset_index(drop=True)
    MIN_GAP = 6.0  
    ys = last["pct"].tolist()
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < MIN_GAP:
            ys[i] = ys[i - 1] + MIN_GAP
    over = (ys[-1] if ys else 0) - Y_DOMAIN[1]
    if over > 0:
        ys = [y - over for y in ys]
    last["ylab"] = ys

    # Leader line: connect each line's true endpoint (year_max, pct) to its
    # nudged label anchor (label_x, ylab). Because MIN_GAP pushes labels off
    # their lines, the connector keeps label -> line unambiguous.
    LABEL_X = int(df["year"].max()) + 0.35   # anchor just right of the last point
    last["label_x"] = LABEL_X

    connectors = alt.Chart(last).mark_rule(strokeWidth=1, opacity=0.55).encode(
        x=alt.X("year:Q", scale=x_scale),
        y=alt.Y("pct:Q", scale=y_scale),
        x2=alt.X2("label_x:Q"),
        y2=alt.Y2("ylab:Q"),
        color=alt.Color("label:N", scale=color_scale, legend=None))

    cat_labels = alt.Chart(last).mark_text(
        align="left", baseline="middle", dx=4, fontSize=LABEL_SIZE, fontWeight=LABEL_WEIGHT).encode(
        x=alt.X("label_x:Q", scale=x_scale),
        y=alt.Y("ylab:Q", scale=y_scale),
        text="short:N",
        color=alt.Color("label:N", scale=color_scale, legend=None))

    bukele_rule, bukele_label = bukele_annotation(x_scale, y_scale, y_pos=96)

    main = alt.layer(bukele_rule, lines, connectors, cat_labels, bukele_label).properties(
        width=WIDTH, height=HEIGHT)
    footer = make_footer("Source: Freedom House, Freedom in the World.", WIDTH)
    return compose(header, main, footer)


# =============================================================================
# REGISTRY + RUNNER
# =============================================================================
FIGURES = {
    "fig1_gdp_relative": build_fig1,
    "fig2_market_share": build_fig2,
    "fig3_exports_per_capita": build_fig3,
    "fig5_net_migration": build_fig5,
    "fig6_investment": build_fig6,
    "fig7_gdp_growth": build_fig7,
    "fig8_fdi": build_fig8,
    "fig9_freedom_house": build_fig9,
}


def run(*names):
    names = names or list(FIGURES.keys())
    for n in names:
        if n not in FIGURES:
            print(f"[skip] unknown figure '{n}'. Known: {', '.join(FIGURES)}", file=sys.stderr)
            continue
        print(f"\n=== {n} ===")
        try:
            save_chart(FIGURES[n](), n)
        except Exception as e:  # noqa: BLE001
            print(f"[error] {n} failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    requested = [a for a in sys.argv[1:] if a in FIGURES]
    run(*requested)