import altair as alt
import pandas as pd
import eco_style
import vl_convert as vlc

# ── Register ECO theme (sets Circular Std, axis style, colour range) ─────
alt.themes.enable("report")

# ── Paths ────────────────────────────────────────────────────────────────
DATA_PATH = "/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/debt/IMF.FAD_GDD_2.0.0.csv"
SAVE_PATH = "/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/debt/debt_stacked_bar.png"

# ── Load IMF Global Debt Database ────────────────────────────────────────
raw = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

COUNTRIES = [
    "United Kingdom", "United States", "France",
    "Canada", "Italy", "Germany", "Japan",
]
YEAR = "2024"

# ── Select indicators ────────────────────────────────────────────────────
INDICATORS = {
    "Debt securities and loans, Households, Percent of GDP":                 "Household debt",
    "Debt securities and loans, Non-financial corporations, Percent of GDP": "Non-financial corporate debt",
    "Debt instruments, General government, Percent of GDP":                  "Government debt",
}

sub = raw.loc[
    raw["COUNTRY"].isin(COUNTRIES) & raw["INDICATOR"].isin(INDICATORS),
    ["COUNTRY", "INDICATOR", YEAR],
].copy()

sub["sector"]   = sub["INDICATOR"].map(INDICATORS)
sub["debt_pct"] = pd.to_numeric(sub[YEAR], errors="coerce")
sub = sub.dropna(subset=["debt_pct"])

# ── Wide table for totals ────────────────────────────────────────────────
pivot = (
    sub.pivot(index="COUNTRY", columns="sector", values="debt_pct")
    .reset_index()
    .rename(columns={"COUNTRY": "country"})
)
pivot.columns.name = None
pivot["Total"] = pivot[list(INDICATORS.values())].sum(axis=1)

# ── Long-form for Altair ────────────────────────────────────────────────
df = sub.rename(columns={"COUNTRY": "country"}).merge(
    pivot[["country", "Total"]], on="country",
)

# ── Styling (eco_style palette) ──────────────────────────────────────────
sector_colors = {
    "Government debt":               eco_style.pallete["nominal_2"],
    "Non-financial corporate debt":  eco_style.pallete["nominal_3"],
    "Household debt":                eco_style.pallete["nominal_1"],
}

country_order = pivot.sort_values("Total", ascending=False)["country"].tolist()
sector_order  = ["Government debt", "Non-financial corporate debt", "Household debt"]

x_max = int(pivot["Total"].max() // 50 + 2) * 50

# ── Bars ─────────────────────────────────────────────────────────────────
bars = (
    alt.Chart(df)
    .mark_bar(cornerRadiusEnd=2, size=28)
    .encode(
        y=alt.Y(
            "country:N",
            sort=country_order,
            axis=alt.Axis(title=None, labelFontSize=12),
        ),
        x=alt.X(
            "debt_pct:Q",
            title=None,
            axis=alt.Axis(
                format=".0f",
                labelExpr="datum.value + '%'",
                tickCount=6,
            ),
            scale=alt.Scale(domain=[0, x_max]),
        ),
        color=alt.Color(
            "sector:N",
            scale=alt.Scale(
                domain=list(sector_colors.keys()),
                range=list(sector_colors.values()),
            ),
            legend=alt.Legend(
                title=None,
                orient="none",
                direction="horizontal",
                legendX=0,
                legendY=-16,
                symbolSize=100,
                symbolStrokeWidth=0,
                labelLimit=280,
            ),
        ),
        order=alt.Order("sector_sort:Q"),
    )
    .transform_calculate(
        sector_sort=f"indexof({sector_order}, datum.sector)"
    )
)

# ── Total labels ─────────────────────────────────────────────────────────
totals = (
    alt.Chart(pivot)
    .mark_text(
        align="left",
        dx=5,
        fontSize=12,
        fontWeight="bold",
        color=eco_style.pallete["domain"],
    )
    .encode(
        y=alt.Y("country:N", sort=country_order),
        x=alt.X("Total:Q"),
        text=alt.Text("label:N"),
    )
    .transform_calculate(
        label="format(datum.Total, '.0f') + '%'"
    )
)

# ── Assemble main chart ─────────────────────────────────────────────────
main = (
    (bars + totals)
    .properties(
        width=480,
        height=300,
        title=alt.Title(
            text="Debt in G7 countries",
            subtitle=f"Total debt as % of GDP ({YEAR})",
            anchor="start",
            fontSize=16,
            fontWeight="bold",
            color=eco_style.pallete["domain"],
            subtitleFontSize=11,
            subtitleColor="#676A86",
            offset=30,
        ),
    )
)

# ── Source caption ───────────────────────────────────────────────────────
caption = (
    alt.Chart(pd.DataFrame([{"text": "Source: IMF Global Debt Database (GDD)"}]))
    .mark_text(align="left", fontSize=10, color="#676A86")
    .encode(text="text:N", x=alt.value(300))
    .properties(width=520, height=5)
)

chart = (
    alt.vconcat(main, caption, spacing=15)
    .properties(padding={"top": 10, "left": 5, "right": 5, "bottom": 5})
    .configure_view(stroke="transparent")
    .configure_concat(spacing=15)
)

chart

# ── Export high-res PNG ──────────────────────────────────────────────────
png = vlc.vegalite_to_png(chart.to_dict(), scale=3, ppi=300)

with open(SAVE_PATH, "wb") as f:
    f.write(png)

print(f"Saved → {SAVE_PATH}")
print()
print("── Data summary ──")
print(
    pivot[["country"] + list(INDICATORS.values()) + ["Total"]]
    .sort_values("Total", ascending=False)
    .to_string(index=False)
)