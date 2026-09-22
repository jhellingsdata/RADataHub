from pathlib import Path
import numpy as np, pandas as pd
DATA=Path(__file__).resolve().parent.parent/"data"
df=pd.read_csv(DATA/"outcome_with_gdp.csv")

# IMF WEO Advanced Economies -> exclude to leave the EMDE spine
AE={"AUS","AUT","BEL","CAN","CYP","CZE","DNK","EST","FIN","FRA","DEU","GRC",
    "HKG","ISL","IRL","ISR","ITA","JPN","KOR","LVA","LTU","LUX","MAC","MLT",
    "NLD","NZL","NOR","PRT","PRI","SMR","SGP","SVK","SVN","ESP","SWE","CHE",
    "TWN","GBR","USA","AND"}
dropped=sorted(df.loc[df['iso3'].isin(AE),'country'].unique())
n0=df['iso3'].nunique()
df=df[~df['iso3'].isin(AE)].copy()
print(f"Dropped {n0-df['iso3'].nunique()} advanced economies:\n  {dropped}\n")

# Fix: distress = NaN where GDP missing (not 0)
for thr in (1,5):
    col=f"in_default_{thr}pct"
    df[col]=np.where(df['gdp'].notna(),(df['def_total_pctgdp']>=thr).astype(float),np.nan)
    print(f">= {thr}% of GDP: {int(np.nansum(df[col]))} flagged, "
          f"{int(df[col].isna().sum())} country-years now NaN (missing GDP)")

print("\nFragile states that were being coded 0, now NaN where GDP is gone:")
print(df[df['iso3'].isin(['YEM','ERI','SYR'])]
      [['country','year','def_total','gdp','in_default_1pct']].dropna(subset=['def_total']).tail(9).to_string(index=False))

df.to_csv(DATA/"outcome_emde.csv",index=False)
print("\nSaved:",DATA/"outcome_emde.csv","| countries:",df['iso3'].nunique())
