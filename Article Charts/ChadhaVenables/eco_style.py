import altair as alt

deemphasize_color = "#B4B4B4"

OECD_iso3 = [
  "AUS",
  "AUT",
  "BEL",
  "CAN",
  "CHL",
  "COL",
  "CRI",
  "CZE",
  "DNK",
  "EST",
  "FIN",
  "FRA",
  "DEU",
  "GRC",
  "HUN",
  "ISL",
  "IRL",
  "ISR",
  "ITA",
  "JPN",
  "KOR",
  "LVA",
  "LTU",
  "LUX",
  "MEX",
  "NLD",
  "NZL",
  "NOR",
  "POL",
  "PRT",
  "SVK",
  "SVN",
  "ESP",
  "SWE",
  "CHE",
  "TUR",
  "GBR",
  "USA"
]


pallete = {
    "shadow": "rgba(24, 42, 56, 0.1)",
    "USA": "#e6224b",
    "GBR": "#179fdb",
    "DEU": "#f4c245",
    "FRA": "#122b39",
    "Other_1": "#eb5c2e",
    "Other_2": "#36b7b4",
    "Other_3":"#d6d4d4",
    #"Deemphasize_Discrete": "rgb(173, 195, 215)",
    "Deemphasize_Discrete": "rgba(24, 42, 56)",
    "Deemphasize_Other": "rgba(93, 115, 102, 1)",
    "Deemphasize_Continuous": "rgba(24, 42, 56, 0.2)",
    "accent": "#179fdb",
    "domain": "#122b39",
    "bar": {
        "accent_1": "#122b39",
        "other" : "#a8c0de",
        "accent_2" : "#eb5c2e"
    }
}

pallete["UK"] = pallete["GBR"]
pallete["United Kingdom"] = pallete["GBR"]
pallete["United States"] = pallete["USA"]
pallete["Germany"] = pallete["DEU"]
pallete["France"] = pallete["FRA"]


def x_axis(override_args={}):
    # Default axis configuration
    default_args = {
      "labelColor": pallete["domain"],
      "tickColor": pallete["domain"],
      "domainColor": pallete["domain"],
      "domainOpacity": 0.5,
      "gridOpacity": 0,
      "labelFont": "Circular Std",
      "labelAngle": 0,
      "labelAlign": "center",
      "labelFontSize": 11,
        "labelPadding": 5,
      "tickCount": 10,
      "tickSize": 0,
      "title": ""
    }
    
    # Update default arguments with any overriding arguments
    axis_args = {**default_args, **override_args}
    
    # Create and return an alt.Axis object
    return alt.Axis(**axis_args)


def y_axis(override_args={}):
    # Default axis configuration
    default_args = {
      "labelColor": pallete["domain"],
      "labelFont": "Circular Std",
      "tickColor": pallete["domain"],
      "domainColor": pallete["domain"],
      "gridColor": pallete["domain"],
      "gridDash": [
        1,
        5
      ],
      "gridOpacity": 0.5,
      "labelPadding": 5,
      "labelFontSize": 11,
      "domainOpacity": 0.5,
      "tickSize": 0,
      "title": None,
      "titleAlign": "left",
      "titleAngle": 0,
      "titleBaseline": "bottom",
      "titleColor": pallete["domain"],
      "titleOpacity": 0.9,
      "titleX": 0,
      "titleY": -7
    }
    
    # Update default arguments with any overriding arguments
    axis_args = {**default_args, **override_args}
    
    # Create and return an alt.Axis object
    return alt.Axis(**axis_args)

def color_scale(override_args={}, other_1 = "", other_2 = "", other_3="OTHER"):
    # Default color scale configuration
    default_args = {
        "domain": ["GBR", "USA", "DEU", "FRA", other_1, other_2, other_3],
        "range": [pallete["GBR"], pallete["USA"], pallete["DEU"], pallete["FRA"], pallete["Other_1"], pallete["Other_2"], pallete["Other_3"], pallete["Deemphasize_Discrete"], pallete["Deemphasize_Continuous"]],
    }

    # Update default arguments with any overriding arguments
    scale_args = {**default_args, **override_args}

    # Create and return an alt.Scale object
    return alt.Scale(**scale_args)

def properties(override_args={}):
    default_args= {
        "width":400,
        "height":300,
    }
    chart_args = {**default_args, **override_args}
    return chart_args

def title(title, subtitle, override_args={}):
    # Default title configuration
    default_args = {
        "font": "Circular Std",
        "subtitleFont": "Circular Std",
        "text": title,
        "subtitle": subtitle,
        "anchor": "start",
        "dx": 0,
        "fontSize": 14,
        "subtitleFontSize": 12,
        "color": "rgb(24,42,56)", #pallete["domain"],
        "subtitleColor": "rgba(24,42,56,0.8)", #"#122b39E6",
        "subtitlePadding": 4,
        "offset": -1
    }

    # Update default arguments with any overriding arguments
    title_args = {**default_args, **override_args}
    
    # Create and return an alt.TitleParams object
    return alt.TitleParams(**title_args)

def properties(override_args={}):
    default_args= {
        "width":400,
        "height":300,
    }
    chart_args = {**default_args, **override_args}
    return chart_args

def color_legend(override_args={}):
    default_args= {
        'orient': 'none',
        'title': '',
        'labelFont': "Circular Std",
        'direction': 'horizontal',
        'labelColor': '#676A86',
        'legendY': -15,
    }
    legend_args = {**default_args, **override_args}
    return alt.Legend(**legend_args)

def line_label(override_args={}):
    default_args= {
        'align':'left',
        'fontSize': 11,
        'baseline': 'middle',
        'dx': 5,
        'font': 'Circular Std',
    }
    label_args = {**default_args, **override_args}
    return label_args