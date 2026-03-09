"""
UC by Local Authority choropleth map.
Uses matplotlib + geopandas for rendering, styled with ecostyles colours.
Note: Altair's vl-convert has a known incompatibility with the ecostyles theme
for geoshape marks, so this chart uses matplotlib directly.
"""
import json

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import requests

# ── 1. Load UC data ───────────────────────────────────────────────────────────
df = pd.read_csv("../data/universal credit by LA.csv", skiprows=3, header=0)
df = df.iloc[:, :2]
df.columns = ["LA_name", "UC_pct"]
df = df.dropna(subset=["LA_name"])
df = df[df["LA_name"].str.strip() != ""]
df = df[df["LA_name"] != "Total"]
df["UC_pct"] = df["UC_pct"].str.replace("%", "", regex=False).astype(float)


def clean_la_name(name):
    if " / " in name:
        name = name.split(" / ")[0].strip()
    return name


df["match_name"] = df["LA_name"].apply(clean_la_name)
uc_lookup = dict(zip(df["match_name"], df["UC_pct"]))

# ── 2. Load simplified GeoJSON ────────────────────────────────────────────────
geojson_path = "../data/uc_la_processed.geojson"
try:
    with open(geojson_path) as f:
        geojson = json.load(f)
except FileNotFoundError:
    url = (
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
        "Local_Authority_Districts_May_2024_Boundaries_UK_BGC/FeatureServer/0/query"
        "?where=1%3D1&outFields=LAD24CD,LAD24NM&returnGeometry=true"
        "&f=geojson&maxAllowableOffset=0.001"
    )
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    geojson = response.json()
    with open(geojson_path, "w") as f:
        json.dump(geojson, f)

gdf = gpd.GeoDataFrame.from_features(geojson["features"])
gdf = gdf[~gdf["LAD24CD"].str.startswith("N")]
gdf["UC_pct"] = gdf["LAD24NM"].map(uc_lookup)

# ── 3. Assign colours ─────────────────────────────────────────────────────────
bins = [0, 4, 8, 12, 16, 20, 24, 100]
labels = [
    "0.0-3.9%", "4.0-7.9%", "8.0-11.9%", "12.0-15.9%",
    "16.0-19.9%", "20.0-23.9%", "24.0% and over",
]
# Sequential blues built on ecostyles blue-dark (#122b39)
eco_blues = ["#deedf7", "#b4d4ea", "#87badd", "#579ccc", "#357ab0", "#1a558a", "#122b39"]


def get_color(pct):
    if pd.isna(pct):
        return "#d6d4d4"
    for i, (lo, hi) in enumerate(zip(bins[:-1], bins[1:])):
        if lo <= pct < hi:
            return eco_blues[i]
    return eco_blues[-1]


gdf["color"] = gdf["UC_pct"].apply(get_color)

# ── 4. Plot ───────────────────────────────────────────────────────────────────
# Project to British National Grid so the UK isn't squished
gdf = gdf.set_crs("EPSG:4326").to_crs("EPSG:27700")

fig, ax = plt.subplots(figsize=(6.5, 9), facecolor="white")
# Leave right portion for legend; tight top to minimise white space
plt.subplots_adjust(left=0.01, right=0.62, top=0.93, bottom=0.01)
gdf.plot(ax=ax, color=gdf["color"].tolist(), edgecolor="white", linewidth=0.3)
ax.axis("off")

# Title — placed at top of figure
fig.text(
    0.02, 0.99,
    "Percentage of the 18 to 21-year-old population on\nUniversal Credit by Local Authority",
    fontsize=12, fontweight="bold", color="#122b39", ha="left", va="top",
)
fig.text(
    0.02, 0.945,
    "Percentage of 18\u201321 year olds on UC in Great Britain: 11.1%",
    fontsize=9, color="#596870", ha="left", va="top",
)

# Legend — placed in right margin
patches = [mpatches.Patch(color=eco_blues[i], label=labels[i]) for i in range(len(labels))]
patches.append(mpatches.Patch(color="#d6d4d4", label="No data"))
legend = ax.legend(
    handles=patches,
    loc="upper left",
    frameon=False,
    fontsize=8.5,
    title="% of 18\u201321 year\nolds on UC",
    title_fontsize=9,
    labelcolor="#122b39",
    bbox_to_anchor=(1.05, 1.0),
)
legend.get_title().set_color("#122b39")
legend.get_title().set_fontweight("bold")

plt.savefig("uc_by_la.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved to charts/uc_by_la.png")
