"""
London 2022 Borough Council Elections — composed infographic.

Produces four deliverables, each in both PNG (for quick viewing / emailing)
and SVG (vector, for print or further editing in Illustrator):

  1. london_2022_wards_map.{png,svg}      (map only, standalone)
  2. london_2022_tug_of_war.{png,svg}     (bar chart only, standalone)
  3. london_2022_composition.{png,svg}    (map + tug-of-war, side-by-side)
  4. london_2022_wards_map.html           (interactive map, standalone)

The map shows the winning party per ward at full colour saturation, with
thick borough outlines overlaid and a hatched overlay on Kensington &
Chelsea (which underwent a mid-cycle ward-boundary review).

The tug-of-war chart strips each borough down to its two main contestants:
a horizontal stacked bar, first-place on the left, runner-up on the right,
remainder in neutral grey. Boroughs are sorted from closest race (top) to
biggest landslide (bottom). Boroughs under No Overall Control (largest
group short of a majority) carry an NOC badge.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from matplotlib.patheffects import withStroke


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Convert the base string into a Path object
HERE = Path("/Users/alonso/Desktop/LSE/GROWTH LAB/Borough Council Election Results")

# Now the / operator will work perfectly
XLSX_PATH = HERE / "data/London 2022 Wards.xlsx"
WARDS_GEOJSON = HERE / "geoJSON/Wards_December_2022_Boundaries_UK_BSC_2187748736575637542.geojson"
LADS_GEOJSON = HERE / "geoJSON/Local_Authority_Districts_May_2022_UK_BGC_V3_2022_8678644324030741436.geojson"

OUT_MAP_BASE      = HERE / "london_2022_wards_map"
OUT_BARS_BASE     = HERE / "london_2022_tug_of_war"
OUT_COMPOSED_BASE = HERE / "london_2022_composition"
OUT_MAP_HTML      = HERE / "london_2022_wards_map.html"


def save_png(fig, path: Path, width: float, height: float, dpi: int = 220) -> None:
    fig.set_size_inches(width, height)
    # NB: no bbox_inches="tight" — it overrides subplots_adjust and causes
    # titles/source notes to overlap the axes in figures with hand-placed
    # fig.text() elements. We reserve margins explicitly via subplots_adjust.
    fig.savefig(path.with_suffix(".png"), dpi=dpi,
                facecolor=fig.get_facecolor())


def save_svg(fig, path: Path, width: float, height: float) -> None:
    fig.set_size_inches(width, height)
    fig.savefig(path.with_suffix(".svg"),
                facecolor=fig.get_facecolor())

# ---------------------------------------------------------------------------
# Party metadata
# ---------------------------------------------------------------------------
PARTY_COLOURS = {
    "Labour Party":           "#E4003B",
    "Conservative Party":     "#0087DC",
    "Liberal Democrats":      "#FAA61A",
    "Green Party":            "#6AB023",
    "Aspire":                 "#6B2C91",
    "Residents' Association": "#1FA2A2",
    "Independent":            "#5B4636",   # deep bronze — clearly intentional
    "Other":                  "#B0B0B0",   # retained for safety; not expected to be used
}

SHORT_NAME = {
    "Labour Party":           "Lab",
    "Conservative Party":     "Con",
    "Liberal Democrats":      "LD",
    "Green Party":            "Grn",
    "Aspire":                 "Aspire",
    "Residents' Association": "RA",
    "Independent":            "Ind",
    "Other":                  "Oth",
}


def normalise_party(name: str) -> str:
    if name in PARTY_COLOURS:
        return name
    # Local residents-style parties — grouped with Residents' Association
    if "Residents" in name or "Tenants" in name:
        return "Residents' Association"
    if name == "Chislehurst Matters":  # Bromley local party, same category
        return "Residents' Association"
    if "Hornchurch and Upminster Independents" in name:  # Havering local group
        return "Residents' Association"
    if name == "Independent":
        return "Independent"
    return "Other"


# ---------------------------------------------------------------------------
# Election maths — GLA "average votes per candidate" correction
# ---------------------------------------------------------------------------
def _per_party_ward(cands: pd.DataFrame) -> pd.DataFrame:
    cands = cands.copy()
    cands["party_grp"] = cands["Party name"].map(normalise_party)
    out = (
        cands.groupby(
            ["LAD22CD", "Borough", "WD22CD", "Ward name", "party_grp"],
            as_index=False,
        ).agg(votes=("Votes", "sum"), n_cands=("Votes", "size"))
    )
    out["avg_per_cand"] = out["votes"] / out["n_cands"]
    return out


def load_candidates(xlsx_path: Path) -> pd.DataFrame:
    """Read the Candidates sheet once and attach the normalised party group."""
    cands = pd.read_excel(xlsx_path, sheet_name="Candidates")
    cands["party_grp"] = cands["Party name"].map(normalise_party)
    return cands


def compute_ward_results(per_ward: pd.DataFrame) -> pd.DataFrame:
    per_ward = per_ward.copy()
    totals = per_ward.groupby("WD22CD")["avg_per_cand"].sum().rename("tot")
    per_ward = per_ward.join(totals, on="WD22CD")
    per_ward["share"] = per_ward["avg_per_cand"] / per_ward["tot"]
    per_ward = per_ward.sort_values(["WD22CD", "share"],
                                    ascending=[True, False])
    per_ward["rank"] = per_ward.groupby("WD22CD").cumcount() + 1

    top = per_ward.query("rank == 1").set_index("WD22CD")[
        ["Borough", "Ward name", "party_grp", "share"]
    ].rename(columns={
        "party_grp": "winner", "share": "winner_share",
        "Ward name": "ward_name", "Borough": "borough_name",
    })
    second = per_ward.query("rank == 2").set_index("WD22CD")[
        ["party_grp", "share"]
    ].rename(columns={"party_grp": "runner_up", "share": "runner_up_share"})

    out = top.join(second).fillna({"runner_up": "—", "runner_up_share": 0})
    out["margin"] = out["winner_share"] - out["runner_up_share"]
    return out.reset_index()


def compute_borough_results(cands: pd.DataFrame, per_ward: pd.DataFrame) -> pd.DataFrame:
    """Borough-level vote shares + winner/runner-up tags + seat-based control."""
    per_bor = (
        per_ward.groupby(["LAD22CD", "Borough", "party_grp"], as_index=False)
                .agg(avg_sum=("avg_per_cand", "sum"))
    )
    totals = per_bor.groupby("LAD22CD")["avg_sum"].sum().rename("tot")
    per_bor = per_bor.join(totals, on="LAD22CD")
    per_bor["share"] = per_bor["avg_sum"] / per_bor["tot"]

    per_bor = per_bor.sort_values(["LAD22CD", "share"],
                                  ascending=[True, False])
    per_bor["rank"] = per_bor.groupby("LAD22CD").cumcount() + 1

    top = per_bor.query("rank == 1").set_index("LAD22CD")[
        ["Borough", "party_grp", "share"]
    ].rename(columns={"party_grp": "winner", "share": "winner_share",
                      "Borough": "borough_name"})
    second = per_bor.query("rank == 2").set_index("LAD22CD")[
        ["party_grp", "share"]
    ].rename(columns={"party_grp": "runner_up", "share": "runner_up_share"})

    out = top.join(second)
    out["margin"] = out["winner_share"] - out["runner_up_share"]

    # -----------------------------------------------------------------------
    # Seats-based political control.
    # A party needs floor(total_seats/2) + 1 seats for a majority. If the
    # largest group falls short, the borough is under No Overall Control.
    # This is flagged on the tug-of-war chart because the vote-share winner
    # isn't always the party that actually runs the council (Croydon,
    # Havering in 2022 are the two London cases).
    # -----------------------------------------------------------------------
    elected = cands[cands["Elected"] == True]
    seats = (elected.groupby(["LAD22CD", "party_grp"])
             .size()
             .unstack(fill_value=0))
    seats["total_seats"] = seats.sum(axis=1)
    seats["majority_needed"] = seats["total_seats"] // 2 + 1

    control_rows = []
    for lad_cd, row in seats.iterrows():
        total = int(row["total_seats"])
        majority = int(row["majority_needed"])
        party_cols = [c for c in row.index
                      if c not in ("total_seats", "majority_needed")]
        party_seats = row[party_cols]
        party_seats = party_seats[party_seats > 0].sort_values(ascending=False)
        largest_seats = int(party_seats.iloc[0])
        control_rows.append({
            "LAD22CD": lad_cd,
            "largest_seats": largest_seats,
            "total_seats": total,
            "majority_needed": majority,
            "has_majority": largest_seats >= majority,
        })
    control_df = pd.DataFrame(control_rows).set_index("LAD22CD")
    out = out.join(control_df)

    return out.reset_index()


# ---------------------------------------------------------------------------
# Map helpers
# ---------------------------------------------------------------------------
def _fill_rgba_series(winners: pd.Series, alpha: float = 0.92) -> list:
    """Vectorised winner -> RGBA colour lookup."""
    default = PARTY_COLOURS["Other"]
    return [to_rgba(PARTY_COLOURS.get(w, default), alpha) for w in winners]


def _draw_map(ax,
              wards27700: gpd.GeoDataFrame,
              kc27700: gpd.GeoDataFrame,
              boroughs27700: gpd.GeoDataFrame,
              label_fontsize: float = 7.4):
    """Render the ward map onto a given Axes."""
    wards27700.plot(ax=ax, color=_fill_rgba_series(wards27700["winner"]),
                    edgecolor="#2a2a2a", linewidth=0.25)

    kc27700.plot(ax=ax, color=_fill_rgba_series(kc27700["winner"]),
                 edgecolor="#2a2a2a", linewidth=0.25, hatch="////")

    boroughs27700.boundary.plot(ax=ax, color="#0a0a0a", linewidth=1.0)

    for _, row in boroughs27700.iterrows():
        pt = row.geometry.representative_point()
        name = row["LAD22NM"]
        if len(name) > 14:
            name = (name.replace(" and ", " &\n")
                        .replace(" upon ", " upon\n"))
        ax.text(pt.x, pt.y, name,
                ha="center", va="center",
                fontsize=label_fontsize, color="#0a0a0a",
                fontweight="medium",
                path_effects=[withStroke(linewidth=2.4, foreground="#f7f4ee")],
                zorder=5)

    ax.set_axis_off()


def build_standalone_map(wards27700, kc27700, boroughs27700, base_path):
    fig, ax = plt.subplots(figsize=(16, 16), dpi=300)
    fig.patch.set_facecolor("#f7f4ee")
    ax.set_facecolor("#f7f4ee")

    _draw_map(ax, wards27700, kc27700, boroughs27700, label_fontsize=7.4)

    fig.text(0.06, 0.96, "London local elections",
             fontsize=32, fontweight="bold", color="#111", family="serif")
    fig.text(0.06, 0.928,
             "Winning party by ward, May 2022 local elections",
             fontsize=14, color="#333", family="serif", style="italic")
    fig.text(0.06, 0.906,
             "Each ward is filled in the colour of the party that won it.",
             fontsize=9.5, color="#555")

    present = wards27700["winner"].unique().tolist()
    handles = [
        mpatches.Patch(color=PARTY_COLOURS[p], label=p.replace(" Party", ""))
        for p in PARTY_COLOURS if p in present
    ]
    leg = ax.legend(handles=handles, loc="lower left",
                    bbox_to_anchor=(0.0, 0.0),
                    frameon=False, fontsize=10,
                    title="Winning party", title_fontsize=11)
    leg.get_title().set_fontweight("bold")

    fig.text(0.06, 0.04,
             "Source: Greater London Authority — London Borough Elections May 2022. "
             "Boundaries: ONS Open Geography Portal (Wards Dec 2022 BSC; LADs May 2022 BGC). "
             "City of London excluded. Hatched = Kensington & Chelsea (mid-cycle boundary review).",
             fontsize=7.0, color="#555")

    save_png(fig, base_path, width=16, height=16)
    save_svg(fig, base_path, width=16, height=16)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Tug-of-war chart
# ---------------------------------------------------------------------------
def _draw_tug_of_war(ax, borough_df: pd.DataFrame):
    """
    Horizontal 'tug-of-war' bars. One bar per borough:
      winner's share (left)  |  other parties (grey)  |  runner-up share (right).
    Sorted from tightest race (top) to biggest landslide (bottom).
    """
    df = borough_df.copy().sort_values("margin", ascending=True).reset_index(drop=True)

    bar_height = 0.72

    for i, row in df.iterrows():
        w_share = row["winner_share"]
        r_share = row["runner_up_share"]
        w_col = PARTY_COLOURS.get(row["winner"], PARTY_COLOURS["Other"])
        r_col = PARTY_COLOURS.get(row["runner_up"], PARTY_COLOURS["Other"])

        # Tug-of-war: winner anchored to the left edge, runner-up anchored to
        # the right edge, grey "other" fills whatever gap remains in between.
        # Anchoring the runner-up on the right (rather than stacking after the
        # grey) is what makes the bar read as a pull in two directions.
        r_left = 1.0 - r_share
        mid_left = w_share
        mid_width = max(0.0, r_left - w_share)

        # Winner on the left.
        ax.barh(i, w_share, left=0.0,
                color=w_col, edgecolor="white", linewidth=0.8,
                height=bar_height, zorder=2)
        # Grey middle — only if there's actually a gap between the two parties.
        if mid_width > 0:
            ax.barh(i, mid_width, left=mid_left,
                    color="#dad5cc", edgecolor="white", linewidth=0.8,
                    height=bar_height, zorder=2)
        # Runner-up anchored to the right edge.
        ax.barh(i, r_share, left=r_left,
                color=r_col, edgecolor="white", linewidth=0.8,
                height=bar_height, zorder=2)

        # Percentage labels inside the bars (when segment is big enough)
        if w_share >= 0.15:
            ax.text(w_share / 2, i, f"{w_share * 100:.0f}%",
                    ha="center", va="center",
                    color="white", fontsize=8.2, fontweight="bold", zorder=3)
        if r_share >= 0.10:
            ax.text(r_left + r_share / 2, i, f"{r_share * 100:.0f}%",
                    ha="center", va="center",
                    color="white", fontsize=8.2, fontweight="bold", zorder=3)

        # Party abbreviations outside the bars, flanking left and right
        w_abbrev = SHORT_NAME.get(row["winner"], row["winner"][:3])
        r_abbrev = SHORT_NAME.get(row["runner_up"], row["runner_up"][:3])
        ax.text(-0.005, i, w_abbrev, ha="right", va="center",
                color=w_col, fontsize=9, fontweight="bold", zorder=3)
        ax.text(1.005, i, r_abbrev, ha="left", va="center",
                color=r_col, fontsize=9, fontweight="bold", zorder=3)

        # NOC badge — shown only where the largest group fell short of a
        # majority. These are the boroughs where the vote-share winner on
        # the bar doesn't actually control the council (Croydon, Havering
        # in 2022). Comfortable majorities get no annotation.
        has_majority = row.get("has_majority")
        if has_majority is False:
            ax.text(-0.10, i, "NOC",
                    ha="center", va="center",
                    color="white", fontsize=7.5, fontweight="bold",
                    zorder=4,
                    bbox=dict(boxstyle="round,pad=0.28",
                              facecolor="#1a1a1a",
                              edgecolor="none"))

    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(df["borough_name"], fontsize=9)
    ax.invert_yaxis()

    # Widen left side to leave room for the NOC badge; right side unchanged.
    ax.set_xlim(-0.15, 1.09)
    ax.set_xticks([0, 0.25, 0.50, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    # No x-label — it would overlap the shared legend in the composed figure.
    # The meaning is obvious from the ticks and it's spelled out in the header.

    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#888")
    ax.spines["bottom"].set_bounds(0.0, 1.0)  # spine stops before the badge area
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors="#555")
    ax.grid(axis="x", color="#eee", linewidth=0.7, zorder=1)
    ax.set_axisbelow(True)


def build_standalone_tug_of_war(borough_df, base_path):
    fig, ax = plt.subplots(figsize=(10, 12), dpi=300)
    fig.patch.set_facecolor("#f7f4ee")
    ax.set_facecolor("#f7f4ee")

    # Header stack sits in the top 16%; source note gets the bottom 6%.
    # The axes occupy the middle 78% so the first bar never collides with
    # the subtitle and the x-tick labels never collide with the source note.
    fig.subplots_adjust(top=0.84, bottom=0.08, left=0.14, right=0.97)

    _draw_tug_of_war(ax, borough_df)

    # Title
    fig.text(0.05, 0.955, "Two-horse races by borough",
             fontsize=22, fontweight="bold", color="#111", family="serif")


    save_png(fig, base_path, width=10, height=12)
    save_svg(fig, base_path, width=10, height=12)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Composed figure
# ---------------------------------------------------------------------------
def build_composition(wards27700, kc27700, boroughs27700,
                      wards_gdf, borough_df, base_path):
    fig = plt.figure(figsize=(22, 14), dpi=300)
    fig.patch.set_facecolor("#f7f4ee")

    # Left panel: map — lifted up a touch to clear the legend
    ax_map = fig.add_axes([0.02, 0.10, 0.52, 0.78])
    ax_map.set_facecolor("#f7f4ee")
    _draw_map(ax_map, wards27700, kc27700, boroughs27700, label_fontsize=7.0)

    # Right panel: tug-of-war
    ax_bar = fig.add_axes([0.60, 0.11, 0.37, 0.77])
    ax_bar.set_facecolor("#f7f4ee")
    _draw_tug_of_war(ax_bar, borough_df)

    # Shared header
    fig.text(0.02, 0.955, "London local elections",
             fontsize=34, fontweight="bold", color="#111", family="serif")
    fig.text(0.02, 0.925,
             "Borough council elections, May 2022",
             fontsize=15, color="#444", family="serif", style="italic")

    # Per-panel mini headers
    fig.text(0.02, 0.895,
             "Left  —  who won each ward",
             fontsize=11, color="#222", fontweight="bold")
    fig.text(0.60, 0.895,
             "Right  —  who came first and second borough-wide",
             fontsize=11, color="#222", fontweight="bold")

    fig.text(0.02, 0.878,
             "Ward-level choropleth. Each ward is coloured by its winning party.",
             fontsize=9, color="#666")
    fig.text(0.60, 0.878,
             "Sorted from tightest race at the top to biggest landslide at the bottom. "
             "NOC = council under no overall control.",
             fontsize=9, color="#666")

    # Shared legend along the bottom
    all_parties = set(borough_df["winner"]) | set(borough_df["runner_up"])
    all_parties |= set(wards_gdf["winner"])
    handles = [
        mpatches.Patch(color=PARTY_COLOURS[p], label=p.replace(" Party", ""))
        for p in PARTY_COLOURS if p in all_parties
    ]

    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(0.5, 0.045),
               ncol=len(handles), frameon=False, fontsize=10)

    # Source note at the very bottom
    fig.text(
        0.02, 0.012,
        "Source: Greater London Authority — London Borough Elections May 2022. "
        "Boundaries: ONS Open Geography Portal (Wards Dec 2022 BSC; LADs May 2022 BGC). "
        "City of London excluded. Hatched = Kensington & Chelsea (mid-cycle boundary review). "
        "Vote shares use the GLA 'average-per-candidate' correction (see report p.42).",
        fontsize=7.5, color="#555",
    )

    save_png(fig, base_path, width=22, height=14, dpi=200)
    save_svg(fig, base_path, width=22, height=14)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Interactive map
# ---------------------------------------------------------------------------
def build_interactive_map(wards_gdf, kc_gdf, borough_outlines, out_path):
    import folium
    from folium.features import GeoJsonTooltip

    wards_wgs = wards_gdf.to_crs(4326).copy()
    kc_wgs = kc_gdf.to_crs(4326).copy()
    bor_wgs = borough_outlines.to_crs(4326).copy()

    for df in (wards_wgs, kc_wgs):
        df["fill_hex"] = df["winner"].map(
            lambda p: PARTY_COLOURS.get(p, PARTY_COLOURS["Other"])
        )
        df["winner_pct"] = (df["winner_share"] * 100).round(1)
        df["runner_up_pct"] = (df["runner_up_share"] * 100).round(1)
        df["margin_pct"] = (df["margin"] * 100).round(1)

    m = folium.Map(location=[51.509, -0.11], zoom_start=10,
                   tiles="CartoDB positron", control_scale=True)

    def style_ward(feat):
        return {"fillColor": feat["properties"]["fill_hex"],
                "color": "#2a2a2a", "weight": 0.4, "fillOpacity": 0.88}

    def style_kc(feat):
        return {"fillColor": feat["properties"]["fill_hex"],
                "color": "#2a2a2a", "weight": 0.8, "fillOpacity": 0.88,
                "dashArray": "4,3"}

    def highlight(_feat):
        return {"weight": 2.4, "color": "#000"}

    folium.GeoJson(
        data=json.loads(wards_wgs.to_json()),
        name="Wards — winning party",
        style_function=style_ward, highlight_function=highlight,
        tooltip=GeoJsonTooltip(
            fields=["ward_name", "borough_name", "winner", "winner_pct",
                    "runner_up", "runner_up_pct", "margin_pct"],
            aliases=["Ward", "Borough", "Winner", "Winner %",
                     "Runner-up", "Runner-up %", "Margin (pt)"],
            sticky=True,
            style=("background-color: #f7f4ee; color: #111;"
                   "font-family: system-ui, sans-serif; font-size: 12px;"
                   "padding: 8px 10px; border: 1px solid #222;"),
        ),
    ).add_to(m)

    folium.GeoJson(
        data=json.loads(kc_wgs.to_json()),
        name="Kensington & Chelsea (boundary change)",
        style_function=style_kc, highlight_function=highlight,
        tooltip=GeoJsonTooltip(
            fields=["borough_name", "winner", "winner_pct",
                    "runner_up", "runner_up_pct", "margin_pct"],
            aliases=["Borough", "Winner", "Winner %",
                     "Runner-up", "Runner-up %", "Margin (pt)"],
            sticky=True,
            style=("background-color: #f7f4ee; color: #111;"
                   "font-family: system-ui, sans-serif; font-size: 12px;"
                   "padding: 8px 10px; border: 1px solid #222;"),
        ),
    ).add_to(m)

    folium.GeoJson(
        data=json.loads(bor_wgs[["LAD22NM", "geometry"]].to_json()),
        name="Borough boundaries",
        style_function=lambda _: {
            "fill": False, "color": "#000", "weight": 1.6, "opacity": 0.9,
        },
    ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)

    legend_items = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        f'<span style="display:inline-block;width:14px;height:14px;'
        f'background:{PARTY_COLOURS[p]};border:1px solid #333"></span>'
        f'<span>{p.replace(" Party", "")}</span></div>'
        for p in PARTY_COLOURS if p in wards_wgs["winner"].values
    )
    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
        background: #f7f4ee; padding: 12px 14px; border: 1px solid #1a1a1a;
        border-radius: 3px; font-family: system-ui, sans-serif; font-size: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,.15);">
      <div style="font-weight:600;margin-bottom:6px;font-size:13px">
        London 2022 — winning party per ward
      </div>
      {legend_items}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(out_path)
    print(f"Saved {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading election data...")
    cands = load_candidates(XLSX_PATH)
    per_ward = _per_party_ward(cands)
    ward_results = compute_ward_results(per_ward)
    borough_df = compute_borough_results(cands, per_ward)
    print(f"  -> {len(ward_results)} wards, {len(borough_df)} boroughs")

    print("Loading ward boundaries...")
    wards_all = gpd.read_file(WARDS_GEOJSON)
    london_wards = wards_all[wards_all["LAD22CD"].str.startswith("E09")].copy()
    wards_joined = london_wards.merge(
        ward_results, on="WD22CD", how="inner"
    )
    print(f"  -> {len(wards_joined)} wards joined to geometry")

    print("Loading LAD boundaries...")
    lads = gpd.read_file(LADS_GEOJSON)
    kc_lad = lads[lads["LAD22CD"] == "E09000020"].copy()
    kc_result = borough_df[borough_df["LAD22CD"] == "E09000020"][
        ["LAD22CD", "borough_name", "winner", "winner_share",
         "runner_up", "runner_up_share", "margin"]
    ]
    kc_lad = kc_lad.merge(kc_result, on="LAD22CD", how="left")
    kc_lad["ward_name"] = "— borough-level (boundary change) —"

    borough_outlines = lads[
        lads["LAD22CD"].str.startswith("E09") &
        (lads["LAD22CD"] != "E09000001")
    ].copy()

    # Project once for all static figures (the interactive map needs WGS84
    # separately, so it handles its own reprojection).
    wards27700 = wards_joined.to_crs(27700)
    kc27700 = kc_lad.to_crs(27700)
    boroughs27700 = borough_outlines.to_crs(27700)

    print("\nBuilding standalone ward map...")
    build_standalone_map(wards27700, kc27700, boroughs27700, OUT_MAP_BASE)

    print("Building standalone tug-of-war chart...")
    build_standalone_tug_of_war(borough_df, OUT_BARS_BASE)

    print("Building composed figure (map + tug-of-war)...")
    build_composition(wards27700, kc27700, boroughs27700,
                      wards_joined, borough_df, OUT_COMPOSED_BASE)

    print("Building interactive map...")
    build_interactive_map(wards_joined, kc_lad, borough_outlines, OUT_MAP_HTML)

    print("\nDone.")


if __name__ == "__main__":
    main()