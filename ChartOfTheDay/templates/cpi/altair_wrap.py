import altair as alt, pandas as pd, os, json, subprocess
import vl_convert as vlc

class CustomChart:
    def __init__(self, data, theme='dark', start_date=None, end_date=None):
        # Filter data by date range if start_date and/or end_date is provided
        if start_date is not None:
            data = data[data['date'] >= start_date]
        if end_date is not None:
            data = data[data['date'] <= end_date]

        self.data = data.copy()  # Making a copy of the DataFrame after filtering
        self.chart = None
        self.title = ""
        self.subtitle = ""
        self.line_colour = '#e6224b'

        # Set the theme
        self.set_theme(theme)


    def set_theme(self, theme):
        dark = True if theme == 'dark' else False

        background = '#122b39' if dark else '#fff'
        detail = '#b4c8d8' if dark else '#122b39'
        line_colour = self.line_colour

        # set opacity for hex - https://gist.github.com/lopspower/03fb1cc0ac9f32ef38f4
        subtitle_colour = detail + 'E6'

        # Custom Theme Function
        def custom_theme():
            return {
                'config': {
                    'background': background,
                    'font': 'Circular Std',
                    'axisX': {
                        'labelColor': detail,
                        'tickColor': detail,
                        'domainColor': detail,
                        'domainOpacity': 0.5,
                        'grid': False,
                        'labelAngle': 0,
                        'tickCount': 10,
                        'tickOpacity': 0.5,
                        'title': None
                    },
                    'axisY': {
                        'labelColor': detail,
                        'tickColor': detail,
                        'domainColor': detail,
                        'gridColor': detail,
                        'gridDash': [1, 5],
                        'gridOpacity': 0.5,
                        'labelPadding': 5,
                        'tickCount': 8,
                        'tickOpacity': 0.5,
                        'ticks': False,
                        'title': '12-month percent change | Source: BLS via FRED',
                        'titleAlign': 'left',
                        'titleAngle': 0,
                        'titleBaseline': 'bottom',
                        'titleColor': detail,
                        'titleFontSize': 12,
                        'titleOpacity': 0.9,
                        'titleX': 0,
                        'titleY': -7,
                        'format': '%'
                    },
                    'line': {
                        'color': line_colour
                    },
                    'view': {
                        'stroke': None,
                        'continuousWidth':350,
                        'continuousHeight':280
                    },
                    'title': {
                        'anchor': 'start',
                        'dx': 24,
                        'fontSize': 12,
                        'subtitleFontSize': 12,
                        'color': detail,
                        'subtitleColor': subtitle_colour,
                        'subtitlePadding': 4,
                        "offset": -1
                    }
                }
            }

        # Registering and enabling the custom theme
        alt.themes.register('custom_theme', custom_theme)
        alt.themes.enable('custom_theme')

        # set `detail` colour globally so we can access it in other methods
        self.detail = detail


    def create_line_chart(self, x, y, title="", subtitle="", y_format="%"):
        # Creating a line chart
        self.chart = alt.Chart(self.data).mark_line().encode(
            x=x,
            y=y
        )

        # Check if the data is in percentage scale (0-100) and adjust if necessary
        if y_format == "%" and self.data[y].max() > 1:
            self.data[y] = self.data[y] / 100



        last_point = self.data.loc[self.data[x].astype('datetime64[ns]').idxmax()].copy()

        
        # # Always adding a point to the final data point
        # last_point = self.data.loc[self.data[x].astype('datetime64').idxmax()].copy()
        point = alt.Chart(pd.DataFrame([last_point])).mark_point(
            color=self.line_colour,
            filled=True,
            size=60,
            opacity=0.9
        ).encode(
            x=alt.X(x),
            y=alt.Y(y)
        )
        self.chart += point
        
        # Adding text to the final data point
        text_value = point.mark_text(
            align='left',
            baseline='middle',
            dx=7,
            dy=0,
            fontSize=14,
            color=self.detail
            
        ).encode(
            text=alt.Text(y, format=".1%")
        )
        self.chart += text_value
        
        # Adding month text if the data is monthly
        date_diffs = self.data[x].sort_values().diff().dropna().dt.days
        # calculated the difference in days between consecutive dates and checked if all differences are between 25 and 35 days (approximately one month). If this condition is met, the month text is added to the chart.
        if all(25 < diff < 35 for diff in date_diffs):
            text_month = point.mark_text(
                align='left',
                baseline='middle',
                dx=7,
                dy=-16,
                fontSize=14,
                color=self.detail
            ).encode(
                text=alt.Text(x, format="%B")
            )
            self.chart += text_month

        # Adding title and subtitle
        self.title = title
        self.subtitle = subtitle
        self.chart = self.chart.properties(
            title={
                "text": self.title,
                "subtitle": self.subtitle
            }
        )
        return self

    def display(self):
        return self.chart.display()
    

    def save(self, path, name, width=350, height=280):
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Convert chart to dictionary and modify width and height
        chart_dict = self.chart.to_dict()
        chart_dict['width'] = width
        chart_dict['height'] = height

        # Convert the dictionary back to JSON
        vega_spec = json.dumps(chart_dict, indent=2)

        # Save as JSON
        json_path = os.path.join(path, f'{name}.json')
        with open(json_path, 'w') as f:
            f.write(vega_spec)

        # # Convert JSON to PNG using vl2png
        png_path = os.path.join(path, f'{name}.png')
        # cmd = f'vl2png {json_path} {png_path}'
        # /Users/joshhellings/miniforge3/envs/datasci
        # subprocess.run(cmd, shell=True, check=True)

        png_data = vlc.vegalite_to_png(vl_spec=vega_spec, scale=2)
        with open(png_path, "wb") as f:
            f.write(png_data)