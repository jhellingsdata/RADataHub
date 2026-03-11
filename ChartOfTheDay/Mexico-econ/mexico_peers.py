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
alt.themes.enable('report')

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

#UK and US
uk_us = ['GBR', 'USA']

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

# ── Save dataset filtered ──
df_filtered.to_csv('mexico_peers_data.csv', index=False)
# -------------------------
# Import the filtered dataset
df_filtered = pd.read_csv('mexico_peers_data.csv')
# -------------------------

# indexing function to convert to index with base year = 100
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
# CHART 1 — ORIGINAL (unchanged)
# ──────────────────────────────────────────────────

# Define the line order and colors (OECD-style palette)
line_order = ['Mexico', 'Chile', 'Costa Rica', 'Dynamic Asia', 'LAC']
color_map = {
    'Dynamic Asia':  eco_style.pallete['nominal_1'],  # blue
    'Chile':         eco_style.pallete['nominal_2'],  # red
    'Costa Rica':    eco_style.pallete['nominal_3'],  # yellow
    'LAC':        eco_style.pallete['nominal_4'],  # dark navy
    'Mexico':           eco_style.pallete['nominal_6'],  # teal
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
    .mark_rule(color=eco_style.pallete['domain'], strokeWidth=2, opacity=0.9, strokeDash=[1, 0])
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


## ──────────────────────────────────────────────────
# CHART 2 — WITH UK AND US ADDED
# ──────────────────────────────────────────────────

# Expand the dataset to include GBR and USA
all_iso_needed_v2 = set(individual_countries + lac_countries + dynamic_asia_countries + uk_us)
df_filtered_v2 = df[df['iso'].isin(all_iso_needed_v2)].copy()

df_filtered_v2.to_csv('mexico_peers_with_uk_us_data.csv', index=False)
df_filtered_v2 = pd.read_csv('mexico_peers_with_uk_us_data.csv')

df_indexed_v2 = build_index(df_filtered_v2)

# Build records: start from the original records, then add UK and US
records_v2 = list(records)  # copy original records (MEX, CHL, CRI, LAC, Dynamic Asia)

# Labels for UK and US
country_labels_v2 = {
    'GBR': 'United Kingdom',
    'USA': 'United States',
}

for iso in uk_us:
    tmp = df_indexed_v2[df_indexed_v2['iso'] == iso][['year', 'index']].dropna()
    label = country_labels_v2[iso]
    for _, row in tmp.iterrows():
        records_v2.append({'year': int(row['year']), 'index': row['index'], 'group': label})

chart_df_v2 = pd.DataFrame(records_v2)

# Line order and colors — UK/US use their predefined eco_style colors
# Reassign remaining series to avoid color clashes
line_order_v2 = [
    'Mexico', 'Chile', 'Costa Rica',
    'Dynamic Asia', 'LAC',
    'United Kingdom'
]

color_map_v2 = {
    'United Kingdom':  eco_style.pallete['United Kingdom'],  # nominal_1 — #179fdb blue
    'United States':   eco_style.pallete['United States'],   # nominal_2 — #e6224b red
    'Chile':           eco_style.pallete['nominal_3'],       # #f4c245 — yellow
    'Dynamic Asia':    eco_style.pallete['nominal_5'],       # #eb5c2e — orange
    'LAC':             eco_style.pallete['nominal_4'],       # #122b39 — dark navy
    'Mexico':          eco_style.pallete['nominal_6'],       # #36b7b4 — teal
    'Costa Rica':      "grey",         # #d6d4d4 — grey
}

# Last common year for end-of-line labels
last_year_v2 = chart_df_v2.groupby('group')['year'].max().min()
label_df_v2 = chart_df_v2[chart_df_v2['year'] == last_year_v2].copy()

# Lines
lines_v2 = (
    alt.Chart(chart_df_v2)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X('year:O', title='', axis=alt.Axis(values=list(range(2000, 2025, 5)))),
        y=alt.Y('index:Q', title='Index, 2000 = 100',
                 scale=alt.Scale(domain=[75, 275])),
        color=alt.Color(
            'group:N',
            scale=alt.Scale(domain=line_order_v2, range=[color_map_v2[g] for g in line_order_v2]),
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
labels_v2 = (
    alt.Chart(label_df_v2)
    .mark_text(align='left', dx=6, fontSize=11, fontWeight=500)
    .encode(
        x=alt.X('year:O'),
        y=alt.Y('index:Q'),
        text=alt.Text('group:N'),
        color=alt.Color(
            'group:N',
            scale=alt.Scale(domain=line_order_v2, range=[color_map_v2[g] for g in line_order_v2]),
            legend=None
        ),
    )
)

# Horizontal baseline at y = 100
baseline_v2 = (
    alt.Chart(pd.DataFrame({'y': [100]}))
    .mark_rule(color=eco_style.pallete['domain'], strokeWidth=2, opacity=0.9, strokeDash=[1, 0])
    .encode(y='y:Q')
)

chart_v2 = (
    (baseline_v2 + lines_v2 + labels_v2)
    .properties(
        title={
            "text": "Mexico's GDP per capita has barely grown compared to peers",
            "subtitle": [
                "Index of real PPP-adjusted GDP per capita",
                "Constant 2017 international $, PPP"
            ],
        },
        width=500,
        height=320,
    )
)

chart_v2
# Save Chart 2
chart_v2.save('mexico_peers_uk_us_chart.png', scale_factor=3, ppi=300)
chart_v2.save('mexico_peers_uk_us_chart.svg', scale_factor=3, ppi=300)
print("Chart 1 saved to mexico_peers_chart.png and .svg")
print("Chart 2 saved to mexico_peers_uk_us_chart.png and .svg")