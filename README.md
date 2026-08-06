# RADataHub

Data and chart specs for ECO RA projects.

This repo is closer to a shared folder than a strict software project. It holds
the data, notebooks and scripts behind charts for the website and for one-off
research. Most work follows the same shape: fetch or clean some data (API, local
file, scrape), then chart it with [Altair](https://altair-viz.github.io/) using
our house theme.

---

## Setup

We use [uv](https://docs.astral.sh/uv/) to manage Python and packages. It
replaces the older conda instructions - it is much faster, and because
`uv.lock` is committed, everyone ends up with identical package versions.

### 1. Install uv

```bash
# macOS
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and sync

```bash
git clone https://github.com/jhellingsdata/RADataHub.git
cd RADataHub
uv sync
```

That is the whole setup. `uv sync` creates a `.venv/` in the repo, installs
Python 3.13 if you don't have it, and installs every core package. You do not
need to create or activate a virtualenv yourself.

### 3. Point your editor at the environment

- **VS Code** - `Cmd/Ctrl + Shift + P` → *Python: Select Interpreter* → choose
  `./.venv/bin/python`. Notebooks will then pick it up automatically.
- **JupyterLab** - `uv run jupyter lab`

To run a script without activating anything:

```bash
uv run python "Article Charts/wc2026/a1/chart.py"
```

---

## Packages

`pyproject.toml` is the source of truth. Everything else is derived from it.

The **core** set is installed by `uv sync` and covers what almost every
notebook here needs: Altair + `vl-convert-python` + `ecostyles` for charting,
pandas/numpy/scipy/openpyxl for data, requests/beautifulsoup4 for fetching,
geopandas/shapely/pyproj for maps, pycountry/country-converter for country
codes, and jupyterlab/ipykernel for notebooks.

Less common packages live in **optional groups**, so nobody has to install a
Java runtime just to open a chart notebook:

| Group | Install | What's in it |
|---|---|---|
| `scraping` | `uv sync --group scraping` | selenium, html2text |
| `data-sources` | `uv sync --group data-sources` | fredapi, wbgapi, wbdata, comtradeapicall, census, us, tabula-py |
| `ai` | `uv sync --group ai` | openai, anthropic, markitdown, annoy |
| `extras` | `uv sync --group extras` | plotly, kaleido, folium, statsmodels, cairosvg, pillow, tqdm |

Install everything with `uv sync --all-groups`.

### Adding a package

```bash
uv add pingouin                      # add to the core set
uv add --group data-sources eurostat # add to an optional group
uv remove pingouin
```

`uv add` updates `pyproject.toml`, re-resolves `uv.lock` and installs into
`.venv` in one step. **Commit both `pyproject.toml` and `uv.lock`** so the rest
of the team gets the same versions.

Only put a package in the core set if notebooks across several folders will use
it. Anything niche belongs in a group (or `extras` if it doesn't fit one).

### If someone else changed the packages

```bash
git pull
uv sync
```

`uv sync` removes packages that are no longer declared, so your environment
matches the lockfile exactly.

---

## Fallbacks

Only needed if you can't use uv.

- **pip** - `pip install -r requirements.txt`. This file is *generated* from
  `pyproject.toml`; don't edit it by hand. Regenerate with:
  ```bash
  uv export --no-hashes --no-emit-project --format requirements.txt \
    --output-file requirements.txt
  ```
- **conda** - `conda env create -f environment.yml && conda activate radatahub`.
  Hand-maintained to mirror the core set; update it if you change
  `pyproject.toml`.

---

## Repo conventions

- **`Article Charts/<article>/`** - one folder per article, holding its data,
  notebook and exported chart specs.
- **`ChartOfTheDay/<topic>/`** - daily charts.
- **`Chart Packs/<topic>/`** - chart packs.
- **`Newsletters/<date>-<topic>/`** - newsletter charts.

Keep each piece of work self-contained in its own folder, including the data it
needs, so charts can be rebuilt later without hunting for inputs.

---

## Things worth knowing

**Use the `ecostyles` package, not a copied `eco_style.py`.** There are ~78
copies of an old `eco_style.py` scattered through the repo, in five different
versions. New work should use the installed package:

```python
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme()
```

Leave the existing copies alone - they keep old notebooks working - but don't
add new ones.

**Saving charts: use `chart.save()`.** Some older notebooks import
`altair_saver` or `altair_viewer`. Both are unmaintained, expect Altair 4, and
will not work with the Altair 6 we now use. They are deliberately not in
`pyproject.toml`. The modern equivalent needs no extra package, because
`vl-convert-python` is in the core set:

```python
chart.save("fig1.png", scale_factor=2)   # also .svg, .pdf, .json, .html
```

**Keep API keys out of notebooks.** Several notebooks currently have keys
assigned inline, which means they end up in git history. `python-dotenv` is in
the core set - put keys in a `.env` file (already gitignored) and read them:

```python
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
api_key = os.environ["FRED_API_KEY"]
```

**Old notebooks may need tweaks.** We track recent pandas and Altair, so
notebooks written years ago won't always run unchanged. That's expected - fix
them as you go rather than pinning the whole repo backwards.
