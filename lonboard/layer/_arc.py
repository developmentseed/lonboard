from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard.layer._base import BaseArrowLayer
from lonboard.traits import (
    ArrowTableTrait,
    ColorAccessor,
    FloatAccessor,
    PointAccessor,
)

if TYPE_CHECKING:
    import sys

    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import ArcLayerKwargs, PointAccessorInput

    if sys.version_info >= (3, 11):
        pass
    else:
        pass

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class ArcLayer(BaseArrowLayer):
    """Render raised arcs joining pairs of source and target coordinates."""

    _layer_type = t.Unicode("arc").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)
    """A GeoArrow table.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).
    """

    great_circle = t.Bool(None, allow_none=True).tag(sync=True)
    """If `True`, create the arc along the shortest path on the earth surface.

    - Type: `bool`, optional
    - Default: `False`
    """

    num_segments = t.Int(None, allow_none=True).tag(sync=True)
    """The number of segments used to draw each arc.

    - Type: `int`, optional
    - Default: `50`
    """

    width_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    width_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The scaling multiplier for the width of each line.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """The minimum line width in pixels.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """The maximum line width in pixels.

    - Type: `float`, optional
    - Default: `None`
    """

    get_source_position = PointAccessor(None, allow_none=True)
    """Source position of each object
    """

    get_target_position = PointAccessor(None, allow_none=True)
    """Target position of each object
    """

    get_source_color = ColorAccessor(None, allow_none=True)
    """Source color of each object
    """

    get_target_color = ColorAccessor(None, allow_none=True)
    """Target color of each object
    """

    get_width = FloatAccessor(None, allow_none=True)
    """The line width of each object, in units specified by `widthUnits`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `1`.
    """

    get_height = FloatAccessor(None, allow_none=True)
    """Height color of each object
    """

    get_tilt = FloatAccessor(None, allow_none=True)
    """
    Use to tilt the arc to the side if you have multiple arcs with the same source and
    target positions.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `0`.
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        get_source_position: PointAccessorInput,
        get_target_position: PointAccessorInput,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[ArcLayerKwargs],
    ) -> None:
        """Construct an ArcLayer from existing Arrow data.

        Args:
            table: An Arrow table from any Arrow-compatible library. This does not need to have a geometry column as geometries are passed separately in `get_source_position` and `get_target_position`.

        Keyword Args:
            get_source_position: Source position of each object.
            get_target_position: Target position of each object.
            kwargs: Extra args passed down as ArcLayer attributes.

        """
        super().__init__(
            table=table,
            _rows_per_chunk=_rows_per_chunk,
            get_source_position=get_source_position,  # type: ignore
            get_target_position=get_target_position,  # type: ignore
            **kwargs,
        )
