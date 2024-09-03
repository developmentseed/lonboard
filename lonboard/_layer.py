"""Notes:

- When we pass a value of `None` as a default value to a trait, that value will be
  serialized to JS as `null` and will not be passed into the GeoArrow model (see the
  lengthy assignments of type `..(isDefined(this.param) && { param: this.param })`).
  Then the default value in the JS GeoArrow layer (defined in
  `@geoarrow/deck.gl-layers`) will be used.
"""

from __future__ import annotations

import sys
import warnings
from textwrap import dedent
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import ipywidgets
import traitlets
from arro3.core import Table
from arro3.core.types import ArrowStreamExportable

from lonboard._base import BaseExtension, BaseWidget
from lonboard._constants import EXTENSION_NAME, OGC_84
from lonboard._geoarrow._duckdb import from_duckdb as _from_duckdb
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.ops import reproject_table
from lonboard._geoarrow.ops.bbox import Bbox, total_bounds
from lonboard._geoarrow.ops.centroid import WeightedCentroid, weighted_centroid
from lonboard._geoarrow.ops.coord_layout import transpose_table
from lonboard._geoarrow.parse_wkb import parse_serialized_table
from lonboard._serialization import infer_rows_per_chunk
from lonboard._utils import auto_downcast as _auto_downcast
from lonboard._utils import get_geometry_column_index, remove_extension_kwargs
from lonboard.traits import (
    ArrowTableTrait,
    ColorAccessor,
    FloatAccessor,
    NormalAccessor,
    VariableLengthTuple,
)

if TYPE_CHECKING:
    import geopandas as gpd

    from lonboard.types.layer import (
        BaseLayerKwargs,
        BitmapLayerKwargs,
        BitmapTileLayerKwargs,
        ColumnLayerKwargs,
        HeatmapLayerKwargs,
        PathLayerKwargs,
        PointCloudLayerKwargs,
        PolygonLayerKwargs,
        ScatterplotLayerKwargs,
        SolidPolygonLayerKwargs,
    )

if TYPE_CHECKING:
    import duckdb
    import pyproj

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class BaseLayer(BaseWidget):
    # Note: these class attributes are **not** serialized to JS
    _bbox = Bbox()
    _weighted_centroid = WeightedCentroid()

    # The following traitlets **are** serialized to JS

    def __init__(self, *, extensions: Sequence[BaseExtension] = (), **kwargs):
        # We allow layer extensions to dynamically inject properties onto the layer
        # widgets where the layer is defined. We wish to allow extensions and their
        # properties to be passed in the layer constructor. _However_, if

        extension_kwargs = remove_extension_kwargs(extensions, kwargs)

        super().__init__(extensions=extensions, **kwargs)

        # Dynamically set layer traits from extensions after calling __init__
        self._add_extension_traits(extensions)

        # Assign any extension properties that we took out before calling __init__
        added_names: List[str] = []
        for prop_name, prop_value in extension_kwargs.items():
            self.set_trait(prop_name, prop_value)
            added_names.append(prop_name)

        self.send_state(added_names)

    # TODO: validate that only one extension per type is included. E.g. you can't have
    # two data filter extensions.
    extensions = VariableLengthTuple(traitlets.Instance(BaseExtension)).tag(
        sync=True, **ipywidgets.widget_serialization
    )
    """
    A list of [layer extension](https://developmentseed.org/lonboard/latest/api/layer-extensions/)
    objects to add additional features to a layer.
    """

    def _add_extension_traits(self, extensions: Sequence[BaseExtension]):
        """Assign selected traits from the extension onto this Layer."""
        for extension in extensions:
            # NOTE: here it's important that we call `traitlets.HasTraits.add_traits`
            # and not `self.add_traits`. This is because `add_traits` is originally
            # defined on `HasTraits` but `ipywidgets.Widget` overrides that method to
            # additionally call `send_state` for any trait that has `"sync"` tagged in
            # its metadata. But this is incompatible with traits that don't have default
            # values.
            #
            # For example, with the DataFilterExtension, we want to dynamically add the
            # `get_filter_value` trait, but require that the user pass in a value. With
            # the `Widget` implementation, `send_state` will fail, even if the user
            # passes in a value, because `send_state` is called before we call
            # `super().__init__()`
            traitlets.HasTraits.add_traits(self, **extension._layer_traits)

            # Note: This is part of `Widget.add_traits` (in the direct superclass) that
            # we skip by calling `traitlets.HasTraits.add_traits`
            for name, trait in extension._layer_traits.items():
                if trait.get_metadata("sync"):
                    self.keys.append(name)

    # This doesn't currently work due to I think some race conditions around syncing
    # traits vs the other parameters.

    # def add_extension(self, extension: BaseExtension, **props):
    #     """Add a new layer extension to an existing layer instance.

    #     Any properties for the added extension should also be passed as keyword
    #     arguments to this function.

    #     Examples:

    #     ```py
    #     from lonboard import ScatterplotLayer
    #     from lonboard.layer_extension import DataFilterExtension

    #     gdf = geopandas.GeoDataFrame(...)
    #     layer = ScatterplotLayer.from_geopandas(gdf)

    #     extension = DataFilterExtension(filter_size=1)
    #     filter_values = gdf["filter_column"]

    #     layer.add_extension(
    #         extension,
    #         get_filter_value=filter_values,
    #         filter_range=[0, 1]
    #     )
    #     ```

    #     Args:
    #         extension: The new extension to add.

    #     Raises:
    #         ValueError: if another extension of the same type already exists on the
    #             layer.
    #     """
    #     if any(isinstance(extension, type(ext)) for ext in self.extensions):
    #         raise ValueError("Only one extension of each type permitted")

    #     with self.hold_trait_notifications():
    #         self._add_extension_traits([extension])
    #         self.extensions += (extension,)

    #         # Assign any extension properties
    #         added_names: List[str] = []
    #         for prop_name, prop_value in props.items():
    #             self.set_trait(prop_name, prop_value)
    #             added_names.append(prop_name)

    #     self.send_state(added_names + ["extensions"])

    pickable = traitlets.Bool(True).tag(sync=True)
    """
    Whether the layer responds to mouse pointer picking events.

    This must be set to `True` for tooltips and other interactive elements to be
    available. This can also be used to only allow picking on specific layers within a
    map instance.

    Note that picking has some performance overhead in rendering. To get the absolute
    best rendering performance with large data (at the cost of removing interactivity),
    set this to `False`.

    - Type: `bool`
    - Default: `True`
    """

    visible = traitlets.Bool(True).tag(sync=True)
    """
    Whether the layer is visible.

    Under most circumstances, using the `visible` attribute to control the visibility of
    layers is recommended over removing/adding the layer from the `Map.layers` list.

    In particular, toggling the `visible` attribute will persist the layer on the
    JavaScript side, while removing/adding the layer from the `Map.layers` list will
    re-download and re-render from scratch.

    - Type: `bool`
    - Default: `True`
    """

    opacity = traitlets.Float(1, min=0, max=1).tag(sync=True)
    """
    The opacity of the layer.

    - Type: `float`. Must range between 0 and 1.
    - Default: `1`
    """

    auto_highlight = traitlets.Bool(False).tag(sync=True)
    """
    When true, the current object pointed to by the mouse pointer (when hovered over) is
    highlighted with `highlightColor`.

    Requires `pickable` to be `True`.

    - Type: `bool`
    - Default: `False`
    """

    selected_bounds = traitlets.Tuple(
        traitlets.Float(),
        traitlets.Float(),
        traitlets.Float(),
        traitlets.Float(),
        allow_none=True,
        default_value=None,
    ).tag(sync=True)
    """
    Bounds selected by the user, represented as a tuple of floats ordered as

    ```
    (minx, miny, maxx, maxy)
    ```
    """

    selected_index = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The positional index of the most-recently clicked on row of data.

    You can use this to access the full row of data from a GeoDataFrame

    ```py
    gdf.iloc[layer.selected_index]
    ```

    Setting a value here from Python will do nothing. This attribute only exists to be
    updated from JavaScript on a map click. Note that `pickable` must be `True` (the
    default) on this layer for the JavaScript `onClick` handler to work; if `pickable`
    is set to `False`, `selected_index` will never update.

    Note that you can use `observe` to call a function whenever a new value is received
    from JavaScript. Refer
    [here](https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20Events.html#signatures)
    for an example.
    """


def default_geoarrow_viewport(
    table: Table,
) -> Optional[Tuple[Bbox, WeightedCentroid]]:
    # Note: in the ArcLayer we won't necessarily have a column with a geoarrow
    # extension type/metadata
    geom_col_idx = get_geometry_column_index(table.schema)
    if geom_col_idx is None:
        return None

    geom_field = table.schema.field(geom_col_idx)
    geom_col = table.column(geom_col_idx)

    table_bbox = total_bounds(geom_field, geom_col)
    table_centroid = weighted_centroid(geom_field, geom_col)

    # Check each layer's data _individually_ to ensure that no layer is outside of
    # epsg:4326 bounds
    if table_centroid.num_items > 0:
        if table_centroid.x is not None and (
            table_centroid.x < -180 or table_centroid.x > 180
        ):
            msg = "Longitude of data's center is outside of WGS84 bounds.\n"
            msg += "Is data in WGS84 projection?"
            raise ValueError(msg)

        if table_centroid.y is not None and (
            table_centroid.y < -90 or table_centroid.y > 90
        ):
            msg = "Latitude of data's center is outside of WGS84 bounds.\n"
            msg += "Is data in WGS84 projection?"
            raise ValueError(msg)

    return table_bbox, table_centroid


class BaseArrowLayer(BaseLayer):
    """Any Arrow-based layer should subclass from BaseArrowLayer"""

    # Note: these class attributes are **not** serialized to JS

    # Number of rows per chunk for serializing table and accessor columns.
    #
    # This is a _layer-level_ construct because we need to ensure the main table and all
    # accessors have exactly the same chunking, because each chunk is rendered
    # independently as a separate deck.gl layer
    _rows_per_chunk: int

    # The following traitlets **are** serialized to JS

    table: ArrowTableTrait

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[BaseLayerKwargs],
    ):
        table_o3 = Table.from_arrow(table)
        parsed_tables = parse_serialized_table(table_o3)
        assert len(parsed_tables) == 1, (
            "Mixed geometry type input not supported here. Use the top "
            "level viz() function or separate your geometry types in advanced."
        )
        table_o3 = parsed_tables[0]
        table_o3 = transpose_table(table_o3)

        # Reproject table to WGS84 if needed
        # Note this must happen before calculating the default viewport
        table_o3 = reproject_table(table_o3, to_crs=OGC_84)

        default_viewport = default_geoarrow_viewport(table_o3)
        if default_viewport is not None:
            self._bbox = default_viewport[0]
            self._weighted_centroid = default_viewport[1]

        rows_per_chunk = _rows_per_chunk or infer_rows_per_chunk(table_o3)
        if rows_per_chunk <= 0:
            raise ValueError("Cannot serialize table with 0 rows per chunk.")

        self._rows_per_chunk = rows_per_chunk

        super().__init__(table=table_o3, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[BaseLayerKwargs],
    ) -> Self:
        """Construct a Layer from a geopandas GeoDataFrame.

        The GeoDataFrame will be reprojected to EPSG:4326 if it is not already in that
        coordinate system.

        Args:
            gdf: The GeoDataFrame to set on the layer.

        Keyword Args:
            auto_downcast: If `True`, automatically downcast to smaller-size data types
                if possible without loss of precision. This calls
                [pandas.DataFrame.convert_dtypes][pandas.DataFrame.convert_dtypes] and
                [pandas.to_numeric][pandas.to_numeric] under the hood.

        Returns:
            A Layer with the initialized data.
        """
        if auto_downcast:
            # Note: we don't deep copy because we don't need to clone geometries
            gdf = _auto_downcast(gdf.copy())  # type: ignore

        table = geopandas_to_geoarrow(gdf)
        return cls(table=table, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[BaseLayerKwargs],
    ) -> Self:
        """Construct a Layer from a duckdb-spatial query.

        DuckDB Spatial does not currently expose coordinate reference system
        information, so **the user must ensure that data has been reprojected to
        EPSG:4326** or pass in the existing CRS of the data in the `crs` keyword
        parameter.

        Args:
            sql: The SQL input to visualize. This can either be a string containing a
                SQL query or the output of the duckdb `sql` function.
            con: The current DuckDB connection. This is required when passing a `str` to
                the `sql` parameter or when using a non-global DuckDB connection.
                Defaults to None.

        Keyword Args:
            crs: The CRS of the input data. This can either be a string passed to
                `pyproj.CRS.from_user_input` or a `pyproj.CRS` object. Defaults to None.

        Returns:
            A Layer with the initialized data.
        """
        if isinstance(sql, str):
            assert con is not None, "con must be provided when sql is a str"

            rel = con.sql(sql)
            table = _from_duckdb(rel, con=con, crs=crs)
        else:
            table = _from_duckdb(sql, con=con, crs=crs)

        return cls(table=table, **kwargs)


class BitmapLayer(BaseLayer):
    """
    The `BitmapLayer` renders a bitmap (e.g. PNG, JPEG, or WebP) at specified
    boundaries.

    **Example:**

    ```py
    from lonboard import Map, BitmapLayer

    layer = BitmapLayer(
        image='https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/sf-districts.png',
        bounds=[-122.5190, 37.7045, -122.355, 37.829]
    )
    m = Map(layer)
    m
    ```
    """

    def __init__(self, **kwargs: BitmapLayerKwargs):
        super().__init__(**kwargs)  # type: ignore

    _layer_type = traitlets.Unicode("bitmap").tag(sync=True)

    image = traitlets.Unicode().tag(sync=True)
    """The URL to an image to display.

    - Type: `str`
    """

    bounds = traitlets.Union(
        [
            VariableLengthTuple(traitlets.Float(), minlen=4, maxlen=4),
            VariableLengthTuple(
                VariableLengthTuple(traitlets.Float(), minlen=2, maxlen=2),
                minlen=4,
                maxlen=4,
            ),
        ]
    ).tag(sync=True)
    """The bounds of the image.

    Supported formats:

        - Coordinates of the bounding box of the bitmap `[left, bottom, right, top]`
        - Coordinates of four corners of the bitmap, should follow the sequence of
          `[[left, bottom], [left, top], [right, top], [right, bottom]]`.
    """

    desaturate = traitlets.Float(0, min=0, max=1).tag(sync=True)
    """The desaturation of the bitmap. Between `[0, 1]`.

    - Type: `float`, optional
    - Default: `0`
    """

    transparent_color = VariableLengthTuple(
        traitlets.Float(), default_value=None, allow_none=True, minlen=3, maxlen=4
    )
    """The color to use for transparent pixels, in `[r, g, b, a]`.

    - Type: `List[float]`, optional
    - Default: `[0, 0, 0, 0]`
    """

    tint_color = VariableLengthTuple(
        traitlets.Float(), default_value=None, allow_none=True, minlen=3, maxlen=4
    )
    """The color to tint the bitmap by, in `[r, g, b]`.

    - Type: `List[float]`, optional
    - Default: `[255, 255, 255]`
    """

    @property
    def _bbox(self) -> Bbox:
        a, b, c, d = self.bounds

        # Four corners
        if isinstance(a, tuple):
            bbox = Bbox()
            bbox.update(Bbox(a[0], a[1], a[0], a[1]))
            bbox.update(Bbox(b[0], b[1], b[0], b[1]))
            bbox.update(Bbox(c[0], c[1], c[0], c[1]))
            bbox.update(Bbox(d[0], d[1], d[0], d[1]))
            return bbox

        return Bbox(a, b, c, d)

    @property
    def _weighted_centroid(self) -> WeightedCentroid:
        bbox = self._bbox
        center_x = (bbox.minx + bbox.maxx) / 2
        center_y = (bbox.miny + bbox.maxy) / 2
        # no idea what weight to put on this; we don't know how many "objects" this
        # image should represent.
        return WeightedCentroid(x=center_x, y=center_y, num_items=100)


class BitmapTileLayer(BaseLayer):
    """
    The BitmapTileLayer renders image tiles (e.g. PNG, JPEG, or WebP) in the web
    mercator tiling system. Only the tiles visible in the current viewport are loaded
    and rendered.

    **Example:**

    ```py
    from lonboard import Map, BitmapTileLayer

    # We set `max_requests < 0` because `tile.openstreetmap.org` supports HTTP/2.
    layer = BitmapTileLayer(
        data="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        tile_size=256,
        max_requests=-1,
        min_zoom=0,
        max_zoom=19,
    )
    m = Map(layer)
    ```
    """

    def __init__(self, **kwargs: BitmapTileLayerKwargs):
        super().__init__(**kwargs)  # type: ignore

    _layer_type = traitlets.Unicode("bitmap-tile").tag(sync=True)

    data = traitlets.Union(
        [traitlets.Unicode(), VariableLengthTuple(traitlets.Unicode(), minlen=1)]
    ).tag(sync=True)
    """
    Either a URL template or an array of URL templates from which the tile data should
    be loaded.

    If the value is a string: a URL template. Substrings {x} {y} and {z}, if present,
    will be replaced with a tile's actual index when it is requested.

    If the value is an array: multiple URL templates. Each endpoint must return the same
    content for the same tile index. This can be used to work around domain sharding,
    allowing browsers to download more resources simultaneously. Requests made are
    balanced among the endpoints, based on the tile index.
    """

    tile_size = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The pixel dimension of the tiles, usually a power of 2.

    Tile size represents the target pixel width and height of each tile when rendered.
    Smaller tile sizes display the content at higher resolution, while the layer needs
    to load more tiles to fill the same viewport.

    - Type: `int`, optional
    - Default: `512`
    """

    zoom_offset = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    This offset changes the zoom level at which the tiles are fetched. Needs to be an
    integer.

    - Type: `int`, optional
    - Default: `0`
    """

    max_zoom = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The max zoom level of the layer's data. When overzoomed (i.e. `zoom > max_zoom`),
    tiles from this level will be displayed.

    - Type: `int`, optional
    - Default: `None`
    """

    min_zoom = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The min zoom level of the layer's data. When underzoomed (i.e. `zoom < min_zoom`),
    the layer will not display any tiles unless `extent` is defined, to avoid issuing
    too many tile requests.

    - Type: `int`, optional
    - Default: `None`
    """

    extent = VariableLengthTuple(
        traitlets.Float(), minlen=4, maxlen=4, allow_none=True, default_value=None
    ).tag(sync=True)
    """
    The bounding box of the layer's data, in the form of `[min_x, min_y, max_x, max_y]`.
    If provided, the layer will only load and render the tiles that are needed to fill
    this box.

    - Type: `List[float]`, optional
    - Default: `None`
    """

    max_cache_size = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The maximum number of tiles that can be cached. The tile cache keeps loaded tiles in
    memory even if they are no longer visible. It reduces the need to re-download the
    same data over and over again when the user pan/zooms around the map, providing a
    smoother experience.

    If not supplied, the `max_cache_size` is calculated as 5 times the number of tiles
    in the current viewport.

    - Type: `int`, optional
    - Default: `None`
    """

    # TODO: Not sure if `getTileData` returns a `byteLength`?
    # max_cache_byte_size = traitlets.Int(None, allow_none=True).tag(sync=True)
    # """
    # """

    refinement_strategy = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """How the tile layer refines the visibility of tiles.

    When zooming in and out, if the layer only shows tiles from the current zoom level,
    then the user may observe undesirable flashing while new data is loading. By setting
    `refinement_strategy` the layer can attempt to maintain visual continuity by
    displaying cached data from a different zoom level before data is available.

    This prop accepts one of the following:

    - `"best-available"`: If a tile in the current viewport is waiting for its data to
      load, use cached content from the closest zoom level to fill the empty space. This
      approach minimizes the visual flashing due to missing content.
    - `"no-overlap"`: Avoid showing overlapping tiles when backfilling with cached
      content. This is usually favorable when tiles do not have opaque backgrounds.
    - `"never"`: Do not display any tile that is not selected.

    - Type: `str`, optional
    - Default: `"best-available"`
    """

    max_requests = traitlets.Int(None, allow_none=True).tag(sync=True)
    """The maximum number of concurrent data fetches.

    If <= 0, no throttling will occur, and `get_tile_data` may be called an unlimited
    number of times concurrently regardless of how long that tile is or was visible.

    If > 0, a maximum of `max_requests` instances of `get_tile_data` will be called
    concurrently. Requests may never be called if the tile wasn't visible long enough to
    be scheduled and started. Requests may also be aborted (through the signal passed to
    `get_tile_data`) if there are more than `max_requests` ongoing requests and some of
    those are for tiles that are no longer visible.

    If `get_tile_data` makes fetch requests against an HTTP 1 web server, then
    max_requests should correlate to the browser's maximum number of concurrent fetch
    requests. For Chrome, the max is 6 per domain. If you use the data prop and specify
    multiple domains, you can increase this limit. For example, with Chrome and 3
    domains specified, you can set max_requests=18.

    If the web server supports HTTP/2 (Open Chrome dev tools and look for "h2" in the
    Protocol column), then you can make an unlimited number of concurrent requests (and
    can set max_requests=-1). Note that this will request data for every tile, no matter
    how long the tile was visible, and may increase server load.
    """

    desaturate = traitlets.Float(0, min=0, max=1).tag(sync=True)
    """The desaturation of the bitmap. Between `[0, 1]`.

    - Type: `float`, optional
    - Default: `0`
    """

    transparent_color = VariableLengthTuple(
        traitlets.Float(), default_value=None, allow_none=True, minlen=3, maxlen=4
    )
    """The color to use for transparent pixels, in `[r, g, b, a]`.

    - Type: `List[float]`, optional
    - Default: `[0, 0, 0, 0]`
    """

    tint_color = VariableLengthTuple(
        traitlets.Float(), default_value=None, allow_none=True, minlen=3, maxlen=4
    )
    """The color to tint the bitmap by, in `[r, g, b]`.

    - Type: `List[float]`, optional
    - Default: `[255, 255, 255]`
    """


class ColumnLayer(BaseArrowLayer):
    """
    The ColumnLayer renders extruded cylinders (tessellated regular polygons) at given
    coordinates.
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[ColumnLayerKwargs],
    ):
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[ColumnLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[ColumnLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("column").tag(sync=True)

    table = ArrowTableTrait(allowed_geometry_types={EXTENSION_NAME.POINT})
    """A GeoArrow table with a Point or MultiPoint column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    disk_resolution = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The number of sides to render the disk as. The disk is a regular polygon that fits
    inside the given radius. A higher resolution will yield a smoother look close-up,
    but also need more resources to render.

    - Type: `int`, optional
    - Default: `20`
    """

    radius = traitlets.Float(None, allow_none=True).tag(sync=True)
    """
    Disk size in units specified by `radius_units` (default meters).

    - Type: `float`, optional
    - Default: `1000`
    """

    angle = traitlets.Float(None, allow_none=True).tag(sync=True)
    """
    Disk rotation, counter-clockwise in degrees.

    - Type: `float`, optional
    - Default: `0`
    """

    offset = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=None, allow_none=True
    ).tag(sync=True)
    """
    Disk offset from the position, relative to the radius. By default, the disk is
    centered at each position.

    - Type: `tuple[float, float]`, optional
    - Default: `(0, 0)`
    """

    coverage = traitlets.Float(None, allow_none=True).tag(sync=True)
    """
    Radius multiplier, between 0 - 1. The radius of the disk is calculated by
    `coverage * radius`

    - Type: `float`, optional
    - Default: `1`
    """

    elevation_scale = traitlets.Float(None, allow_none=True).tag(sync=True)
    """
    Column elevation multiplier. The elevation of column is calculated by
    `elevation_scale * get_elevation(d)`. `elevation_scale` is a handy property
    to scale all column elevations without updating the data.

    - Type: `float`, optional
    - Default: `1`
    """

    filled = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to draw a filled column (solid fill).

    - Type: `bool`, optional
    - Default: `True`
    """

    stroked = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to draw an outline around the disks. Only applies if `extruded=False`.

    - Type: `bool`, optional
    - Default: `False`
    """

    extruded = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to extrude the columns. If set to `false`, all columns will be rendered as
    flat polygons.

    - Type: `bool`, optional
    - Default: `True`
    """

    wireframe = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to generate a line wireframe of the column. The outline will have
    "horizontal" lines closing the top and bottom polygons and a vertical line
    (a "strut") for each vertex around the disk. Only applies if `extruded=True`.

    - Type: `bool`, optional
    - Default: `False`
    """

    flat_shading = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, the vertical surfaces of the columns use [flat
    shading](https://en.wikipedia.org/wiki/Shading#Flat_vs._smooth_shading). If `false`,
    use smooth shading. Only effective if `extruded` is `True`.

    - Type: `bool`, optional
    - Default: `False`
    """

    radius_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The line width multiplier that multiplied to all outlines if the `stroked` attribute
    is `True`.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum outline width in pixels. This can be used to prevent the line from
    getting too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum outline width in pixels. This can be used to prevent the line from
    getting too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    get_fill_color = ColorAccessor(None, allow_none=True)
    """
    The filled color of each object in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the filled color for
          all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the filled color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_color = ColorAccessor(None, allow_none=True)
    """
    The outline color of each object in the format of `[r, g, b, [a]]`. Each channel is
    a number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the outline color for
          all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the outline color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_elevation = FloatAccessor(None, allow_none=True)
    """
    The elevation of each cell in meters.

    Only applies if `extruded=True`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all polygons.
        - If an array is provided, each value in the array will be used as the width for
          the polygon at the same row index.
    - Default: `1000`.
    """

    get_line_width = FloatAccessor(None, allow_none=True)
    """
    The width of the outline of each column, in units specified by `line_width_units`
    (default `'meters'`). Only applies if `extruded: false` and `stroked: true`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the outline width for all columns.
        - If an array is provided, each value in the array will be used as the outline
          width for the column at the same row index.
    - Default: `1`.
    """


class PolygonLayer(BaseArrowLayer):
    """The `PolygonLayer` renders filled, stroked and/or extruded polygons.

    !!! note

        This layer is essentially a combination of a [`PathLayer`][lonboard.PathLayer]
        and a [`SolidPolygonLayer`][lonboard.SolidPolygonLayer]. This has some overhead
        beyond a `SolidPolygonLayer`, so if you're looking for the maximum performance
        with large data, you may want to use a `SolidPolygonLayer` directly.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, PolygonLayer

    # A GeoDataFrame with Polygon or MultiPolygon geometries
    gdf = gpd.GeoDataFrame()
    layer = PolygonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
        get_line_color=[0, 100, 100, 150],
    )
    m = Map(layer)
    ```

    From [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.core import read_parquet
    from lonboard import Map, PolygonLayer

    # Example: A GeoParquet file with Polygon or MultiPolygon geometries
    table = read_parquet("path/to/file.parquet")
    layer = PolygonLayer(
        table=table,
        get_fill_color=[255, 0, 0],
        get_line_color=[0, 100, 100, 150],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[PolygonLayerKwargs],
    ):
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[PolygonLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[PolygonLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("polygon").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON}
    )
    """A GeoArrow table with a Polygon or MultiPolygon column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.PolygonLayer.from_geopandas] instead.
    """

    stroked = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """Whether to draw an outline around the polygon (solid fill).

    Note that both the outer polygon as well the outlines of any holes will be drawn.

    - Type: `bool`, optional
    - Default: `True`
    """

    filled = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """Whether to draw a filled polygon (solid fill).

    Note that only the area between the outer polygon and any holes will be filled.

    - Type: `bool`, optional
    - Default: `True`
    """

    extruded = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """Whether to extrude the polygons.

    Based on the elevations provided by the `getElevation` accessor.

    If set to `false`, all polygons will be flat, this generates less geometry and is
    faster than simply returning 0 from getElevation.

    - Type: `bool`, optional
    - Default: `False`
    """

    wireframe = traitlets.Bool(None, allow_none=True).tag(sync=True)
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

    elevation_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """Elevation multiplier.

    The final elevation is calculated by `elevationScale * getElevation(d)`.
    `elevationScale` is a handy property to scale all elevation without updating the
    data.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The line width multiplier that multiplied to all outlines of `Polygon` and
    `MultiPolygon` features if the `stroked` attribute is true.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum line width in pixels. This can be used to prevent the line from getting
    too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum line width in pixels. This can be used to prevent the line from getting
    too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    line_joint_rounded = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """Type of joint. If `true`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    line_miter_limit = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
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
    The line color of each polygon in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    Only applies if `extruded=True`.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the line color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the line color for the polygon at the same row index.
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


class ScatterplotLayer(BaseArrowLayer):
    """The `ScatterplotLayer` renders circles at given coordinates.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, ScatterplotLayer

    # A GeoDataFrame with Point or MultiPoint geometries
    gdf = gpd.GeoDataFrame()
    layer = ScatterplotLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    From [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.core import read_parquet
    from lonboard import Map, ScatterplotLayer

    # Example: A GeoParquet file with Point or MultiPoint geometries
    table = read_parquet("path/to/file.parquet")
    layer = ScatterplotLayer(
        table=table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[ScatterplotLayerKwargs],
    ):
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[ScatterplotLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[ScatterplotLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("scatterplot").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT}
    )
    """A GeoArrow table with a Point or MultiPoint column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    radius_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    radius_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    A global radius multiplier for all points.

    - Type: `float`, optional
    - Default: `1`
    """

    radius_min_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum radius in pixels. This can be used to prevent the circle from getting
    too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    radius_max_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum radius in pixels. This can be used to prevent the circle from getting
    too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    line_width_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    A global line width multiplier for all points.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum line width in pixels. This can be used to prevent the stroke from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum line width in pixels. This can be used to prevent the stroke from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    stroked = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Draw the outline of points.

    - Type: `bool`, optional
    - Default: `False`
    """

    filled = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Draw the filled area of points.

    - Type: `bool`, optional
    - Default: `True`
    """

    billboard = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, rendered circles always face the camera. If `False` circles face up (i.e.
    are parallel with the ground plane).

    - Type: `bool`, optional
    - Default: `False`
    """

    antialiasing = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, circles are rendered with smoothed edges. If `False`, circles are
    rendered with rough edges. Antialiasing can cause artifacts on edges of overlapping
    circles.

    - Type: `bool`, optional
    - Default: `True`
    """

    get_radius = FloatAccessor(None, allow_none=True)
    """
    The radius of each object, in units specified by `radius_units` (default
    `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the radius for all objects.
        - If an array is provided, each value in the array will be used as the radius
          for the object at the same row index.
    - Default: `1`.
    """

    get_fill_color = ColorAccessor(None, allow_none=True)
    """
    The filled color of each object in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the filled color for
          all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the filled color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_color = ColorAccessor(None, allow_none=True)
    """
    The outline color of each object in the format of `[r, g, b, [a]]`. Each channel is
    a number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the outline color
          for all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the outline color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_width = FloatAccessor(None, allow_none=True)
    """
    The width of the outline of each object, in units specified by `line_width_units`
    (default `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the outline width for all objects.
        - If an array is provided, each value in the array will be used as the outline
          width for the object at the same row index.
    - Default: `1`.
    """


class PathLayer(BaseArrowLayer):
    """
    The `PathLayer` renders lists of coordinate points as extruded polylines with
    mitering.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, PathLayer

    # A GeoDataFrame with LineString or MultiLineString geometries
    gdf = gpd.GeoDataFrame()
    layer = PathLayer.from_geopandas(
        gdf,
        get_color=[255, 0, 0],
        width_min_pixels=2,
    )
    m = Map(layer)
    ```

    From [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.core import read_parquet
    from lonboard import Map, PathLayer

    # Example: A GeoParquet file with LineString or MultiLineString geometries
    table = read_parquet("path/to/file.parquet")
    layer = PathLayer(
        table=table,
        get_color=[255, 0, 0],
        width_min_pixels=2,
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[PathLayerKwargs],
    ):
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[PathLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[PathLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("path").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={
            EXTENSION_NAME.LINESTRING,
            EXTENSION_NAME.MULTILINESTRING,
        }
    )
    """A GeoArrow table with a LineString or MultiLineString column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.PathLayer.from_geopandas] instead.
    """

    width_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    width_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The path width multiplier that multiplied to all paths.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum path width in pixels. This prop can be used to prevent the path from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum path width in pixels. This prop can be used to prevent the path from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    joint_rounded = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Type of joint. If `True`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    cap_rounded = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Type of caps. If `True`, draw round caps. Otherwise draw square caps.

    - Type: `bool`, optional
    - Default: `False`
    """

    miter_limit = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    The maximum extent of a joint in ratio to the stroke width.
    Only works if `jointRounded` is `False`.

    - Type: `float`, optional
    - Default: `4`
    """

    billboard = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, extrude the path in screen space (width always faces the camera).
    If `False`, the width always faces up.

    - Type: `bool`, optional
    - Default: `False`
    """

    get_color = ColorAccessor(None, allow_none=True)
    """
    The color of each path in the format of `[r, g, b, [a]]`. Each channel is a number
    between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the color for all
          paths.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the color for the path at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_width = FloatAccessor(None, allow_none=True)
    """
    The width of each path, in units specified by `width_units` (default `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `1`.
    """


class PointCloudLayer(BaseArrowLayer):
    """
    The `PointCloudLayer` renders a point cloud with 3D positions, normals and colors.

    The `PointCloudLayer` can be more efficient at rendering large quantities of points
    than the [`ScatterplotLayer`][lonboard.ScatterplotLayer], but has fewer rendering
    options. In particular, you can have only one point size across all points in your
    data.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, PointCloudLayer

    # A GeoDataFrame with Point geometries
    gdf = gpd.GeoDataFrame()
    layer = PointCloudLayer.from_geopandas(
        gdf,
        get_color=[255, 0, 0],
        point_size=2,
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[PointCloudLayerKwargs],
    ):
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[PointCloudLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[PointCloudLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("point-cloud").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POINT}, allowed_dimensions={3}
    )
    """A GeoArrow table with a Point column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.PointCloudLayer.from_geopandas] instead.
    """

    size_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    point_size = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    Global radius of all points, in units specified by `size_units`.

    - Type: `float`, optional
    - Default: `10`
    """

    get_color = ColorAccessor(None, allow_none=True)
    """
    The color of each path in the format of `[r, g, b, [a]]`. Each channel is a number
    between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the color for all
          paths.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the color for the path at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_normal = NormalAccessor(None, allow_none=True)
    """
    The normal of each object, in `[nx, ny, nz]`.

    - Type: [NormalAccessor][lonboard.traits.NormalAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the normal for all
          points.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the normal for the point at the same row index.
    - Default: `1`.
    """


class SolidPolygonLayer(BaseArrowLayer):
    """
    The `SolidPolygonLayer` renders filled and/or extruded polygons.

    !!! note

        This layer is similar to the [`PolygonLayer`][lonboard.PolygonLayer] but will
        not render an outline around polygons. In most cases, you'll want to use the
        `PolygonLayer` directly, but for very large datasets not drawing the outline can
        significantly improve performance, in which case you may want to use this layer.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, SolidPolygonLayer

    # A GeoDataFrame with Polygon or MultiPolygon geometries
    gdf = gpd.GeoDataFrame()
    layer = SolidPolygonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    From [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.core import read_parquet
    from lonboard import Map, SolidPolygonLayer

    # Example: A GeoParquet file with Polygon or MultiPolygon geometries
    table = read_parquet("path/to/file.parquet")
    layer = SolidPolygonLayer(
        table=table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        _rows_per_chunk: Optional[int] = None,
        **kwargs: Unpack[SolidPolygonLayerKwargs],
    ):
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[SolidPolygonLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[SolidPolygonLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("solid-polygon").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON}
    )
    """A GeoArrow table with a Polygon or MultiPolygon column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.SolidPolygonLayer.from_geopandas] instead.
    """

    filled = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to fill the polygons (based on the color provided by the
    `get_fill_color` accessor).

    - Type: `bool`, optional
    - Default: `True`
    """

    extruded = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to extrude the polygons (based on the elevations provided by the
    `get_elevation` accessor'). If set to `False`, all polygons will be flat, this
    generates less geometry and is faster than simply returning `0` from
    `get_elevation`.

    - Type: `bool`, optional
    - Default: `False`
    """

    wireframe = traitlets.Bool(None, allow_none=True).tag(sync=True)
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

    elevation_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    Elevation multiplier. The final elevation is calculated by `elevation_scale *
    get_elevation(d)`. `elevation_scale` is a handy property to scale all elevation
    without updating the data.

    - Type: `float`, optional
    - Default: `1`
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
    The line color of each polygon in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    Only applies if `extruded=True`.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the line color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the line color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """


class HeatmapLayer(BaseArrowLayer):
    """The `HeatmapLayer` visualizes the spatial distribution of data.

    **Example**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, HeatmapLayer

    # A GeoDataFrame with Point geometries
    gdf = gpd.GeoDataFrame()
    layer = HeatmapLayer.from_geopandas(gdf)
    m = Map(layer)
    ```

    From [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.core import read_parquet
    from lonboard import Map, HeatmapLayer

    # Example: A GeoParquet file with Point geometries
    table = read_parquet("path/to/file.parquet")
    layer = HeatmapLayer(
        table=table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    """

    def __init__(
        self, *, table: ArrowStreamExportable, **kwargs: Unpack[HeatmapLayerKwargs]
    ):
        err_msg = """
        The `HeatmapLayer` is not currently working.

        As of Lonboard v0.10, Lonboard upgraded to version 9.0 of the underlying
        [deck.gl](https://deck.gl/) library. deck.gl [appears to have a
        bug](https://github.com/visgl/deck.gl/issues/8960#issuecomment-2284791644) with
        the HeatmapLayer in 9.0, that has not yet been fixed.

        Please temporarily downgrade to Lonboard v0.9 if you would like to use the
        `HeatmapLayer`.
        """
        warnings.warn(dedent(err_msg), UserWarning)

        # NOTE: we override the default for _rows_per_chunk because otherwise we render
        # one heatmap per _chunk_ not for the entire dataset.
        table_o3 = Table.from_arrow(table)
        super().__init__(table=table, _rows_per_chunk=len(table_o3), **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[HeatmapLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: Union[str, duckdb.DuckDBPyRelation],
        con: Optional[duckdb.DuckDBPyConnection] = None,
        *,
        crs: Optional[Union[str, pyproj.CRS]] = None,
        **kwargs: Unpack[HeatmapLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = traitlets.Unicode("heatmap").tag(sync=True)

    table = ArrowTableTrait(allowed_geometry_types={EXTENSION_NAME.POINT})
    """A GeoArrow table with a Point column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.HeatmapLayer.from_geopandas] instead.
    """

    radius_pixels = traitlets.Float(None, allow_none=True).tag(sync=True)
    """Radius of the circle in pixels, to which the weight of an object is distributed.

    - Type: `float`, optional
    - Default: `30`
    """

    # TODO: stabilize ColormapTrait
    # color_range?: Color[];
    # """Specified as an array of colors [color1, color2, ...].

    # - Default: `6-class YlOrRd` - [colorbrewer](http://colorbrewer2.org/#type=sequential&scheme=YlOrRd&n=6)
    # """

    intensity = traitlets.Float(None, allow_none=True).tag(sync=True)
    """
    Value that is multiplied with the total weight at a pixel to obtain the final
    weight.

    - Type: `float`, optional
    - Default: `1`
    """

    threshold = traitlets.Float(None, allow_none=True, min=0, max=1).tag(sync=True)
    """Ratio of the fading weight to the max weight, between `0` and `1`.

    For example, `0.1` affects all pixels with weight under 10% of the max.

    Ignored when `color_domain` is specified.

    - Type: `float`, optional
    - Default: `0.05`
    """

    color_domain = VariableLengthTuple(
        traitlets.Float(), default_value=None, allow_none=True, minlen=2, maxlen=2
    ).tag(sync=True)
    # """
    # Controls how weight values are mapped to the `color_range`, as an array of two
    # numbers [`min_value`, `max_value`].

    # - Type: `(float, float)`, optional
    # - Default: `None`
    # """

    aggregation = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """Defines the type of aggregation operation

    Valid values are 'SUM', 'MEAN'.

    - Type: `str`, optional
    - Default: `"SUM"`
    """

    weights_texture_size = traitlets.Int(None, allow_none=True).tag(sync=True)
    """Specifies the size of weight texture.

    - Type: `int`, optional
    - Default: `2048`
    """

    debounce_timeout = traitlets.Int(None, allow_none=True).tag(sync=True)
    """
    Interval in milliseconds during which changes to the viewport don't trigger
    aggregation.

    - Type: `int`, optional
    - Default: `500`
    """

    get_weight = FloatAccessor(None, allow_none=True)
    """The weight of each object.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the weight for all objects.
        - If an array is provided, each value in the array will be used as the weight
          for the object at the same row index.
    - Default: `1`.
    """
