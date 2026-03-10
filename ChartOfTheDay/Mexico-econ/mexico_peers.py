"""
Recreating OECD Figure 1.3: Sluggish GDP per capita growth over the past two decades constrains living standards
Index of real PPP-adjusted GDP per capita, 2000 = 100

Variable: wdi_ny_gdp_pcap_pp_kd — GDP per capita, PPP (constant 2017 international $)
Source: World Bank World Development Indicators (WDI)
"""

import pandas as pd
import altair as alt
import sys
sys.path.append(".")  # Adjust if eco_style.py is elsewhere
import eco_style

# ─── Register and enable the OECD-style theme ───
#alt.themes.enable('report')

# ─── DATA PATH ───
DATA_PATH = '/Users/alonso/Desktop/LSE/Growth/Course_Database_Newest.csv'

# ─── VARIABLE ───
VARIABLE = 'wdi_ny_gdp_pcap_pp_kd'  # GDP per capita, PPP (constant 2017 international $)
BASE_YEAR = 2000

# ──────────────────────────────────────────────────
# COUNTRY LIST — Edit these lists to change comparisons
# ──────────────────────────────────────────────────

# Individual countries to plot as separate lines
individual_countries = ['MEX', 'CHL', 'CRI']

# Group 1: LAC — simple average (Chile, Colombia, Costa Rica, Argentina, Brazil, Peru)
lac_countries = ['CHL', 'COL', 'CRI', 'ARG', 'BRA', 'PER']

# Group 2: Dynamic Asia — simple average (India, Indonesia, Malaysia, Philippines, Thailand, Viet Nam)
dynamic_asia_countries = ['IND', 'IDN', 'MYS', 'PHL', 'THA', 'VNM']

# Labels for individual countries (maps ISO code → display name)
country_labels = {
    'MEX': 'Mexico',
    'CHL': 'Chile',
    'CRI': 'Costa Rica',
}

# ──────────────────────────────────────────────────
# LOAD AND PROCESS DATA
# ──────────────────────────────────────────────────

df = pd.read_csv(DATA_PATH, low_memory=False)

# Keep only needed columns
cols = ['countrycodeiso', 'year', VARIABLE]
df = df[cols].rename(columns={
    'countrycodeiso': 'iso',
    VARIABLE: 'gdp_pc_ppp'
})
df['year'] = df['year'].astype(int)
df['gdp_pc_ppp'] = pd.to_numeric(df['gdp_pc_ppp'], errors='coerce')

# Filter years from base year onward
df = df[df['year'] >= BASE_YEAR].copy()

# ── Individual countries ──
all_iso_needed = set(individual_countries + lac_countries + dynamic_asia_countries)
df_filtered = df[df['iso'].isin(all_iso_needed)].copy()

def build_index(group_df, base_year=BASE_YEAR):
    """Convert levels to index = 100 in base_year."""
    base_vals = group_df[group_df['year'] == base_year].set_index('iso')['gdp_pc_ppp']
    group_df = group_df.copy()
    group_df['index'] = group_df.apply(
        lambda r: (r['gdp_pc_ppp'] / base_vals.get(r['iso'], float('nan'))) * 100
        if pd.notna(r['gdp_pc_ppp']) else float('nan'),
        axis=1
    )
    return group_df

df_indexed = build_index(df_filtered)

# Individual country series
records = []
for iso in individual_countries:
    tmp = df_indexed[df_indexed['iso'] == iso][['year', 'index']].dropna()
    label = country_labels.get(iso, iso)
    for _, row in tmp.iterrows():
        records.append({'year': int(row['year']), 'index': row['index'], 'group': label})

# LAC average
lac_df = df_indexed[df_indexed['iso'].isin(lac_countries)].groupby('year')['index'].mean().reset_index()
for _, row in lac_df.iterrows():
    records.append({'year': int(row['year']), 'index': row['index'], 'group': 'LAC'})

# Dynamic Asia average
asia_df = df_indexed[df_indexed['iso'].isin(dynamic_asia_countries)].groupby('year')['index'].mean().reset_index()
for _, row in asia_df.iterrows():
    records.append({'year': int(row['year']), 'index': row['index'], 'group': 'Dynamic Asia'})

chart_df = pd.DataFrame(records)

## ──────────────────────────────────────────────────
# CHART
# ──────────────────────────────────────────────────

# Define the line order and colors (OECD-style palette)
line_order = ['Mexico', 'Chile', 'Costa Rica', 'Dynamic Asia', 'LAC']
color_map = {
    'Mexico':        eco_style.pallete['nominal_1'],  # blue
    'Chile':         eco_style.pallete['nominal_2'],  # red
    'Costa Rica':    eco_style.pallete['nominal_3'],  # yellow
    'Dynamic Asia':  eco_style.pallete['nominal_4'],  # dark navy
    'LAC':           eco_style.pallete['nominal_6'],  # teal
}

# Get the last data point per group for end-of-line labels
last_year = chart_df.groupby('group')['year'].max().min()  # last common year
label_df = chart_df[chart_df['year'] == last_year].copy()

# Lines
lines = (
    alt.Chart(chart_df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X('year:O', title='', axis=alt.Axis(values=list(range(2000, 2025, 5)))),
        y=alt.Y('index:Q', title='Index, 2000 = 100',
                 scale=alt.Scale(domain=[75, 250])),
        color=alt.Color(
            'group:N',
            scale=alt.Scale(domain=line_order, range=[color_map[g] for g in line_order]),
            legend=None
        ),
        strokeDash=alt.condition(
            alt.datum.group == 'LAC',
            alt.value([5, 3]),
            alt.value([0])
        ),
    )
)

# End-of-line text labels
labels = (
    alt.Chart(label_df)
    .mark_text(align='left', dx=6, fontSize=11, fontWeight=500)
    .encode(
        x=alt.X('year:O'),
        y=alt.Y('index:Q'),
        text=alt.Text('group:N'),
        color=alt.Color(
            'group:N',
            scale=alt.Scale(domain=line_order, range=[color_map[g] for g in line_order]),
            legend=None
        ),
    )
)

# Horizontal baseline at y = 100
baseline = (
    alt.Chart(pd.DataFrame({'y': [100]}))
    .mark_rule(color=eco_style.pallete['domain'], strokeWidth=1, opacity=0.9, strokeDash=[1, 0])
    .encode(y='y:Q')
)

chart = (
    (baseline + lines + labels)
    .properties(
        title={
            "text": "Mexico's GDP per capita has barely grown in two decades",
            "subtitle": ["Index of real PPP-adjusted GDP per capita", "Constant 2017 international $, PPP"],
        },
        width=500,
        height=320,
    )
)

chart
# Save
#chart.save('figure_1_3.html')
#print("Chart saved to figure_1_3.html")
# To save as PNG (requires altair_saver + vl-convert or selenium):
chart.save('mexico_peers_chart.png', scale_factor=3, ppi=300)
#save as svg highest resolution 
chart.save('mexico_peers_chart.svg', scale_factor=3, ppi=300)



