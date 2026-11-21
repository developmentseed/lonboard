import altair as alt
from vega_datasets import data

source = data.stocks()

source

alt.Chart(source).mark_line().encode(
    x="date:T",
    y="price:Q",
    color="symbol:N",
)

import pandas as pd

data = [
    ["ipyleaflet", 10_000, 1.16],
    ["ipyleaflet", 50_000, 5.3],
    ["ipyleaflet", 100_000, 12.4],
    ["ipyleaflet", 150_000, 17.43],
    ["ipyleaflet", 200_000, 24.84],
    ["ipyleaflet", 300_000, 50.29],
    ["pydeck", 10_000, 0.96],
    ["pydeck", 50_000, 3.75],
    ["pydeck", 100_000, 6.52],
    ["pydeck", 250_000, 17.79],
    ["pydeck", 500_000, 35.63],
    ["pydeck", 750_000, 55.1],
    ["pydeck", 1_000_000, 74.25],
    ["lonboard", 100_000, 0.55],
    ["lonboard", 500_000, 0.71],
    ["lonboard", 1_000_000, 0.92],
    ["lonboard", 2_000_000, 1.25],
    ["lonboard", 3_000_000, 1.67],
    ["lonboard", 5_000_000, 3.32],
    ["lonboard", 7_500_000, 4.33],
    ["lonboard", 10_000_000, 5.61],
    ["lonboard", 15_000_000, 7.95],
]

columns = ["Library", "# of rows", "Render time (s)"]
df = pd.DataFrame(data, columns=columns)

color_scale = alt.Scale(
    domain=["ipyleaflet", "pydeck"],  # , "lonboard"],
    range=["#4e79a7", "#f28e2b"],  # , "#59A14F"],
)


chart = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=f"{columns[1]}:Q",
        y=f"{columns[2]}:Q",
        color=alt.Color(shorthand=f"{columns[0]}:N", scale=color_scale),
    )
)
chart = chart.properties(
    title="Time to render interactive map by number of points",
    # width=alt.Step(80),  # Adjust the width of bars if needed
)
chart
# chart.save("ipyleaflet.png", ppi=200, scale_factor=10)
chart.save("ipyleaflet_pydeck.png", ppi=200, scale_factor=10)
# !pip install vl-convert-python
