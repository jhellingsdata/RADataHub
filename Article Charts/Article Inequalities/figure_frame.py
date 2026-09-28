"""Title, subtitle and source block shared by the article figures.

    framed(chart, title, subtitle, source) -> chart with the title and
    subtitle above and the source line(s) below, left-aligned, in eco_style ink.

Pass configure_* calls on the returned chart, not on the input: Vega-Lite only
accepts config at the top level.
"""

import altair as alt
import pandas as pd

import eco_style

FONT = "Circular Std"
INK = eco_style.pallete["domain"]


def framed(chart, title, subtitle, source, source_width=400):
    src = alt.Chart(pd.DataFrame({"t": [source]})).mark_text(
        font=FONT, fontSize=11, color=INK, opacity=0.9,
        align="left", baseline="top", lineBreak="\n", lineHeight=14,
    ).encode(x=alt.value(0), y=alt.value(0), text="t:N").properties(
        width=source_width, height=14 * (source.count("\n") + 1))
    return alt.vconcat(chart, src, spacing=18).properties(
        title=alt.TitleParams(
            title, subtitle=subtitle, anchor="start", offset=18,
            font=FONT, fontSize=14, fontWeight=600, color=INK,
            subtitleFont=FONT, subtitleFontSize=11, subtitleColor=INK, subtitlePadding=6,
        ),
    )
