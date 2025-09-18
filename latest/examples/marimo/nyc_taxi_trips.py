# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "datafusion",
#     "geodatafusion",
#     "lonboard>=0.12.1",
#     "matplotlib",
#     "palettable",
#     "pyarrow",
#     "requests==2.32.5",
#     "tqdm==4.67.1",
# ]
# ///

import marimo

__generated_with = "0.15.3"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(
        r"""
    # NYC Taxi Trips in [`Marimo`][Marimo] with [`GeoDataFusion`][datafusion-geo]

    [Marimo]: https://docs.marimo.io/
    [datafusion-geo]: https://github.com/datafusion-contrib/datafusion-geo

    This is a basic example to use the [DataFusion Python API](https://datafusion.apache.org/python/) with the [GeoDataFusion extension][datafusion-geo] to filter and visualize Parquet data.

    This example is best viewed in a local instance of Marimo. [Download this file](https://github.com/developmentseed/lonboard/blob/main/examples/marimo/nyc_taxi_trips.py) then start a local Marimo session with:

    ```
    uv run marimo edit nyc_taxi_trips.py --sandbox
    ```

    <video controls autoplay loop>
        <source src="https://github.com/user-attachments/assets/77f6a2b3-80c9-4524-8be2-79152746da1d" type="video/mp4">
    </video>
    """
    )
    return


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import requests
    from arro3.core import Table
    from datafusion import SessionContext
    from geodatafusion import register_all
    from matplotlib.colors import Normalize
    from palettable.colorbrewer.diverging import BrBG_10
    from tqdm.notebook import tqdm

    from lonboard import Map, ScatterplotLayer
    from lonboard.colormap import apply_continuous_cmap
    from lonboard.experimental import ArcLayer
    from lonboard.layer_extension import BrushingExtension
    return (
        ArcLayer,
        BrBG_10,
        BrushingExtension,
        Map,
        Normalize,
        Path,
        ScatterplotLayer,
        SessionContext,
        Table,
        apply_continuous_cmap,
        mo,
        register_all,
        requests,
        tqdm,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
    This example uses data from the [NYC Taxi & Limousine Commission (TLC) Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

    We'll first download a file from January 2010 to disk if it's not already downloaded. (We use data from January 2010 because some later files don't have raw longitude-latitude pickup and dropoff locations).
    """
    )
    return


@app.cell
def _(Path, requests, tqdm):
    def download_file_with_progress(url: str, filename: Path):
        """Downloads a file from a given URL and displays a progress bar."""
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get("content-length", 0))

        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=str(filename),
        ) as pbar:
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

    file_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2010-01.parquet"
    output_path = Path("yellow_tripdata_2010-01.parquet")

    if not output_path.exists():
        download_file_with_progress(file_url, output_path)
    return (output_path,)


@app.cell
def _(mo):
    mo.md(r"""Now we'll create the DataFusion `SessionContext`—the primary API for interacting with a Datafusion session—and register our spatial extension onto it.""")
    return


@app.cell
def _(SessionContext, output_path, register_all):
    ctx = SessionContext()
    register_all(ctx)
    ctx.register_parquet("trips", output_path)
    return (ctx,)


@app.cell
def _(mo):
    mo.md(
        r"""
    Next we'll initialize a bounding box to be used in a spatial intersection query in DataFusion.

    This bounding box can be overridden by drawing a bounding box on the map instance (click on the box in the top right of the map to start drawing a bounding box selection).
    """
    )
    return


@app.cell
def _(mo):
    get_bbox, set_bbox = mo.state([-74.258843, 40.476578, -73.700233, 40.91763])
    return get_bbox, set_bbox


@app.cell
def _(mo):
    mo.md(r"""Now we'll write and run our SQL command that we use to fetch data. This creates GeoArrow point columns named `pickup` and `dropoff`, then selects rows where the pickup is inside the above bounding box.""")
    return


@app.cell
def _(ctx, get_bbox):
    bbox = get_bbox()
    sql = """
        WITH trips_geo AS (
            SELECT
                *,
                ST_Point(pickup_longitude, pickup_latitude, 4326) as pickup,
                ST_Point(dropoff_longitude, dropoff_latitude, 4326) as dropoff
            FROM trips
        )
        SELECT *
        FROM trips_geo
        WHERE ST_Intersects(
                pickup,
                ST_MakeBox2D(
                    ST_Point({minx}, {miny}),
                    ST_Point({maxx}, {maxy})
                )
            )
        LIMIT 100000;
        """.format(minx=bbox[0], miny=bbox[1], maxx=bbox[2], maxy=bbox[3])
    df = ctx.sql(sql)
    df
    return (df,)


@app.cell
def _(mo):
    mo.md(r"""Now that we have our query, we can work to visualize this data on the map. We'll materialize this to an Arrow [`Table`](https://kylebarron.dev/arro3/latest/api/core/table/) so that we can apply transformations on the columns in Python. You could probably also do these transformations in SQL, but my Python skills are better than my SQL skills.""")
    return


@app.cell
def _(Table, df):
    table = Table.from_arrow(df)
    return (table,)


@app.cell
def _(mo):
    mo.md(r"""Now let's create colors for each row of the data. We'll use the [brown-blue-green](https://jiffyclub.github.io/palettable/colorbrewer/diverging/#brbg_10) colormap from `palettable`:""")
    return


@app.cell
def _(BrBG_10):
    BrBG_10.mpl_colormap
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    Next we need to normalize values from their source range to a range of 0-1 so that we can apply the colormap.

    We'll use the Matplotlib [`Normalize`](https://matplotlib.org/stable/api/_as_gen/matplotlib.colors.Normalize.html) helper, which applies linear normalization from a source range to `0-1`. Then Lonboard's [`apply_continuous_cmap`](https://developmentseed.org/lonboard/latest/api/colormap/#lonboard.colormap.apply_continuous_cmap) helps to apply those values onto the provided colormap.
    """
    )
    return


@app.cell
def _(BrBG_10, Normalize, apply_continuous_cmap, table):
    amount_normalizer = Normalize(1, 50, clip=True)
    normalized_total_amount = amount_normalizer(table["total_amount"])
    amount_color = apply_continuous_cmap(
        normalized_total_amount,
        BrBG_10,
        alpha=0.7,
    )
    return amount_color, normalized_total_amount


@app.cell
def _(mo):
    mo.md(r"""Now we're ready to construct our Lonboard layers for the map:""")
    return


@app.cell
def _(
    ArcLayer,
    BrushingExtension,
    ScatterplotLayer,
    amount_color,
    normalized_total_amount,
    table,
):
    pickup_layer = ScatterplotLayer(
        # There are two geometry columns in the input table, so we remove one of them
        table=table.select([name for name in table.column_names if name != "dropoff"]),
        get_fill_color=amount_color,
        get_radius=normalized_total_amount * 90,
        radius_units="meters",
        radius_min_pixels=0.1,
        auto_highlight=True,
        extensions=[BrushingExtension()],
    )
    arc_layer = ArcLayer(
        # We remove both geometry columns as they are passed separately below
        table=table.select(
            [name for name in table.column_names if name not in ["dropoff", "pickup"]]
        ),
        get_source_position=table["pickup"],
        get_target_position=table["dropoff"],
        get_source_color=amount_color,
        get_target_color=amount_color,
        get_width=table["trip_distance"],
        width_units="meters",
        width_min_pixels=0.2,
        opacity=0.1,
        auto_highlight=True,
        extensions=[BrushingExtension()],
    )
    return arc_layer, pickup_layer


@app.cell
def _(mo):
    mo.md(
        r"""
    Now we can plot our map! The colors of the arcs and points correspond to the total fare, while the width of the arc corresponds to the total distance of the trip.

    If you select a bounding box on the map (using the box icon on the top right) then that **bounding box will propagate back to the original SQL query**, limiting the amount of data loaded from the original Parquet file.

    Try toggling the buttons below to interact with the map.Toggle the button below to additionally apply the Lonboard [`BrushingExtension`](https://developmentseed.org/lonboard/latest/api/layer-extensions/brushing-extension/). Note that the `BrushingExtension` is applied **in the native frontend visualization**. So this is a filter that applies **on top** of whatever bounding box filter is applied to the native DataFusion query.
    """
    )
    return


@app.cell
def _(Map, arc_layer, mo, pickup_layer, set_bbox):
    arc_layer_enabled = mo.ui.switch(True, label="Render trips")
    pickup_layer_enabled = mo.ui.switch(True, label="Render pickups")
    brushing_toggle = mo.ui.switch(
        label="Enable [**`BrushingExtension`**](https://developmentseed.org/lonboard/latest/api/layer-extensions/brushing-extension/) (with this enabled, hover over the map)"
    )
    arc_opacity = mo.ui.slider(
        start=0, stop=1, step=0.01, label="Arc opacity", value=0.1
    )
    brushing_radius = mo.ui.slider(
        start=100, stop=1000, label="Brushing radius (in meters)", value=300
    )

    view_state = {
        "longitude": -73.92655187786016,
        "latitude": 40.70598365478098,
        "zoom": 10,
        "pitch": 44.70821693807123,
        "bearing": 60.62264150943396,
    }
    m = Map([arc_layer, pickup_layer], view_state=view_state)

    # Register a callback so that we update the stored bbox when we select a new bbox from the map
    m.observe(lambda change: set_bbox(change["new"]), names="selected_bounds")

    toggles = mo.hstack([arc_layer_enabled, pickup_layer_enabled, brushing_toggle])
    sliders = mo.hstack([arc_opacity, brushing_radius], justify="start")
    mo.vstack([m, toggles, sliders])
    return (
        arc_layer_enabled,
        arc_opacity,
        brushing_radius,
        brushing_toggle,
        pickup_layer_enabled,
    )


@app.cell
def _(
    arc_layer,
    arc_layer_enabled,
    arc_opacity,
    brushing_radius,
    brushing_toggle,
    pickup_layer,
    pickup_layer_enabled,
):
    # Note: this is defined in a cell other than where we create the layers so that it doesn't re-render
    # the layers from scratch whenever we change these layer properties
    arc_layer.visible = arc_layer_enabled.value
    arc_layer.brushing_enabled = brushing_toggle.value
    arc_layer.brushing_radius = brushing_radius.value
    arc_layer.opacity = arc_opacity.value
    pickup_layer.visible = pickup_layer_enabled.value
    pickup_layer.brushing_enabled = brushing_toggle.value
    pickup_layer.brushing_radius = brushing_radius.value
    return


if __name__ == "__main__":
    app.run()
