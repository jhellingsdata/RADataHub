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


def parse_percent(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace('%', '', regex=False), errors='coerce') / 100


EcoStyles = load_ecostyles()
styles = EcoStyles()
styles.register_and_enable_theme(theme_name='article')

DATA_URL = 'https://raw.githubusercontent.com/jhellingsdata/RADataHub/refs/heads/main/Article%20Charts/trains/data/6.csv'

df = pd.read_csv(DATA_URL, encoding='utf-8-sig')

df['city_centre_share'] = parse_percent(df['Share in City Centres (Registered)'])
df['uk_share'] = parse_percent(df['Northumberland, Durham and Tyne & Wear'])
df['all_business_share'] = parse_percent(df['All business share'])

all_business_share = df['all_business_share'].dropna().iloc[0]

plot_df = df[
    df['Sector'].notna()
    & (df['Sector'].str.strip() != '')
    & (df['Sector'] != 'All Business Share')
    & df['city_centre_share'].notna()
    & df['uk_share'].notna()
].copy()

points = (
    alt.Chart(plot_df)
    .mark_point(size=28, color='#0b5d7c')
    .encode(
        x=alt.X(
            'city_centre_share:Q',
            title='Share of businesses in a cutting-edge sector that are located in a city centre',
            scale=alt.Scale(domain=[0, 0.6]),
            axis=alt.Axis(format='.0%', tickCount=7),
        ),
        y=alt.Y(
            'uk_share:Q',
            title='Share of UK total',
            scale=alt.Scale(domain=[0, 0.045]),
            axis=alt.Axis(format='.1%', tickCount=10),
        ),
        tooltip=[
            alt.Tooltip('Sector:N'),
            alt.Tooltip('city_centre_share:Q', title='City centre share', format='.2%'),
            alt.Tooltip('uk_share:Q', title='Share of UK total', format='.2%'),
        ],
    )
)

reference_line = (
    alt.Chart(pd.DataFrame({'x': [0]}))
    .mark_rule(color='black', strokeWidth=1.8)
    .encode(y=alt.datum(all_business_share))
)

reference_label = (
    alt.Chart(pd.DataFrame({'x': [0]}))
    .mark_text(align='right', baseline='bottom', dy=-4, fontSize=10, color='black')
    .encode(
        x=alt.datum(0.595),
        y=alt.datum(all_business_share),
        text=alt.value("North East's share of all businesses"),
    )
)

chart = (
    (points + reference_line + reference_label)
    .properties(width=500, height=320)
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

# URL-backed JSON chart spec.
url_data = alt.UrlData(DATA_URL, format=alt.DataFormat(type='csv'))

url_points = (
    alt.Chart(url_data)
    .transform_calculate(
        city_centre_share="toNumber(replace(datum['Share in City Centres (Registered)'], '%', '')) / 100",
        uk_share="toNumber(replace(datum['Northumberland, Durham and Tyne & Wear'], '%', '')) / 100",
    )
    .transform_filter(
        "datum.Sector != null && trim(datum.Sector) !== '' && datum.Sector !== 'All Business Share' && "
        'isValid(datum.city_centre_share) && isValid(datum.uk_share)'
    )
    .mark_point(size=28, color='#0b5d7c')
    .encode(
        x=alt.X(
            'city_centre_share:Q',
            title='Share of businesses in a cutting-edge sector that are located in a city centre',
            scale=alt.Scale(domain=[0, 0.6]),
            axis=alt.Axis(format='.0%', tickCount=7),
        ),
        y=alt.Y(
            'uk_share:Q',
            title='Share of UK total',
            scale=alt.Scale(domain=[0, 0.045]),
            axis=alt.Axis(format='.1%', tickCount=10),
        ),
        tooltip=[
            alt.Tooltip('Sector:N'),
            alt.Tooltip('city_centre_share:Q', title='City centre share', format='.2%'),
            alt.Tooltip('uk_share:Q', title='Share of UK total', format='.2%'),
        ],
    )
)

url_reference_line = (
    alt.Chart(url_data)
    .transform_filter("datum['All business share'] != null && trim(datum['All business share']) !== ''")
    .transform_calculate(all_business_share="toNumber(replace(datum['All business share'], '%', '')) / 100")
    .mark_rule(color='black', strokeWidth=1.8)
    .encode(y='all_business_share:Q')
)

url_reference_label = (
    alt.Chart(url_data)
    .transform_filter("datum['All business share'] != null && trim(datum['All business share']) !== ''")
    .transform_calculate(all_business_share="toNumber(replace(datum['All business share'], '%', '')) / 100")
    .mark_text(align='right', baseline='bottom', dy=-4, fontSize=10, color='black')
    .encode(
        x=alt.datum(0.595),
        y='all_business_share:Q',
        text=alt.value("North East's share of all businesses"),
    )
)

chart_json = (
    (url_points + url_reference_line + url_reference_label)
    .properties(width=500, height=320)
    .configure(background='#ececec')
    .configure_axis(grid=False)
)

styles.save(chart, path='charts', name='6_ecostyles', width=500, height=320)
with open('charts/6_ecostyles.json', 'w', encoding='utf-8') as f:
    json.dump(chart_json.to_dict(), f, separators=(',', ':'))

print('Saved charts/6_ecostyles.json and charts/6_ecostyles.png')
