import sys, subprocess, importlib.util
def ensure(pkgs):
    miss=[p for p in pkgs if importlib.util.find_spec(p) is None]
    if miss:
        print("Installing:",miss); subprocess.check_call([sys.executable,"-m","pip","install",*miss])
ensure(["pandas","openpyxl","country_converter"])
import re, logging
from pathlib import Path
import pandas as pd
import country_converter as coco
logging.getLogger("country_converter").setLevel(logging.CRITICAL)

HERE=Path(__file__).resolve().parent
DATA=HERE.parent/"data"

# 1. BoC-BoE outcome, rebuilt from source (with ISO3)
xlsx=next((p for p in [DATA/"boc-boe-database.xlsx", HERE/"boc-boe-database.xlsx"] if p.exists()),None)
if xlsx is None: raise SystemExit("boc-boe-database.xlsx not found in data/")
xls=pd.ExcelFile(xlsx)
sheet=next((s for s in xls.sheet_names if s.lower().startswith("data")),xls.sheet_names[-1])
scan=pd.read_excel(xlsx,sheet_name=sheet,header=None)
hrow=int(scan.index[scan.apply(lambda r:("DEBT_COUNTRY" in r.values) and ("DEBT_YEAR" in r.values),axis=1)][0])
boc=pd.read_excel(xlsx,sheet_name=sheet,header=hrow)
def find(pat):
    h=[c for c in boc.columns if re.fullmatch(pat,str(c))]; return h[0] if h else None
boc=boc.rename(columns={"DEBT_COUNTRY":"country","DEBT_YEAR":"year",
    find(r"DEBT_TOTAL_\d{4}"):"def_total",
    find(r"DEBT_PRIVATE_CREDITORS_\d{4}"):"def_private",
    find(r"DEBT_CHINA_\d{4}"):"def_china"})[["country","year","def_total","def_private","def_china"]]
for c in ["def_total","def_private","def_china","year"]:
    boc[c]=pd.to_numeric(boc[c],errors="coerce")
boc=boc.dropna(subset=["year"])
boc["iso3"]=coco.convert(boc["country"].tolist(),to="ISO3")
boc=boc[boc["iso3"].str.match(r"^[A-Z]{3}$",na=False)]

# 2. WDI GDP: auto-find in data/, any filename or delimiter
def find_wdi():
    for p in list(DATA.glob("*.csv"))+list(DATA.glob("*.txt"))+list(DATA.glob("*.tsv")):
        try: head="".join(open(p,encoding="utf-8",errors="ignore").readlines()[:8])
        except Exception: continue
        if "Country Code" in head and "NY.GDP" in head: return p
    return None
wdi=find_wdi()
if wdi is None: raise SystemExit("WDI GDP file not found in data/ (needs 'Country Code' + 'NY.GDP').")
print("WDI file:",wdi.name)
lines=open(wdi,encoding="utf-8",errors="ignore").readlines()
hdr=next(i for i,l in enumerate(lines) if "Country Code" in l)
delim="\t" if lines[hdr].count("\t")>lines[hdr].count(",") else ","
gdp=pd.read_csv(wdi,skiprows=hdr,sep=delim,engine="python")
gdp.columns=[str(c).strip() for c in gdp.columns]
ycols=[c for c in gdp.columns if re.fullmatch(r"\d{4}",str(c))]
g=gdp.melt(id_vars=["Country Code"],value_vars=ycols,var_name="year",value_name="gdp").rename(columns={"Country Code":"iso3"})
g["year"]=g["year"].astype(int); g["gdp"]=pd.to_numeric(g["gdp"],errors="coerce")
g=g.dropna(subset=["gdp"])

# 3. Join + rebuild the outcome as share of GDP
df=boc.merge(g,on=["iso3","year"],how="left")
print(f"GDP matched for {df['gdp'].notna().mean():.0%} of BoC-BoE country-years")
df["def_total_pctgdp"]=(df["def_total"].fillna(0)*1e6)/df["gdp"]*100   # debt is US$ MILLIONS
for thr in (1,5):
    df[f"in_default_{thr}pct"]=((df["def_total_pctgdp"]>=thr)&df["gdp"].notna()).astype(int)
    print(f"  >= {thr}% of GDP: {int(df[f'in_default_{thr}pct'].sum())} country-years flagged")
print("\nSri Lanka (watch the 1% flag switch on in 2022):")
print(df[df['iso3']=='LKA'][['year','def_total','gdp','def_total_pctgdp','in_default_1pct']].tail(6).to_string(index=False))
df.to_csv(DATA/"outcome_with_gdp.csv",index=False)
print("\nSaved:",DATA/"outcome_with_gdp.csv")
