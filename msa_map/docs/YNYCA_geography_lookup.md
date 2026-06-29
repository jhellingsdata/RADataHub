# YNYCA geography lookup

A reference for how York & North Yorkshire Combined Authority (YNYCA) is built up from
ONS standard geographies, and the code/name crosswalks needed to join data correctly
across them. Built from the same lookups and fixes used throughout `rural_urban.ipynb`
and `YNYCA.ipynb` — this consolidates that logic into one place rather than
re-deriving it notebook by notebook.

## The hierarchy

```
2,765 Output Areas (OA21CD)
   └─ 500 LSOAs (LSOA21CD / LSOA21NM)
        └─ 101 MSOAs (MSOA21CD / MSOA21NM)
             └─ 2 current Local Authority Districts (York, North Yorkshire)
                  └─ 1 Combined Authority — YNYCA (E47000012)
```

Every level nests cleanly into the one above (no splits), so a simple `groupby`/`merge`
on these codes is enough to move between levels — the one real complication is the
**LAD vintage mismatch** below.

## The LAD vintage gotcha

ONS Output Area lookups are fixed at **December 2021** geography. North Yorkshire went
unitary in **April 2023**, merging seven former districts into one council — *after*
that lookup was published. So any OA/LSOA-level data (the Rural Urban Classification,
the December 2021 OA→LSOA→LAD lookup, etc.) still carries the seven old district codes,
not the current one. Data published more recently — IMD 2025, mid-2023/2024 population
estimates — already uses the current code directly. Mixing the two without converting
first is the single most common way a join against this geography silently drops rows
or mismatches names.

| Old LAD22 code | Old name | → | Current LAD25 code | Current name | OAs | LSOAs |
|---|---|---|---|---|---|---|
| E07000163 | Craven | → | E06000065 | North Yorkshire | 194 | 33 |
| E07000164 | Hambleton | → | E06000065 | North Yorkshire | 319 | 53 |
| E07000165 | Harrogate | → | E06000065 | North Yorkshire | 540 | 105 |
| E07000166 | Richmondshire | → | E06000065 | North Yorkshire | 170 | 34 |
| E07000167 | Ryedale | → | E06000065 | North Yorkshire | 198 | 32 |
| E07000168 | Scarborough | → | E06000065 | North Yorkshire | 391 | 68 |
| E07000169 | Selby | → | E06000065 | North Yorkshire | 294 | 54 |
| E06000014 | York | → | E06000014 | York *(unchanged)* | 659 | 121 |

Also saved as `data/processed/ynyca_lad_crosswalk.csv`.

Ripon is a special case worth flagging separately: it has no LAD or LSOA-name prefix of
its own (its LSOAs are all prefixed "Harrogate," since Ripon sits inside the old
Harrogate district). It only shows up if you split it out by actual distance to Ripon's
own centre — see `YNYCA.ipynb` Section 10. It is **not** a separate row in this lookup;
it's a subset of the Harrogate-prefixed LSOAs.

## The naming gotcha ("and" vs "&")

YNYCA's name is spelled differently across our own sources — both refer to the same
place (E47000012):

| Spelling | Used by |
|---|---|
| "York and North Yorkshire" | ONS's own `CAUTH25NM` field; `msa_rural_urban.csv` / `msa_rural_urban_scores.csv` (pre name-fix) |
| "York & North Yorkshire" | `msa_population_ranks.csv`, `msa_gva_ranks.csv`, `msa_imd_ranks.csv`, `msa_all_indicators.json`, the dashboard (id: `ynyca`) |

Every notebook in this project that joins across these sources applies a `NAME_FIX` /
`RURAL_URBAN_NAME_FIX` dict to normalise to "&" before merging — same pattern, copied
forward each time. Worth remembering if you add a new data source: check which spelling
it uses before joining.

## The lookup files

| File | Grain | Rows | Use it for |
|---|---|---|---|
| `data/processed/ynyca_oa_lookup.csv` | Output Area | 2,765 | Joining anything published at OA level (e.g. the ONS Rural Urban Classification) up to LSOA/LAD/CA |
| `data/processed/ynyca_lsoa_lookup.csv` | LSOA | 500 | The day-to-day reference — one row per LSOA with every code/name above it, plus `n_oas` (how many OAs roll up into it) |
| `data/processed/ynyca_lad_crosswalk.csv` | LAD | 8 | The old→current LAD mapping table above, on its own |
| `data/processed/ynyca_lsoa_indicators.csv` | LSOA | 500 | Not a geography lookup — this is the actual rurality/IMD/deprivation *data* built in `YNYCA.ipynb`, keyed on the same `LSOA21CD` |

Columns on `ynyca_lsoa_lookup.csv` and `ynyca_oa_lookup.csv`:

`OA21CD` (OA file only) · `LSOA21CD` · `LSOA21NM` · `MSOA21CD` · `MSOA21NM` ·
`LAD22CD` / `LAD22NM` (Dec 2021 vintage — what OA-level source data uses) ·
`LAD25CD` / `LAD25NM` (current vintage — what IMD 2025 / mid-2023+ population data
uses) · `CAUTH25CD` (`E47000012`) · `CAUTH25NM` (`"York and North Yorkshire"`, ONS
spelling) · `n_oas` (LSOA file only — OA count per LSOA).

To join any LSOA-level dataset to this lookup: merge on `LSOA21CD`. To join an
OA-level dataset: merge on `OA21CD`. To get from old-vintage LAD-keyed data to the
current LAD: merge on `LAD22CD` and read off `LAD25CD`/`LAD25NM`.
