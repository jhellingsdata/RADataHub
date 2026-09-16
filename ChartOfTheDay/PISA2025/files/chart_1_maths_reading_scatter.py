"""
Chart of the Day — PISA 2025: UK maths and reading against the OECD average.

Economics Observatory house style. Retrieval only: every value plotted is a mean
score published by OECD. Nothing here is computed.

SOURCE
    OECD (2026), PISA 2025 Results (Volume I): Future-Ready Students,
    OECD Publishing, Paris. https://doi.org/10.1787/73451bc5-en
    Annex B1, Table I.B1.2 — Student performance in PISA 2025.
    StatLink: https://stat.link/mrq53f  (mrq53f.xlsx, version 1, 08-Sep-2026)

    The workbook holds 50 sub-tables. Mean scores live in three of them:
        Table I.B1.2a.1  science
        Table I.B1.2a.2  reading
        Table I.B1.2a.3  mathematics
    Each carries its title in rows 1-2 and a three-deep column header ending on
    row 9, then 'OECD average', 'OECD total', and economies alphabetically.
    Column A is the economy, B the mean, C its standard error. A trailing '*'
    on an economy name is OECD's flag for sampling standards not met.

WHAT THIS CHART DELIBERATELY DOES NOT DO
    No k-means clusters. Cluster membership and cluster counts are computed
    statistics, not published ones, so they are out of bounds.
    No size channel for science. Encoding a third domain as dot area on top of
    a two-domain scatter is over-encoding and unreadable at social-image size.
    No ranks. OECD publishes ranks; deriving them from a score table is
    arithmetic.

OUTPUTS (written beside this script)
    pisa_2025_maths_reading.png   (scale_factor=3)
    pisa_2025_maths_reading.svg
    pisa_2025_maths_reading.json  (Vega-Lite, data inlined)
    pisa_2025_maths_reading_data.csv
"""

import copy
import json
import math
import os
import re

import altair as alt
import pandas as pd
import vl_convert as vlc

import eco_style  # registers the 'report' theme and exposes `pallete`

alt.theme.enable("report")
alt.data_transformers.disable_max_rows()

# Single editable route. The dataset is read from here and every output
# is written to the charts/ folder beside it, created on first run.
SOURCE_FILE = "/Users/alonso/Documents/GitHub/RADataHub/ChartOfTheDay/PISA2025/mrq53f.xlsx"
OUT_DIR = os.path.join(os.path.dirname(SOURCE_FILE), "charts")
os.makedirs(OUT_DIR, exist_ok=True)
STEM = os.path.join(OUT_DIR, "pisa_2025_maths_reading")

SHEETS = {
    "science": "Table I.B1.2a.1",
    "reading": "Table I.B1.2a.2",
    "maths": "Table I.B1.2a.3",
}
SKIPROWS = 9        # first data row after the header is 'OECD average'
COL_ECONOMY = 0
COL_MEAN = 1
COL_SE = 2

HIGHLIGHT = "United Kingdom"
HIGHLIGHT_CODE = "UK"   # flagged by code, like the peers

# Peers labelled with ISO 3166 three-letter codes rather than full names, which
# do not fit in the crowded 450-530 band. Keys must match the OECD economy
# strings exactly; asserted below so a rename fails loudly. B-S-J-Z has no ISO
# code, so OECD's own abbreviation is used.
PEERS = {
    "Singapore": "SGP",
    "B-S-J-Z (China)": "B-S-J-Z",
    "Japan": "JPN",
    "Korea": "KOR",
    "Estonia": "EST",
    "Canada": "CAN",
    "United States": "USA",
    "Germany": "DEU",
    "France": "FRA",
    "Italy": "ITA",
    "Denmark": "DNK",
}

# Adding these back overlaps: IRL/NZL, FIN/ITA and SWE/DEU sit within a couple
# of score points of each other, as do FRA/ESP. Enable only with fresh offsets.
#   "Ireland": "IRL", "New Zealand": "NZL", "Australia": "AUS",
#   "Netherlands": "NLD", "Poland": "POL", "Switzerland": "CHE",
#   "Finland": "FIN", "Sweden": "SWE", "Norway": "NOR", "Spain": "ESP",

# Label offsets in SCORE UNITS (not pixels), so a leader line can be drawn in
# data space from each dot to its label. Solved against all 90 dot positions:
# no label box contains a dot and no two label boxes overlap. Re-solve if the
# peer set changes — these are specific to the PISA 2025 cloud.
#   code: (offset_maths, offset_reading, align, baseline)
LABEL_OFFSET = {
    "UK": (0, 12, "center", "bottom"),
    "B-S-J-Z": (-12, 0, "right", "middle"),
    "SGP": (-12, 0, "right", "middle"),
    "JPN": (0, 12, "center", "bottom"),
    "KOR": (-8.6, 8.6, "right", "bottom"),
    "EST": (0, -12, "center", "top"),
    "CAN": (18.0, -18.0, "left", "top"),
    "DNK": (12, 0, "left", "middle"),
    "ITA": (12, 0, "left", "middle"),
    "DEU": (-12, 0, "right", "middle"),
    "USA": (-12, 0, "right", "middle"),
    "FRA": (-18.0, 18.0, "right", "bottom"),
}
# Leader stops short of the label so the line never touches a glyph.
LEADER_FRAC = 0.78

# Published OECD averages and UK means, read off the table and cross-checked
# against OECD's Education GPS country profiles. Used as parse tripwires.
EXPECT = {"maths": 463, "reading": 461, "science": 482}
EXPECT_UK = {"maths": 488, "reading": 494, "science": 511}


# ----------------------------------------------------------------------------
# Colour helpers. eco_style stores some palette entries as rgba(); vl-convert
# silently drops alpha on mark colour properties, so bake it into solid hex.
# ----------------------------------------------------------------------------
def tint(colour, alpha=None, over=(255, 255, 255)):
    """Composite an eco_style palette colour onto `over` at `alpha`."""
    m = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)",
        str(colour),
    )
    if m:
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
    else:
        h = str(colour).lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = 1.0
    if alpha is not None:
        a = alpha
    mix = [round(a * c + (1 - a) * o) for c, o in zip((r, g, b), over)]
    return "#{:02x}{:02x}{:02x}".format(*mix)


INK = eco_style.pallete["domain"]

# Dots, labels and leaders take eco_style palette keys directly. tint() is used
# only for the reference rules and the note typography, because those palette
# entries are rgba() and vl-convert drops the alpha on a mark colour, which
# would render them as solid navy.
DOT_OTHER = eco_style.pallete["Other_3"]        # #d6d4d4
DOT_PEER = eco_style.pallete["nominal_4"]       # #122b39
DOT_UK = eco_style.pallete["United Kingdom"]    # #179fdb, == nominal_1
LEADER = eco_style.pallete["bar"]["other"]      # #a8c0de
PEER_LABEL = eco_style.pallete["nominal_4"]

RULE = tint(INK, 0.45)
MUTED = tint(INK, 0.75)
SUBTITLE = tint(INK, 0.70)
NOTE = tint(INK, 0.65)


# ----------------------------------------------------------------------------
# Load. Reads the OECD workbook directly, no intermediate CSV.
# ----------------------------------------------------------------------------
def pull(sheet, label):
    raw = pd.read_excel(SOURCE_FILE, sheet_name=sheet, header=None,
                        skiprows=SKIPROWS, dtype=object)
    df = pd.DataFrame({
        "economy": raw.iloc[:, COL_ECONOMY].astype(str).str.strip(),
        label: pd.to_numeric(raw.iloc[:, COL_MEAN], errors="coerce"),
        f"{label}_se": pd.to_numeric(raw.iloc[:, COL_SE], errors="coerce"),
    })
    df = df[df["economy"].ne("nan") & df[label].notna()].copy()
    df[f"flag_{label}"] = df["economy"].str.endswith("*")
    df["economy"] = df["economy"].str.replace(r"\s*\*+\s*$", "", regex=True)

    # Verify the published average before discarding it, so a column shift or a
    # sheet reshuffle crashes rather than plotting the wrong series.
    avg = df.loc[df["economy"].eq("OECD average"), label]
    assert not avg.empty, f"'OECD average' row missing from {sheet}."
    got = round(float(avg.iloc[0]))
    assert got == EXPECT[label], (
        f"{sheet}: OECD {label} average parsed as {got}, expected "
        f"{EXPECT[label]}. Wrong sheet or wrong column."
    )
    return df[~df["economy"].str.startswith("OECD")].reset_index(drop=True)


if not os.path.exists(SOURCE_FILE):
    raise FileNotFoundError(
        f"{SOURCE_FILE} not found. Download Table I.B1.2 from "
        "https://stat.link/mrq53f and save it to that path."
    )

print("Reading OECD Table I.B1.2 …")
parts = {label: pull(sheet, label) for label, sheet in SHEETS.items()}

df = parts["maths"]
for label in ("reading", "science"):
    df = df.merge(parts[label], on="economy", how="outer")

flag_cols = [c for c in df.columns if c.startswith("flag_")]
df["flagged"] = df[flag_cols].fillna(False).any(axis=1)
df = df.drop(columns=flag_cols)

# One economy (Uzbekistan) reports science only. A maths-vs-reading scatter
# needs both, so the plotted set is those with both, and the subtitle says so.
df = df.dropna(subset=["maths", "reading"]).reset_index(drop=True)
df["is_uk"] = df["economy"].eq(HIGHLIGHT)

assert df["is_uk"].sum() == 1, f"Expected exactly one '{HIGHLIGHT}' row."
uk = df.loc[df["is_uk"]].iloc[0]
for label, want in EXPECT_UK.items():
    got = round(float(uk[label]))
    assert got == want, f"UK {label} parsed as {got}, expected {want}."
for name in PEERS:
    assert name in set(df["economy"]), f"Peer '{name}' not in the OECD table."
df["code"] = df["economy"].map(PEERS)
df["is_peer"] = df["code"].notna() & ~df["is_uk"]
df["label"] = df["code"]
df.loc[df["is_uk"], "label"] = HIGHLIGHT_CODE

assert set(df["label"].dropna()) == set(LABEL_OFFSET), (
    "Every labelled economy needs an offset: "
    f"{set(df['label'].dropna()) ^ set(LABEL_OFFSET)}"
)

# Label anchors and leader endpoints, in score units.
lab = df[df["label"].notna()].copy()
lab[["off_x", "off_y", "align", "baseline"]] = pd.DataFrame(
    lab["label"].map(LABEL_OFFSET).tolist(), index=lab.index)
lab["lab_x"] = lab["maths"] + lab["off_x"]
lab["lab_y"] = lab["reading"] + lab["off_y"]
lab["lead_x"] = lab["maths"] + lab["off_x"] * LEADER_FRAC
lab["lead_y"] = lab["reading"] + lab["off_y"] * LEADER_FRAC

N_ECONOMIES = len(df)        # read off the table, never asserted from memory
N_FLAGGED = int(df["flagged"].sum())
print(f"  {N_ECONOMIES} economies with both maths and reading means "
      f"({N_FLAGGED} carry OECD's sampling-standards flag)")
print(f"  UK: maths {round(uk['maths'])}, reading {round(uk['reading'])}, "
      f"science {round(uk['science'])}")


# ----------------------------------------------------------------------------
# Encodings
# ----------------------------------------------------------------------------
# Rule data reuses the score column names so the identical alt.X / alt.Y
# objects can be passed to every layer. Any layer that swaps in a different
# encoding (or axis=None) suppresses the shared axis for the whole layered view.
rules = pd.DataFrame({"maths": [EXPECT["maths"]], "reading": [EXPECT["reading"]]})


def refit(enc, field):
    """Copy an X/Y encoding, changing only the field it points at.

    A helper layer that builds its own alt.X/alt.Y (or passes axis=None) drops
    the shared axis for the whole layered view, so the scale and axis objects
    have to be carried over intact.
    """
    out = copy.deepcopy(enc)
    out.shorthand = field
    return out


def bound(series, pad=12, step=25):
    lo = math.floor((series.min() - pad) / step) * step
    hi = math.ceil((series.max() + pad) / step) * step
    return [lo, hi]


enc_x = alt.X(
    "maths:Q",
    scale=alt.Scale(domain=bound(df["maths"]), nice=False),
    axis=alt.Axis(title="Mathematics score", titleFontSize=12, titleColor=INK,
                  titlePadding=10, format="d", tickCount=5),
)
enc_y = alt.Y(
    "reading:Q",
    scale=alt.Scale(domain=bound(df["reading"]), nice=False),
    axis=alt.Axis(title="Reading score", titleFontSize=12, titleColor=INK,
                  titleAlign="left", titleAngle=0, titleBaseline="bottom",
                  titleX=0, titleY=-10, format="d", tickCount=5),
)

W, H = 620, 440

others = (
    alt.Chart(df[~df["is_uk"] & ~df["is_peer"]])
    .mark_circle(size=62, color=DOT_OTHER)
    .encode(x=enc_x, y=enc_y,
            tooltip=["economy:N", "maths:Q", "reading:Q", "science:Q"])
    .properties(width=W, height=H)
)

v_rule = alt.Chart(rules).mark_rule(
    color=RULE, strokeDash=[3, 4], strokeWidth=1).encode(x=enc_x)
h_rule = alt.Chart(rules).mark_rule(
    color=RULE, strokeDash=[3, 4], strokeWidth=1).encode(y=enc_y)

# alt.value() for the off-axis coordinate keeps these labels out of the scale
# domain entirely, which alt.datum() would distort.
v_rule_label = (
    alt.Chart(rules)
    .mark_text(align="left", baseline="top", dx=6, fontSize=11, color=MUTED,
               text=f"OECD average, maths: {EXPECT['maths']}")
    .encode(x=enc_x, y=alt.value(6))
)
h_rule_label = (
    alt.Chart(rules)
    .mark_text(align="left", baseline="bottom", dx=2, dy=-6, fontSize=11,
               color=MUTED, text=f"OECD average, reading: {EXPECT['reading']}")
    .encode(y=enc_y, x=alt.value(4))
)

peers = (
    alt.Chart(df[df["is_peer"]])
    .mark_circle(size=62, color=DOT_PEER)
    .encode(x=enc_x, y=enc_y,
            tooltip=["economy:N", "maths:Q", "reading:Q", "science:Q"])
)

enc_x_lab = refit(enc_x, "lab_x:Q")
enc_y_lab = refit(enc_y, "lab_y:Q")

# Leader lines. mark_rule with x/y and x2/y2 draws dot-to-label in data space;
# X2/Y2 carry no axis of their own so they inherit the shared scale safely.
def leader(sub, colour):
    return (
        alt.Chart(sub)
        .mark_rule(color=colour, strokeWidth=0.9)
        .encode(x=enc_x, y=enc_y,
                x2=alt.X2("lead_x:Q"), y2=alt.Y2("lead_y:Q"))
    )


leaders_peer = leader(lab[~lab["is_uk"]], LEADER)
leaders_uk = leader(lab[lab["is_uk"]], DOT_UK)

# One text layer per (align, baseline) pair, since those are mark-level.
peer_labels = [
    alt.Chart(sub)
    .mark_text(align=al, baseline=bl, fontSize=11, color=PEER_LABEL)
    .encode(x=enc_x_lab, y=enc_y_lab, text="label:N")
    for (al, bl), sub in lab[~lab["is_uk"]].groupby(["align", "baseline"])
]

uk_dot = (
    alt.Chart(df[df["is_uk"]])
    .mark_circle(size=115, color=DOT_UK)
    .encode(x=enc_x, y=enc_y)
)
uk_label = (
    alt.Chart(lab[lab["is_uk"]])
    .mark_text(align="center", baseline="bottom", fontSize=14, fontWeight=700,
               color=DOT_UK)
    .encode(x=enc_x_lab, y=enc_y_lab, text="label:N")
)

chart = (
    alt.layer(v_rule, h_rule, leaders_peer, leaders_uk, others, peers,
              *peer_labels, uk_dot, uk_label, v_rule_label, h_rule_label)
    .properties(
        width=W,
        height=H,
        title=alt.TitleParams(
            "Where UK 15-year-olds stand in maths and reading",
            subtitle=[
                f"Mean PISA score, 2025. Each dot is one of {N_ECONOMIES} "
                "countries and economies with results in both domains.",
            ],
            fontSize=18,
            subtitleFontSize=12,
            subtitleColor=SUBTITLE,
            anchor="start",
            offset=14,
            subtitlePadding=7,
        ),
    )
)
# No .resolve_axis() here. Every layer reuses the identical enc_x / enc_y
# objects and none passes axis=None, so the shared axis survives; asking for an
# independent y instead mirrors the whole axis onto the right edge.

FLAGGED_PEERS = sorted(df.loc[df["is_peer"] & df["flagged"], "code"])

note = alt.TitleParams(
    [
        "Source: OECD (2026), PISA 2025 Results (Volume I), Table I.B1.2 "
        "(stat.link/mrq53f), published 8 September 2026.",
        "Labels are ISO three-letter codes; B-S-J-Z is Beijing, Shanghai, "
        "Jiangsu and Zhejiang (China). "
        + (f"{' and '.join(FLAGGED_PEERS)} are among {N_FLAGGED} economies "
           "OECD flags for not meeting sampling standards."
           if FLAGGED_PEERS else
           f"{N_FLAGGED} economies are flagged by OECD for not meeting "
           "sampling standards."),
        "Maths and reading are separate score scales, not percentages. Figures "
        "cover the whole United Kingdom; the four UK nations report separately.",
    ],
    fontSize=10,
    fontWeight=400,
    color=NOTE,
    anchor="start",
    orient="bottom",
    offset=18,
    lineHeight=13,
)

# A second TitleParams on the outer vconcat anchors the note to the same
# canvas-left edge as the title, whatever the y-label width turns out to be.
final = (
    alt.vconcat(chart, title=note)
    .configure_view(strokeWidth=0, stroke=None)
    .configure_axis(labelFontSize=11)
)

# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
spec = final.to_dict()

with open(f"{STEM}.png", "wb") as f:
    f.write(vlc.vegalite_to_png(spec, scale=3))
with open(f"{STEM}.svg", "w", encoding="utf-8") as f:
    f.write(vlc.vegalite_to_svg(spec))
with open(f"{STEM}.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
df.drop(columns=["is_uk", "is_peer", "label"]).to_csv(f"{STEM}_data.csv", index=False)

print(f"\nWrote 4 files to {OUT_DIR}")
