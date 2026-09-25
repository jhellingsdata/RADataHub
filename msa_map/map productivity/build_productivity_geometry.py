"""Join ONS LAD-level labour productivity to LAD boundaries (England only),
and stage the Strategic Authority ("MSA") outline layer alongside it.

Pipeline
    build_productivity_geometry.py -> geo/lad_productivity.geojson
    productivity_map.py            -> outputs/lad_productivity_map.{png,svg,html,vl.json}

Data
    sources/05_ONS_LAD_labour_productivity_2025edition.xls
        ONS "Subregional productivity: labour productivity indices by local
        authority district", released 19 June 2025. Sheet A1 = current-price
        (smoothed) GVA per hour worked index, UK=100, Local Authority
        District, 2004-2023. Header row at index 4: LAD_Code, LAD_Name,
        Index_2004 ... Index_2023.
    geo/lad_may2024.geojson
        ONS Open Geography Portal, "Local Authority Districts (May 2024)
        Boundaries UK BGC", fetched from the ArcGIS FeatureServer. Verified
        by exact-match diff against the productivity file's 296 English LAD
        codes (zero mismatches either direction) - this is the correct
        boundary vintage, no Isles-of-Scilly-style dropout occurred.
    geo/sa_areas.geojson
        Copied as-is from the user's existing RADataHub/msa_map project:
        22 England Strategic/Combined Authority footprints, dissolved from
        2013 LAD boundaries, already cleaned (water-hole removal, 250m
        simplify, 1m precision snap), EPSG:27700. Reused unmodified as an
        outline-only overlay - authority *outer* boundaries are stable
        across the 2023 LAD reorganisation even though the dissolve predates
        it (see that project's README for the rationale).
"""

import geopandas as gpd
import pandas as pd

BNG = "EPSG:27700"
YEAR = "Index_2023"  # most recent year in the current ONS edition

# ---------------------------------------------------------------------------
# Productivity data
# ---------------------------------------------------------------------------

prod = pd.read_excel(
    "sources/05_ONS_LAD_labour_productivity_2025edition.xls",
    sheet_name="A1", header=4,
)
prod = prod[prod.LAD_Code.str.startswith("E", na=False)].copy()
prod = prod[["LAD_Code", "LAD_Name", YEAR]].rename(columns={YEAR: "productivity"})

print(f"Productivity file: {len(prod)} English LADs, "
      f"range {prod.productivity.min():.1f}-{prod.productivity.max():.1f} (UK=100)")

# ---------------------------------------------------------------------------
# LAD boundaries (England only)
# ---------------------------------------------------------------------------

lads = gpd.read_file("geo/lad_may2024.geojson")
lads = lads.set_crs("EPSG:4326", allow_override=True).to_crs(BNG)
lads = lads[lads.LAD24CD.str.startswith("E")].copy()

# Vintage check: this must be zero/zero, or the join below is silently wrong.
data_codes = set(prod.LAD_Code)
geo_codes = set(lads.LAD24CD)
only_in_data = sorted(data_codes - geo_codes)
only_in_geo = sorted(geo_codes - data_codes)
print(f"LAD boundary file: {len(lads)} English LADs")
print(f"  codes in data but not boundary: {only_in_data}")
print(f"  codes in boundary but not data: {only_in_geo}")
assert not only_in_data and not only_in_geo, "LAD boundary/data vintage mismatch"

# ---------------------------------------------------------------------------
# Join (left, on boundary, so every polygon survives even if unmatched)
# ---------------------------------------------------------------------------

lads = lads.merge(prod, left_on="LAD24CD", right_on="LAD_Code", how="left")
n_matched = lads.productivity.notna().sum()
print(f"Joined: {n_matched}/{len(lads)} LADs have a productivity value")
if n_matched < len(lads):
    missing = lads[lads.productivity.isna()][["LAD24CD", "LAD24NM"]]
    print("  unmatched:\n", missing.to_string(index=False))

# Spot checks
for code, label in [("E08000003", "Manchester"), ("E07000047", "West Devon (rural)")]:
    row = lads[lads.LAD24CD == code]
    if not row.empty:
        print(f"  spot check {label} ({code}): {row.productivity.iloc[0]}")
    else:
        print(f"  spot check {label} ({code}): NOT FOUND in boundary file")

lads.to_file("geo/lad_productivity.geojson", driver="GeoJSON")
print("wrote geo/lad_productivity.geojson")
