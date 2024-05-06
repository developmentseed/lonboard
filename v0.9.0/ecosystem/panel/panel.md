# Panel

[Panel](https://panel.holoviz.org/) is a tool to build interactive web applications and dashboards using Python code.

Panel [has been reported to work](https://github.com/developmentseed/lonboard/issues/262) with Lonboard. However, it appears that Panel [does not support reactive updates](https://github.com/holoviz/panel/issues/5921) in the same way that [Shiny](./shiny.md) does, so the map will necessarily be recreated from scratch on every update.

## Example

This example was written by [@MarcSkovMadsen](https://github.com/MarcSkovMadsen) in [issue #262](https://github.com/developmentseed/lonboard/issues/262).

```py
"""Panel data app based on https://developmentseed.org/lonboard/latest/examples/north-america-roads/"""
# pip install panel colorcet ipywidgets_bokeh geopandas palettable lonboard
import colorcet as cc
import geopandas as gpd

from lonboard import Map, PathLayer
from lonboard.colormap import apply_continuous_cmap
from palettable.palette import Palette

import panel as pn

url = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_roads_north_america.zip"
path = "ne_10m_roads_north_america.zip"

try:
    gdf = pn.state.as_cached(
        "ne_10m_roads_north_america", gpd.read_file, filename=path, engine="pyogrio"
    )
except:
    gdf = pn.state.as_cached(
        "ne_10m_roads_north_america", gpd.read_file, filename=url, engine="pyogrio"
    )

state_options = sorted(state for state in gdf["state"].unique() if state)


def to_rgb(hex: str) -> list:
    h = hex.strip("#")
    return list(int(h[i : i + 2], 16) for i in (0, 2, 4))


def to_palette(cmap) -> Palette:
    """Returns the ColorCet colormap as a palettable Palette"""
    colors = [to_rgb(item) for item in cmap]
    return Palette(name="colorcet", map_type="colorcet", colors=colors)


def create_map(state="California", cmap=cc.fire, alpha=0.8):
    palette = to_palette(cmap)
    data = gdf[gdf["state"] == state]
    layer = PathLayer.from_geopandas(data, width_min_pixels=0.8)
    normalized_scale_rank = (data["scalerank"] - 3) / 9
    layer.get_color = apply_continuous_cmap(normalized_scale_rank, palette, alpha=alpha)
    map_ = Map(layer, _height=650)
    return map_


description = """# lonboard

A Python library for **fast, interactive geospatial vector data visualization** in Jupyter (and Panel).

By utilizing new technologies like `GeoArrow` and `GeoParquet` in conjunction with GPU-based map rendering, lonboard aims to enable visualizing large geospatial datasets interactively through a simple interface."""


# THE PANEL APP
pn.extension("ipywidgets")
state = pn.widgets.Select(
    value="California",
    options=state_options,
    width=150,
    name="State",
    sizing_mode="stretch_width",
)
cmap = pn.widgets.ColorMap(
    value=cc.fire,
    options=cc.palette,
    ncols=3,
    swatch_width=100,
    name="cmap by Colorcet",
    sizing_mode="stretch_width",
)
alpha = pn.widgets.FloatSlider(
    value=0.8, start=0, end=1, name="Alpha", min_width=100, sizing_mode="stretch_width"
)
logo = pn.pane.Image(
    "https://github.com/developmentseed/lonboard/raw/main/assets/dalle-lonboard.jpg"
)
def title(state):
    return f"# North America Roads: {state}"

settings = pn.Column(state, cmap, alpha)
description = pn.Column(pn.pane.Markdown(description, margin=5), logo)
component = pn.Column(
    pn.bind(title, state=state),
    pn.panel(
        pn.bind(create_map, state=state, cmap=cmap, alpha=alpha.param.value_throttled),
        sizing_mode="stretch_both",
    ),
    sizing_mode="stretch_both",
)
pn.template.FastListTemplate(
    logo="https://panel.holoviz.org/_static/logo_horizontal_dark_theme.png",
    title="Works with LonBoard",
    main=[component],
    sidebar=[description, settings],
).servable()
```
