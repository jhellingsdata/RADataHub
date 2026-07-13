"""
York & North Yorkshire business dynamics — three charts.

Reads the ONS 'UK Business: Activity, Size and Location 2025' workbook,
aggregates LA-level enterprise counts up to MSA level, and writes three
PNG charts styled with the eco_style Altair theme:

    03_sector_composition.png — YNY enterprise share by broad industry
    04_size_distribution.png  — YNY enterprises by employment size band
    05_yny_specialisation.png — YNY sector location quotients vs England

Requires: pandas, altair >= 5, openpyxl, vl-convert-python (for PNG).
The eco_style.py theme file must sit next to this script.
"""
from pathlib import Path
import pandas as pd
import altair as alt

import eco_style
from eco_style import pallete


def _sub_font(node, font):
    if isinstance(node, dict):
        return {k: (font if k in ("font", "labelFont")
                    else _sub_font(v, font)) for k, v in node.items()}
    return node


def _report_local():
    return _sub_font(eco_style.report(),
                     "Liberation Sans, Helvetica, Arial, sans-serif")


alt.themes.register("report_local", _report_local)
alt.themes.enable("report_local")

# --- Config ---------------------------------------------------------------

WORKBOOK = Path("/Users/alonso/Desktop/York and North Yorkshire/ukbusinessworkbook2025new.xlsx")
OUTPUT_DIR = Path("/Users/alonso/Desktop/York and North Yorkshire")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# LA code (9 chars) -> MSA name. Codes drop the description that follows ':'.
MSA_LAS = {
    "York and North Yorkshire": ["E06000014", "E06000065"],
    "West Yorkshire":           ["E08000032", "E08000033", "E08000034",
                                 "E08000035", "E08000036"],
    "South Yorkshire":          ["E08000016", "E08000017", "E08000018",
                                 "E08000019"],
    "Tees Valley":              ["E06000001", "E06000002", "E06000003",
                                 "E06000004", "E06000005"],
    "Greater Manchester":       ["E08000001", "E08000002", "E08000003",
                                 "E08000004", "E08000005", "E08000006",
                                 "E08000007", "E08000008", "E08000009",
                                 "E08000010"],
}
ENGLAND_CODE = "E92000001"

HIGHLIGHT = "York and North Yorkshire"
PEER_ORDER = list(MSA_LAS.keys())

COLORS = {
    "York and North Yorkshire": pallete["nominal_2"],
    "West Yorkshire":           pallete["nominal_1"],
    "South Yorkshire":          pallete["nominal_6"],
    "Tees Valley":              pallete["nominal_5"],
    "Greater Manchester":       pallete["nominal_4"],
    "England":                  pallete["Deemphasize_Discrete"],
}
COLOR_SCALE = alt.Scale(
    domain=PEER_ORDER + ["England"],
    range=[COLORS[n] for n in PEER_ORDER + ["England"]],
)

# --- Data loading & aggregation ------------------------------------------

def _load_and_aggregate(sheet, header_data_row, value_cols):
    """Read a workbook sheet, parse LA codes, aggregate rows by MSA.
    Returns a DataFrame indexed by MSA name, with `value_cols` as columns.
    """
    raw = pd.read_excel(WORKBOOK, sheet_name=sheet, header=None)
    header = list(raw.iloc[header_data_row - 1])  # column labels row
    body = raw.iloc[header_data_row:].copy()

    # First column contains "CODE : NAME" — extract the code prefix.
    body.columns = ["area_raw"] + header[1:]
    body["code"] = body["area_raw"].astype(str).str.slice(0, 9)

    # Coerce value columns to numeric (some ONS cells hold codes like "c").
    for c in value_cols:
        body[c] = pd.to_numeric(body[c], errors="coerce")

    # Aggregate: sum LA rows for each MSA, take England row directly.
    rows = {}
    for msa, codes in MSA_LAS.items():
        sub = body[body["code"].isin(codes)]
        rows[msa] = sub[value_cols].sum()
    rows["England"] = body[body["code"] == ENGLAND_CODE][value_cols].iloc[0]

    return pd.DataFrame(rows).T


def load_industry_counts():
    industries = [
        "01-03 : Agriculture, forestry & fishing",
        "05-39 : Production",
        "41-43 : Construction",
        "45 : Motor trades",
        "46 : Wholesale",
        "47 : Retail",
        "49-53 : Transport & Storage (inc postal)",
        "55-56 : Accommodation & food services",
        "58-63 : Information & communication",
        "64-66 : Finance & insurance",
        "68 : Property",
        "69-75 : Professional, scientific & technical",
        "77-82 : Business administration & support services",
        "84 : Public administration & defence",
        "85 : Education",
        "86-88 : Health",
        "90-99 : Arts, entertainment, recreation & other services",
        "Total",
    ]
    # In workbook, header row is index 3, data starts at index 4.
    return _load_and_aggregate("Table 1", header_data_row=4,
                               value_cols=industries)


def load_size_counts():
    sizes = ["0-4", "5-9", "10-19", "20-49", "50-99", "100-249", "250+", "Total"]
    return _load_and_aggregate("Table 10 ", header_data_row=5,
                               value_cols=sizes)


# --- Chart A: Sector composition -----------------------------------------

def chart_sector_composition():
    df = load_industry_counts()
    total = df.loc[HIGHLIGHT, "Total"]
    shares = df.loc[HIGHLIGHT].drop("Total") / total * 100

    short_names = {
        "01-03 : Agriculture, forestry & fishing": "Agriculture, forestry & fishing",
        "05-39 : Production": "Production",
        "41-43 : Construction": "Construction",
        "45 : Motor trades": "Motor trades",
        "46 : Wholesale": "Wholesale",
        "47 : Retail": "Retail",
        "49-53 : Transport & Storage (inc postal)": "Transport & storage",
        "55-56 : Accommodation & food services": "Accommodation & food services",
        "58-63 : Information & communication": "Information & communication",
        "64-66 : Finance & insurance": "Finance & insurance",
        "68 : Property": "Property",
        "69-75 : Professional, scientific & technical": "Professional, scientific & technical",
        "77-82 : Business administration & support services": "Business admin. & support",
        "84 : Public administration & defence": "Public administration & defence",
        "85 : Education": "Education",
        "86-88 : Health": "Health",
        "90-99 : Arts, entertainment, recreation & other services": "Arts, entertainment & recreation",
    }

    plot_df = pd.DataFrame({
        "sector": [short_names[s] for s in shares.index],
        "share": shares.values,
    }).sort_values("share", ascending=True)
    plot_df["label"] = plot_df["share"].map(lambda v: f"{v:.1f}%")
    order = plot_df["sector"].tolist()

    top_sector = plot_df["sector"].iloc[-1]
    top_share = plot_df["share"].iloc[-1]

    bars = alt.Chart(plot_df).mark_bar(color=pallete["nominal_2"]).encode(
        x=alt.X("share:Q", title="Share of YNY enterprises (%)",
                scale=alt.Scale(domain=[0, plot_df["share"].max() * 1.15])),
        y=alt.Y("sector:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=250)),
    )
    labels = alt.Chart(plot_df).mark_text(
        align="left", dx=4, fontSize=10,
    ).encode(
        x=alt.X("share:Q"),
        y=alt.Y("sector:N", sort=order),
        text="label:N",
    )

    chart = (bars + labels).properties(
        title=alt.TitleParams(
            text=f"{top_sector} leads YNY's enterprise base at {top_share:.1f}%",
            subtitle="Share of VAT/PAYE-registered enterprises in YNY by broad industry, March 2025. "
                     "Source: ONS UK Business: Activity, Size and Location 2025, Table 1.",
            anchor="start", fontSize=13,
            subtitleFontSize=10, subtitleColor="#555", subtitleFontStyle="italic",
        ),
        width=600, height=440,
    )
    save_chart(chart, "03_sector_composition")


# --- Chart B: Business size distribution ---------------------------------

def chart_size_distribution():
    df = load_size_counts()
    total = df.loc[HIGHLIGHT, "Total"]
    shares = df.loc[HIGHLIGHT].drop("Total") / total * 100

    size_order = ["0-4", "5-9", "10-19", "20-49", "50-99", "100-249", "250+"]
    plot_df = pd.DataFrame({
        "size": size_order,
        "share": [shares[s] for s in size_order],
    })
    plot_df["label"] = plot_df["share"].map(lambda v: f"{v:.1f}%")

    micro_share = plot_df.loc[plot_df["size"] == "0-4", "share"].iloc[0]

    bars = alt.Chart(plot_df).mark_bar(color=pallete["nominal_2"]).encode(
        x=alt.X("size:N", sort=size_order, title="Employment size band"),
        y=alt.Y("share:Q", title="Share of YNY enterprises (%)",
                scale=alt.Scale(domain=[0, plot_df["share"].max() * 1.12])),
    )
    labels = alt.Chart(plot_df).mark_text(
        align="center", dy=-6, fontSize=10,
    ).encode(
        x=alt.X("size:N", sort=size_order),
        y=alt.Y("share:Q"),
        text="label:N",
    )

    chart = (bars + labels).properties(
        title=alt.TitleParams(
            text=f"{micro_share:.0f}% of YNY enterprises employ fewer than 5 people",
            subtitle="Share of VAT/PAYE-registered enterprises in YNY by employment size band, March 2025. "
                     "Source: ONS UK Business: Activity, Size and Location 2025, Table 10.",
            anchor="start", fontSize=13,
            subtitleFontSize=10, subtitleColor="#555", subtitleFontStyle="italic",
        ),
        width=560, height=340,
    )
    save_chart(chart, "04_size_distribution")


# --- Chart C: YNY sector specialisation ----------------------------------

def chart_location_quotients():
    df = load_industry_counts()
    totals = df["Total"]
    shares = df.drop(columns=["Total"]).div(totals, axis=0)

    england_shares = shares.loc["England"]
    yny_shares = shares.loc[HIGHLIGHT]
    lq = (yny_shares / england_shares).sort_values()

    # Trim long sector names for the axis
    short = {
        "01-03 : Agriculture, forestry & fishing": "Agriculture, forestry & fishing",
        "05-39 : Production": "Production",
        "41-43 : Construction": "Construction",
        "45 : Motor trades": "Motor trades",
        "46 : Wholesale": "Wholesale",
        "47 : Retail": "Retail",
        "49-53 : Transport & Storage (inc postal)": "Transport & storage",
        "55-56 : Accommodation & food services": "Accommodation & food services",
        "58-63 : Information & communication": "Information & communication",
        "64-66 : Finance & insurance": "Finance & insurance",
        "68 : Property": "Property",
        "69-75 : Professional, scientific & technical": "Professional, scientific & technical",
        "77-82 : Business administration & support services": "Business admin. & support",
        "84 : Public administration & defence": "Public administration & defence",
        "85 : Education": "Education",
        "86-88 : Health": "Health",
        "90-99 : Arts, entertainment, recreation & other services": "Arts, entertainment & recreation",
    }

    plot_df = pd.DataFrame({
        "sector": [short[s] for s in lq.index],
        "lq": lq.values,
        "over_under": ["Overrepresented" if v >= 1 else "Underrepresented"
                       for v in lq.values],
        "label": [f"{v:.2f}x" for v in lq.values],
    })
    order = plot_df["sector"].tolist()

    bars = alt.Chart(plot_df).mark_bar().encode(
        x=alt.X("lq:Q",
                title="Location quotient (YNY share ÷ England share)",
                scale=alt.Scale(domain=[0, plot_df["lq"].max() * 1.15])),
        y=alt.Y("sector:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=250)),
        color=alt.Color("over_under:N",
                        scale=alt.Scale(
                            domain=["Overrepresented", "Underrepresented"],
                            range=[pallete["nominal_2"], pallete["Other_3"]]),
                        legend=None),
    )
    labels = alt.Chart(plot_df).mark_text(
        align="left", dx=4, fontSize=10,
    ).encode(
        x=alt.X("lq:Q"),
        y=alt.Y("sector:N", sort=order),
        text="label:N",
    )
    ref = alt.Chart(pd.DataFrame({"x": [1]})).mark_rule(
        strokeDash=[3, 3], color="#666", strokeWidth=1,
    ).encode(x="x:Q")

    chart = (bars + labels + ref).properties(
        title=alt.TitleParams(
            text="YNY is 4× more agricultural — and barely half as tech-heavy — as England",
            subtitle="Ratio of YNY's share of enterprises in each sector to England's share. "
                     "1.0 = same concentration as national average. "
                     "Source: ONS UK Business: Activity, Size and Location 2025, Table 1.",
            anchor="start", fontSize=13,
            subtitleFontSize=10, subtitleColor="#555", subtitleFontStyle="italic",
        ),
        width=600, height=420,
    )
    save_chart(chart, "05_yny_specialisation")


# --- Save ----------------------------------------------------------------

def save_chart(chart, name):
    p = OUTPUT_DIR / f"{name}.png"
    chart.save(str(p), scale_factor=2.0)
    print(f"Wrote {p}")


def main():
    chart_sector_composition()
    chart_size_distribution()
    chart_location_quotients()


if __name__ == "__main__":
    main()