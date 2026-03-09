import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

# ── Unemployment rate (quarterly) ─────────────────────────────────────────────
unemp_raw = pd.read_csv(
    "../data/series-090326 copy 2.csv", skiprows=7, header=None
)
unemp_raw.columns = ["Period", "Rate"]
unemp_raw = unemp_raw.dropna(subset=["Period"])
unemp_raw["Period"] = unemp_raw["Period"].str.strip()
unemp_raw["Rate"] = pd.to_numeric(unemp_raw["Rate"], errors="coerce")

# Keep only quarterly rows: "YYYY QN"
unemp_q = unemp_raw[unemp_raw["Period"].str.match(r"^\d{4} Q[1-4]$")].copy()

q_to_month = {"Q1": 2, "Q2": 5, "Q3": 8, "Q4": 11}

def parse_ons_quarter(label):
    year, q = label.strip().split()
    return pd.Timestamp(year=int(year), month=q_to_month[q], day=1)

unemp_q["date"] = unemp_q["Period"].apply(parse_ons_quarter)
unemp_q = unemp_q.dropna(subset=["Rate"])
unemp_q = unemp_q[unemp_q["date"].dt.year >= 2001]

# ── Resignations (quarterly) ──────────────────────────────────────────────────
quits_raw = pd.read_csv("../data/Quits.csv")
quits_raw.columns = ["Period", "Resignations"]
quits_raw = quits_raw.dropna(subset=["Period"])
quits_raw["Period"] = (
    quits_raw["Period"]
    .str.strip()
    .str.replace(r"(\d{4})\d+", r"\1", regex=True)  # fix "20196" typo
)
quits_raw["Resignations"] = pd.to_numeric(
    quits_raw["Resignations"].replace("..", float("nan")), errors="coerce"
)

label_to_month = {"Jan-Mar": 2, "Apr-Jun": 5, "Jul-Sep": 8, "Oct-Dec": 11}

def parse_quits_quarter(label):
    label = label.strip()
    for prefix, month in label_to_month.items():
        if label.startswith(prefix):
            year = int(label[-4:])
            return pd.Timestamp(year=year, month=month, day=1)
    return pd.NaT

quits_raw["date"] = quits_raw["Period"].apply(parse_quits_quarter)
quits_raw = quits_raw.dropna(subset=["date", "Resignations"])
quits_raw = quits_raw[quits_raw["date"].dt.year >= 2001]

# ── Chart ──────────────────────────────────────────────────────────────────────
BLUE = "#17648D"
RED  = "#C0504D"

base_q = alt.Chart(quits_raw)
base_u = alt.Chart(unemp_q)

resignations_line = (
    base_q
    .mark_line(strokeWidth=2.5, color=BLUE)
    .encode(
        x=alt.X(
            "date:T",
            title="",
            axis=alt.Axis(format="%Y", tickCount="year"),
        ),
        y=alt.Y(
            "Resignations:Q",
            title="Resignations (thousands)",
            scale=alt.Scale(domain=[50, 500]),
            axis=alt.Axis(titleColor=BLUE, format="d"),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Quarter", format="%b %Y"),
            alt.Tooltip("Resignations:Q", title="Resignations (000s)", format=",d"),
        ],
    )
)

unemployment_line = (
    base_u
    .mark_line(strokeWidth=2.5, color=RED)
    .encode(
        x=alt.X("date:T"),
        y=alt.Y(
            "Rate:Q",
            title="Unemployment rate (%)",
            scale=alt.Scale(domain=[3, 9]),
            axis=alt.Axis(
                titleColor=RED,
                orient="right",
                format=".1f",
            ),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Quarter", format="%b %Y"),
            alt.Tooltip("Rate:Q", title="Unemployment rate (%)", format=".1f"),
        ],
    )
)

chart = (
    alt.layer(resignations_line, unemployment_line)
    .resolve_scale(y="independent")
    .properties(
        width=600,
        height=380,
        title=alt.TitleParams(
            text="Resignations and unemployment rate, 2001–2025",
            subtitle=(
                "Quarterly resignations (thousands, left) vs unemployment rate % (right), UK"
                " | Sources: ONS LFS Flows; ONS LMS"
            ),
            fontSize=15,
            subtitleFontSize=11,
            anchor="start",
        ),
    )
)

chart.save("quits_unemployment.png", scale_factor=2)
