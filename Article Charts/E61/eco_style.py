import altair as alt
import numpy as np

pallete = {
    "shadow": "rgba(24, 42, 56, 0.1)",
    "nominal_1": "#179fdb",
    "nominal_2": "#e6224b",
    "nominal_3": "#f4c245",
    "nominal_4": "#122b39",
    "nominal_5": "#eb5c2e",
    "nominal_6": "#36b7b4",
    "Other_3":"#d6d4d4",
    #"Deemphasize_Discrete": "rgb(173, 195, 215)",
    "Deemphasize_Discrete": "rgba(24, 42, 56)",
    "Deemphasize_Other": "rgba(93, 115, 102, 1)",
    "Deemphasize_Continuous": "rgba(24, 42, 56, 0.2)",
    "accent": "#179fdb",
    "domain": "#122b39",
    "bar": {
        "accent_1": "#122b39",
        "other" : "rgb(168, 192, 222)",
        "accent_2" : "#eb5c2e"
    }
}

pallete["GBR"] = pallete["nominal_1"]
pallete["USA"] = pallete["nominal_2"]
pallete["DEU"] = pallete["nominal_3"]
pallete["FRA"] = pallete["nominal_4"]
pallete["Other_1"] = pallete["nominal_5"]
pallete["Other_2"] = pallete["nominal_6"]

pallete["UK"] = pallete["GBR"]
pallete["United Kingdom"] = pallete["GBR"]
pallete["United States"] = pallete["USA"]
pallete["Germany"] = pallete["DEU"]
pallete["France"] = pallete["FRA"]

def report():
  return {"config": {
    "font": "Circular Std",
    "mark" : {
      "line": {
        "interpolate": "linear",
      }
    },
    "view" : {
      "stroke": "transparent",
      "width": 400,
      "height": 300
    },
    "range": {
      "category" : [
        pallete["nominal_1"],
        pallete["nominal_2"],
        pallete["nominal_3"],
        pallete["nominal_4"],
        pallete["nominal_5"],
        pallete["nominal_6"],
      ],
      "diverging" : ["#E6224B","#E54753","#C9C9C9","#179FDB","#122B39"],
      "heatmap" : ["#C9C9C9","#179FDB","#0063AF","#122B39"],
      "ordinal" : ["#00A767","#36B7B4","#179FDB","#0063AF","#243B5A"]
    },
    "axisX": {
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
    },
    "axisY": {
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
  }}

alt.themes.register('report', report)        

def light():
  return {"config": {
    "font": "Circular Std",
    "mark" : {
      "line": {
        "interpolate": "monotone",
      }
    },
    "view" : {
      "stroke": "transparent",
      "width": 400,
      "height": 300
    },
    "range": {
      "category" : ["#36B7B4","#E6224B","#F4C245","#0063AF","#00A767","#179FDB","#EB5C2E"],
      "diverging" : ["#E6224B","#E54753","#C9C9C9","#179FDB","#122B39"],
      "heatmap" : ["#C9C9C9","#179FDB","#0063AF","#122B39"],
      "ordinal" : ["#00A767","#36B7B4","#179FDB","#0063AF","#243B5A"]
    },
    "axisX": {
      "domainColor": "#676A86",
      "domainOpacity": 0.5,
      "grid": False,
      "labelAngle": 0,
      "labelColor": "#676A86",
      "labelOpacity": 0.7,
      "orient": "bottom",
      "tickColor": "#676A86",
      "tickCount": 10,
      "tickOpacity": 0.5,
      "title" : False,
      "titleAlign": "center",
      "titleAnchor": "middle",
      "titleColor": "#676A86",
      "titleFontSize": 12,
      "titleOpacity": 0.8,
      "titleY": -15
    },
    "axisY": {
      "domainColor": "#676A86",
      "domainOpacity": 0.5,
      "gridColor": "#676A86",
      "gridDash": [1, 5],
      "gridOpacity": 0.5,
      "labelColor": "#676A86",
      "labelOpacity": 0.7,
      "labelPadding": 5,
      "tickColor": "#676A86",
      "tickCount": 8,
      "tickOpacity": 0.5,
      "ticks": False,
      "titleAlign": "left",
      "titleAngle": 0,
      "titleBaseline": "bottom",
      "titleColor": "#676A86",
      "titleFontSize": 12,
      "titleOpacity": 0.8,
      "titleX": 0,
      "titleY": -7
    }
  }}

alt.themes.register('light', light)

def dark():
    return {"config": {
        "background": "#122B39",
        "font": "Circular Std",
        "title": {
            "color": "#b4c8d8",
            "fontSize": 14,
            "fontWeight": 400,
        },
        "mark": {
            "line": {
                "interpolate": "monotone",
            }
        },
        "view": {
            "stroke": "transparent",
            "width": 400,
            "height": 300
        },
        "range": {
            "category": ["#36B7B4", "#E6224B", "#F4C245", "#0063AF", "#00A767", "#179FDB", "#EB5C2E"],
            "diverging": ["#E6224B", "#E54753", "#C9C9C9", "#179FDB", "#122B39"],
            "heatmap": ["#C9C9C9", "#179FDB", "#0063AF", "#122B39"],
            "ordinal": ["#00A767", "#36B7B4", "#179FDB", "#0063AF", "#243B5A"]
        },
        "axisX": {
            "domainColor": "#b4c8d8",
            "domainOpacity": 0.5,
            "grid": False,
            "labelAngle": 0,
            "labelColor": "#b4c8d8",
                "labelOpacity": 0.7,
                "orient": "bottom",
                "tickColor": "#b4c8d8",
                "tickCount": 10,
                "tickOpacity": 0.5,
                "title": "",
                "titleAlign": "center",
                "titleAnchor": "middle",
                "titleColor": "#b4c8d8",
                "titleFontSize": 12,
                "titleOpacity": 0.8,
                "titleX": 207,
                "titleY": -15
        },
        "axisY": {
            "domainColor": "#b4c8d8",
            "domainOpacity": 0.5,
            "format": ".0f",
            "gridColor": "#b4c8d8",
            "gridDash": [
                1,
                5
            ],
            "gridOpacity": 0.5,
            "labelColor": "#b4c8d8",
            "labelOpacity": 0.7,
            "labelPadding": 5,
            "tickColor": "#b4c8d8",
            "tickCount": 8,
            "tickOpacity": 0.5,
            "ticks": False,
            "title": "FAO price index",
            "titleAlign": "left",
            "titleAngle": 0,
            "titleBaseline": "bottom",
            "titleColor": "#b4c8d8",
            "titleFontSize": 12,
            "titleOpacity": 0.8,
            "titleX": 0,
            "titleY": -7

        }
    }}


alt.themes.register('dark', dark)