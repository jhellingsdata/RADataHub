
"""
Chart of the Day: Share of Workers Using Generative AI for Work, 2026
Data: Bick, Blandin, Deming, Fuchs-Schundeln & Jessen (2026),
      'Mind the Gap: AI Adoption in Europe and the U.S.', NBER WP No. 34995
"""

import altair as alt
import pandas as pd
import vl_convert as vlc
import eco_style

# ── Theme ─────────────────────────────────────────────────────────────
alt.themes.enable("report")

SAVE_PATH = "ai_adoption_chart.png"

# ── Data ──────────────────────────────────────────────────────────────
data = pd.DataFrame({
    "country": [
        "United States", "United Kingdom", "Sweden",
        "Netherlands", "Germany", "France", "Italy"
    ],
    "share": [43.0, 36.3, 35.6, 35.6, 31.5, 28.1, 25.6]
})

data["label"] = data["share"].apply(lambda v: f"{v:.1f}%")

# ── Colour mapping using palette keys ─────────────────────────────────
color_map = {
    "United States":  eco_style.pallete["United States"],   # red
    "United Kingdom": eco_style.pallete["United Kingdom"],  # blue
    "Sweden":         eco_style.pallete["nominal_3"],       # yellow
    "Netherlands":    eco_style.pallete["nominal_5"],       # orange
    "Germany":        eco_style.pallete["nominal_4"],       # dark navy
    "France":         eco_style.pallete["nominal_6"],       # teal
    "Italy":          eco_style.pallete["Other_3"],         # light grey
}

countries = list(color_map.keys())
colors    = [color_map[c] for c in countries]

# ── Sort order (top = highest share) ──────────────────────────────────
sort_order = data.sort_values("share", ascending=False)["country"].tolist()  # highest at top

# ── Bars ──────────────────────────────────────────────────────────────
bars = alt.Chart(data).mark_bar(
    cornerRadiusEnd=3,
    height=28,
).encode(
    x=alt.X(
        "share:Q",
        scale=alt.Scale(domain=[0, 50]),
        axis=alt.Axis(
            title="Share using generative AI for work (%)",
            titleFontSize=11,
            titleColor=eco_style.pallete["domain"],
            titlePadding=12,
            values=list(range(0, 50, 5)),
            format="d",
            labelExpr="datum.value + '%'",
            grid=False,
            labelFontSize=11,
        )
    ),
    y=alt.Y(
        "country:N",
        sort=sort_order,
        axis=alt.Axis(
            labelFontSize=12,
            labelFont="Circular Std",
            title=None,
        )
    ),
    color=alt.Color(
        "country:N",
        scale=alt.Scale(domain=countries, range=colors),
        legend=None,
    ),
)

# ── Value labels at end of each bar ───────────────────────────────────
labels = alt.Chart(data).mark_text(
    align="left",
    baseline="middle",
    dx=5,
    fontSize=13,
    fontWeight="bold",
    font="Circular Std",
    color=eco_style.pallete["domain"],
).encode(
    x=alt.X("share:Q"),
    y=alt.Y("country:N", sort=sort_order),
    text=alt.Text("label:N"),
)

# ── Main chart ────────────────────────────────────────────────────────
main = (bars + labels).properties(
    width=420,
    height=260,
    title={
        "text": "One in three UK workers uses AI on the job",
        "subtitle": "Share of workers using generative AI for work, 2026 (%)",
        "anchor": "start",
        "fontSize": 16,
        "fontWeight": "bold",
        "font": "Circular Std",
        "color": eco_style.pallete["domain"],
        "subtitleFontSize": 12,
        "subtitleColor": "#666666",
        "subtitleFont": "Circular Std",
        "subtitlePadding": 8,
    }
)

# ── Source caption ────────────────────────────────────────────────────
source_line = (
    "Source: Bick, Blandin, Deming, Fuchs-Schundeln & Jessen (2026), "
    "Mind the Gap: AI Adoption in Europe and the U.S."
)

source = alt.Chart(
    pd.DataFrame({"text": [source_line]})
).mark_text(
    align="left",
    baseline="top",
    fontSize=9,
    font="Circular Std",
    color="#999999",
    limit=600,
).encode(
    text="text:N",
    x=alt.value(0),
    y=alt.value(0),
).properties(
    width=400,
    height=15,
)

chart = alt.vconcat(
    main, source
).configure_view(
    stroke="transparent"
).configure_concat(
    spacing=5
)

# ── Export high-res SVG ───────────────────────────────────────────────
svg = vlc.vegalite_to_svg(chart.to_dict())

svg_path = SAVE_PATH.replace(".png", ".svg")
with open(svg_path, "w") as f:
    f.write(svg)

# ── Export high-res PNG ───────────────────────────────────────────────
png = vlc.vegalite_to_png(chart.to_dict(), scale=3, ppi=300)

with open(SAVE_PATH, "wb") as f:
    f.write(png)

print(f"Saved → {SAVE_PATH}")
print(f"Saved → {svg_path}")