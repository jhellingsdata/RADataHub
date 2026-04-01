import altair as alt
import pandas as pd
from ecostyles import EcoStyles

styles = EcoStyles()
styles.register_and_enable_theme("article")

df = pd.read_csv("../data/Flourish-data_data.csv")
df = df.rename(columns={"Column1": "Year"})

# Convert to millions
value_cols = ["No level", "Below level 2", "Level 2", "Skills for Life/English/maths", "Level 3", "Level 4+"]
for col in value_cols:
    df[col] = df[col] / 1_000_000

# Melt to long format
long_df = df.melt(id_vars="Year", value_vars=value_cols, var_name="Category", value_name="Qualifications")

# Add numeric order for stacking (bottom=0 to top=5)
order_map = {cat: i for i, cat in enumerate(["No level", "Below level 2", "Level 2", "Skills for Life/English/maths", "Level 3", "Level 4+"])}
long_df["order"] = long_df["Category"].map(order_map)

# Ordered bottom to top as in original chart
category_order = ["No level", "Below level 2", "Level 2", "Skills for Life/English/maths", "Level 3", "Level 4+"]

# Colors matching the original chart
color_scale = alt.Scale(
    domain=category_order,
    range=["#4CAF50", "#F5C518", "#1C3A3A", "#7B2D5E", "#E8612C", "#3F6FBF"],
)

chart = (
    alt.Chart(long_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "Year:N",
            title="Academic year (starting in August)",
            sort=None,
            axis=alt.Axis(labelAngle=-45),
        ),
        y=alt.Y(
            "Qualifications:Q",
            title="Number of qualifications started (millions)",
            stack="zero",
        ),
        color=alt.Color(
            "Category:N",
            title=None,
            sort=category_order,
            scale=color_scale,
            legend=alt.Legend(orient="top", columns=6, labelLimit=200),
        ),
        order=alt.Order("order:Q"),
        tooltip=[
            alt.Tooltip("Year:N", title="Year"),
            alt.Tooltip("Category:N", title="Category"),
            alt.Tooltip("Qualifications:Q", title="Qualifications (millions)", format=".2f"),
        ],
    )
    .properties(
        width=800,
        height=450,
        title=alt.TitleParams(
            text="Participation in classroom-based further education qualifications by adults (19+) in England",
            fontSize=15,
            anchor="start",
        ),
    )
)

chart.save("further_education.png", scale_factor=2)
print("Saved further_education.png")
