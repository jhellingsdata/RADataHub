# Final article figures

Three figures for "How do health inequalities shape regional economic performance in the UK?".

The folder is self-contained: download it anywhere and it rebuilds every figure and dataset.

- `figures/`: each figure as `.png` and `.vl.json`, with title and source (`<name>`) and without (`<name>_no_title`)
- `data/`: the data behind each figure, `.xlsx` (sheet `data` + sheet `notes` with source and filters)
- `inputs/`: the original source files the code reads (ONS workbooks, boundary files, Health for Wealth 2025 report)
- `code/final_figures.py`: builds everything; `eco_style.py` and `figure_frame.py` are the style helpers it imports
- `requirements.txt`: pinned package versions (tested with Python 3.11.5)
- `fonts/`: empty; see "Font" below

## How to reproduce

From this folder:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python code/final_figures.py
```

This overwrites `figures/` and `data/`. Tested in a clean environment: the output is pixel-identical to the files shipped here.

## Font

The figures use **Circular Std**, a licensed font that is not included. On a machine without it, the figures
still build but text renders in a fallback font. To match exactly, install Circular Std or copy its `.ttf`/`.otf`
files into `fonts/`; the script loads that folder automatically.

## Inputs

| File | Used for |
|---|---|
| `01_ONS_HLE_by_deprivation_decile_England_timeseries.xlsx` | Figure 1 (sheet 4) |
| `03_ONS_SRPROD01_subregional_productivity_current2025.xlsx` | Figure 2 (sheet A1, Index_2023) |
| `International_Territorial_Level_3_(January_2025)_Boundaries_UK_BGC_V2.geojson` | Figure 2 boundaries |
| `lad_may2024.geojson` | Figure 2, Powys outline only |
| `02_HealthEquityNorth_HealthForWealth2025.pdf` | Figure 3: values transcribed from Figure 25 into the code (reference copy) |

## Figure text for the article

**Figure 1** (`figure1_hle_by_deprivation_decile`): after "Geographical inequalities in health are substantial…"
People in England's most deprived areas spend around 20 fewer years in good health.
Healthy life expectancy at birth by area deprivation decile (IMD 2019), England, 2022–2024.
Source: ONS, Healthy life expectancy by national area deprivation, England (April 2026).

**Figure 2** (`figure2_productivity_map_itl3_uk`): after "Economic outcomes are similarly unevenly distributed…"
Labour productivity varies widely across the UK.
GVA per hour worked by ITL3 subregion, current prices, 2023 (UK=100).
Source: ONS, Subregional productivity: labour productivity indices by UK ITL2 and ITL3 subregions (June 2025),
Table A1. Boundaries: ONS ITL3 January 2025. Powys outline: ONS local authority districts, May 2024.
Note: the map shows 2023; the text cites 2021 figures (ONS, 2023 edition).

**Figure 3** (`figure3_health_inactivity_by_region`): after "…health-related economic inactivity is around 50% higher in the North…"
Health-related economic inactivity is highest in the North of England.
Share of the working-age population economically inactive due to ill health, English regions, 2024.
Source: Simpson et al. (2025), Health for Wealth 2025, Figure 25; based on ONS Annual Population Survey.
