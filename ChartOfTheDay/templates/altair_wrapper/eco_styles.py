import altair as alt    # for charts
import pandas as pd     # for data wrangling
import vl_convert as vlc    # for saving Altair charts
import country_converter as coco    # for converting between country codes <-> country names

####### USAGE #######
# import sys, importlib
# sys.path.append("..")
# import alt_style

# importlib.reload(alt_style)
# styles = alt_style.EcoStyles()
# styles.register_and_enable_theme()


class EcoStyles:
    def __init__(self) -> None:
    
        # Remove Altair warning about max 5000 rows
        alt.data_transformers.disable_max_rows()

        self.eco_colours = {
            "red": "#e6224b",                       # light red
            "blue-light": "#179fdb",                # bright blue
            "blue-dark": "#122b39",                 # dark blue
            "yellow": "#f4c245",                    # light yellow
            "orange": "#eb5c2e",                    # orange
            "turquoise": "#36b7b4",                 # turquoise
        }

        self.palette = {
            "light": {
                "Other_3": "#d6d4d4",             # light gray
                "deemphasise_color": "#B4B4B4",   # gray
                "dark_grey": "#596870",           # dark gray
                "Deemphasise_Discrete": "#182a38",# dark bluish-gray
                "Deemphasise_Continuous": "#182a3833", # dark bluish-gray with transparency
                "accent": "#179fdb",              # bright blue (same as GBR)
                "text": "#122b39",                # dark blue (same as FRA)
                "domain": "#122b39",              # dark blue (same as FRA)
                "non-uk": "#a8c0de",              # light blue / grey
                "country-group": "#eb5c2e",       # 
                "background": "#fff",
            },
            "dark": {
                "Other_3": "#d6d4d4",             # light gray
                "deemphasise_color": "#B4B4B4",   # gray
                "dark_grey": "#596870",           # dark gray
                "Deemphasise_Discrete": "#182a38",# dark bluish-gray
                "Deemphasise_Continuous": "#182a3833", # dark bluish-gray with transparency
                "accent": "#179fdb",              # bright blue (same as GBR)
                "text": '#b4c8d8',              # dark blue (same as FRA)
                "domain": "#b4c8d8",              # dark blue (same as FRA)
                "non-uk": "#a8c0de",              # light blue / grey
                "country-group": "#eb5c2e",       # 
                "background": "#122b39",          
            },
            "light-transparent": {
                "background": None,               # transparent
            },
            "dark-transparent": {
                "text": "#fff",
                "background": None,               # transparent
            },
        }

        # # Define country group identifiers that may appear in datasets along with ISO country codes
        # self.country_groups = ['OECD', 'OECDE', 'EU27', 'EU27_2020', 'EA19', 'G-7', 'G7']

        # Define custom dictionary with country group identifiers and their corresponding country codes
        # This can be passed to country_converter when converting a column of ISO codes to country names to avoid 'not found'
        self.country_groups = {
            'OECD': 'OECD',
            'OECDE': 'OECD-Europe',
            'EU27': 'EU27',
            'EU27_2020': 'EU27 (2020)',
            'EA19': 'EA19',
            'G-7': 'G7',
            'G7': 'G7'
        }

    def get_country_groups_list(self, type) -> list:
        """
        Return a list of country group identifiers
        """
        return self.country_groups.keys()

    def get_country_groups_dict(self) -> dict:
        """
        Return a dictionary of country group identifiers and their corresponding country codes
        """
        return self.country_groups


    # def add_colour(self, df: pd.DataFrame, country_column: str='ISO3', colour_override: dict=None) -> pd.DataFrame:
    #     """
    #     Add colour columns 'color-bar' and 'color-line' to a dataframe. The colours are based on the country code.
    #     """
    #     palette = self.palette.copy()

    #     # If a dictionary of colour overrides is provided, override the default palette
    #     if colour_override:
    #         palette.update(colour_override)

    #     # Add 'color-bar' column to highlight UK & any country group for bar charts
    #     df['color-bar'] = df[country_column].apply(
    #         lambda x: palette.get('GBR-bar') if x == 'GBR' else
    #         palette.get('country-group') if x in self.country_groups else
    #         palette.get('non-uk')
    #     )

    #     # Add 'color-line' column for line charts
    #     df['color-line'] = df[country_column].apply(
    #         lambda x: palette.get(x, palette.get('domain'))
    #     )

    #     return df

    def custom_theme(self, dark_mode=False):

        if dark_mode:
            theme = 'dark'
        else:
            theme = 'light'


        background = self.palette.get(theme).get('background')
        domain = self.palette.get(theme).get('domain')
        text = self.palette.get(theme).get('text')
        subtitle_colour = text + 'E6'


        # Define chart theme, with axis options set based on axis type
        # "If multiple axis config blocks apply to a single axis, type-based options take precedence over orientation-based options, which in turn take precedence over general options."
        return {
            'config': {
                'background': background,
                'font': 'Circular Std',
                'text': {
                    'color': text,
                    'font': 'Circular Std',
                    'align': 'left',
                    'dx': 7,
                    'dy': 0,
                    'fontSize': 11
                },
                'view': {
                    'stroke': None,
                    'continuousWidth': 350,
                    'continuousHeight': 280,
                    'discreteWidth': 400,
                    'discreteHeight': 300,
                },
                'bar': {
                    'color': self.eco_colours['blue-light']
                },
                'line': {
                    'color': self.eco_colours['red']
                },
                'rule': {
                    'color': domain,
                },
                'point': {
                    'filled': True,
                    'size': 80,
                    'color': self.eco_colours['red'],
                    'opacity': 0.95
                },
                'geoshape': {
                    'stroke': 'white',
                    'strokeWidth': 0.3
                },
                # Set shared axis options
                'axis': {
                    'labelColor': text,
                    'labelFontSize': 11,
                    'labelFont': 'Circular Std',
                    'tickColor': text,
                    'tickOpacity': 0.5,
                    'domainColor': domain,
                    'domainOpacity': 0.5,
                    'gridColor': domain,
                    'gridDash': [2, 2],
                    'gridOpacity': 0.5,
                    'title': None,
                    'titleColor': text,
                    'tickSize': 4
                },
                'axisXDiscrete': {
                    'grid': False,
                    'labelAngle': 0,
                    'tickCount': 10,
                    'tickOpacity': 0.5,
                    'title': None 
                },
                'axisYDiscrete': {
                    'ticks': False,
                    'labelPadding': 5
                },
                'axisXTemporal': {
                    'grid': False,
                    'ticks': True,

                },
                'axisXQuantitative': {
                    'grid': True,
                    
                },
                'axisYQuantitative': {
                    'gridColor': domain,
                    'gridDash': [1, 5],
                    'gridOpacity': 0.5,
                    'ticks': False,
                    'labelPadding': 5,
                    'tickCount': 8
                },
                'title': {
                    'color': text,
                    'subtitleColor': subtitle_colour,
                    'font': 'Circular Std',
                    'subtitleFont': 'Circular Std',
                    'anchor': 'start',
                    'frame': 'group',
                    'fontSize': 14,
                    'subtitleFontSize': 12,
                    'subtitlePadding': 4,
                    "offset": 0
                },
                'legend': {
                    'titleColor': text,
                    'labelColor': text
                }
            }
        }
    
    def register_and_enable_theme(self, theme_name: str="cotd", dark_mode: bool=False):
        """
        Registers and enables the custom theme.
        @param dark_mode: True for dark mode, False for light mode
        """
        # Define a wrapper function that calls custom_theme with the dark_mode parameter
        def theme_function():
            return self.custom_theme(dark_mode)
        # Why do we need this?
        # The alt.themes.register() function does not expect the configuration dictionary itself; it expects a callable — a function without the parentheses, which means "here's a reference to a function you can call," not "here's the result of a function call."
        alt.themes.register(theme_name, theme_function)
        alt.themes.enable(theme_name)

    def add_colour(self, df: pd.DataFrame, country_column: str, colour_override: dict=None) -> pd.DataFrame:
        """
        Add colour columns 'color-bar' and 'color-line' to a dataframe. The colours are based on the country code or country name.
        """
        palette = self.palette.copy()

        # If a dictionary of colour overrides is provided, override the default palette
        if colour_override:
            palette.update(colour_override)

        # Check if the country column contains ISO3 codes or full country names
        first_country = df[country_column].iloc[0]
        if len(first_country) != 3:  # Assuming it's a full country name
            df['ISO3'] = coco.convert(df[country_column].tolist(), to='ISO3')
            country_col_to_use = 'ISO3'
        else:
            country_col_to_use = country_column

        # Add 'color-bar' column to highlight UK & any country group for bar charts
        df['color-bar'] = df[country_col_to_use].apply(
            lambda x: palette.get('GBR-bar') if x == 'GBR' else
            palette.get('country-group') if x in self.country_groups else
            palette.get('non-uk')
        )

        # Add 'color-line' column for line charts
        df['color-line'] = df[country_col_to_use].apply(
            lambda x: palette.get(x, palette.get('domain'))
        )

        return df



    def save(self, chart, path, name, width=350, height=280, svg=False):
        """Save an Altair chart to a specified path in both JSON and PNG formats."""
        import os, json, vl_convert as vlc

        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Convert chart to dictionary and modify width and height
        chart_dict = chart.to_dict()
        chart_dict['width'] = width
        chart_dict['height'] = height

        # Convert the dictionary back to JSON
        vega_spec = json.dumps(chart_dict, indent=2)

        # Save as JSON
        json_path = os.path.join(path, f'{name}.json')
        with open(json_path, 'w') as f:
            f.write(vega_spec)

        # Convert JSON to PNG using vl2png
        png_path = os.path.join(path, f'{name}.png')
        png_data = vlc.vegalite_to_png(vl_spec=vega_spec, scale=2)
        with open(png_path, "wb") as f:
            f.write(png_data)

        if svg:
            # Convert JSON to SVG using vl2svg
            svg_path = os.path.join(path, f'{name}.svg')
            svg_data = vlc.vegalite_to_svg(vl_spec=vega_spec)
            with open(svg_path, "w") as f:
                f.write(svg_data)