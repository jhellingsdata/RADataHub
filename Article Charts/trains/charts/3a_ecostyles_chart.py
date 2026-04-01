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
DATA_URL = 'https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/Article%20Charts/trains/data/3a.csv'

colour_domain = ['West Leeds', 'Leamside', 'Current stations']
colour_range = ['#1f7a1f', '#e07b39', '#9ac7d8']

def build_chart(data_source: object) -> alt.Chart:
    base = (
        alt.Chart(data_source)
        .transform_calculate(
            Population_num='toNumber(datum.Population)',
            series="datum['Current/Leamside'] === 'Current' ? 'Current stations' : datum['Current/Leamside']",
        )
        .transform_window(
            rank='row_number()',
            sort=[alt.SortField('Population_num', order='descending')],
        )
    )
    
    
    area = (
        base
        .transform_filter("datum.series === 'Current stations'")
        .mark_area(opacity=0.9)
        .encode(
            x=alt.X(
                'Population_num:Q',
                title='Population within 1km',
                scale=alt.Scale(domain=[0, 160000]),
                axis=alt.Axis(format=',d', tickCount=9),
            ),
            x2=alt.value(0),
            y=alt.Y('rank:Q', axis=None),
            color=alt.value('#9ac7d8'),
        )
    )

    marker_base = (
        base
        .transform_filter("datum.series !== 'Current stations'")
        .transform_filter("datum.Labels != null && trim(datum.Labels) !== ''")
        .transform_calculate(zero='0')
    )

   
    markers = (
        marker_base
        .mark_rule(strokeWidth=1.8)
        .encode(
            x='zero:Q',
            x2='Population_num:Q',
            y='rank:Q',
            color=alt.Color(
                'series:N',
                title=None,
                scale=alt.Scale(domain=colour_domain, range=colour_range),
                legend=alt.Legend(orient='bottom', direction='horizontal', symbolType='square'),
            ),
        )
    )

    label_base = (
        marker_base
        .transform_calculate(label_x='datum.Population_num + 25000')
    )
    
    connectors = (
        label_base
        .mark_rule(color='#8d8d8d', strokeWidth=0.8)
        .encode(
            x='Population_num:Q',
            y='rank:Q',
            x2='label_x:Q',
            y2='rank:Q',
        )
    )
    
    labels = (
        label_base
        .mark_text(
            align='left',
            baseline='middle',
            dx=3,
            fontSize=10,
            color='#444',
        )
        .encode(
            x='label_x:Q',
            y='rank:Q',
            text='Labels:N',
        )
    )
    
    return (
        (area + markers + connectors + labels)
        .properties(
            width=540,
            height=520,
            title='Population within 1km of a station',
        )
        .configure(background='#ececec')
        .configure_axis(grid=False)
    )


url_data = alt.UrlData(DATA_URL, format=alt.DataFormat(type='csv'))
chart_json = build_chart(url_data)

df_png = pd.read_csv(DATA_URL, encoding='utf-8-sig')
chart_png = build_chart(df_png)

# Save outputs
styles.save(chart_png, path='charts', name='3a_ecostyles', width=540, height=520)
with open('charts/3a_ecostyles.json', 'w', encoding='utf-8') as f:
    json.dump(chart_json.to_dict(), f, indent=2)

print('Saved charts/3a_ecostyles.json and charts/3a_ecostyles.png')
