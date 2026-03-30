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

# Load and prepare data.
DATA_URL = 'https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/Article%20Charts/trains/data/3b.csv'

df = pd.read_csv(DATA_URL, encoding='utf-8-sig')

current_share = pd.to_numeric(
    df['Share level 4+'].astype(str).str.replace('%', '', regex=False),
    errors='coerce',
) / 100

wl_share = pd.to_numeric(df['West Leeds'], errors='coerce')
leamside_share = pd.to_numeric(df['Leamside'], errors='coerce')

df['share'] = current_share
df.loc[df['Current/Leamside'] == 'West Leeds', 'share'] = wl_share
df.loc[df['Current/Leamside'] == 'Leamside', 'share'] = leamside_share

plot_df = (
    df.sort_values('share', ascending=False)
    .reset_index(drop=True)
    .assign(rank=lambda d: d.index + 1)
)

plot_df['series'] = plot_df['Current/Leamside'].replace({'Current': 'Current stations'})

colour_domain = ['West Leeds', 'Leamside', 'Current stations']
colour_range = ['#1f7a1f', '#e07b39', '#9ac7d8']

# Base area chart.
area = (
    alt.Chart(plot_df)
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X(
            'share:Q',
            title=[
                'Share of population within 1km of a station that has a level 4+ qualification',
            ],
            scale=alt.Scale(domain=[0, 0.8]),
            axis=alt.Axis(format='.0%', tickCount=9),
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

# Label rows with manual offset tweaks to reduce overlap.
label_df = (
    plot_df.loc[plot_df['Labels'].notna() & (plot_df['Labels'].str.strip() != '')]
    .copy()
    .sort_values('share', ascending=True)
    .reset_index(drop=True)
)

label_df['label_x'] = label_df['share'] + 0.10
label_df['label_y'] = label_df['rank']

connectors = (
    alt.Chart(label_df)
    .mark_rule(color='#6f6f6f', strokeCap='round', strokeWidth=1.2, opacity=1.0)
    .encode(
        x='share:Q',
        y='rank:Q',
        x2='label_x:Q',
        y2='label_y:Q',
    )
)

labels = (
    alt.Chart(label_df)
    .mark_text(align='left', baseline='middle', dx=3, fontSize=10, fontWeight='bold')
    .encode(
        x='label_x:Q',
        y='label_y:Q',
        text='Labels:N',
        color=alt.Color(
            'series:N',
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=None,
        ),
    )
)

chart = (
    (area + connectors + labels)
    .properties(
        width=540,
        height=520,
        title='Skills of the surrounding population',
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

# URL-backed JSON chart spec.
url_base = (
    alt.Chart(alt.UrlData(DATA_URL, format=alt.DataFormat(type='csv')))
    .transform_calculate(
        current_share="toNumber(replace(datum['Share level 4+'], '%', '')) / 100",
        west_leeds_share="toNumber(datum['West Leeds'])",
        leamside_share="toNumber(datum['Leamside'])",
    )
    .transform_calculate(
        share=(
            "datum['Current/Leamside'] === 'West Leeds' ? datum.west_leeds_share : "
            "datum['Current/Leamside'] === 'Leamside' ? datum.leamside_share : datum.current_share"
        ),
        series="datum['Current/Leamside'] === 'Current' ? 'Current stations' : datum['Current/Leamside']",
    )
    .transform_window(
        rank='row_number()',
        sort=[alt.SortField('share', order='descending')],
    )
)

url_area = (
    url_base
    .mark_area(opacity=0.9)
    .encode(
        x=alt.X(
            'share:Q',
            title=[
                'Share of population within 1km of a station that has a level 4+',
                'qualification',
            ],
            scale=alt.Scale(domain=[0, 0.8]),
            axis=alt.Axis(format='.0%', tickCount=9),
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

url_label_base = (
    url_base
    .transform_filter("datum.Labels != null && trim(datum.Labels) !== ''")
    .transform_calculate(label_x='datum.share + 0.10')
)

url_connectors = (
    url_label_base
    .mark_rule(color='#6f6f6f', strokeCap='round', strokeWidth=1.2, opacity=1.0)
    .encode(
        x='share:Q',
        y='rank:Q',
        x2='label_x:Q',
        y2='rank:Q',
    )
)

url_labels = (
    url_label_base
    .mark_text(align='left', baseline='middle', dx=3, fontSize=10, fontWeight='bold')
    .encode(
        x='label_x:Q',
        y='rank:Q',
        text='Labels:N',
        color=alt.Color(
            'series:N',
            scale=alt.Scale(domain=colour_domain, range=colour_range),
            legend=None,
        ),
    )
)

chart_json = (
    (url_area + url_connectors + url_labels)
    .properties(
        width=540,
        height=520,
        title='Skills of the surrounding population',
    )
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

# Save outputs.
styles.save(chart, path='charts', name='3b_ecostyles', width=540, height=520)
with open('charts/3b_ecostyles.json', 'w', encoding='utf-8') as f:
    json.dump(chart_json.to_dict(), f, separators=(',', ':'))

print('Saved charts/3b_ecostyles.json and charts/3b_ecostyles.png')
