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
