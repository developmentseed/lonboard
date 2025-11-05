# ruff: noqa: ERA001, SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ipywidgets
import traitlets
import traitlets as t
from arro3.core import ChunkedArray, Schema, Table

from lonboard._base import BaseExtension, BaseWidget
from lonboard._constants import OGC_84
from lonboard._geoarrow._duckdb import from_duckdb as _from_duckdb
from lonboard._geoarrow.c_stream_import import import_arrow_c_stream
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.ops import (
    Bbox,
    WeightedCentroid,
    reproject_table,
    total_bounds,
    weighted_centroid,
)
from lonboard._geoarrow.ops.coord_layout import make_geometry_interleaved
from lonboard._geoarrow.parse_wkb import parse_serialized_table
from lonboard._geoarrow.row_index import add_positional_row_index
from lonboard._serialization import infer_rows_per_chunk
from lonboard._utils import auto_downcast as _auto_downcast
from lonboard._utils import get_geometry_column_index, remove_extension_kwargs
from lonboard.traits import ArrowTableTrait, VariableLengthTuple

if TYPE_CHECKING:
    import sys
    from collections.abc import Generator, Sequence

    import duckdb
    import geopandas as gpd
    import pyproj
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import BaseLayerKwargs

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

    def __init__(
        self,
        *,
        extensions: Sequence[BaseExtension] = (),
        **kwargs: Any,
    ) -> None:
        # We allow layer extensions to dynamically inject properties onto the layer
        # widgets where the layer is defined. We wish to allow extensions and their
        # properties to be passed in the layer constructor. _However_, if

        extension_kwargs = remove_extension_kwargs(extensions, kwargs)

        super().__init__(extensions=extensions, **kwargs)

        # Dynamically set layer traits from extensions after calling __init__
        self._add_extension_traits(extensions)

        # Assign any extension properties that we took out before calling __init__
        added_names: list[str] = []
        for prop_name, prop_value in extension_kwargs.items():
            self.set_trait(prop_name, prop_value)
            added_names.append(prop_name)

        self.send_state(added_names)

    # TODO: validate that only one extension per type is included. E.g. you can't have
    # two data filter extensions.
    extensions = VariableLengthTuple(t.Instance(BaseExtension)).tag(
        sync=True,
        **ipywidgets.widget_serialization,
    )
    """
    A list of [layer extension](https://developmentseed.org/lonboard/latest/api/layer-extensions/)
    objects to add additional features to a layer.
    """

    def _add_extension_traits(self, extensions: Sequence[BaseExtension]) -> None:
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

    pickable = t.Bool(default_value=True).tag(sync=True)
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

    visible = t.Bool(default_value=True).tag(sync=True)
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

    opacity = t.Float(1, min=0, max=1).tag(sync=True)
    """
    The opacity of the layer.

    - Type: `float`. Must range between 0 and 1.
    - Default: `1`
    """

    auto_highlight = t.Bool(default_value=False).tag(sync=True)
    """
    When true, the current object pointed to by the mouse pointer (when hovered over) is
    highlighted with `highlightColor`.

    Requires `pickable` to be `True`.

    - Type: `bool`
    - Default: `False`
    """

    highlight_color = VariableLengthTuple(
        t.Int(),
        default_value=None,
        minlen=3,
        maxlen=4,
    )
    """
    RGBA color to blend with the highlighted object (the hovered over object if
    `auto_highlight=true`). When the value is a 3 component (RGB) array, a default alpha
    of 255 is applied.

    - Type: List or Tuple of integers
    - Default: `[0, 0, 128, 128]`
    """

    selected_index = t.Int(None, allow_none=True).tag(sync=True)
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

    before_id = t.Unicode(None, allow_none=True).tag(sync=True)
    """The identifier of a layer in the Maplibre basemap layer stack.

    This deck.gl layer will be rendered just before the layer with the given identifier. You can find such an identifier by inspecting the basemap style JSON.

    For example, in the [Carto Positron style][lonboard.basemap.CartoStyle.Positron], if
    you look at the [raw JSON
    data](https://basemaps.cartocdn.com/gl/positron-gl-style/style.json), each layer has
    an `"id"` property. The first layer in the basemap stack has `"id": "background"`.
    So if you pass `before_id="background"`, you won't see your deck.gl layer because it
    will be rendered below **all** layers in the Maplibre basemap.

    A common choice for Carto-based styles is to use `before_id="watername_ocean"` so
    that your deck.gl layer is rendered above the core basemap elements but below all
    text labels.

    !!! info
        This only has an effect when the map's [`basemap`][lonboard.Map.basemap] is a
        [`MaplibreBasemap`][lonboard.basemap.MaplibreBasemap], and the map is rendering
        in [`"interleaved"` mode][lonboard.basemap.MaplibreBasemap.mode].
    """


def default_geoarrow_viewport(
    table: Table,
) -> tuple[Bbox, WeightedCentroid] | None:
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
    """Any Arrow-based layer should subclass from BaseArrowLayer."""

    # Note: these class attributes are **not** serialized to JS

    # Number of rows per chunk for serializing table and accessor columns.
    #
    # This is a _layer-level_ construct because we need to ensure the main table and all
    # accessors have exactly the same chunking, because each chunk is rendered
    # independently as a separate deck.gl layer
    _rows_per_chunk: int

    # The following traitlets **are** serialized to JS

    table: ArrowTableTrait
    """An Arrow table with data for this layer.

    Some downstream layers will require this table to have a geospatial column. Other
    layers, such as the [`H3HexagonLayer`][lonboard.layer.H3HexagonLayer] will accept
    non-geospatial data in conjunction with other accessors.
    """

    def _repr_keys(self) -> Generator[str, Any, None]:
        # Avoid rendering `table` in the string repr
        #
        # By default, `_repr_mimebundle_` creates the rich HTML content **and** a plain
        # text repr to show in environments that don't support rendering HTML. We want
        # to avoid generating a str repr of any large values.
        # https://github.com/developmentseed/lonboard/issues/1014
        for key in super()._repr_keys():
            if key != "table":
                yield key

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[BaseLayerKwargs],
    ) -> None:
        """Construct a Layer from a [GeoArrow] table.

        [GeoArrow]: https://geoarrow.org/

        This accepts Arrow data from any library implementing the [Arrow PyCapsule
        Interface], including pyarrow, arro3, DuckDB, and others.

        [Arrow PyCapsule Interface]: https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html

        The geometry column will be reprojected to `EPSG:4326` if it is not already in
        that coordinate system.

        Args:
            table: An Arrow table or stream object from a library implementing the [Arrow PyCapsule Interface]. This object must contain a column with a geometry type that has the `geoarrow` extension metadata.

        Keyword Args:
            kwargs: parameters passed on to `__init__`

        Returns:
            A Layer with the initialized data.

        """
        imported_stream = import_arrow_c_stream(table)
        if isinstance(imported_stream, Table):
            table_o3 = imported_stream
        else:
            assert isinstance(imported_stream, ChunkedArray)
            schema = Schema([imported_stream.field.with_name("geometry")])
            table_o3 = Table.from_arrays([imported_stream], schema=schema)
            table_o3 = add_positional_row_index(table_o3)

        parsed_tables = parse_serialized_table(table_o3)
        assert len(parsed_tables) == 1, (
            "Mixed geometry type input not supported here. Use the top "
            "level viz() function or separate your geometry types in advance."
        )
        table_o3 = parsed_tables[0]
        table_o3 = make_geometry_interleaved(table_o3)

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

        table_o3 = table_o3.rechunk(max_chunksize=rows_per_chunk)

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

        The GeoDataFrame will be reprojected to `EPSG:4326` if it is not already in that
        coordinate system.

        Args:
            gdf: The GeoDataFrame to set on the layer.

        Keyword Args:
            auto_downcast: If `True`, automatically downcast to smaller-size data types
                if possible without loss of precision. This calls
                [pandas.DataFrame.convert_dtypes][pandas.DataFrame.convert_dtypes] and
                [pandas.to_numeric][pandas.to_numeric] under the hood.
            kwargs: parameters passed on to `__init__`

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
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
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
                the `sql` parameter.

        Keyword Args:
            crs: The CRS of the input data. This can either be a string passed to
                `pyproj.CRS.from_user_input` or a `pyproj.CRS` object. Defaults to None.
            kwargs: parameters passed on to `__init__`

        Returns:
            A Layer with the initialized data.

        """
        if isinstance(sql, str):
            assert con is not None, "con must be provided when sql is a str"

            rel = con.sql(sql)
            table = _from_duckdb(rel, crs=crs)
        else:
            table = _from_duckdb(sql, crs=crs)

        return cls(table=table, **kwargs)
