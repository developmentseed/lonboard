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
    gdf = gpd.read_file(gpd.datasets.get_path("naturalearth_cities"))
    return ScatterplotLayer.from_geopandas(gdf, radius_min_pixels=2)


@render_widget
def map():
    return Map([])


@reactive.effect
def set_fill_color():
    layer.widget.get_fill_color = colors[input.color_select()]
