from psutil import disk_partitions
import altair as alt
import pandas as pd
import eco_style
from eco_style import pallete

alt.themes.enable('report')

# Data from Figure in 2026 AI Index report
# Source: Chegg Global Student Survey, 2023 and 2025
data = pd.DataFrame({
    'country': ['Indonesia', 'Malaysia', 'Saudi Arabia', 'Spain', 'Brazil',
                'South Korea', 'India', 'Kenya', 'Mexico', 'South Africa',
                'Canada', 'Australia', 'Turkey', 'United States', 'United Kingdom'],
    'y2023': [53, 49, 62, 62, 52, 23, 44, 63, 33, 33, 54, 33, 30, 20, 19],
    'y2025': [95, 90, 89, 87, 84, 84, 84, 83, 83, 81, 79, 77, 68, 67, 67]
})

data['change'] = data['y2025'] - data['y2023']
data['label_2025'] = data['y2025'].astype(str) + '% (+' + data['change'].astype(str) + ' pp)'
data['label_2023'] = data['y2023'].astype(str) + '%'

# Sort by 2025 value descending (top to bottom)
sort_order = data.sort_values('y2025', ascending=False)['country'].tolist()

# Melt for the dots
dots = data.melt(id_vars=['country'], value_vars=['y2023', 'y2025'],
                 var_name='year', value_name='pct')
dots['year'] = dots['year'].map({'y2023': '2023', 'y2025': '2025'})

# Connector lines (rule from 2023 to 2025)
connectors = alt.Chart(data).mark_rule(
    strokeWidth=1.5, color='#aaa'
).encode(
    x='y2023:Q',
    x2='y2025:Q',
    y=alt.Y('country:N', sort=sort_order, axis=alt.Axis(title=None, labelFontSize=12))
)

# Dots
points = alt.Chart(dots).mark_circle(size=80).encode(
    x=alt.X('pct:Q',
             title='% of students who have used GenAI',
             scale=alt.Scale(domain=[0, 100]),
             axis=alt.Axis(format='d',
                           labelExpr="datum.value + '%'",
                           grid=True, gridDash=[1, 5], gridOpacity=0.3,
                           values=[0, 20, 40, 60, 80, 100],
                           titlePadding=10)),
    y=alt.Y('country:N', sort=sort_order,
             axis=alt.Axis(title=None, labelFontSize=12)),
    color=alt.Color('year:N',
                     scale=alt.Scale(domain=['2023', '2025'],
                                     range=['#d4b5e9', pallete['nominal_1']]),
                     legend=alt.Legend(
                         title=None,
                         orient='bottom-right',
                         labelFontSize=11,
                         symbolSize=80
                     ))
)
# 2025 labels (right of dot)
labels_2025 = alt.Chart(data).mark_text(
    align='left', dx=8, fontSize=10, color=pallete['domain']
).encode(
    x='y2025:Q',
    y=alt.Y('country:N', sort=sort_order),
    text='label_2025:N'
)

# 2023 labels (left of dot)
labels_2023 = alt.Chart(data).mark_text(
    align='right', dx=-8, fontSize=10, color='#999'
).encode(
    x='y2023:Q',
    y=alt.Y('country:N', sort=sort_order),
    text='label_2023:N'
)

# Main chart
main = (connectors + points + labels_2025 + labels_2023).properties(
    width=450,
    height=440,
    title={
        'text': 'University students who have used GenAI to support their studies, 2023-2025',
        'subtitle': 'Source: Chegg Global Student Survey on 2026 AI Index report',
        'fontSize': 14, 'fontWeight': 'bold',
        'subtitleFontSize': 10,
        'subtitleColor': '#666', 'anchor': 'start'
    }
).configure_view(strokeWidth=0)

main

main.save('/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/genai-uni-students/genai_students.svg')
main.save('/Users/alonso/Desktop/LSE/GROWTH LAB/ChartofthedayRepo/genai-uni-students/genai_students.png', dpi=300)
