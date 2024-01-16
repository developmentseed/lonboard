import traitlets

from lonboard._base import BaseExtension
from lonboard.traits import FloatAccessor


class BrushingExtension(BaseExtension):
    """
    Adds GPU-based data brushing functionalities to layers. It allows the layer to
    show/hide objects based on the current pointer position.
    """

    _extension_type = traitlets.Unicode("brushing").tag(sync=True)

    brushing_enabled = traitlets.Bool(True).tag(sync=True)
    """
    Enable/disable brushing. If brushing is disabled, all objects are rendered.

    - Type: `bool`, optional
    - Default: `True`
    """

    brushing_target = traitlets.Unicode("source", allow_none=True).tag(sync=True)
    """
    The position used to filter each object by.

    - Type: `str`, optional

        One of: 'source' | 'target' | 'source_target' | 'custom'

    - Default: `10000`

    """

    brushing_radius = traitlets.Float(allow_none=True, min=0).tag(sync=True)
    """
    The brushing radius centered at the pointer, in meters. If a data object is within
    this circle, it is rendered; otherwise it is hidden.

    - Type: `float`, optional
    - Default: `10000`
    """

    # TODO: update trait
    get_brushing_target = traitlets.Any(allow_none=True).tag(sync=True)
    """
    Called to retrieve an arbitrary position for each object that it will be filtered
    by.

    Only effective if `brushingTarget` is set to `"custom"`.
    """


class CollisionFilterExtension(BaseExtension):
    """Allows layers to hide overlapping objects."""

    _extension_type = traitlets.Unicode("collision-filter").tag(sync=True)

    #   /**
    #    * Props to override when rendering collision map
    #    */
    #   collisionTestProps?: {};

    collision_enabled = traitlets.Bool(True).tag(sync=True)
    """Enable/disable collisions. If collisions are disabled, all objects are rendered.

    - Type: `bool`, optional
    - Default: `True`
    """

    collision_group = traitlets.Unicode().tag(sync=True)
    """
    Collision group this layer belongs to. If it is not set, the 'default' collision
    group is used

    - Type: `string`, optional
    - Default: `None`
    """

    get_collision_priority = FloatAccessor(allow_none=True)
    """
    Accessor for collision priority. Must return a number in the range -1000 -> 1000.
    Features with higher values are shown preferentially.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the priority for all objects.
        - If an array is provided, each value in the array will be used as the priority
          for the object at the same row index.
    - Default: `0`.
    """


# TODO: support filterSize > 1
class DataFilterExtension(BaseExtension):
    """
    Adds GPU-based data filtering functionalities to layers. It allows the layer to
    show/hide objects based on user-defined properties.

    ### Layer Parameters

    ```
    get_filter_value = FloatAccessor(None, allow_none=False)
    ```

    Accessor to retrieve the value for each object that it will be filtered by.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor]
        - If a number is provided, it is used as the value for all objects.
        - If an array is provided, each value in the array will be used as the value
          for the object at the same row index.
    """

    _extension_type = traitlets.Unicode("data-filter").tag(sync=True)

    _layer_traits = {
        "get_filter_value": FloatAccessor(None, allow_none=False),
        "filter_range": traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=(-1, 1)
        ).tag(sync=True),
        "filter_soft_range": traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=None, allow_none=True
        ).tag(sync=True),
    }

    filter_enabled = traitlets.Bool(True).tag(sync=True)
    """
    Enable/disable the data filter. If the data filter is disabled, all objects are
    rendered.

    - Type: `bool`, optional
    - Default: `True`
    """

    filter_range = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(-1, 1)
    ).tag(sync=True)
    """The (min, max) bounds which defines whether an object should be rendered.

    If an object's filtered value is within the bounds, the object will be rendered;
    otherwise it will be hidden.

    - Type: Tuple[float, float], optional
    - Default: `(-1, 1)`
    """

    filter_soft_range = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=None, allow_none=True
    ).tag(sync=True)
    """If specified, objects will be faded in/out instead of abruptly shown/hidden.

    When the filtered value is outside of the bounds defined by `filter_soft_range` but
    still within the bounds defined by `filter_range`, the object will be rendered as
    "faded".

    - Type: Tuple[float, float], optional
    - Default: `None`
    """

    filter_transform_size = traitlets.Bool(True).tag(sync=True)
    """
    When an object is "faded", manipulate its size so that it appears smaller or
    thinner. Only works if `filter_soft_range` is specified.

    - Type: `bool`, optional
    - Default: `True`
    """

    filter_transform_color = traitlets.Bool(True).tag(sync=True)
    """
    When an object is "faded", manipulate its opacity so that it appears more
    translucent. Only works if `filter_soft_range` is specified.

    - Type: `bool`, optional
    - Default: `True`
    """
