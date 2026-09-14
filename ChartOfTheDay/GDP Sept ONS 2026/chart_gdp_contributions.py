"""
Chart of the Day options - UK monthly GDP, July 2026 release.

Single named primary source:
    ONS, "Contributions to monthly GDP", monthlycontributionstablesjuly26.xlsx,
    released 11 September 2026, published alongside
    "GDP monthly estimate, UK: July 2026".
    https://www.ons.gov.uk/economy/grossdomesticproductgdp/datasets/contributionstomonthlygdp

Every plotted value is read straight out of the CONTRIBUTIONS worksheet. Nothing
is summed, differenced, rebased, ranked or converted to a share. Sector
aggregates and their components are never mixed in one chart, so no figure is
double counted.

The source file is expected at:
    /Users/alonso/Documents/GitHub/RADataHub/ChartOfTheDay/GDP Sept ONS 2026/
        monthlycontributionstablesjuly26.xlsx

Usage:  python chart_gdp_contributions.py [a|b|c]   (default: all three)
"""

import json
import os
import sys

import altair as alt
import pandas as pd

import eco_style

PROJECT = "/Users/alonso/Documents/GitHub/RADataHub/ChartOfTheDay/GDP Sept ONS 2026"

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # Positron does not define __file__
    HERE = PROJECT

# Read the ONS download directly. No intermediate CSV, no copy in the repo root.
SRC = os.path.join(PROJECT, "monthlycontributionstablesjuly26.xlsx")

# Outputs land beside the script. Point this at os.path.join(HERE, "charts") if
# you would rather keep the folder tidy.
OUTDIR = HERE

alt.theme.enable("report")

_FONTS = os.path.join(HERE, "fonts")
if os.path.isdir(_FONTS):
    import vl_convert as vlc

    vlc.register_font_directory(_FONTS)

SHEET = "CONTRIBUTIONS"
HEADER_ROW = 4  # zero-indexed: worksheet row 5 carries the column names
LATEST = "2026 Jul"

CAT_MM = "Contribution to growth, latest month on previous month"
CAT_3M = "Contribution to growth, latest 3 months on previous 3 months"

TOTAL = "Total GVA at basic prices (A - T)"
PRODUCTION = "Total production industries (B - E)"
SERVICES = "Total service industries (G-T)"
CONSTRUCTION = "Construction (F) [note 5]"
AGRICULTURE = "Agriculture, forestry and fishing (A)"
INFOCOMM = "Information and communication (J)"

# SIC sections only. Deliberately excludes TOTAL, PRODUCTION and SERVICES so no
# industry is counted twice inside its own aggregate.
SECTIONS = {
    AGRICULTURE: "Agriculture, forestry and fishing",
    "Mining and Quarrying (B)": "Mining and quarrying",
    "Manufacturing (C)": "Manufacturing",
    "Electricity, gas, steam and air (D)": "Electricity and gas supply",
    "Water supply, sewerage etc (E)": "Water and waste",
    CONSTRUCTION: "Construction",
    "Wholesale and retail: repair of motor vehicles and motorcycles (G)": "Wholesale and retail",
    "Transport and storage (H)": "Transport and storage",
    "Accommodation and food service activities (I)": "Accommodation and food",
    INFOCOMM: "Information and communication",
    "Financial and insurance activities (K)": "Finance and insurance",
    "Real estate activities (L)": "Real estate",
    "Professional, scientific and technical activities (M)": "Professional and scientific",
    "Administrative and support service activities (N)": "Admin and support services",
    "Public administration and defence (O)": "Public administration and defence",
    "Education (P)": "Education",
    "Human health and social work activities (Q)": "Health and social work",
    "Arts, entertainment and recreation (R)": "Arts and recreation",
    "Other service activities (S)": "Other services",
    "Activities of households as employers, undifferentiated goods and services (T)": "Households as employers",
}

NOTE_SRC = "Source: ONS, Contributions to monthly GDP, released 11 September 2026."
NOTE_REV = "Early estimates of GDP are subject to revision."


# ---------------------------------------------------------------- helpers ----
def tint(key: str, alpha: float) -> str:
    """Bake opacity into a solid hex: vl-convert drops rgba() alpha on mark
    colour properties. Colours stay sourced from eco_style.pallete."""
    base = eco_style.pallete[key].lstrip("#")
    rgb = [int(base[i : i + 2], 16) for i in (0, 2, 4)]
    mixed = [round(c * alpha + 255 * (1 - alpha)) for c in rgb]
    return "#" + "".join(f"{c:02x}" for c in mixed)


def fmt(x: float, dp: int = 2) -> str:
    """Display formatting only. Unicode minus (U+2212) for rendered negatives."""
    s = f"{abs(x):.{dp}f}"
    if x < 0:
        return "\u2212" + s
    return s


def title_block(text, subtitle=None, size=17, dx=0):
    return alt.TitleParams(
        text=text,
        subtitle=subtitle if subtitle is not None else "",
        anchor="start",
        fontSize=size,
        subtitleFontSize=13,
        subtitleColor=tint("domain", 0.7),
        offset=18,
        dx=dx,
    )


def wrap(plot, note, dx=2):
    """vconcat wrapper anchors title, plot and note to the same canvas-left
    edge whatever the axis labels do."""
    return (
        alt.vconcat(plot)
        .properties(
            title=alt.TitleParams(
                text=note,
                orient="bottom",
                anchor="start",
                fontSize=10,
                fontWeight="normal",
                color=tint("domain", 0.65),
                dx=dx,
                offset=14,
            )
        )
        .configure_view(strokeWidth=0, stroke=None)
    )


# Every layer on a shared scale must carry an identical y encoding: one layer
# with axis=None rewrites the axis for the whole layered view. So all frames use
# a column called "value" and this builds the same encoding each time.
Y_VALUES = [-0.2, 0, 0.2, 0.4, 0.6, 0.8]


def Y(domain, title=None, pct=False):
    """pct appends a % sign to tick labels. Values are already in percent
    units, so the d3 '%' format (which multiplies by 100) is not used."""
    axis = dict(title=title, values=Y_VALUES, format=".1f")
    if pct:
        axis["labelExpr"] = "format(datum.value, '.1f') + '%'"
    return alt.Y("value:Q", scale=alt.Scale(domain=domain), axis=alt.Axis(**axis))


def X_MONTHS(start, end, ticks):
    """Domain runs past the last observation so end-of-line labels fit inside
    the plot. Ticks are listed explicitly so no empty month gets one."""
    return alt.X(
        "date:T",
        scale=alt.Scale(domain=[start, end]),
        axis=alt.Axis(title=None, format="%b %Y", labelFontSize=11,
                      values=[{"year": y, "month": m, "date": 1} for y, m in ticks],
                      grid=False),
    )


def annot(text, colour_key, date, value, x, y, size=12, align="left"):
    """Series name parked in empty plot space, in place of a legend entry. Takes
    the shared x and y encodings so it cannot rewrite the axes."""
    return (
        alt.Chart(pd.DataFrame({"date": [pd.Timestamp(date)], "value": [value]}))
        .mark_text(align=align, baseline="middle", fontSize=size, fontWeight="bold",
                   color=eco_style.pallete[colour_key])
        .encode(x=x, y=y, text=alt.value(text))
    )


# ------------------------------------------------------------------- load ----
def load() -> pd.DataFrame:
    if not os.path.isfile(SRC):
        raise FileNotFoundError(
            f"ONS source file not found at:\n  {SRC}\n"
            "Download 'Contributions to monthly GDP' from "
            "https://www.ons.gov.uk/economy/grossdomesticproductgdp/datasets/"
            "contributionstomonthlygdp and save it there."
        )
    raw = pd.read_excel(SRC, sheet_name=SHEET, header=HEADER_ROW)
    raw.columns = [str(c).strip() for c in raw.columns]

    # --- parse tripwires: a shifted column must crash, never plot ------------
    assert list(raw.columns[:2]) == ["Time Period", "Category"], "header row moved"
    for col in (TOTAL, PRODUCTION, SERVICES, CONSTRUCTION, AGRICULTURE, INFOCOMM):
        assert col in raw.columns, f"missing column: {col}"
    for col in SECTIONS:
        assert col in raw.columns, f"missing section column: {col}"

    # Each growth measure has its own block of ONS four-character series IDs.
    # Checking them pins the column positions: a shifted column changes the ID.
    ids = raw[raw["Time Period"] == "[Not applicable]"].set_index("Category")
    assert len(ids) == 4, "expected one series-ID row per growth measure"
    EXPECTED_IDS = {
        CAT_MM: {TOTAL: "EDKH", SERVICES: "EDKP", INFOCOMM: "EDKT"},
        CAT_3M: {TOTAL: "EDMB", SERVICES: "EDMJ", INFOCOMM: "EDMN"},
    }
    for cat, wanted in EXPECTED_IDS.items():
        for col, sid in wanted.items():
            got = ids.loc[cat, col]
            assert got == sid, f"{cat}: expected {sid} under {col}, found {got}"

    df = raw[raw["Time Period"] != "[Not applicable]"].copy()
    df = df[df["Category"] != "Weight"]
    assert set(df["Category"]) >= {CAT_MM, CAT_3M}, "growth measures renamed"
    df["date"] = pd.to_datetime(df["Time Period"], format="%Y %b")
    # month names do not sort lexicographically, so check the parsed date
    newest = df.loc[df["date"].idxmax(), "Time Period"]
    assert newest == LATEST, f"latest period is {newest}, expected {LATEST}"

    num = [c for c in raw.columns if c not in ("Time Period", "Category")]
    df[num] = df[num].apply(pd.to_numeric, errors="raise")

    # anchor on the two figures the bulletin prints in words
    latest3 = df[(df.Category == CAT_3M) & (df["Time Period"] == LATEST)].iloc[0]
    assert round(latest3[TOTAL], 2) == 0.40, "headline GDP no longer 0.4%"
    assert round(latest3[SERVICES], 2) == 0.48, "services contribution changed"

    # Title claims, checked against the full series rather than assumed.
    # A: "Services is the only sector still adding to UK growth"
    others = [PRODUCTION, CONSTRUCTION, AGRICULTURE]
    assert latest3[SERVICES] > 0 and all(latest3[c] <= 0 for c in others), \
        "services is no longer the only positive main-sector contribution"
    # B: "Professional services and IT drove UK growth"
    top2 = sorted(SECTIONS, key=lambda c: latest3[c], reverse=True)[:2]
    assert set(top2) == {"Professional, scientific and technical activities (M)", INFOCOMM}, \
        f"largest two section contributions have changed: {top2}"
    # C: "adding steadily more since last autumn"
    j = three_month(df)[INFOCOMM]
    assert j.iloc[-1] > j.iloc[-10], "information and communication is no longer climbing"
    assert (j >= 0).all(), "section J contribution has turned negative"
    return df


def three_month(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.Category == CAT_3M].sort_values("date").reset_index(drop=True)


# -------------------------------------------------------------- figure A -----
def fig_a(df: pd.DataFrame):
    """Direct recreation: stacked sector contributions plus the GDP line."""
    w = three_month(df)
    w = w[w.date >= pd.Timestamp("2025-07-01")]

    order = ["Services", "Production", "Construction"]
    colours = [
        eco_style.pallete["nominal_1"],
        eco_style.pallete["nominal_2"],
        eco_style.pallete["nominal_6"],
    ]
    bars_df = (
        w[["date", SERVICES, PRODUCTION, CONSTRUCTION]]
        .rename(columns={SERVICES: "Services", PRODUCTION: "Production",
                         CONSTRUCTION: "Construction"})
        .melt("date", var_name="sector", value_name="value")
    )
    line_df = w[["date", TOTAL]].rename(columns={TOTAL: "value"})
    line_df["series"] = "GDP (%)"

    DOM = [-0.22, 0.85]
    y = Y(DOM, title="", pct=True)
    x = X_MONTHS("2025-06-12", "2026-08-14",
                 [(2025, 7), (2025, 9), (2025, 11), (2026, 1), (2026, 3), (2026, 5), (2026, 7)])

    bars = (
        alt.Chart(bars_df)
        .mark_bar(width=22)
        .encode(
            x=x,
            y=y,
            color=alt.Color(
                "sector:N",
                scale=alt.Scale(domain=order, range=colours),
                legend=alt.Legend(title=None, orient="none", legendX=-58, legendY=-30,
                                  direction="horizontal", labelFontSize=12,
                                  symbolType="square", symbolSize=120),
            ),
            order=alt.Order("sector:N", sort="ascending"),
        )
    )
    line = (
        alt.Chart(line_df)
        .mark_line(color=eco_style.pallete["nominal_4"], strokeWidth=2.5,
                   point=alt.OverlayMarkDef(color=eco_style.pallete["nominal_4"], size=30))
        .encode(
            x=x,
            y=y,
            # Own colour scale (resolved independent below) so the legend entry
            # draws as a line rather than a bar square.
            color=alt.Color(
                "series:N",
                scale=alt.Scale(domain=["GDP (%)"], range=[eco_style.pallete["nominal_4"]]),
                legend=alt.Legend(title=None, orient="none", legendX=204, legendY=-32,
                                  labelFontSize=12, symbolType="stroke",
                                  symbolStrokeWidth=2.5, symbolSize=200),
            ),
        )
    )
    tag = (
        alt.Chart(line_df.tail(1))
        .mark_text(align="left", baseline="middle", dx=8, fontSize=12, fontWeight="bold",
                   color=eco_style.pallete["nominal_4"])
        .encode(x=x, y=y, text=alt.value("0.4%"))
    )
    zero = (
        alt.Chart(pd.DataFrame({"value": [0.0]}))
        .mark_rule(color=eco_style.pallete["domain"], strokeWidth=1, opacity=0.55)
        .encode(y=y)
    )

    plot = alt.layer(zero, bars, line, tag).resolve_scale(color="independent").properties(
        width=560,
        height=272,
        title=title_block(
            "The services sector contributed to UK growth over the three months to July",
            "Sector contributions to three-month on three-month GDP growth, UK",
            dx=-29,
        ),
    )
    note = [
        "Source: ONS, Contributions to monthly GDP, released 11 September 2026."
    ]
    return wrap(plot, note), "a_gdp_contributions_stack"


# -------------------------------------------------------------- figure B -----
def fig_b(df: pd.DataFrame):
    """Where the growth came from: SIC section contributions to the latest period."""
    row = three_month(df).iloc[-1]
    d = pd.DataFrame(
        {"industry": list(SECTIONS.values()),
         "pp": [row[c] for c in SECTIONS]}
    ).sort_values("pp", ascending=False)
    d["label"] = d["pp"].map(lambda v: fmt(v, 2))
    order = d["industry"].tolist()  # explicit: sort= is unreliable when layered

    x = alt.X("pp:Q", scale=alt.Scale(domain=[-0.09, 0.22]), axis=None)
    y = alt.Y("industry:N", scale=alt.Scale(domain=order, paddingInner=0.28),
              axis=alt.Axis(title=None, labelFontSize=11, labelPadding=8,
                            labelLimit=260, domain=False))
    colour = alt.Color(
        "sign:N",
        scale=alt.Scale(domain=["up", "down"],
                        range=[eco_style.pallete["nominal_1"], eco_style.pallete["nominal_2"]]),
        legend=None,
    )
    d["sign"] = d["pp"].map(lambda v: "down" if v < 0 else "up")

    bars = alt.Chart(d).mark_bar(height=13).encode(x=x, y=y, color=colour)
    zero = (
        alt.Chart(pd.DataFrame({"pp": [0.0]}))
        .mark_rule(color=eco_style.pallete["domain"], strokeWidth=1, opacity=0.55)
        .encode(x=x)
    )

    def labels(sub, align, dx):
        return (
            alt.Chart(sub)
            .mark_text(align=align, baseline="middle", dx=dx, fontSize=11,
                       color=eco_style.pallete["domain"])
            .encode(x=x, y=y, text="label:N")
        )

    plot = alt.layer(
        zero, bars, labels(d[d.pp >= 0], "left", 5), labels(d[d.pp < 0], "right", -5)
    ).properties(
        width=330,
        height=430,
        title=title_block(
            "Professional services and IT drove UK growth",
            "Industry contributions to the UK's 0.4% growth, three months to July 2026, "
            "percentage points",
        ),
    )
    note = [
        "Source: ONS, Contributions to monthly GDP, released 11 September 2026. SIC 2007",
        "sections. Sector aggregates are excluded, so no industry is counted twice.",
        "Components may not sum to the total. " + NOTE_REV,
    ]
    return wrap(plot, note), "b_industry_contributions"


# -------------------------------------------------------------- figure C -----
def fig_c(df: pd.DataFrame):
    """The AI hook: information and communication against total GDP growth."""
    w = three_month(df)
    bars_df = w[["date", INFOCOMM]].rename(columns={INFOCOMM: "value"})
    line_df = w[["date", TOTAL]].rename(columns={TOTAL: "value"})

    DOM = [-0.22, 0.85]
    x = X_MONTHS("2024-06-14", "2026-09-06",
                 [(2024, 7), (2024, 10), (2025, 1), (2025, 4), (2025, 7), (2025, 10),
                  (2026, 1), (2026, 4), (2026, 7)])

    bars = (
        alt.Chart(bars_df)
        .mark_bar(width=13, color=eco_style.pallete["nominal_1"])
        .encode(x=x, y=Y(DOM))
    )
    line = (
        alt.Chart(line_df)
        .mark_line(color=eco_style.pallete["nominal_4"], strokeWidth=2.5)
        .encode(x=x, y=Y(DOM))
    )
    zero = (
        alt.Chart(pd.DataFrame({"value": [0.0]}))
        .mark_rule(color=eco_style.pallete["domain"], strokeWidth=1, opacity=0.55)
        .encode(y=Y(DOM))
    )
    tag_total = (
        alt.Chart(line_df.tail(1))
        .mark_text(align="left", baseline="middle", dx=8, fontSize=12, fontWeight="bold",
                   color=eco_style.pallete["nominal_4"])
        .encode(x=x, y=Y(DOM), text=alt.value("0.40"))
    )
    tag_j = (
        alt.Chart(bars_df.tail(1))
        .mark_text(align="left", baseline="middle", dx=8, fontSize=12, fontWeight="bold",
                   color=eco_style.pallete["nominal_1"])
        .encode(x=x, y=Y(DOM), text=alt.value("0.17"))
    )
    names = alt.layer(
        annot("All GDP growth", "nominal_4", "2024-07-20", 0.80, x, Y(DOM)),
        annot("Information and communication", "nominal_1", "2024-07-20", 0.70, x, Y(DOM)),
    )

    plot = alt.layer(zero, bars, line, tag_total, tag_j, names).properties(
        width=560,
        height=280,
        title=title_block(
            "Information and communication is adding steadily more to UK growth",
            "Contribution to three-month on three-month GDP growth, UK, percentage points",
            size=16,
        ),
    )
    note = [
        "Source: ONS, Contributions to monthly GDP, released 11 September 2026. Information and",
        "communication is SIC 2007 section J. ONS reports that many of the largest-turnover businesses",
        "in it are involved in AI and cloud computing, but says the exact impact is difficult to",
        "quantify. " + NOTE_REV,
    ]
    return wrap(plot, note), "c_info_comms_contribution"


FIGURES = {"a": fig_a, "b": fig_b, "c": fig_c}


def main() -> None:
    # Positron leaks kernel arguments into sys.argv, so filter to known names.
    wanted = [a for a in sys.argv[1:] if a in FIGURES] or list(FIGURES)
    os.makedirs(OUTDIR, exist_ok=True)
    df = load()
    print("read", SRC)
    for key in wanted:
        chart, name = FIGURES[key](df)
        chart.save(os.path.join(OUTDIR, f"{name}.png"), scale_factor=3)
        chart.save(os.path.join(OUTDIR, f"{name}.svg"))
        with open(os.path.join(OUTDIR, f"{name}.json"), "w") as fh:
            json.dump(chart.to_dict(), fh, indent=2)
        print("wrote", name)
    print("outputs in", OUTDIR)


if __name__ == "__main__":
    main()
