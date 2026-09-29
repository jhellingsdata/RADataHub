# LAD Productivity Map

England labour productivity (GVA per hour worked, UK=100, 2023) by local authority district, with the
Strategic Authorities ("MSAs") outlined and labelled. Moved out of `Article Inequalities` on 28 Sep 2026.

- `figures/`: final maps, `fullcolor` (every LAD coloured) and `dimoutside` (LADs outside the selected
  authorities faded), for three authority sets: 17 (default, no suffix), `_21msa`, `_22msa`;
  each as .png, .svg, .html, .vl.json, plus a 17.5 x 15.5 cm 300 dpi PNG
- `code/`: `build_productivity_geometry.py` (joins ONS data to LAD boundaries), `productivity_map_final.py`
  (draws the maps), `eco_style.py` (style)
- `inputs/`: ONS LAD productivity table (June 2025), LAD May 2024 boundaries, the joined
  `lad_productivity.geojson`, and the MSA outlines `sa_areas.geojson`
- `archive/`: exploration drafts and scripts from the design rounds (not maintained; paths inside
  them point to the old project layout)

## Rebuild

Run from anywhere (paths are relative to this folder):

```
python3 code/build_productivity_geometry.py          # only if the inputs change
python3 code/productivity_map_final.py --msa-set 17
python3 code/productivity_map_final.py --msa-set 21
python3 code/productivity_map_final.py --msa-set 22
```

Verified 28 Sep 2026: rebuilt from this folder, all 12 PNGs are pixel-identical to the previous outputs.
Needs the Circular Std font installed for an exact match.
