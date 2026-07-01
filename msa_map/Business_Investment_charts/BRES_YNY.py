"""
York & North Yorkshire employment portrait — three charts from BRES.

Reads a Nomis Business Register and Employment Survey (BRES) download
(covering 2015-2024, 15 MSAs, four employment measures) and writes three
PNG charts styled with the eco_style Altair theme:

    06_sector_employment.png — YNY employment by broad industry, 2024
    07_sector_change.png     — YNY employment change by sector, 2015-2024
    08_employment_trend.png  — YNY total employment 2015-2024

Requires: pandas, altair >= 5, vl-convert-python (for PNG export).
The eco_style.py theme file must sit next to this script.
"""
from io import StringIO
from pathlib import Path

import altair as alt
import pandas as pd

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

CSV_PATH = Path("/Users/alonso/Desktop/York and North Yorkshire/"
                "Business_Register_and_Employment_Survey.csv")
OUTPUT_DIR = Path("/Users/alonso/Desktop/York and North Yorkshire")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "York and North Yorkshire"

# Broad industry codes 1-18: (raw label -> display name). These are the
# non-overlapping headline categories; the CSV also carries SIC letters
# (A-U) and 2-digit divisions which we ignore.
BROAD = {
    "1 : Agriculture, forestry & fishing (A)": "Agriculture, forestry & fishing",
    "2 : Mining, quarrying & utilities (B,D and E)": "Mining, quarrying & utilities",
    "3 : Manufacturing (C)": "Manufacturing",
    "4 : Construction (F)": "Construction",
    "5 : Motor trades (Part G)": "Motor trades",
    "6 : Wholesale (Part G)": "Wholesale",
    "7 : Retail (Part G)": "Retail",
    "8 : Transport & storage (inc postal) (H)": "Transport & storage",
    "9 : Accommodation & food services (I)": "Accommodation & food services",
    "10 : Information & communication (J)": "Information & communication",
    "11 : Financial & insurance (K)": "Financial & insurance",
    "12 : Property (L)": "Property",
    "13 : Professional, scientific & technical (M)": "Professional, scientific & technical",
    "14 : Business administration & support services (N)": "Business admin. & support",
    "15 : Public administration & defence (O)": "Public administration & defence",
    "16 : Education (P)": "Education",
    "17 : Health (Q)": "Health",
    "18 : Arts, entertainment, recreation & other services (R,S,T and U)":
        "Arts, entertainment & recreation",
}


# --- Parser ---------------------------------------------------------------

def parse_bres(path):
    """Parse the multi-block Nomis BRES CSV into a long-form DataFrame
    with columns [year, status, industry, msa, count].
    """
    lines = Path(path).read_text().splitlines()

    # Find each block's header row along with its date/status metadata.
    blocks = []
    year = status = None
    for i, line in enumerate(lines):
        if line.startswith('"Date'):
            year = int(line.split('"')[3])
        elif line.startswith('"Employment status'):
            status = line.split('"')[3]
        elif line.startswith('"Industry"'):
            blocks.append((year, status, i))

    records = []
    for year, status, header_line in blocks:
        # Skip blank lines between header and data, then read to next
        # blank line or start of the next block.
        i = header_line + 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        data_start = i
        while (i < len(lines) and lines[i].strip()
               and not lines[i].startswith('"Date')
               and not lines[i].startswith('"Employment')):
            i += 1
        if data_start == i:
            continue

        block_text = lines[header_line] + "\n" + "\n".join(lines[data_start:i])
        block = pd.read_csv(StringIO(block_text))
        real_cols = [c for c in block.columns
                     if not c.startswith("Unnamed") and c != "Industry"]

        for _, row in block.iterrows():
            industry = row["Industry"]
            for msa in real_cols:
                val = row[msa]
                if pd.notna(val):
                    records.append({
                        "year": year, "status": status,
                        "industry": industry, "msa": msa, "count": val,
                    })

    return pd.DataFrame(records)


def yny_broad_series(data, status="Employment"):
    """Return a DataFrame indexed by year with one column per broad industry
    (display name), containing YNY counts.
    """
    df = data[(data["msa"] == TARGET)
              & (data["status"] == status)
              & (data["industry"].isin(BROAD))].copy()
    df["sector"] = df["industry"].map(BROAD)
    return df.pivot_table(index="year", columns="sector",
                          values="count", aggfunc="sum")


# --- Chart 06: sector employment 2024 ------------------------------------

def chart_sector_employment(data):
    latest_year = int(data["year"].max())
    wide = yny_broad_series(data)
    latest = wide.loc[latest_year].sort_values(ascending=True)

    plot = pd.DataFrame({
        "sector": latest.index,
        "jobs": latest.values,
        "label": [f"{v/1000:.1f}k" for v in latest.values],
    })
    order = plot["sector"].tolist()

    top_sector, top_jobs = plot["sector"].iloc[-1], plot["jobs"].iloc[-1]
    total = plot["jobs"].sum()

    bars = alt.Chart(plot).mark_bar(color=pallete["nominal_2"]).encode(
        x=alt.X("jobs:Q", title="Employment (people)",
                scale=alt.Scale(domain=[0, plot["jobs"].max() * 1.15]),
                axis=alt.Axis(format=",.0f")),
        y=alt.Y("sector:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=250)),
    )
    labels = alt.Chart(plot).mark_text(
        align="left", dx=4, fontSize=10,
    ).encode(
        x=alt.X("jobs:Q"),
        y=alt.Y("sector:N", sort=order),
        text="label:N",
    )

    chart = (bars + labels).properties(
        title=alt.TitleParams(
            text=f"{top_sector} is YNY's largest employer at {top_jobs/1000:.0f}k jobs",
            subtitle=f"Total YNY employment by broad industry, {latest_year} "
                     f"({total/1000:.0f}k jobs). "
                     "Source: ONS Business Register and Employment Survey (Nomis).",
            anchor="start", fontSize=13,
            subtitleFontSize=10, subtitleColor="#555", subtitleFontStyle="italic",
        ),
        width=620, height=460,
    )
    save_chart(chart, "06_sector_employment")


# --- Chart 07: sector change 2015 → 2024 ---------------------------------

def chart_sector_change(data):
    wide = yny_broad_series(data)
    first_year, last_year = int(wide.index.min()), int(wide.index.max())
    start, end = wide.loc[first_year], wide.loc[last_year]

    change = pd.DataFrame({
        "sector": start.index,
        "start": start.values,
        "end": end.values,
    })
    change["abs_change"] = change["end"] - change["start"]
    change["pct_change"] = (change["end"] / change["start"] - 1) * 100
    change = change.sort_values("pct_change", ascending=True)
    change["direction"] = ["Decline" if v < 0 else "Growth"
                           for v in change["pct_change"]]
    change["label"] = [f"{v:+.0f}%" for v in change["pct_change"]]

    order = change["sector"].tolist()
    max_abs = change["pct_change"].abs().max()

    bars = alt.Chart(change).mark_bar().encode(
        x=alt.X("pct_change:Q",
                title=f"Employment change {first_year}–{last_year} (%)",
                scale=alt.Scale(domain=[-max_abs * 1.2, max_abs * 1.2])),
        y=alt.Y("sector:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=250)),
        color=alt.Color("direction:N",
                        scale=alt.Scale(
                            domain=["Growth", "Decline"],
                            range=[pallete["nominal_1"], pallete["nominal_2"]]),
                        legend=None),
    )
    def label_layer(subset, align, dx):
        return alt.Chart(subset).mark_text(
            fontSize=10, align=align, dx=dx,
        ).encode(
            x=alt.X("pct_change:Q"),
            y=alt.Y("sector:N", sort=order),
            text="label:N",
        )

    labels = (label_layer(change[change["pct_change"] >= 0], "left", 4)
              + label_layer(change[change["pct_change"] < 0], "right", -4))
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(
        color="#444", strokeWidth=0.8,
    ).encode(x="x:Q")

    top_growth = change.iloc[-1]
    top_decline = change.iloc[0]

    chart = (zero + bars + labels).properties(
        title=alt.TitleParams(
            text=f"{top_growth['sector']} grew {top_growth['pct_change']:+.0f}%; "
                 f"{top_decline['sector']} fell {top_decline['pct_change']:+.0f}%",
            subtitle=f"YNY employment change by broad industry, "
                     f"{first_year} to {last_year}. "
                     "Source: ONS Business Register and Employment Survey (Nomis).",
            anchor="start", fontSize=13,
            subtitleFontSize=10, subtitleColor="#555", subtitleFontStyle="italic",
        ),
        width=620, height=460,
    )
    save_chart(chart, "07_sector_change")


# --- Chart 08: total employment trend 2015-2024 --------------------------

def chart_employment_trend(data):
    wide = yny_broad_series(data)
    totals = wide.sum(axis=1)
    trend = pd.DataFrame({"year": totals.index, "jobs": totals.values})
    trend["label"] = [f"{v/1000:.0f}k" for v in trend["jobs"]]

    first, last = trend.iloc[0], trend.iloc[-1]
    pct = (last["jobs"] / first["jobs"] - 1) * 100
    covid_idx = trend["jobs"].idxmin()
    covid = trend.loc[covid_idx]

    line = alt.Chart(trend).mark_line(
        color=pallete["nominal_2"], strokeWidth=3,
    ).encode(
        x=alt.X("year:O", title=None,
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y("jobs:Q",
                title="Total employment",
                scale=alt.Scale(domain=[trend["jobs"].min() * 0.97,
                                        trend["jobs"].max() * 1.02]),
                axis=alt.Axis(format=",.0f")),
    )
    points = alt.Chart(trend).mark_circle(
        color=pallete["nominal_2"], size=60,
    ).encode(
        x=alt.X("year:O"),
        y=alt.Y("jobs:Q"),
    )

    # Highlight endpoints and COVID trough. Text mark properties (dy, align)
    # can't be encoded per row, so build one layer per milestone.
    start_row = pd.DataFrame([{"year": int(first["year"]),
                               "jobs": first["jobs"], "label": first["label"]}])
    end_row = pd.DataFrame([{"year": int(last["year"]),
                             "jobs": last["jobs"], "label": last["label"]}])
    covid_row = pd.DataFrame([{"year": int(covid["year"]),
                               "jobs": covid["jobs"],
                               "label": f"COVID trough  {covid['label']}"}])

    def milestone_text(source, dy):
        return alt.Chart(source).mark_text(
            fontSize=10, fontWeight="bold",
            color=pallete["nominal_2"], dy=dy, align="center",
        ).encode(x=alt.X("year:O"), y=alt.Y("jobs:Q"), text="label:N")

    text = (milestone_text(start_row, -14)
            + milestone_text(covid_row, 22)
            + milestone_text(end_row, -14))

    chart = (line + points + text).properties(
        title=alt.TitleParams(
            text=f"YNY employment grew {pct:+.1f}% over the decade, "
                 f"with a sharp COVID dip in {int(covid['year'])}",
            subtitle=f"Total YNY employment, {int(first['year'])}–{int(last['year'])}. "
                     "Source: ONS Business Register and Employment Survey (Nomis).",
            anchor="start", fontSize=13,
            subtitleFontSize=10, subtitleColor="#555", subtitleFontStyle="italic",
        ),
        width=620, height=360,
    )
    save_chart(chart, "08_employment_trend")


# --- Save ----------------------------------------------------------------

def save_chart(chart, name):
    p = OUTPUT_DIR / f"{name}.png"
    chart.save(str(p), scale_factor=2.0)
    print(f"Wrote {p}")


def main():
    data = parse_bres(CSV_PATH)
    chart_sector_employment(data)
    chart_sector_change(data)
    chart_employment_trend(data)


if __name__ == "__main__":
    main()