"""
YNY peer comparison charts, styled with the eco_style Altair theme.

Reads two ONS Explore Local Statistics files and writes two chart PNGs
comparing York & North Yorkshire against West Yorkshire, South Yorkshire,
Tees Valley, Greater Manchester and England on:
    1. Modelled unemployment rate, 2004-2023
    2. Inward FDI stock, 2015-2024 (indexed growth + 2024 absolute ranking)

Requires: pandas, altair >= 5, openpyxl, vl-convert-python (for PNG export).
The eco_style.py theme file must sit next to this script (or be importable).
"""
from pathlib import Path

import altair as alt
import pandas as pd

# Importing eco_style registers 'report', 'light', 'dark' themes with Altair.
import eco_style
from eco_style import pallete


def _sub_font(node, font):
    """Recursively replace any 'font' or 'labelFont' key inside a theme dict."""
    if isinstance(node, dict):
        return {k: (font if k in ("font", "labelFont") else _sub_font(v, font))
                for k, v in node.items()}
    return node


def _report_local():
    """The eco 'report' theme with Circular Std swapped for a font that
    vl-convert bundles. Falls back gracefully in the browser too.
    """
    return _sub_font(eco_style.report(), "Liberation Sans, Helvetica, Arial, sans-serif")


alt.themes.register("report_local", _report_local)
alt.themes.enable("report_local")

# --- Config ---------------------------------------------------------------

DATA_DIR = Path("/Users/alonso/Desktop/York and North Yorkshire")
UNEMP_FILE = DATA_DIR / "modelled-unemployment.xlsx"
FDI_FILE = DATA_DIR / "inward-foreign-direct-investment.xlsx"
OUTPUT_DIR = DATA_DIR

# ONS area code -> display name. Order controls legend order.
PEERS = {
    "E47000012": "York and North Yorkshire",
    "E47000003": "West Yorkshire",
    "E47000002": "South Yorkshire",
    "E47000006": "Tees Valley",
    "E47000001": "Greater Manchester",
    "E92000001": "England",
}
HIGHLIGHT = "York and North Yorkshire"
BASELINE = "England"

# Peers mapped to eco palette colours. YNY takes the accent red;
# England uses the theme's baseline "deemphasize" colour and a dashed stroke.
COLORS = {
    "York and North Yorkshire": pallete["nominal_2"],  # #e6224b red — highlight
    "West Yorkshire":           pallete["nominal_1"],  # #179fdb blue
    "South Yorkshire":          pallete["nominal_6"],  # #36b7b4 teal
    "Tees Valley":              pallete["nominal_5"],  # #eb5c2e orange
    "Greater Manchester":       pallete["nominal_4"],  # #122b39 dark navy
    "England":                  pallete["Deemphasize_Discrete"],
}

# --- Data loading ---------------------------------------------------------

def load_peer_long(path, header_row, measure_filter=None):
    """Read an ONS Explore Local Statistics workbook and return a long-form
    DataFrame with columns [year, msa, value] for the PEERS defined above.
    """
    df = pd.read_excel(path, sheet_name="1", header=header_row)
    if measure_filter is not None:
        df = df[df["Measure"] == measure_filter]
    df = df.set_index("Area code")

    year_cols = [c for c in df.columns if isinstance(c, str) and c.startswith("20")]
    records = []
    for code, name in PEERS.items():
        for c in year_cols:
            records.append({
                "year": int(c[:4]),
                "msa": name,
                "value": pd.to_numeric(df.loc[code, c], errors="coerce"),
            })
    return pd.DataFrame(records).dropna(subset=["value"])


def stagger(series, min_gap):
    """Return y-positions matching `series` order, shifted so consecutive
    labels never sit closer than `min_gap`.
    """
    order = sorted(enumerate(series), key=lambda t: t[1])
    placed = {}
    prev = None
    for i, v in order:
        y = v if prev is None else max(v, prev + min_gap)
        placed[i] = y
        prev = y
    return [placed[i] for i in range(len(series))]


# --- Shared encoding helpers ---------------------------------------------

PEER_ORDER = list(PEERS.values())
COLOR_SCALE = alt.Scale(domain=PEER_ORDER, range=[COLORS[n] for n in PEER_ORDER])


def layered_lines(df, x_field, y_field, y_title,
                  x_domain=None, y_domain=None,
                  highlight_stroke=3.0, other_stroke=1.6):
    """Line chart in three layers: non-highlight peers, dashed baseline,
    then the highlighted peer on top.
    """
    def base(source):
        x_scale = alt.Scale(domain=x_domain) if x_domain else alt.Undefined
        y_scale = alt.Scale(domain=y_domain) if y_domain else alt.Undefined
        return alt.Chart(source).encode(
            x=alt.X(f"{x_field}:Q", title=None, axis=alt.Axis(format="d"),
                    scale=x_scale),
            y=alt.Y(f"{y_field}:Q", title=y_title, scale=y_scale),
            color=alt.Color("msa:N", scale=COLOR_SCALE,
                            legend=alt.Legend(title=None, orient="top-right",
                                              symbolStrokeWidth=2)),
        )

    others = df[~df["msa"].isin([HIGHLIGHT, BASELINE])]
    highlight = df[df["msa"] == HIGHLIGHT]
    baseline = df[df["msa"] == BASELINE]

    return (
        base(others).mark_line(strokeWidth=other_stroke) +
        base(baseline).mark_line(strokeWidth=other_stroke, strokeDash=[4, 3]) +
        base(highlight).mark_line(strokeWidth=highlight_stroke)
    )


def endpoint_labels(df, x_field, y_field, x_offset=0.4, min_gap=0.35, fmt="{:.1f}%"):
    """Text-mark layer showing values at the latest x for each peer, with
    labels vertically staggered to avoid overlap.
    """
    latest = df.loc[df[x_field] == df[x_field].max()].copy()
    latest = latest.set_index("msa").loc[PEER_ORDER].reset_index()
    latest["label_y"] = stagger(latest[y_field].tolist(), min_gap)
    latest["label"] = latest[y_field].map(lambda v: fmt.format(v))
    latest["label_x"] = latest[x_field] + x_offset

    def text_layer(source, weight):
        return alt.Chart(source).mark_text(
            align="left", fontSize=11, fontWeight=weight,
        ).encode(
            x=alt.X("label_x:Q"),
            y=alt.Y("label_y:Q"),
            text="label:N",
            color=alt.Color("msa:N", scale=COLOR_SCALE, legend=None),
        )

    hi = latest[latest["msa"] == HIGHLIGHT]
    other = latest[latest["msa"] != HIGHLIGHT]
    return text_layer(other, "normal") + text_layer(hi, "bold")


# --- Chart 1: unemployment -----------------------------------------------

def chart_unemployment():
    df = load_peer_long(UNEMP_FILE, header_row=5,
                        measure_filter="Observation value")

    lines = layered_lines(
        df, x_field="year", y_field="value",
        y_title="Modelled unemployment rate (%)",
        x_domain=[2003.5, 2026], y_domain=[0, 13.5],
    )
    labels = endpoint_labels(df, x_field="year", y_field="value",
                             x_offset=0.4, min_gap=0.4, fmt="{:.1f}%")

    chart = (lines + labels).properties(
        title=alt.TitleParams(
            text="York & North Yorkshire has the lowest unemployment rate "
                 "of its Yorkshire and Established peers",
            subtitle="Source: ONS Explore Local Statistics — Modelled "
                     "unemployment rate, published 16/04/2024. Ages 16+.",
            anchor="start",
            fontSize=14,
            subtitleFontSize=10,
            subtitleColor="#555",
            subtitleFontStyle="italic",
        ),
        width=720, height=420,
    )
    save_chart(chart, "01_unemployment")


# --- Chart 2: inward FDI --------------------------------------------------

def chart_fdi():
    df = load_peer_long(FDI_FILE, header_row=4)  # no Measure column

    # Index each peer to its 2015 value = 100
    base_year = df["year"].min()
    baselines = df[df["year"] == base_year].set_index("msa")["value"]
    df["index"] = df.apply(lambda r: r["value"] / baselines[r["msa"]] * 100, axis=1)

    # Left panel: indexed growth
    idx_df = df.rename(columns={"value": "raw", "index": "value"})
    lines = layered_lines(
        idx_df, x_field="year", y_field="value",
        y_title="Inward FDI stock (index, 2015 = 100)",
        x_domain=[2014.5, 2025.5],
    )
    labels = endpoint_labels(idx_df, x_field="year", y_field="value",
                             x_offset=0.15, min_gap=8, fmt="{:.0f}")
    reference = alt.Chart(pd.DataFrame({"y": [100]})).mark_rule(
        strokeDash=[2, 3], color="#999", strokeWidth=0.7
    ).encode(y="y:Q")

    left = (reference + lines + labels).properties(
        title=alt.TitleParams(
            text="YNY FDI stock grew fastest — 157% since 2015",
            subtitle="Source: ONS Explore Local Statistics — Inward foreign "
                     "direct investment, published 12/05/2026. End-period "
                     "stock values.",
            anchor="start", fontSize=13,
            subtitleFontSize=10,
            subtitleColor="#555",
            subtitleFontStyle="italic",
        ),
        width=460, height=380,
    )

    # Right panel: 2024 absolute stock (£bn), horizontal bar, MSAs only
    latest_year = df["year"].max()
    bars_df = (df[(df["year"] == latest_year) & (df["msa"] != BASELINE)]
               .assign(value_bn=lambda x: x["value"] / 1000)
               .sort_values("value_bn"))
    bars_df["label"] = bars_df["value_bn"].map(lambda v: f"£{v:.1f}bn")

    sort_order = bars_df["msa"].tolist()
    bars = alt.Chart(bars_df).mark_bar(opacity=0.9).encode(
        x=alt.X("value_bn:Q", title="Inward FDI stock (£ billion, 2024)"),
        y=alt.Y("msa:N", sort=sort_order, title=None,
                axis=alt.Axis(labelLimit=200)),
        color=alt.Color("msa:N", scale=COLOR_SCALE, legend=None),
    )
    def bar_label_layer(source, weight):
        return alt.Chart(source).mark_text(
            align="left", dx=4, fontWeight=weight,
        ).encode(
            x=alt.X("value_bn:Q"),
            y=alt.Y("msa:N", sort=sort_order),
            text="label:N",
        )
    bar_labels = (
        bar_label_layer(bars_df[bars_df["msa"] != HIGHLIGHT], "normal") +
        bar_label_layer(bars_df[bars_df["msa"] == HIGHLIGHT], "bold")
    )
    right = (bars + bar_labels).properties(
        title=alt.TitleParams(
            text="…but from the smallest absolute base (2024)",
            anchor="start", fontSize=13,
        ),
        width=340, height=380,
    )

    chart = alt.hconcat(left, right, spacing=40)
    save_chart(chart, "02_fdi")


# --- Save with PNG-first, HTML fallback ----------------------------------

def save_chart(chart, name):
    png_path = OUTPUT_DIR / f"{name}.png"
    try:
        chart.save(str(png_path), scale_factor=2.0)
        print(f"Wrote {png_path}")
    except Exception as exc:
        html_path = OUTPUT_DIR / f"{name}.html"
        chart.save(str(html_path))
        print(f"Wrote {html_path} (PNG failed: {exc})")
        print("For PNG output: pip install vl-convert-python")


# --- Entry point ---------------------------------------------------------

def main():
    chart_unemployment()
    chart_fdi()


if __name__ == "__main__":
    main()