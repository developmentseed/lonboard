from __future__ import annotations

import warnings
from pathlib import Path

import geopandas as gpd
import pyarrow as pa
import traitlets
from anywidget import AnyWidget

from lonboard.constants import EPSG_4326, EXTENSION_NAME, OGC_84
from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard.serialization import infer_rows_per_chunk
from lonboard.traits import ColorAccessor, FloatAccessor, PyarrowTableTrait
from lonboard.viewport import compute_view

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = Path(__file__).parent / "static"


class BaseLayer(AnyWidget):
    pass
    # Note: this _repr_keys is useful if subclassing directly from ipywidgets.Widget, as
    # that will try to print all the included keys by default
    # def _repr_keys(self):
    #     # Exclude the table_buffer from the repr; otherwise printing the buffer will
    #     # often crash the kernel.

    #     # TODO: also exclude keys when numpy array?
    #     exclude_keys = {"table_buffer"}
    #     for key in super()._repr_keys():
    #         if key in exclude_keys:
    #             continue

    #         yield key


class ScatterplotLayer(BaseLayer):
    """The `ScatterplotLayer` renders circles at given coordinates."""

    _esm = bundler_output_dir / "scatterplot-layer.js"
    _layer_type = traitlets.Unicode("scatterplot").tag(sync=True)
    _initial_view_state = traitlets.Dict().tag(sync=True)

    # Number of rows per chunk for serializing table and accessor columns
    _rows_per_chunk = traitlets.Int()

    table = PyarrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT}
    )

    radius_units = traitlets.Unicode("meters", allow_none=True).tag(sync=True)
    """
    The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    radius_scale = traitlets.Float(allow_none=True).tag(sync=True)
    """
    A global radius multiplier for all points.

    - Type: `float`, optional
    - Default: `1`
    """

    radius_min_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The minimum radius in pixels. This can be used to prevent the circle from getting
    too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    radius_max_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The maximum radius in pixels. This can be used to prevent the circle from getting
    too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    line_width_units = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = traitlets.Float(allow_none=True).tag(sync=True)
    """
    A global line width multiplier for all points.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The minimum line width in pixels. This can be used to prevent the stroke from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The maximum line width in pixels. This can be used to prevent the stroke from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    stroked = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Draw the outline of points.

    - Type: `bool`, optional
    - Default: `False`
    """

    filled = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Draw the filled area of points.

    - Type: `bool`, optional
    - Default: `True`
    """

    billboard = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    If `True`, rendered circles always face the camera. If `False` circles face up (i.e.
    are parallel with the ground plane).

    - Type: `bool`, optional
    - Default: `False`
    """

    antialiasing = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    If `True`, circles are rendered with smoothed edges. If `False`, circles are
    rendered with rough edges. Antialiasing can cause artifacts on edges of overlapping
    circles.

    - Type: `bool`, optional
    - Default: `True`
    """

    get_radius = FloatAccessor()
    get_fill_color = ColorAccessor()
    get_line_color = ColorAccessor()
    get_line_width = FloatAccessor()

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> ScatterplotLayer:
        """Construct a ScatterplotLayer from a geopandas GeoDataFrame.

        The GeoDataFrame will be reprojected to EPSG:4326 if it is not already in that
        coordinate system.

        Args:
            gdf: The GeoDataFrame to set on the layer.

        Returns:
            A ScatterplotLayer with the initialized data.
        """
        if gdf.crs and gdf.crs not in [EPSG_4326, OGC_84]:
            warnings.warn("GeoDataFrame being reprojected to EPSG:4326")
            gdf = gdf.to_crs(OGC_84)  # type: ignore

        table = geopandas_to_geoarrow(gdf)
        return cls(table=table, **kwargs)

    @traitlets.default("_initial_view_state")
    def _default_initial_view_state(self):
        return compute_view(self.table)

    @traitlets.default("_rows_per_chunk")
    def _default_rows_per_chunk(self):
        return infer_rows_per_chunk(self.table)

    @traitlets.validate("get_radius")
    def _validate_get_radius_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_radius` must have same length as table"
                )

        return proposal["value"]

    @traitlets.validate("get_fill_color")
    def _validate_get_fill_color_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_fill_color` must have same length as table"
                )

        return proposal["value"]

    @traitlets.validate("get_line_color")
    def _validate_get_line_color_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_line_color` must have same length as table"
                )

        return proposal["value"]

    @traitlets.validate("get_line_width")
    def _validate_get_line_width_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_line_width` must have same length as table"
                )

        return proposal["value"]


class PathLayer(BaseLayer):
    _esm = bundler_output_dir / "path-layer.js"
    _layer_type = traitlets.Unicode("path").tag(sync=True)
    _initial_view_state = traitlets.Dict().tag(sync=True)

    # Number of rows per chunk for serializing table and accessor columns
    _rows_per_chunk = traitlets.Int()

    table = PyarrowTableTrait(
        allowed_geometry_types={
            EXTENSION_NAME.LINESTRING,
            EXTENSION_NAME.MULTILINESTRING,
        }
    )

    width_units = traitlets.Unicode(allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    width_scale = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The path width multiplier that multiplied to all paths.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The minimum path width in pixels. This prop can be used to prevent the path from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    """
    The maximum path width in pixels. This prop can be used to prevent the path from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    joint_rounded = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Type of joint. If `True`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    cap_rounded = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Type of caps. If `True`, draw round caps. Otherwise draw square caps.

    - Type: `bool`, optional
    - Default: `False`
    """

    miter_limit = traitlets.Int(allow_none=True).tag(sync=True)
    """
    The maximum extent of a joint in ratio to the stroke width.
    Only works if `jointRounded` is `False`.


    - Type: `float`, optional
    - Default: `4`
    """

    billboard = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    If `True`, extrude the path in screen space (width always faces the camera).
    If `False`, the width always faces up.

    - Type: `bool`, optional
    - Default: `False`
    """

    get_color = ColorAccessor()
    get_width = FloatAccessor()

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> PathLayer:
        """Construct a PathLayer from a geopandas GeoDataFrame.

        The GeoDataFrame will be reprojected to EPSG:4326 if it is not already in that
        coordinate system.

        Args:
            gdf: The GeoDataFrame to set on the layer.

        Returns:
            A PathLayer with the initialized data.
        """
        if gdf.crs and gdf.crs not in [EPSG_4326, OGC_84]:
            warnings.warn("GeoDataFrame being reprojected to EPSG:4326")
            gdf = gdf.to_crs(OGC_84)  # type: ignore

        table = geopandas_to_geoarrow(gdf)
        return cls(table=table, **kwargs)

    @traitlets.default("_initial_view_state")
    def _default_initial_view_state(self):
        return compute_view(self.table)

    @traitlets.default("_rows_per_chunk")
    def _default_rows_per_chunk(self):
        return infer_rows_per_chunk(self.table)

    @traitlets.validate("get_color")
    def _validate_get_color_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError("`get_color` must have same length as table")

        return proposal["value"]

    @traitlets.validate("get_width")
    def _validate_get_width_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError("`get_width` must have same length as table")

        return proposal["value"]


class SolidPolygonLayer(BaseLayer):
    _esm = bundler_output_dir / "solid-polygon-layer.js"
    _layer_type = traitlets.Unicode("solid-polygon").tag(sync=True)
    _initial_view_state = traitlets.Dict().tag(sync=True)

    # Number of rows per chunk for serializing table and accessor columns
    _rows_per_chunk = traitlets.Int()

    table = PyarrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON}
    )

    filled = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Whether to fill the polygons (based on the color provided by the
    `get_fill_color` accessor).

    - Type: `bool`, optional
    - Default: `True`
    """

    extruded = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Whether to extrude the polygons (based on the elevations provided by the
    `get_elevation` accessor'). If set to `False`, all polygons will be flat, this
    generates less geometry and is faster than simply returning `0` from
    `get_elevation`.

    - Type: `bool`, optional
    - Default: `False`
    """

    wireframe = traitlets.Bool(allow_none=True).tag(sync=True)
    """
    Whether to generate a line wireframe of the polygon. The outline will have
    "horizontal" lines closing the top and bottom polygons and a vertical line
    (a "strut") for each vertex on the polygon.

    - Type: `bool`, optional
    - Default: `False`
    """

    elevation_scale = traitlets.Float(allow_none=True).tag(sync=True)
    """
    Elevation multiplier. The final elevation is calculated by `elevation_scale *
    get_elevation(d)`. `elevation_scale` is a handy property to scale all elevation
    without updating the data.

    - Type: `float`, optional
    - Default: `1`

    **Remarks:**

    - These lines are rendered with `GL.LINE` and will thus always be 1 pixel wide.
    - Wireframe and solid extrusions are exclusive, you'll need to create two layers
    with the same data if you want a combined rendering effect.
    """

    get_elevation = FloatAccessor()
    get_fill_color = ColorAccessor()
    get_line_color = ColorAccessor()

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> SolidPolygonLayer:
        """Construct a SolidPolygonLayer from a geopandas GeoDataFrame.

        The GeoDataFrame will be reprojected to EPSG:4326 if it is not already in that
        coordinate system.

        Args:
            gdf: The GeoDataFrame to set on the layer.

        Returns:
            A SolidPolygonLayer with the initialized data.
        """
        if gdf.crs and gdf.crs not in [EPSG_4326, OGC_84]:
            warnings.warn("GeoDataFrame being reprojected to EPSG:4326")
            gdf = gdf.to_crs(OGC_84)  # type: ignore

        table = geopandas_to_geoarrow(gdf)
        return cls(table=table, **kwargs)

    @traitlets.default("_initial_view_state")
    def _default_initial_view_state(self):
        return compute_view(self.table)

    @traitlets.default("_rows_per_chunk")
    def _default_rows_per_chunk(self):
        return infer_rows_per_chunk(self.table)

    @traitlets.validate("get_elevation")
    def _validate_get_elevation_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_elevation` must have same length as table"
                )

        return proposal["value"]

    @traitlets.validate("get_fill_color")
    def _validate_get_fill_color_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_fill_color` must have same length as table"
                )

        return proposal["value"]

    @traitlets.validate("get_line_color")
    def _validate_get_line_color_length(self, proposal):
        if isinstance(proposal["value"], (pa.ChunkedArray, pa.Array)):
            if len(proposal["value"]) != len(self.table):
                raise traitlets.TraitError(
                    "`get_line_color` must have same length as table"
                )

        return proposal["value"]
