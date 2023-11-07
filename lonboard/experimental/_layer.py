from __future__ import annotations

import pyarrow as pa
import traitlets

from lonboard._layer import BaseLayer
from lonboard.experimental.traits import PointAccessor
from lonboard.traits import ColorAccessor, FloatAccessor, PyarrowTableTrait


class ArcLayer(BaseLayer):
    """Render raised arcs joining pairs of source and target coordinates."""

    _layer_type = traitlets.Unicode("arc").tag(sync=True)

    table = PyarrowTableTrait()

    great_circle = traitlets.Bool(allow_none=True).tag(sync=True)
    """If `True`, create the arc along the shortest path on the earth surface.

    - Type: `bool`, optional
    - Default: `False`
    """

    num_segments = traitlets.Int(allow_none=True).tag(sync=True)
    """The number of segments used to draw each arc.

    - Type: `int`, optional
    - Default: `50`
    """

    width_units = traitlets.Unicode(allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    width_scale = traitlets.Float(allow_none=True, min=0).tag(sync=True)
    """
    The scaling multiplier for the width of each line.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = traitlets.Float(allow_none=True, min=0).tag(sync=True)
    """The minimum line width in pixels.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = traitlets.Float(allow_none=True, min=0).tag(sync=True)
    """The maximum line width in pixels.

    - Type: `float`, optional
    - Default: `None`
    """

    get_source_position = PointAccessor()
    """Source position of each object
    """

    get_target_position = PointAccessor()
    """Target position of each object
    """

    get_source_color = ColorAccessor()

    get_target_color = ColorAccessor()

    get_width = FloatAccessor()
    """The line width of each object, in units specified by `widthUnits`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `1`.
    """

    get_height = FloatAccessor()

    get_tilt = FloatAccessor()
    """
    Use to tilt the arc to the side if you have multiple arcs with the same source and
    target positions.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `0`.
    """

    @traitlets.validate(
        "get_source_position",
        "get_target_position",
        "get_source_color",
        "get_target_color",
        "get_width",
        "get_height",
        "get_tilt",
    )
    def _validate_accessor_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError("accessor must have same length as table")

        return proposal["value"]
