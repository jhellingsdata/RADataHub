# MSA tier map: how to rebuild

Run in order from a directory containing `eco_style.py`:

    python build_tables.py     # authority table + LAD crosswalk, with validation
    python build_geometry.py   # dissolve LADs -> authority footprints, anchors
    python msa_map.py          # render PNG / SVG / HTML

`build_tables.py` asserts on four failure modes before writing anything:
unmatched district names, a district assigned to two authorities, an authority
with no districts, and a crosswalk entry with no tier row.

## Outputs
| File | Use |
|---|---|
| `msa_tiers_map.png` | static figure, 2.5x for print |
| `msa_tiers_map.svg` | vector, for editing in Illustrator or Figma |
| `msa_tiers_map.vl.json` | Vega-Lite spec, self-contained |
| `msa_tiers_map.html` | standalone page, tooltips live |
| `data/*.geojson` | authority footprints on their own, EPSG:27700 |

The `.vl.json` spec carries the geometry and every attribute inline, so it
needs no data fetch. For the dashboard:

    vegaEmbed('#map', 'msa_tiers_map.vl.json');

It is written compact because indenting puts every coordinate on its own line
and multiplies the file size. Run `jq . msa_tiers_map.vl.json` to read it.
`msa_map.py` round-trips the file through vl-convert after writing it, so a
malformed spec fails in the build rather than silently in a browser.

## Inputs
- `geo/eng_lad.json` - ONS 2013 local authority districts (326 English districts),
  fetched from github.com/martinjc/UK-GeoJSON. The ONS Open Geography Portal is
  not reachable from this environment; swap in the current
  "Combined Authorities (December 2025) Boundaries EN" product where available.
- `eco_style.py` - project chart theme.

## Why 2013 districts
Every Strategic Authority outer boundary is a union of 2013 districts, so the
2013 layer dissolves correctly even where constituent councils have since been
reorganised. Cumberland and Westmorland and Furness (created 2023) are unions
of the six 2013 Cumbria districts; North Yorkshire is a union of seven.
This also sidesteps the 7 September 2026 reorganisation pause, which unsettles
constituent-council boundaries but leaves authority outer boundaries unchanged.

## Geometry precision
Coordinates are snapped to whole metres with `set_precision(1.0)`. One metre is
a thousandth of a pixel at this projection scale, so nothing visible changes,
and it takes the inlined spec from roughly 1 MB to 187 KB.

## Font
`msa_map.py` sets `FONT = "Carlito"` because Circular Std is not installed here.
Change that one constant where the licensed font is available; nothing else
in the spec depends on it.

## Adding or promoting an authority
Edit the `authorities` list and `crosswalk` dict in `build_tables.py`, add a
label position to `LABELS` in `msa_map.py`, and rerun. `msa_map.py` asserts
that every authority has a label position, so a new row cannot render unlabelled.
