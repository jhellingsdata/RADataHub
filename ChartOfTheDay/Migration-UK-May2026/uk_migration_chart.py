"""
UK net migration almost halved in 2025 — recreation of the FT chart.

Source: ONS, Long-term international migration, Year Ending December 2025
"""

import sys
sys.path.insert(0, '/mnt/project')

import altair as alt
import pandas as pd
import vl_convert as vlc

from eco_style import pallete

alt.themes.enable('report')

# ---------------------------------------------------------------------------
# Load and shape Table 1
# ---------------------------------------------------------------------------
SRC = '/mnt/user-data/uploads/may2026publicationspreadsheet.xlsx'

raw = pd.read_excel(SRC, sheet_name='1', header=5)
raw.columns = ['Flow', 'Period', 'All', 'British', 'EU+', 'Non-EU+']
raw = raw.dropna(subset=['Flow', 'Period']).reset_index(drop=True)

# Period strings like "YE Jun 12", "YE Dec 25 P" → quarter-end date
MONTHS = {'Mar': 3, 'Jun': 6, 'Sep': 9, 'Dec': 12}

def ye_to_date(s: str) -> pd.Timestamp:
    parts = s.replace(' P', '').replace(' R', '').strip().split()
    # ['YE', 'Jun', '12']
    month = MONTHS[parts[1]]
    year = 2000 + int(parts[2])
    return pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)

raw['date'] = raw['Period'].apply(ye_to_date)
raw['value_mn'] = raw['All'] / 1_000_000  # millions

df = raw[['date', 'Flow', 'value_mn']].copy()
df['Flow'] = df['Flow'].replace({'Net migration': 'Net migration'})

# Endpoints for inline labels
endpoints = df.sort_values('date').groupby('Flow').tail(1)

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------
flow_order = ['Immigration', 'Emigration', 'Net migration']
flow_colors = [
    pallete['nominal_1'],   # immigration — blue
    pallete['nominal_2'],   # emigration  — red
    pallete['Other_3'],     # net         — light grey
]

color_scale = alt.Scale(domain=flow_order, range=flow_colors)

base = alt.Chart(df).encode(
    x=alt.X('date:T',
            axis=alt.Axis(format='%Y', tickCount='year', title=None,
                          labelFlush=False)),
    y=alt.Y('value_mn:Q',
            scale=alt.Scale(domain=[0, 1.6]),
            axis=alt.Axis(values=[0, 0.5, 1.0, 1.5],
                          format='.1f',
                          title=None)),
    color=alt.Color('Flow:N', scale=color_scale, legend=None),
)

lines = base.mark_line(strokeWidth=2.5, interpolate='monotone')

dots = alt.Chart(endpoints).mark_circle(size=70).encode(
    x='date:T',
    y='value_mn:Q',
    color=alt.Color('Flow:N', scale=color_scale, legend=None),
)

labels = alt.Chart(endpoints).mark_text(
    align='left', dx=10, dy=0, fontSize=12, fontWeight=500,
).encode(
    x='date:T',
    y='value_mn:Q',
    text='Flow:N',
    color=alt.Color('Flow:N', scale=color_scale, legend=None),
)

main = (lines + dots + labels).properties(
    width=620,
    height=380,
    title=alt.TitleParams(
        text='UK net migration almost halved in 2025',
        subtitle='Long-term UK migration flows, 12-month rolling estimate (millions)',
        anchor='start',
        fontSize=18,
        subtitleFontSize=12,
        subtitleColor='#5a6b75',
        offset=12,
    ),
)

source_caption = alt.Chart(pd.DataFrame({'t': ['']})).mark_text(
    text='Source: Economics Observatory based on ONS Long-term international migration (Dec 2025). '
         'Estimates for YE Mar 2025 onwards are provisional.',
    align='left', baseline='top', fontSize=10, color='#5a6b75', dx=0,
).encode(x=alt.value(0), y=alt.value(0))

chart = alt.vconcat(main, source_caption, spacing=5).configure_view(strokeWidth=0)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
OUT_PNG = '/mnt/user-data/outputs/uk_migration_2025.png'
OUT_SVG = '/mnt/user-data/outputs/uk_migration_2025.svg'

spec = chart.to_json()
with open(OUT_PNG, 'wb') as f:
    f.write(vlc.vegalite_to_png(spec, scale=3))
with open(OUT_SVG, 'w') as f:
    f.write(vlc.vegalite_to_svg(spec))

# Print latest numbers for the post copy
latest = df.sort_values('date').groupby('Flow').tail(1).set_index('Flow')['value_mn']
prior_peak = df[df['Flow']=='Net migration']['value_mn'].max()
prior_peak_date = df[(df['Flow']=='Net migration') & (df['value_mn']==prior_peak)]['date'].iloc[0]
print(f"Latest immigration:   {latest['Immigration']*1e6:,.0f}")
print(f"Latest emigration:    {latest['Emigration']*1e6:,.0f}")
print(f"Latest net migration: {latest['Net migration']*1e6:,.0f}")
print(f"Net peak: {prior_peak*1e6:,.0f} ({prior_peak_date.strftime('%b %Y')})")
print(f"Fall from peak: {(1 - latest['Net migration']/prior_peak)*100:.0f}%")
