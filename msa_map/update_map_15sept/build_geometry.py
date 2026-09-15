"""Dissolve 2013 LADs into Strategic Authority footprints, reproject to
British National Grid, simplify, and write GeoJSON for Altair."""

import geopandas as gpd
import pandas as pd

BNG = "EPSG:27700"
SIMPLIFY_M = 250  # metres; keeps coastline legible at report scale
CLOSE_M = 200     # metres; closes hairline gaps between adjacent LAD polygons


HOLE_KEEP_KM2 = 50  # interior rings above this are reported, never dropped silently


def fill_water_holes(geoseries, label=""):
    """Drop interior rings caused by inland water and estuaries being excluded
    from the LAD polygons. No Strategic Authority encloses a non-member area,
    so every ring here is a water artefact, but anything above the threshold is
    reported rather than removed so a genuine enclave could never vanish."""
    from shapely.geometry import MultiPolygon, Polygon

    kept = []
    for name, geom in zip(geoseries.index, geoseries):
        parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        new_parts = []
        for p in parts:
            keep_rings = []
            for ring in p.interiors:
                a = Polygon(ring).area / 1e6
                if a >= HOLE_KEEP_KM2:
                    print(f"  KEPT interior ring {a:.1f} km2 in {label} {name} - check this")
                    keep_rings.append(ring)
            new_parts.append(Polygon(p.exterior, keep_rings))
        kept.append(new_parts[0] if len(new_parts) == 1 else MultiPolygon(new_parts))
    return gpd.GeoSeries(kept, index=geoseries.index, crs=geoseries.crs)


def clean(geoseries):
    """Close hairline slivers left by dissolving generalised boundaries, then
    simplify and snap to whole metres. Buffer out-and-back must happen before
    simplification, or the gaps survive as white lines through the interior of
    each authority.

    Snapping to 1 m is invisible at report scale (one metre is a thousandth of
    a pixel here) and roughly halves the size of the exported Vega-Lite spec,
    which carries the geometry inline."""
    return (geoseries.buffer(CLOSE_M)
                     .buffer(-CLOSE_M)
                     .simplify(SIMPLIFY_M)
                     .make_valid()
                     .set_precision(1.0))

lads = gpd.read_file("geo/eng_lad.json").set_crs("EPSG:4326", allow_override=True)
lads = lads.to_crs(BNG)
lads = lads.rename(columns={"LAD13NM": "lad13nm", "LAD13CD": "lad13cd"})

xwalk = pd.read_csv("msa_lad_crosswalk.csv")
tiers = pd.read_csv("msa_tiers.csv")

lads = lads.merge(xwalk, on="lad13nm", how="left")
print("LADs unassigned:", lads.short_name.isna().sum())

# England outline (dissolve everything, drop the Isles of Scilly sliver noise)
england = gpd.GeoDataFrame(
    {"name": ["England"]},
    geometry=[lads.union_all()],
    crs=BNG,
)
england["geometry"] = fill_water_holes(clean(england.geometry), "England")

# Strategic Authority footprints
sas = lads.dropna(subset=["short_name"]).dissolve(by="short_name").reset_index()
sas = sas[["short_name", "geometry"]].merge(tiers, on="short_name", how="left")
sas["geometry"] = fill_water_holes(clean(sas.geometry), "SA")
print("SA polygons:", len(sas))

# Representative point for each authority: the centre of its largest part,
# which behaves better than a centroid for multi-part or concave shapes.
def biggest_part(geom):
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom

pts = sas.copy()
pts["geometry"] = pts.geometry.map(biggest_part).representative_point()
pts["anchor_x"] = pts.geometry.x
pts["anchor_y"] = pts.geometry.y

area_km2 = sas.geometry.area / 1e6
sas["area_km2"] = area_km2.round(0)

bounds = england.total_bounds
print("England bounds (BNG):", [round(b) for b in bounds])
print("aspect (h/w):", round((bounds[3] - bounds[1]) / (bounds[2] - bounds[0]), 3))

england.to_file("geo/england.geojson", driver="GeoJSON")
sas.to_file("geo/sa_areas.geojson", driver="GeoJSON")
pts[["short_name", "tier", "anchor_x", "anchor_y"]].to_csv("msa_anchors.csv", index=False)

print(sas[["short_name", "tier", "area_km2"]].sort_values("area_km2").to_string(index=False))
