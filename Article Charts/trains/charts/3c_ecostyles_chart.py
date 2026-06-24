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

# Load and prepare data 
DATA_URL = 'https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/Article%20Charts/trains/data/3c.csv'

df = pd.read_csv(DATA_URL, encoding='utf-8-sig', header=1)

df = df.rename(columns={'Local authority': 'Station'})

for col in ['Other local authorities', 'Sunderland/Newcastle', 'Leeds']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df['wage'] = df['Other local authorities']


df['series'] = 'Other local authorities'
df.loc[df['Sunderland/Newcastle'] > 0, 'series'] = 'Sunderland/Newcastle'
df.loc[df['Leeds'] > 0, 'series'] = 'Leeds'

plot_df = (
    df.sort_values('wage', ascending=False)
    .reset_index(drop=True)
    .assign(rank=lambda d: d.index + 1)
)

colour_domain = ['Leeds', 'Sunderland/Newcastle', 'Other local authorities']
colour_range = ['#1f7a1f', '#e07b39', '#9ac7d8']

area = (
    alt.Chart(plot_df)
    .transform_filter("datum.series === 'Other local authorities'")
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X(
            'wage:Q',
            title='Median wage, 2025 (£)',
            scale=alt.Scale(domain=[0, 1500]),
            axis=alt.Axis(format=',d', tickCount=4),
        ),
        x2=alt.value(0),
        y=alt.Y('rank:Q', axis=None),
        color=alt.value('#9ac7d8'),
    )
)

marker_df = (
    plot_df.loc[
        (plot_df['series'] != 'Other local authorities')
        & plot_df['Labels'].notna()
        & (plot_df['Labels'].str.strip() != '')
    ]
    .copy()
)
marker_df['zero'] = 0
marker_df = marker_df.sort_values('wage', ascending=True).reset_index(drop=True)

markers = (
    alt.Chart(marker_df)
    .mark_rule(strokeWidth=1.8)
    .encode(
        x='zero:Q',
        x2='wage:Q',
        y='rank:Q',
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
    )
)

label_df = marker_df.copy()
label_df['label_x'] = label_df['wage'] + 170
label_df['label_y'] = label_df['rank']

connectors = (
    alt.Chart(label_df)
    .mark_rule(color='#8d8d8d', strokeWidth=0.8)
    .encode(
        x='wage:Q',
        y='rank:Q',
        x2='label_x:Q',
        y2='label_y:Q',
    )
)

labels = (
    alt.Chart(label_df)
    .mark_text(align='left', baseline='middle', dx=3, fontSize=10, color='#444')
    .encode(
        x='label_x:Q',
        y='label_y:Q',
        text='Labels:N',
    )
)

chart = (
    (area + markers + connectors + labels)
    .properties(
        width=330,
        height=420,
        title='Median wage',
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
)


url_base = (
    alt.Chart(alt.UrlData(DATA_URL, format=alt.DataFormat(type='csv')))
    .transform_calculate(
        station='datum.WAGES',
        wage='toNumber(datum["Unnamed: 1"])',
        sn='toNumber(datum["Unnamed: 2"])',
        leeds='toNumber(datum["Unnamed: 3"])',
        labels='datum["Unnamed: 5"]',
    )
    .transform_filter("datum.station != null && datum.station !== 'Local authority' && isValid(datum.wage)")
    .transform_calculate(
        series="datum.leeds > 0 ? 'Leeds' : datum.sn > 0 ? 'Sunderland/Newcastle' : 'Other local authorities'"
    )
    .transform_window(
        rank='row_number()',
        sort=[alt.SortField('wage', order='descending')],
    )
)

url_area = (
    url_base
    .transform_filter("datum.series === 'Other local authorities'")
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X(
            'wage:Q',
            title='Median wage, 2025 (£)',
            scale=alt.Scale(domain=[0, 1500]),
            axis=alt.Axis(format=',d', tickCount=4),
        ),
        x2=alt.value(0),
        y=alt.Y('rank:Q', axis=None),
        color=alt.value('#9ac7d8'),
    )
)

url_marker_base = (
    url_base
    .transform_filter("datum.series !== 'Other local authorities'")
    .transform_filter("datum.labels != null && trim(datum.labels) !== ''")
    .transform_calculate(zero='0')
)

url_markers = (
    url_marker_base
    .mark_rule(strokeWidth=1.8)
    .encode(
        x='zero:Q',
        x2='wage:Q',
        y='rank:Q',
        color=alt.Color(
            'series:N',
            title=None,
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
        ),
    )
)

url_label_base = (
    url_marker_base
    .transform_calculate(label_x='datum.wage + 170')
)

url_connectors = (
    url_label_base
    .mark_rule(color='#8d8d8d', strokeWidth=0.8)
    .encode(
        x='wage:Q',
        y='rank:Q',
        x2='label_x:Q',
        y2='rank:Q',
    )
)

url_labels = (
    url_label_base
    .mark_text(align='left', baseline='middle', dx=3, fontSize=10, color='#444')
    .encode(
        x='label_x:Q',
        y='rank:Q',
        text='labels:N',
    )
)

chart_json = (
    (url_area + url_markers + url_connectors + url_labels)
    .properties(
        width=330,
        height=420,
        title='Median wage',
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

styles.save(chart, path='charts', name='3c_ecostyles', width=330, height=420)
with open('charts/3c_ecostyles.json', 'w', encoding='utf-8') as f:
    json.dump(chart_json.to_dict(), f, indent=2)

print('Saved charts/3c_ecostyles.json and charts/3c_ecostyles.png')
