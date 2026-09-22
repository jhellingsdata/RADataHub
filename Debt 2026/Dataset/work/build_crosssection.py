#!/usr/bin/env python
"""
build_crosssection.py  —  Collapse the annual outcome to a 2020-2024 cross-section,
join gini + V-Dem predictors, report the true modelling N and distress base rates.

Reads:  data/outcome_emde.csv       (annual DV, 1960-2023)
        data/gini_prewindow.csv     (iso3 -> gini_disp_1019)
        data/vdem_prewindow.csv     (iso3 -> polyarchy etc, 2010-19 means)
Writes: data/crosssection.csv       (one row per country: DV flags + all predictors)

Run: cd "/Users/georgerushworth/repos/RADataHub/Debt 2026/Dataset"
     python work/build_crosssection.py
"""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
WIN_START, WIN_END = 2020, 2024          # outcome window (data ends 2023)
PRE_A, PRE_B       = 2018, 2019          # "clean going in" check for entry DV

out = pd.read_csv(DATA / "outcome_emde.csv")

# --- collapse the annual DV two ways -------------------------------------
win  = out[(out.year >= WIN_START) & (out.year <= WIN_END)]
pre  = out[(out.year >= PRE_A)     & (out.year <= PRE_B)]

# (1) incidence: distressed at any point in the window (NaN if all-missing)
inc = (win.groupby("iso3")["in_default_5pct"]
          .apply(lambda s: s.max() if s.notna().any() else pd.NA)
          .rename("distress_incidence"))

# was the country already distressed going in? (max over 2018-19)
already = (pre.groupby("iso3")["in_default_5pct"]
              .apply(lambda s: s.max() if s.notna().any() else pd.NA)
              .rename("pre_distress"))

dv = pd.concat([inc, already], axis=1).reset_index()

# (2) entry: distressed in window AND not already distressed going in
def entry(row):
    if pd.isna(row.distress_incidence):
        return pd.NA
    if row.distress_incidence == 0:
        return 0
    # incidence==1: it's an ENTRY only if it was clean (0) pre-window
    if row.pre_distress == 0:
        return 1
    if row.pre_distress == 1:
        return 0            # chronic, already in -> not an entry
    return pd.NA            # pre-window unknown -> entry status unknown
dv["distress_entry"] = dv.apply(entry, axis=1)

# --- join predictors ------------------------------------------------------
gini = pd.read_csv(DATA / "gini_prewindow.csv")
vdem = pd.read_csv(DATA / "vdem_prewindow.csv")
names = out.drop_duplicates("iso3").set_index("iso3")["country"]

cs = (dv.merge(gini, on="iso3", how="left")
        .merge(vdem, on="iso3", how="left"))
cs["country"] = cs["iso3"].map(names)
cs = cs[["iso3","country","distress_incidence","distress_entry",
         "pre_distress","gini_disp_1019","v2x_polyarchy","v2x_libdem",
         "v2x_rule","v2x_civlib","v2caviol","v2csreprss"]]
cs.to_csv(DATA / "crosssection.csv", index=False)
print(f"Wrote crosssection.csv: {len(cs)} countries\n")

# --- base rates -----------------------------------------------------------
for col in ["distress_incidence","distress_entry"]:
    s = cs[col].dropna()
    print(f"{col:20s} N={len(s):3d}  positives={int(s.sum()):3d}  base rate={s.mean()*100:.0f}%")

# --- true modelling N (complete cases on the core model) ------------------
core = cs.dropna(subset=["distress_incidence","gini_disp_1019","v2x_polyarchy"])
print(f"\nComplete cases (incidence + gini + polyarchy): N={len(core)}")
core_e = cs.dropna(subset=["distress_entry","gini_disp_1019","v2x_polyarchy"])
print(f"Complete cases (entry     + gini + polyarchy): N={len(core_e)}")

# what drops, and why
lost = cs[cs["gini_disp_1019"].isna() | cs["v2x_polyarchy"].isna()]
print(f"\nDropped from core model ({len(lost)}): missing gini and/or polyarchy")
print("  gini-missing :", ", ".join(sorted(cs.loc[cs.gini_disp_1019.isna(),"iso3"])))
print("  vdem-missing :", ", ".join(sorted(cs.loc[cs.v2x_polyarchy.isna(),"iso3"])))

# --- the 2020s entries: who newly fell into deep distress -----------------
entries = cs[cs.distress_entry == 1].sort_values("gini_disp_1019", na_position="last")
print(f"\n2020-24 clean ENTRIES into >=5% distress ({len(entries)}):")
for _,r in entries.iterrows():
    g = f"{r.gini_disp_1019:.0f}" if pd.notna(r.gini_disp_1019) else " ?"
    p = f"{r.v2x_polyarchy:.2f}" if pd.notna(r.v2x_polyarchy) else "  ?"
    print(f"  {r.iso3}  gini={g}  polyarchy={p}  {r.country}")

# --- crude cross-tab: does gini differ by distress? -----------------------
print("\nMean pre-window gini by incidence status (complete cases):")
print(core.groupby("distress_incidence")["gini_disp_1019"].agg(["mean","count"]).round(1).to_string())
print("\nMean polyarchy by incidence status:")
print(core.groupby("distress_incidence")["v2x_polyarchy"].agg(["mean","count"]).round(3).to_string())
