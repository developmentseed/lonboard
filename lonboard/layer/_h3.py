from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard._utils import auto_downcast as _auto_downcast
from lonboard.layer._base import BaseArrowLayer
from lonboard.traits import ArrowTableTrait, ColorAccessor, FloatAccessor, H3Accessor

if TYPE_CHECKING:
    import sys

    import pandas as pd
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import H3AccessorInput, H3HexagonLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class H3HexagonLayer(BaseArrowLayer):
    """The `H3HexagonLayer` renders H3 hexagons.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, H3HexagonLayer

    # A GeoDataFrame with Polygon or MultiPolygon geometries
    gdf = gpd.GeoDataFrame()
    layer = H3HexagonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, H3HexagonLayer

    # Example: A FlatGeobuf file with Polygon or MultiPolygon geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = H3HexagonLayer(
        table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        get_hexagon: H3AccessorInput,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[H3HexagonLayerKwargs],
    ) -> None:
        """Create a new H3HexagonLayer.

        Args:
            table: _description_

        Keyword Args:
            get_hexagon: _description_
            kwargs: Extra args passed down as H3HexagonLayer attributes.

        """
        super().__init__(
            table=table,
            get_hexagon=get_hexagon,
            _rows_per_chunk=_rows_per_chunk,
            **kwargs,
        )

    @classmethod
    def from_pandas(
        cls,
        df: pd.DataFrame,
        *,
        get_hexagon: H3AccessorInput,
        auto_downcast: bool = True,
        **kwargs: Unpack[H3HexagonLayerKwargs],
    ) -> Self:
        """Create a new H3HexagonLayer from a pandas DataFrame.

        Args:
            df: _description_

        Keyword Args:
            get_hexagon: _description_
            auto_downcast: _description_. Defaults to True.
            kwargs: Extra args passed down as H3HexagonLayer attributes.

        Raises:
            ImportError: _description_

        Returns:
            _description_

        """
        try:
            import pyarrow as pa
        except ImportError as e:
            raise ImportError(
                "pyarrow required for converting GeoPandas to arrow.\n"
                "Run `pip install pyarrow`.",
            ) from e

        if auto_downcast:
            # Note: we don't deep copy because we don't need to clone geometries
            df = _auto_downcast(df.copy())  # type: ignore

        table = pa.Table.from_pandas(df)
        return cls(table, get_hexagon=get_hexagon, **kwargs)

    _layer_type = t.Unicode("h3-hexagon").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)

    get_hexagon = H3Accessor()
    """
    todo
    """

    stroked = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to draw an outline around the polygon (solid fill).

    Note that both the outer polygon as well the outlines of any holes will be drawn.

    - Type: `bool`, optional
    - Default: `True`
    """

    filled = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to draw a filled polygon (solid fill).

    Note that only the area between the outer polygon and any holes will be filled.

    - Type: `bool`, optional
    - Default: `True`
    """

    extruded = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to extrude the polygons.

    Based on the elevations provided by the `getElevation` accessor.

    If set to `false`, all polygons will be flat, this generates less geometry and is
    faster than simply returning 0 from getElevation.

    - Type: `bool`, optional
    - Default: `False`
    """

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to generate a line wireframe of the polygon. The outline will have
    "horizontal" lines closing the top and bottom polygons and a vertical line
    (a "strut") for each vertex on the polygon.

    - Type: `bool`, optional
    - Default: `False`

    **Remarks:**

    - These lines are rendered with `GL.LINE` and will thus always be 1 pixel wide.
    - Wireframe and solid extrusions are exclusive, you'll need to create two layers
      with the same data if you want a combined rendering effect.
    """

    elevation_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """Elevation multiplier.

    The final elevation is calculated by `elevationScale * getElevation(d)`.
    `elevationScale` is a handy property to scale all elevation without updating the
    data.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the outline width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The outline width multiplier that multiplied to all outlines of `Polygon` and
    `MultiPolygon` features if the `stroked` attribute is true.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum outline width in pixels. This can be used to prevent the outline from
    getting too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum outline width in pixels. This can be used to prevent the outline from
    getting too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    line_joint_rounded = t.Bool(None, allow_none=True).tag(sync=True)
    """Type of joint. If `true`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    line_miter_limit = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """The maximum extent of a joint in ratio to the stroke width.

    Only works if `line_joint_rounded` is false.

    - Type: `float`, optional
    - Default: `4`
    """

    get_fill_color = ColorAccessor(None, allow_none=True)
    """
    The fill color of each polygon in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the fill color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the fill color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_color = ColorAccessor(None, allow_none=True)
    """
    The outline color of each polygon in the format of `[r, g, b, [a]]`. Each channel is
    a number between 0-255 and `a` is 255 if not supplied.

    Only applies if `stroked=True`.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the outline color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the outline color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_width = FloatAccessor(None, allow_none=True)
    """
    The width of the outline of each polygon, in units specified by `line_width_units`
    (default `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the outline width for all polygons.
        - If an array is provided, each value in the array will be used as the outline
          width for the polygon at the same row index.
    - Default: `1`.
    """

    get_elevation = FloatAccessor(None, allow_none=True)
    """
    The elevation to extrude each polygon with, in meters.

    Only applies if `extruded=True`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all polygons.
        - If an array is provided, each value in the array will be used as the width for
          the polygon at the same row index.
    - Default: `1000`.
    """
