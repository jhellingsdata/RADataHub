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
DATA_URL = 'https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/Article%20Charts/trains/data/3d.csv'

df = pd.read_csv(DATA_URL, encoding='utf-8-sig', header=1)

df = df.rename(columns={df.columns[1]: 'Station', df.columns[-1]: 'Labels'})

for col in ['Other local authorities', 'Sunderland/Newcastle', 'Leeds']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df[df['Station'].notna() & df['Other local authorities'].notna()].copy()

df['jobs'] = df['Other local authorities']

# Category used for colouring highlighted stations.
df['series'] = 'Other stations'
df.loc[df['Sunderland/Newcastle'] > 0, 'series'] = 'Sunderland/Newcastle'
df.loc[df['Leeds'] > 0, 'series'] = 'Leeds'

plot_df = (
    df.sort_values('jobs', ascending=False)
    .reset_index(drop=True)
    .assign(rank=lambda d: d.index + 1)
)
plot_df = plot_df.where(pd.notna(plot_df), None)

colour_domain = ['Leeds', 'Sunderland/Newcastle', 'Other stations']
colour_range = ['#1f7a1f', '#e07b39', '#9ac7d8']

area = (
    alt.Chart(plot_df)
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X(
            'jobs:Q',
            title="Jobs around 'destination' stations",
            scale=alt.Scale(domain=[0, 1200000]),
            axis=alt.Axis(format='d', tickCount=7),
        ),
        x2=alt.value(0),
        y=alt.Y('rank:Q', axis=None),
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
        order=alt.Order('series:N', sort='ascending'),
    )
)

# Right-side callouts for highlighted destinations.
right_labels = plot_df[plot_df['Station'].isin(['Leeds', 'Newcastle', 'Sunderland'])].copy()
right_labels['label_x'] = right_labels['jobs'] + pd.Series(
    right_labels['Station'].map({'Leeds': 100000, 'Newcastle': 115000, 'Sunderland': 130000})
)
right_labels['label_y'] = right_labels['rank']
right_labels = right_labels.where(pd.notna(right_labels), None)

right_connectors = (
    alt.Chart(right_labels)
    .mark_rule(color='#6f6f6f', strokeCap='round', strokeWidth=1.2, opacity=1.0)
    .encode(
        x='jobs:Q',
        y='rank:Q',
        x2='label_x:Q',
        y2='label_y:Q',
    )
)

right_text = (
    alt.Chart(right_labels)
    .mark_text(align='left', baseline='middle', dx=3, fontSize=10, fontWeight='bold')
    .encode(
        x='label_x:Q',
        y='label_y:Q',
        text='Station:N',
        color=alt.Color(
            'series:N',
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=None,
        ),
    )
)

chart = (
    (area + right_connectors + right_text)
    .properties(
        width=560,
        height=360,
        title="Jobs around 'destination' stations",
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

# URL-backed JSON chart spec (raw CSV includes an extra first row).
url_base = (
    alt.Chart(alt.UrlData(DATA_URL, format=alt.DataFormat(type='csv')))
    .transform_calculate(
        station='datum["Unnamed: 1"]',
        jobs='toNumber(datum["Unnamed: 2"])',
        sn='toNumber(datum["Unnamed: 3"])',
        leeds='toNumber(datum["Unnamed: 4"])',
    )
    .transform_filter('datum.station != null && isValid(datum.jobs)')
    .transform_calculate(
        series="datum.leeds > 0 ? 'Leeds' : datum.sn > 0 ? 'Sunderland/Newcastle' : 'Other stations'"
    )
    .transform_window(
        rank='row_number()',
        sort=[alt.SortField('jobs', order='descending')],
    )
)

url_area = (
    url_base
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X(
            'jobs:Q',
            title="Jobs around 'destination' stations",
            scale=alt.Scale(domain=[0, 1200000]),
            axis=alt.Axis(format='d', tickCount=7),
        ),
        x2=alt.value(0),
        y=alt.Y('rank:Q', axis=None),
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
        order=alt.Order('series:N', sort='ascending'),
    )
)

url_right_labels = (
    url_base
    .transform_filter("datum.station === 'Leeds' || datum.station === 'Newcastle' || datum.station === 'Sunderland'")
    .transform_calculate(
        label_offset=(
            "datum.station === 'Leeds' ? 100000 : "
            "datum.station === 'Newcastle' ? 115000 : 130000"
        ),
        label_x='datum.jobs + datum.label_offset',
    )
)

url_right_connectors = (
    url_right_labels
    .mark_rule(color='#6f6f6f', strokeCap='round', strokeWidth=1.2, opacity=1.0)
    .encode(
        x='jobs:Q',
        y='rank:Q',
        x2='label_x:Q',
        y2='rank:Q',
    )
)

url_right_text = (
    url_right_labels
    .mark_text(align='left', baseline='middle', dx=3, fontSize=10, fontWeight='bold')
    .encode(
        x='label_x:Q',
        y='rank:Q',
        text='station:N',
        color=alt.Color(
            'series:N',
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=None,
        ),
    )
)

chart_json = (
    (url_area + url_right_connectors + url_right_text)
    .properties(
        width=560,
        height=360,
        title="Jobs around 'destination' stations",
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

styles.save(chart, path='charts', name='3d_ecostyles', width=560, height=360)
with open('charts/3d_ecostyles.json', 'w', encoding='utf-8') as f:
    json.dump(chart_json.to_dict(), f, separators=(',', ':'))

print('Saved charts/3d_ecostyles.json and charts/3d_ecostyles.png')
