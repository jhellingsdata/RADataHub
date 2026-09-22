#!/usr/bin/env python
"""
join_vdem.py  —  Pull V-Dem v16 political variables, collapse to the 2010-19
pre-window mean, join onto the EMDE spine.

Reads only the columns we need via usecols, so the 406 MB / ~4000-col file
never lands in memory in full.

Run: cd "/Users/georgerushworth/repos/RADataHub/Debt 2026/Dataset"
     python work/join_vdem.py
"""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
VDEM = DATA / "V-Dem-CY-Full+Others-v16.csv"   # comma-delimited, confirmed

IDS  = ["country_text_id", "year"]             # country_text_id IS iso3
VARS = [
    "v2x_polyarchy",   # electoral democracy index (headline)
    "v2x_libdem",      # liberal democracy (robustness)
    "v2x_rule",        # rule of law
    "v2x_civlib",      # civil liberties
    "v2caviol",        # political violence (mechanism; may be sparse)
    "v2csreprss",      # civil society repression (mechanism; may be sparse)
]

if not VDEM.exists():
    raise SystemExit(f"Missing {VDEM}")

# which of VARS actually exist in this file's header
header = pd.read_csv(VDEM, nrows=0).columns
vars_present = [v for v in VARS if v in header]
missing = [v for v in VARS if v not in header]
if missing:
    print(f"note: not in this file, skipped: {missing}")

vd = pd.read_csv(VDEM, usecols=IDS + vars_present, low_memory=False)
vd = vd.rename(columns={"country_text_id": "iso3"})

# EMDE spine
out = pd.read_csv(DATA / "outcome_emde.csv")
emde = sorted(out["iso3"].unique())

# pre-window mean over available 2010-19 years, EMDE only
pre = vd[(vd.year >= 2010) & (vd.year <= 2019) & (vd.iso3.isin(emde))]
coll = pre.groupby("iso3", as_index=False)[vars_present].mean()
coll = coll.set_index("iso3").reindex(emde).reset_index()
coll.to_csv(DATA / "vdem_prewindow.csv", index=False)
print(f"\nWrote vdem_prewindow.csv: {len(coll)} EMDE rows")

# coverage per variable
n = len(coll)
print("\nPre-window (2010-19) coverage by variable:")
for v in vars_present:
    have = coll[v].notna().sum()
    print(f"  {v:16s} {have:3d}/{n}  ({have/n*100:.0f}%)")

names = out.drop_duplicates("iso3").set_index("iso3")["country"]
noncov = sorted(coll.loc[coll["v2x_polyarchy"].isna(), "iso3"])
print("\nNo v2x_polyarchy:")
print("  " + (", ".join(f"{i}({names.get(i,'?')})" for i in noncov) if noncov else "(none)"))

deep = ["LKA","GHA","ZMB","LBN","ETH","MOZ","MRT","TCD","UKR","SUR",
        "VEN","SOM","SDN","HTI","NIC","COG","CAF","ZWE","ARG","IRQ"]
d = coll[coll.iso3.isin(deep)].set_index("iso3")["v2x_polyarchy"].round(3)
print("\npre-window mean v2x_polyarchy, deep-distress 2020s cases:")
print(d.to_string())
