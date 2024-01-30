import traitlets

from lonboard._base import BaseExtension
from lonboard.experimental.traits import GetFilterValueAccessor, PointAccessor
from lonboard.traits import FloatAccessor


class BrushingExtension(BaseExtension):
    """
    Adds GPU-based data brushing functionalities to layers. It allows the layer to
    show/hide objects based on the current pointer position.

    # Example

    An example is in the [County-to-County Migration
    notebook](https://developmentseed.org/lonboard/latest/examples/migration/).

    # Layer Properties

    This extension dynamically enables the following properties onto the layer(s) where
    it is included:

    ## `brushing_enabled`

    Enable/disable brushing. If brushing is disabled, all objects are rendered.

    - Type: `bool`, optional
    - Default: `True`

    ## `brushing_target`

    The position used to filter each object by. One of the following:

    - `"source"`: Use the primary position for each object. This can mean different
      things depending on the layer. It usually refers to the coordinates returned by
      `getPosition` or `getSourcePosition` accessors.
    - `"target"`: Use the secondary position for each object. This may not be available
      in some layers. It usually refers to the coordinates returned by
      `getTargetPosition` accessor.
    - `"source_target"`: Use both the primary position and secondary position for each
      object. Show object if either is in brushing range.
    - `"custom"`: Some layers may not describe their data objects with one or two
      coordinates, for example `PathLayer` and `PolygonLayer`. Use this option with the
      `get_brushing_target` prop to provide a custom position that each object should be
      filtered by.

    - Type: `str`, optional

        One of: "source" | "target" | "source_target" | "custom"

    - Default: `"source"`

    ## `brushing_radius`

    The brushing radius centered at the pointer, in meters. If a data object is within
    this circle, it is rendered; otherwise it is hidden.

    - Type: `float`, optional
    - Default: `10000`

    ## `get_brushing_target`

    An arbitrary position for each object that it will be filtered by.

    Only effective if `brushing_target` is set to `"custom"`.

    - Type: [PointAccessor][lonboard.experimental.traits.PointAccessor], optional
        - If a point is provided, it is used as the target for all rows.
        - If an array of points is provided, each value in the array will be used as the
          target for the row at the same row index.
    - Default: `None`.
    """

    _extension_type = traitlets.Unicode("brushing").tag(sync=True)

    _layer_traits = {
        "brushing_enabled": traitlets.Bool(True).tag(sync=True),
        "brushing_target": traitlets.Unicode(None, allow_none=True).tag(sync=True),
        "brushing_radius": traitlets.Float(None, allow_none=True, min=0).tag(sync=True),
        "get_brushing_target": PointAccessor(None, allow_none=True),
    }


class CollisionFilterExtension(BaseExtension):
    """Allows layers to hide overlapping objects.

    # Layer Properties

    This extension dynamically enables the following properties onto the layer(s) where
    it is included:

    ## `collision_enabled`

    Enable/disable collisions. If collisions are disabled, all objects are rendered.

    - Type: `bool`, optional
    - Default: `True`

    ## `collision_group`

    Collision group this layer belongs to. If it is not set, the 'default' collision
    group is used

    - Type: `str`, optional
    - Default: `None`

    ## `get_collision_priority`

    Accessor for collision priority. Must return a number in the range -1000 -> 1000.
    Features with higher values are shown preferentially.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the priority for all objects.
        - If an array is provided, each value in the array will be used as the priority
          for the object at the same row index.
    - Default: `0`.

    """

    _extension_type = traitlets.Unicode("collision-filter").tag(sync=True)

    _layer_traits = {
        "collision_enabled": traitlets.Bool(True).tag(sync=True),
        "collision_group": traitlets.Unicode(None, allow_none=True).tag(sync=True),
        "get_collision_priority": FloatAccessor(None, allow_none=True),
    }


class DataFilterExtension(BaseExtension):
    """
    Adds GPU-based data filtering functionalities to layers. It allows the layer to
    show/hide objects based on user-defined properties.

    # Example

    ```py
    from lonboard import Map, ScatterplotLayer
    from lonboard.colormap import apply_continuous_cmap
    from lonboard.experimental import DataFilterExtension

    gdf = gpd.GeoDataFrame(...)
    extension = DataFilterExtension()
    layer = ScatterplotLayer.from_geopandas(
        gdf,
        extensions=[extension],
        get_filter_value=gdf["filter_value"], # replace with desired column
        filter_range=[0, 5] # replace with desired filter range
    )
    ```

    The `DataFilterExtension` allows filtering on 1 to 4 attributes at the same time. So
    if you have four numeric columns of interest, you can filter on the intersection of
    all of them.

    For easy visualization, we suggest connecting the `DataFilterExtension` to an
    interactive slider from `ipywidgets`.

    ```py
    from ipywidgets import FloatRangeSlider

    slider = FloatRangeSlider(
        value=(2, 5),
        min=0,
        max=10,
        step=0.1,
        description="Slider: "
    )
    slider

    jsdlink(
        (slider, "value"),
        (layer, "filter_range")
    )
    ```

    If you have 2 to 4 columns, use a
    [`MultiRangeSlider`][lonboard.controls.MultiRangeSlider], which combines multiple
    `FloatRangeSlider` objects in a form that the `DataFilterExtension` expects.

    ```py
    from ipywidgets import FloatRangeSlider, jsdlink

    slider1 = FloatRangeSlider(
        value=(2, 5),
        min=0,
        max=10,
        step=0.1,
        description="First slider: "
    )
    slider2 = FloatRangeSlider(
        value=(30, 40),
        min=0,
        max=50,
        step=1,
        description="Second slider: "
    )
    multi_slider = MultiRangeSlider([slider1, slider2])
    multi_slider

    jsdlink(
        (multi_slider, "value"),
        (layer, "filter_range")
    )
    ```

    # Important notes

    - The DataFilterExtension only supports float32 data, so integer data will be casted
      to float32.
    - The DataFilterExtension copies all data referenced by `get_filter_value` to the
      GPU, so it will increase memory pressure on the GPU.

    # Layer Properties

    ## `filter_enabled`

    Enable/disable the data filter. If the data filter is disabled, all objects are
    rendered.

    - Type: `bool`, optional
    - Default: `True`

    ## `filter_range`

    The bounds which defines whether an object should be rendered. If an object's
    filtered value is within the bounds, the object will be rendered; otherwise it will
    be hidden. This prop can be updated on user input or animation with very little
    cost.

    Format:

    If `filter_size` is 1, provide a single tuple of `(min, max)`.

    If `filter_size` is 2 to 4, provide a list of tuples: `[(min0, max0), (min1,
    max1), ...]` for each filtered property, respectively.

    - Type: either Tuple[float, float] or List[Tuple[float, float]], optional
    - Default: `(-1, 1)`

    ## `filter_soft_range`

    If specified, objects will be faded in/out instead of abruptly shown/hidden.

    When the filtered value is outside of the bounds defined by `filter_soft_range` but
    still within the bounds defined by `filter_range`, the object will be rendered as
    "faded".

    - Type: Tuple[float, float], optional
    - Default: `None`

    ## `filter_transform_size`

    When an object is "faded", manipulate its size so that it appears smaller or
    thinner. Only works if `filter_soft_range` is specified.

    - Type: `bool`, optional
    - Default: `True`

    ## `filter_transform_color`

    When an object is "faded", manipulate its opacity so that it appears more
    translucent. Only works if `filter_soft_range` is specified.

    - Type: `bool`, optional
    - Default: `True`

    ## `get_filter_value`

    Accessor to retrieve the value for each object that it will be filtered by.

    - Type:
      [GetFilterValueAccessor][lonboard.experimental.traits.GetFilterValueAccessor]
        - If a scalar value is provided, it is used as the value for all objects.
        - If an array is provided, each value in the array will be used as the value
          for the object at the same row index.
    """

    _extension_type = traitlets.Unicode("data-filter").tag(sync=True)

    _layer_traits = {
        "filter_enabled": traitlets.Bool(True).tag(sync=True),
        "filter_range": traitlets.Union(
            [
                traitlets.List(traitlets.Float(), minlen=2, maxlen=2),
                traitlets.List(
                    traitlets.List(traitlets.Float(), minlen=2, maxlen=2),
                    minlen=2,
                    maxlen=4,
                ),
            ]
        ).tag(sync=True),
        "filter_soft_range": traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=None, allow_none=True
        ).tag(sync=True),
        "filter_transform_size": traitlets.Bool(True).tag(sync=True),
        "filter_transform_color": traitlets.Bool(True).tag(sync=True),
        "get_filter_value": GetFilterValueAccessor(None, allow_none=False),
    }

    filter_size = traitlets.Int(1, min=1, max=4).tag(sync=True)
    """The size of the filter (number of columns to filter by).

    The data filter can show/hide data based on 1-4 numeric properties of each object.

    - Type: `int`, optional
    - Default 1.
    """
