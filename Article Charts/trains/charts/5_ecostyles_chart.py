import sys
import json
from pathlib import Path

import altair as alt
import pandas as pd


def load_ecostyles():
    """Import EcoStyles, with a fallback to a local clone path if needed."""
    try:
        from ecostyles import EcoStyles  # type: ignore
        return EcoStyles
    except ModuleNotFoundError:
        fallback = Path('/tmp/ecostyles_repo/src')
        if fallback.exists():
            sys.path.insert(0, str(fallback))
            from ecostyles import EcoStyles  # type: ignore
            return EcoStyles
        raise


EcoStyles = load_ecostyles()
styles = EcoStyles()
styles.register_and_enable_theme(theme_name='article')

# Load and prepare data (real header starts on row 2).
DATA_URL = 'https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/Article%20Charts/trains/data/5.csv'

df = pd.read_csv(DATA_URL, encoding='utf-8-sig', header=1)

df = df.rename(columns={'Unnamed: 0': 'rank', 'Unnamed: 1': 'Station', 'Unnamed: 2': 'Group'})

for col in ['rank', 'Current stations', 'Leamside', 'West Leeds']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df[df['Station'].notna() & df['Current stations'].notna()].copy()
df = df.sort_values('Current stations', ascending=False).reset_index(drop=True)
df['x_pos'] = df.index + 1
df['series'] = 'Current stations'

colour_domain = ['Current stations', 'West Leeds', 'Leamside']
colour_range = ['#9ac7d8', '#1f7a1f', '#e07b39']

area = (
    alt.Chart(df)
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X('x_pos:Q', axis=None),
        y=alt.Y(
            'Current stations:Q',
            title='Rank of passenger entries/exits',
            scale=alt.Scale(domain=[0, 2100]),
            axis=alt.Axis(tickCount=5, titleAngle=270),
        ),
        y2=alt.value(0),
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
    )
)

marker_df = df[(df['West Leeds'] > 0) | (df['Leamside'] > 0)].copy()
marker_df['series'] = 'West Leeds'
marker_df.loc[marker_df['Leamside'] > 0, 'series'] = 'Leamside'
marker_df['marker_value'] = marker_df['West Leeds'].fillna(0)
marker_df.loc[marker_df['Leamside'] > 0, 'marker_value'] = marker_df['Leamside']
marker_df['zero'] = 0

rules = (
    alt.Chart(marker_df)
    .mark_rule(strokeWidth=1.4)
    .encode(
        x='x_pos:Q',
        y='zero:Q',
        y2='marker_value:Q',
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
    )
)

label_offsets = {
    'Butcher Hill': -65,
    'Wortley Road': -25,
    'Armley Canal Road': 10,
    'Wyther Lane': 48,
    'Fence Houses': -40,
    'Penshaw': -8,
    'High Shincliffe/Bowburn': 22,
    'Belmont/Durham Parkway': 52,
    'Ferryhill': -6,
    'West Rainton': 8,
}

label_df = marker_df.copy()
label_df['label_x'] = label_df['x_pos'] + label_df['Station'].map(label_offsets).fillna(0)
label_df['label_y'] = label_df['marker_value'] + 130

connectors = (
    alt.Chart(label_df)
    .mark_rule(color='#8d8d8d', strokeWidth=0.8)
    .encode(
        x='x_pos:Q',
        y='marker_value:Q',
        x2='label_x:Q',
        y2='label_y:Q',
    )
)

labels = (
    alt.Chart(label_df)
    .mark_text(angle=270, align='left', baseline='middle', fontSize=10, color='#444')
    .encode(
        x='label_x:Q',
        y='label_y:Q',
        text='Station:N',
    )
)

chart = (
    (area + rules + connectors + labels)
    .properties(
        width=500,
        height=250,
        title='Entries/Exits',
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
    .configure_axisYQuantitative(
        titleAngle=270,
        titleAlign='center',
        titleBaseline='middle',
        titleX=-38,
        titleY=125,
    )
)

# URL-backed JSON chart spec (raw CSV includes an extra first row).
url_base = (
    alt.Chart(alt.UrlData(DATA_URL, format=alt.DataFormat(type='csv')))
    .transform_calculate(
        station='datum["Unnamed: 1"]',
        current='toNumber(datum["Unnamed: 3"])',
        leamside='toNumber(datum["Unnamed: 4"])',
        west_leeds='toNumber(datum["Unnamed: 5"])',
        series='\'Current stations\'',
    )
    .transform_filter('datum.station != null && isValid(datum.current)')
    .transform_window(
        x_pos='row_number()',
        sort=[alt.SortField('current', order='descending')],
    )
)

url_area = (
    url_base
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X('x_pos:Q', axis=None),
        y=alt.Y(
            'current:Q',
            title='Rank of passenger entries/exits',
            scale=alt.Scale(domain=[0, 2100]),
            axis=alt.Axis(tickCount=5, titleAngle=270),
        ),
        y2=alt.value(0),
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
    )
)

url_markers = (
    url_base
    .transform_filter('datum.west_leeds > 0 || datum.leamside > 0')
    .transform_calculate(
        marker_series="datum.leamside > 0 ? 'Leamside' : 'West Leeds'",
        marker_value='datum.leamside > 0 ? datum.leamside : datum.west_leeds',
        zero='0',
        label_offset=(
            "datum.station === 'Butcher Hill' ? -65 : "
            "datum.station === 'Wortley Road' ? -25 : "
            "datum.station === 'Armley Canal Road' ? 10 : "
            "datum.station === 'Wyther Lane' ? 48 : "
            "datum.station === 'Fence Houses' ? -40 : "
            "datum.station === 'Penshaw' ? -8 : "
            "datum.station === 'High Shincliffe/Bowburn' ? 22 : "
            "datum.station === 'Belmont/Durham Parkway' ? 52 : "
            "datum.station === 'Ferryhill' ? -6 : "
            "datum.station === 'West Rainton' ? 8 : 0"
        ),
        label_x='datum.x_pos + datum.label_offset',
        label_y='datum.marker_value + 130',
    )
)

url_rules = (
    url_markers
    .mark_rule(strokeWidth=1.4)
    .encode(
        x='x_pos:Q',
        y='zero:Q',
        y2='marker_value:Q',
        color=alt.Color(
            'marker_series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
    )
)

url_connectors = (
    url_markers
    .mark_rule(color='#8d8d8d', strokeWidth=0.8)
    .encode(
        x='x_pos:Q',
        y='marker_value:Q',
        x2='label_x:Q',
        y2='label_y:Q',
    )
)

url_labels = (
    url_markers
    .mark_text(angle=270, align='left', baseline='middle', fontSize=10, color='#444')
    .encode(
        x='label_x:Q',
        y='label_y:Q',
        text='station:N',
    )
)

chart_json = (
    (url_area + url_rules + url_connectors + url_labels)
    .properties(
        width=500,
        height=250,
        title='Entries/Exits',
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
    .configure_axisYQuantitative(
        titleAngle=270,
        titleAlign='center',
        titleBaseline='middle',
        titleX=-38,
        titleY=125,
    )
)

styles.save(chart, path='charts', name='5_ecostyles', width=500, height=250)
with open('charts/5_ecostyles.json', 'w', encoding='utf-8') as f:
    json.dump(chart_json.to_dict(), f, separators=(',', ':'))

print('Saved charts/5_ecostyles.json and charts/5_ecostyles.png')
