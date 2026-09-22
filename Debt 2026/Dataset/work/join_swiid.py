#!/usr/bin/env python
"""
join_swiid.py  —  Merge SWIID 9.92 disposable-income Gini onto the EMDE outcome panel.

Reads:   data/outcome_emde.csv          (country, year, iso3, def_*, gdp, in_default_*)
         data/swiid9_92_summary.csv      (country, year, gini_disp, gini_mkt, ...)
Writes:  data/emde_with_gini.csv         (full annual panel: outcome + gini side by side)
         data/gini_prewindow.csv         (iso3 -> mean gini_disp over 2010-2019, headline predictor)

Run:     cd "/Users/georgerushworth/repos/RADataHub/Debt 2026/Dataset"
         python work/join_swiid.py
"""
from pathlib import Path
import pandas as pd
import country_converter as coco

# ----------------------------------------------------------------------
# paths — script lives in work/, data lives in ../data/
# ----------------------------------------------------------------------
DATA = Path(__file__).resolve().parent.parent / "data"
OUTCOME = DATA / "outcome_emde.csv"

# ----------------------------------------------------------------------
# 1. load the outcome spine
# ----------------------------------------------------------------------
if not OUTCOME.exists():
    raise SystemExit(f"Missing {OUTCOME}. Run finalize_outcome.py first.")
out = pd.read_csv(OUTCOME)
print(f"Outcome panel: {len(out)} rows, {out['iso3'].nunique()} countries")

# ----------------------------------------------------------------------
# 2. locate the SWIID summary csv anywhere under data/
#    (works whether you dropped it in data/ directly or left it nested
#     in data/swiid9_92/)
# ----------------------------------------------------------------------
def find_swiid(folder: Path):
    # prefer a file with 'summary' in the name; fall back to any csv with gini_disp
    candidates = list(folder.rglob("*summary*.csv")) or list(folder.rglob("*.csv"))
    for p in candidates:
        try:
            head = pd.read_csv(p, nrows=0)
        except Exception:
            continue
        cols = {c.lower() for c in head.columns}
        if {"country", "year", "gini_disp"} <= cols:
            return p
    return None

sp = find_swiid(DATA)
if sp is None:
    raise SystemExit(
        "No SWIID summary CSV found under data/.\n"
        "Expected a file containing columns country, year, gini_disp "
        "(e.g. swiid9_92_summary.csv). Unzip swiid9_92.zip into data/."
    )
print(f"SWIID file:    {sp.relative_to(DATA)}")

# ----------------------------------------------------------------------
# 3. load SWIID, keep the value columns that exist, map names -> iso3
# ----------------------------------------------------------------------
sw = pd.read_csv(sp)
sw.columns = [c.lower() for c in sw.columns]
val = [c for c in ["gini_disp", "gini_mkt", "abs_red", "rel_red"] if c in sw.columns]
sw = sw[["country", "year"] + val].copy()

cc = coco.CountryConverter()
sw["iso3"] = cc.convert(sw["country"].tolist(), to="ISO3", not_found=None)
# 'Soviet Union' / 'Yugoslavia' historical rows won't map -> dropped here, which is correct
dropped = sorted({c for c, i in zip(sw["country"], sw["iso3"]) if i is None})
if dropped:
    print(f"SWIID names not mapped to ISO3 (dropped): {dropped}")

sw = (sw[sw["iso3"].notna()]
      .groupby(["iso3", "year"], as_index=False)[val]
      .mean())

# ----------------------------------------------------------------------
# 4. full-panel left join (annual gini kept beside the outcome)
# ----------------------------------------------------------------------
merged = out.merge(sw, on=["iso3", "year"], how="left")
merged.to_csv(DATA / "emde_with_gini.csv", index=False)
print(f"\nWrote emde_with_gini.csv: {len(merged)} rows")

# ----------------------------------------------------------------------
# 5. coverage diagnostics
# ----------------------------------------------------------------------
n = out["iso3"].nunique()
g = merged.loc[merged["gini_disp"].notna(), "iso3"].nunique()
print(f"\nEMDE countries: {n} | with any gini_disp: {g} ({g/n*100:.0f}%)")

pre = merged[(merged.year >= 2010) & (merged.year <= 2019)]
cov = pre.groupby("iso3")["gini_disp"].apply(lambda s: s.notna().mean())
full = int((cov == 1).sum())
part = int(((cov > 0) & (cov < 1)).sum())
none = int((cov == 0).sum())
print(f"2010-19 gini_disp coverage: full={full}  partial={part}  none={none}")

names = out.drop_duplicates("iso3").set_index("iso3")["country"]
noncov = sorted(cov[cov == 0].index)
print("\nNO 2010-19 gini (these drop out of any inequality model):")
print("  " + ", ".join(f"{i}({names.get(i,'?')})" for i in noncov))

# ----------------------------------------------------------------------
# 6. pre-window inequality = mean over AVAILABLE 2010-19 years
#    (Berg-Sachs used a single inequality snapshot; a partial-decade
#     mean is defensible, so we don't require all ten years present)
# ----------------------------------------------------------------------
gini_pre = pre.groupby("iso3")["gini_disp"].mean().rename("gini_disp_1019")
gini_pre.to_csv(DATA / "gini_prewindow.csv")
print(f"\nWrote gini_prewindow.csv: {gini_pre.notna().sum()} countries with a pre-window mean")

# quick sanity peek: inequality for the deep-distress 2020s cases
deep = ["LKA", "GHA", "ZMB", "LBN", "ETH", "MOZ", "MRT", "TCD", "UKR", "SUR",
        "VEN", "SOM", "SDN", "HTI", "NIC", "COG", "CAF", "ZWE", "ARG", "IRQ"]
print("\npre-window mean gini_disp, deep-distress 2020s cases:")
print(gini_pre[gini_pre.index.isin(deep)].round(1).to_string())

