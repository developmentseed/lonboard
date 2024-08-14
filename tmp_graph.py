import altair as alt
from altair import datum

import pandas as pd

data = [
    ["fiona", 232, "FlatGeobuf"],
    ["pyogrio", 108, "FlatGeobuf"],
    ["GeoArrow", 10, "FlatGeobuf"],
    ["fiona", 227, "GeoPackage"],
    ["pyogrio", 103, "GeoPackage"],
    ["GeoArrow", 10, "GeoPackage"],
]

# Create the pandas DataFrame
df = pd.DataFrame(data, columns=["Method", "Read time (s)", "File Format"])

gp_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        alt.X("Read time (s)"),
        alt.Y("File Format", axis=alt.Axis(grid=True)),
        alt.Color("Method"),
        yOffset="Method",
    )
)
gp_chart = gp_chart.properties(
    title="Reading geospatial data to a GeoPandas GeoDataFrame",
    # width=alt.Step(80),  # Adjust the width of bars if needed
)

gp_chart
gp_chart.save("chart.png", ppi=200, scale_factor=10)
!pip install vl-convert-python



# Example data
data = pd.DataFrame({"Category": ["A", "B", "C", "D"], "Value": [20, 35, 30, 25]})

# Create the Altair chart
chart = alt.Chart(data).mark_bar().encode(x="Category", y="Value")

# Optionally, add titles and adjust appearance
chart = chart.properties(
    title="Bar Chart Example",
    width=alt.Step(80),  # Adjust the width of bars if needed
)

# Show the chart
chart
