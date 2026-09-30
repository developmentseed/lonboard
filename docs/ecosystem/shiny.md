# Shiny

[Shiny](https://shiny.posit.co/py/) is a tool to build interactive web applications and dashboards using Python code. Shiny [integrates with Jupyter Widgets](https://shiny.posit.co/py/docs/jupyter-widgets.html), which means that Lonboard is supported out-of-the-box.

Pay attention to the ["Efficient updates"](https://shiny.posit.co/py/docs/jupyter-widgets.html#efficient-updates) section of the Shiny documentation. This is the most efficient way to create a reactive map. Take care to not recreate the `Map` widget from scratch on updates, as that will send data from Python to the browser anew.


## Example

![](../assets/shiny-example.gif)

```py
import geodatasets
import geopandas as gpd
from shiny import reactive
from shiny.express import input, ui
from shinywidgets import render_widget

from lonboard import Map, ScatterplotLayer

colors = {
    "Red": [200, 0, 0],
    "Green": [0, 200, 0],
    "Blue": [0, 0, 200],
}

ui.input_select("color_select", "Color", choices=list(colors.keys()))


@render_widget
def layer():
    gdf = gpd.read_file(geodatasets.get_path("naturalearth.cities"))
    return ScatterplotLayer.from_geopandas(gdf, radius_min_pixels=2)


@render_widget
def map():
    return Map(layer.widget)


@reactive.effect
def set_fill_color():
    layer.widget.get_fill_color = colors[input.color_select()]
```
