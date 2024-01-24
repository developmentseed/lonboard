import traitlets

from lonboard._base import BaseExtension
from lonboard.traits import FloatAccessor


class BrushingExtension(BaseExtension):
    """
    Adds GPU-based data brushing functionalities to layers. It allows the layer to
    show/hide objects based on the current pointer position.

    # Layer Properties

    This extension dynamically enables the following properties onto the layer(s) where
    it is included:

    ## `brushing_enabled`

    Enable/disable brushing. If brushing is disabled, all objects are rendered.

    - Type: `bool`, optional
    - Default: `True`

    ## `brushing_target`

    The position used to filter each object by.

    - Type: `str`, optional

        One of: 'source' | 'target' | 'source_target' | 'custom'

    - Default: `10000`

    ## `brushing_radius`

    The brushing radius centered at the pointer, in meters. If a data object is within
    this circle, it is rendered; otherwise it is hidden.

    - Type: `float`, optional
    - Default: `10000`

    An example is in the [County-to-County Migration
    notebook](https://developmentseed.org/lonboard/latest/examples/migration/).
    """

    _extension_type = traitlets.Unicode("brushing").tag(sync=True)

    _layer_traits = {
        "brushing_enabled": traitlets.Bool(True).tag(sync=True),
        "brushing_target": traitlets.Unicode("source", allow_none=True).tag(sync=True),
        "brushing_radius": traitlets.Float(allow_none=True, min=0).tag(sync=True),
        # TODO: Add trait and support
        # "get_brushing_target": traitlets.Any(allow_none=True).tag(sync=True),
    }

    # TODO: update trait
    # get_brushing_target = traitlets.Any(allow_none=True).tag(sync=True)
    """
    Called to retrieve an arbitrary position for each object that it will be filtered
    by.

    Only effective if `brushingTarget` is set to `"custom"`.
    """


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
        "collision_group": traitlets.Unicode().tag(sync=True),
        "get_collision_priority": FloatAccessor(allow_none=True),
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

    # Layer Properties

    ## `filter_enabled`

    Enable/disable the data filter. If the data filter is disabled, all objects are
    rendered.

    - Type: `bool`, optional
    - Default: `True`

    ## `filter_range`

    The (min, max) bounds which defines whether an object should be rendered.

    If an object's filtered value is within the bounds, the object will be rendered;
    otherwise it will be hidden.

    - Type: Tuple[float, float], optional
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

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor]
        - If a number is provided, it is used as the value for all objects.
        - If an array is provided, each value in the array will be used as the value
          for the object at the same row index.
    """

    _extension_type = traitlets.Unicode("data-filter").tag(sync=True)

    _layer_traits = {
        "filter_enabled": traitlets.Bool(True).tag(sync=True),
        "filter_range": traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=(-1, 1)
        ).tag(sync=True),
        "filter_soft_range": traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=None, allow_none=True
        ).tag(sync=True),
        "filter_transform_size": traitlets.Bool(True).tag(sync=True),
        "filter_transform_color": traitlets.Bool(True).tag(sync=True),
        "get_filter_value": FloatAccessor(None, allow_none=False),
    }

    # TODO: support filterSize > 1
    # In order to support filterSize > 1, we need to allow the get_filter_value accessor
    # to be either a single float or a fixed size list of up to 4 floats.

    # filter_size = traitlets.Int(1).tag(sync=True)
    """The size of the filter (number of columns to filter by).

    The data filter can show/hide data based on 1-4 numeric properties of each object.

    - Type: `int`, optional
    - Default 1.
    """
