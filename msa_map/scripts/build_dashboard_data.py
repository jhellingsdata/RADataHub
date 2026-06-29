"""
build_dashboard_data.py
========================
Merges population, IMD, and GVA ranking CSVs with hardcoded MSA metadata
into data/processed/msa_all_indicators.json, consumed by dashboard/index.html.

Run from project root:
  python scripts/build_dashboard_data.py
"""

import json
import math
import pandas as pd

BASE = "/Users/h.cantekin/Library/CloudStorage/OneDrive-LondonSchoolofEconomics/Documents/GitHub/RADataHub/msa_map"

POP_CSV          = f"{BASE}/data/processed/msa_population_ranks.csv"
IMD_CSV          = f"{BASE}/data/processed/msa_imd_ranks.csv"
GVA_CSV          = f"{BASE}/data/processed/msa_gva_ranks.csv"
RURAL_URBAN_CSV  = f"{BASE}/data/processed/msa_rural_urban_scores.csv"
LAD_GEOJSON      = f"{BASE}/data/processed/lad.geojson"
DPP_LOOKUP_CSV   = f"{BASE}/data/raw/lookups/dpp_lad_lookup_manual.csv"
OUT_PATH         = f"{BASE}/data/processed/msa_all_indicators.json"

# The rural/urban CSV spells three MSA names with "and" instead of "&", same as the IMD CSV.
RURAL_URBAN_NAME_FIX = {
    "York and North Yorkshire": "York & North Yorkshire",
    "Hull and East Yorkshire": "Hull & East Yorkshire",
    "Cambridgeshire and Peterborough": "Cambridgeshire & Peterborough",
}

# website: null for every MSA — filling in official CA URLs is a manual,
# fact-checked step left to the project owner. The dashboard hides the
# website row whenever this is null.
MSA_METADATA = {
    "Greater Manchester":            {"id":"gmca",  "gss":"E47000001", "tier":"Established", "deal_level":"Trailblazer", "mayor":"Andy Burnham",    "established":"May 2017",      "area_km2":1276, "website": None},
    "West Midlands":                 {"id":"wmca",  "gss":"E47000007", "tier":"Established", "deal_level":"Trailblazer", "mayor":"Richard Parker",  "established":"June 2016",     "area_km2":902,  "website": None},
    "North East":                    {"id":"neca",  "gss":"E47000014", "tier":"Established", "deal_level":"Level 4",     "mayor":"Kim McGuinness",  "established":"May 2024",      "area_km2":3583, "website": None},
    "Liverpool City Region":         {"id":"lcrca", "gss":"E47000004", "tier":"Established", "deal_level":"Level 3",     "mayor":"Steve Rotheram",  "established":"May 2017",      "area_km2":720,  "website": None},
    "South Yorkshire":               {"id":"symca", "gss":"E47000002", "tier":"Established", "deal_level":"Level 3",     "mayor":"Oliver Coppard",  "established":"May 2018",      "area_km2":1552, "website": None},
    "West Yorkshire":                {"id":"wyca",  "gss":"E47000003", "tier":"Established", "deal_level":"Level 3",     "mayor":"Tracy Brabin",    "established":"May 2021",      "area_km2":2029, "website": None},
    "West of England":               {"id":"weca",  "gss":"E47000009", "tier":"Established", "deal_level":"Level 3",     "mayor":"Helen Godwin",    "established":"June 2017",     "area_km2":1326, "website": None},
    "Lancashire":                    {"id":"lcca",  "gss":"E47000018", "tier":"Established", "deal_level":"Level 3",     "mayor":"None yet",        "established":"February 2025", "area_km2":2894, "website": None},
    "Tees Valley":                   {"id":"tvca",  "gss":"E47000006", "tier":"Existing",    "deal_level":"Level 3",     "mayor":"Ben Houchen",     "established":"May 2017",      "area_km2":790,  "website": None},
    "York & North Yorkshire":        {"id":"ynyca", "gss":"E47000012", "tier":"Existing",    "deal_level":"Level 3",     "mayor":"David Skaith",    "established":"February 2024", "area_km2":8309, "website": None},
    "Hull & East Yorkshire":         {"id":"heyca", "gss":"E47000016", "tier":"Existing",    "deal_level":"Level 3",     "mayor":"Luke Campbell",   "established":"February 2025", "area_km2":2455, "website": None},
    "Greater Lincolnshire":          {"id":"glcca", "gss":"E47000017", "tier":"Existing",    "deal_level":"Level 3",     "mayor":"Dame Andrea Jenkyns","established":"February 2025","area_km2":6980, "website": None},
    "East Midlands":                 {"id":"emcca", "gss":"E47000013", "tier":"Existing",    "deal_level":"Level 3",     "mayor":"Claire Ward",     "established":"May 2024",      "area_km2":6164, "website": None},
    "Cambridgeshire & Peterborough": {"id":"cpca",  "gss":"E47000008", "tier":"Existing",    "deal_level":"Level 3",     "mayor":"Paul Bristow",    "established":"May 2017",      "area_km2":3389, "website": None},
    "Sussex & Brighton":             {"id":"sus",   "gss":"TBC",       "tier":"DPP",         "deal_level":"DPP",         "mayor":"None yet",        "established":"2026 (expected)","area_km2":3787, "website": None},
    "Hampshire & Solent":            {"id":"ham",   "gss":"TBC",       "tier":"DPP",         "deal_level":"DPP",         "mayor":"None yet",        "established":"2026 (expected)","area_km2":3769, "website": None},
    "Cheshire & Warrington":         {"id":"che",   "gss":"TBC",       "tier":"DPP",         "deal_level":"DPP",         "mayor":"None yet",        "established":"2026 (expected)","area_km2":2267, "website": None},
    "Cumbria":                       {"id":"cum",   "gss":"TBC",       "tier":"DPP",         "deal_level":"DPP",         "mayor":"None yet",        "established":"2026 (expected)","area_km2":6768, "website": None},
    "Greater Essex":                 {"id":"ess",   "gss":"TBC",       "tier":"DPP",         "deal_level":"DPP",         "mayor":"None yet",        "established":"TBC",           "area_km2":3670, "website": None},
    "Norfolk & Suffolk":             {"id":"nas",   "gss":"TBC",       "tier":"DPP",         "deal_level":"DPP",         "mayor":"None yet",        "established":"TBC",           "area_km2":9169, "website": None},
}

ENGLAND_BENCHMARKS = {
    "pop_2024":               58620101,
    "density_2024":           449.8,
    "gva_ph_2023":            36632,
    "gva_growth_2018_23":     24.2,
    "imd_pct_decile1":        10.0,
    # Population-weighted mean RUC21 rurality score (0=urban, 100=rural) across all
    # 33,755 English LSOAs, mid-2024 SAPE population weights — see scripts/rural_urban.ipynb
    # Section 10. Used both as the "vs England" benchmark and as the Predominantly
    # Rural/Urban tag threshold below.
    "rural_urban_score":      12.7,
}


def to_native(v):
    """Convert numpy/pandas scalars to native Python types; NaN -> None."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def load_indicator_frames():
    pop = pd.read_csv(POP_CSV)
    imd = pd.read_csv(IMD_CSV)
    gva = pd.read_csv(GVA_CSV)
    rural_urban = pd.read_csv(RURAL_URBAN_CSV)

    # The IMD and rural/urban CSVs spell three MSA names with "and" instead of "&" —
    # normalise so all frames key identically on msa_name.
    imd["msa_name"] = imd["msa_name"].str.replace(" and ", " & ", regex=False)
    rural_urban["msa_name"] = rural_urban["msa_name"].replace(RURAL_URBAN_NAME_FIX)

    # rank_pct_decile1 in the source CSV ranks 1 = highest % (most deprived,
    # worst) — backwards from every other indicator here, where 1 = best.
    # Recompute so rank 1 = lowest % most-deprived decile (best), consistent
    # with rank_pop_2024 / rank_gva_ph / rank_gva_growth_1823 conventions.
    imd["rank_pct_decile1_fixed"] = (
        imd["pct_decile_1"].rank(ascending=True, method="min").astype(int)
    )

    # rural_urban_scores.csv covers 21 MSAs (it also includes Devon and Torbay, which
    # isn't part of this dashboard's 20-MSA roster) and ranks across all 21. Restrict to
    # the 20 MSAs in MSA_METADATA before re-ranking, so "Rank in MSAs ... / 20" is correct.
    rural_urban = rural_urban[rural_urban["msa_name"].isin(MSA_METADATA.keys())].copy()
    rural_urban["rank_rural_urban_score"] = (
        rural_urban["pop_weighted_rurality_score"].rank(ascending=False, method="min").astype(int)
    )

    return (
        pop.set_index("msa_name"),
        imd.set_index("msa_name"),
        gva.set_index("msa_name"),
        rural_urban.set_index("msa_name"),
    )


def load_dpp_lad_lookup():
    """{dpp_area_name: {'codes': [LAD25CD,...], 'names': [LAD25NM,...]}} from the manual DPP lookup."""
    df = pd.read_csv(DPP_LOOKUP_CSV)
    out = {}
    for area, grp in df.groupby("dpp_area"):
        codes = [c for c in grp["lad25_code"].dropna().tolist() if c]
        names = [n for n in grp["lad25_name"].dropna().tolist() if n]
        out[area] = {"codes": codes, "names": sorted(names)}
    return out


def load_constituent_las(gss_code, lad_features):
    names = sorted({
        f["properties"]["LAD25NM"]
        for f in lad_features
        if f["properties"].get("ca_gss_code") == gss_code
    })
    return names


def build():
    print("── Loading indicator CSVs ───────────────────────────────────────")
    pop_idx, imd_idx, gva_idx, rural_urban_idx = load_indicator_frames()
    print(f"   pop rows: {len(pop_idx)}  imd rows: {len(imd_idx)}  gva rows: {len(gva_idx)}  rural/urban rows: {len(rural_urban_idx)}")

    print("\n── Loading DPP LAD lookup ────────────────────────────────────────")
    dpp_lookup = load_dpp_lad_lookup()
    print(f"   DPP areas: {list(dpp_lookup.keys())}")

    print("\n── Loading LAD boundaries for constituent LA names ──────────────")
    with open(LAD_GEOJSON) as f:
        lad_features = json.load(f)["features"]

    print("\n── Building MSA records ──────────────────────────────────────────")
    msas = []
    for name, meta in MSA_METADATA.items():
        pop_row = pop_idx.loc[name] if name in pop_idx.index else None
        imd_row = imd_idx.loc[name] if name in imd_idx.index else None
        gva_row = gva_idx.loc[name] if name in gva_idx.index else None
        ru_row  = rural_urban_idx.loc[name] if name in rural_urban_idx.index else None

        indicators = {
            "pop_2024":           to_native(pop_row["pop_2024"])           if pop_row is not None else None,
            "density_2024":       to_native(pop_row["density_2024"])       if pop_row is not None else None,
            "gva_ph_2023":        to_native(gva_row["gva_ph_2023"])        if gva_row is not None else None,
            "gva_growth_2018_23": to_native(gva_row["gva_growth_2018_23"]) if gva_row is not None else None,
            "imd_pct_decile1":    to_native(imd_row["pct_decile_1"])       if imd_row is not None else None,
            "rural_urban_score":  to_native(ru_row["pop_weighted_rurality_score"]) if ru_row is not None else None,
        }

        ranks = {
            "pop_2024":           to_native(pop_row["rank_pop_2024"])         if pop_row is not None else None,
            "density_2024":       to_native(pop_row["rank_density_2024"])     if pop_row is not None else None,
            "gva_ph_2023":        to_native(gva_row["rank_gva_ph"])           if gva_row is not None else None,
            "gva_growth_2018_23": to_native(gva_row["rank_gva_growth_1823"])  if gva_row is not None else None,
            "imd_pct_decile1":    to_native(imd_row["rank_pct_decile1_fixed"]) if imd_row is not None else None,
            "rural_urban_score":  to_native(ru_row["rank_rural_urban_score"]) if ru_row is not None else None,
        }

        # Predominantly Rural/Urban tag: compared against England's own population-weighted
        # average rurality score (12.7, see ENGLAND_BENCHMARKS), not a literal "majority of
        # population in a rural LSOA" threshold — empirically no MSA clears 50% on that
        # measure (Cumbria, the most rural, sits at 49.8%), so a strict-majority rule would
        # tag every single MSA "Urban" and defeat the point of the tag.
        rural_urban_tag = None
        if ru_row is not None:
            score = to_native(ru_row["pop_weighted_rurality_score"])
            rural_urban_tag = (
                "Predominantly Rural" if score > ENGLAND_BENCHMARKS["rural_urban_score"]
                else "Predominantly Urban"
            )

        record = {
            "id":              meta["id"],
            "name":            name,
            "gss_code":        meta["gss"],
            "tier":            meta["tier"],
            "deal_level":      meta["deal_level"],
            "mayor":           meta["mayor"],
            "established":     meta["established"],
            "area_km2":        meta["area_km2"],
            "website":         meta["website"],
            "rural_urban_tag": rural_urban_tag,
            "indicators":      indicators,
            "ranks":           ranks,
        }

        if meta["gss"] == "TBC":
            dpp = dpp_lookup.get(name, {"codes": [], "names": []})
            record["constituent_lad_codes"] = dpp["codes"]
            record["constituent_las"]       = dpp["names"]
        else:
            record["constituent_las"] = load_constituent_las(meta["gss"], lad_features)

        missing = [k for k, v in indicators.items() if v is None]
        flag = f"  ⚠  missing: {missing}" if missing else "  ✓"
        print(f"   {name:<32} {flag}")

        msas.append(record)

    output = {
        "metadata": {
            "last_updated":       "2026-06",
            "england_benchmarks": ENGLAND_BENCHMARKS,
        },
        "msas": msas,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n── Saved: {OUT_PATH} ({len(msas)} MSAs) ──────────────────────────")


if __name__ == "__main__":
    build()
