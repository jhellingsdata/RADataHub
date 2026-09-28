# Health-inequalities article: figures

Code: `productivity_map_itl3_uk.py` (map) and `health_article_charts.py` (charts), run from the project root.
Each figure has a .png and a .vl.json; chart data is in `data/`.

## Suggested captions

1. **itl3_productivity_map_uk**: Labour productivity (GVA per hour worked, UK=100) by ITL3 subregion, 2023.
   Source: ONS, Subregional productivity (SRPROD01), June 2025, Table A1.
   Supports: *"Economic outcomes are similarly unevenly distributed…"*. The text cites 2021 data from the June 2023
   edition; update the text to 2023 figures or download that edition (see next steps).
2. **hle_by_deprivation_decile**: Healthy life expectancy at birth by deprivation decile (IMD 2019), England, 2022–2024.
   Source: ONS, Healthy life expectancy by national area deprivation, England, 15 April 2026.
   Supports: intro and *"Geographical inequalities in health are substantial…"*.
3. **health_inactivity_by_region**: Economic inactivity due to ill health (% of working-age population), English regions.
   Source: Simpson et al. (2025a), Health for Wealth 2025, Figure 25.
   Supports: *"health-related economic inactivity is around 50% higher in the North…"*.
4. **ill_health_onset_north_vs_rest**: Change in the probability of staying in work and in monthly pay after an onset
   of ill health. n.s. = not statistically significant. Source: Simpson et al. (2025a), Health for Wealth 2025,
   Figures 22 and 24 (Understanding Society). Supports: *"people living in northern regions are more likely to leave
   employment following the onset of poor health…"*.

## Next steps (data still to find)

- **Regional employment and inactivity (ONS HI00, 18 Aug 2026, Apr–Jun 2026).** `sources/04_…xlsx` is the 18 June
  release (Feb–Apr 2026) and does not match the text (78.3%, 18.4%). Download the August release.
- **Productivity for 2021 as cited (ONS SRPROD01, June 2023 edition).** `sources/03b_…xls` is the July 2022 release
  (data to 2020), despite its file name. Needed only if the text keeps its 2021 figures.
- **Disability-employment gap by area (Bryan et al. 2026).** Values are in `sources/07_…pdf` Table A2 (difference from
  GB average, NUTS3 2016 codes). Needs table extraction, plus NUTS3 2016 boundaries for a map, or a ranked dot plot.
- **Sources not in the folder:** Dodd et al. 2025 (Talking Therapies), IPPR 2026 (youth jobs index + ONS job adverts by
  LA), Britteon et al. 2022, GMCA 2025 / TPI growth figures, Simpson et al. 2025b (supplementary data), Mignon et al.
  2026 (data behind Figure 5).
- **Text checks:** male HLE gap (ONS range 19.5, SII 19.3, text says 19.4); "almost three times" holds for Tower Hamlets vs
  Powys only (LAD max/min 2023 is 3.5×); Bryan et al. 2022 finds no significant north/south difference.

## Added 26 Sep 2026

Code: `health_map_uk.py` (HLE maps) and `health_article_charts_regional.py` (six regional charts).

| Figure | Supports |
|---|---|
| `itl3_productivity_map_uk_ylgnbu_annotated` | Productivity paragraph; marks North of England, Powys, Tower Hamlets (names only) |
| `hle_map_uk_female`, `hle_map_uk_male` | Health inequalities across the UK; pairs with the productivity map |
| `employment_inactivity_by_region` | "71.1% in the North East to 78.3%… inactivity 18.4%… 25.1%" (HI00, 18 Aug 2026) |
| `hle_by_region` | "people in the North of England having greater rates of… morbidity" |
| `gm_hle_over_time` | Devolution paragraph: GM HLE stays ~3 years below England (gap 2.5–3.9 years) |
| `gm_gdp_growth` | "economy growing by 28%…": GM +24.0% 2015–2024, 3rd of 38 ITL2 areas with data |
| `gm_productivity_growth` | "highest average annual productivity growth": GM 1.7%/yr 2015–2023, 3rd of 38, not 1st |
| `gdhi_by_region` | "household income… contributors to health inequalities" (Simpson et al. 2025b) |

Notes: ONS suppressed 8 ITL2 areas (south-west England, Wales, Highlands and Islands, West Central Scotland)
in its Sept 2026 regional GDP release; they are excluded from both growth charts. Growth rates are own
calculations from ONS chained volume indices.

Sources: `04_…` (HI00 v127) and `03b_…` (SRPROD01 v11) are the verified editions the text cites. The old,
mislabelled `04x_…` and `03x_…` files were deleted on 28 Sep 2026.

## Cleanup, 28 Sep 2026

- The three chosen figures, their data (.xlsx) and self-contained code are in `outputs/final_article_figures/`.
- The England LAD productivity map (formerly `outputs/final/`, `productivity_map_final.py`,
  `build_productivity_geometry.py`, `_archivo/`) moved to its own folder: `GROWTH LAB/LAD Productivity Map/`.
- The unannotated ITL3 map drafts were deleted; `productivity_map_itl3_uk.py` now writes only the annotated map.
