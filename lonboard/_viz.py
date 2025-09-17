"""High-level, super-simple API for visualizing GeoDataFrames."""

# ruff: noqa: C901, PLR0911, PLR0912, PLR0913, PLR0915

from __future__ import annotations

import json
import warnings
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, cast

import numpy as np
from arro3.core import Array, ChunkedArray, Schema, Table, struct_field

from lonboard._compat import check_pandas_version
from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.c_stream_import import import_arrow_c_stream
from lonboard._geoarrow.extension_types import construct_geometry_array
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.parse_wkb import parse_serialized_table
from lonboard._geoarrow.row_index import add_positional_row_index
from lonboard._layer import PathLayer, PolygonLayer, ScatterplotLayer
from lonboard._map import Map
from lonboard._utils import (
    get_geometry_column_index,
    split_mixed_gdf,
    split_mixed_shapely_array,
)
from lonboard.basemap import CartoBasemap

if TYPE_CHECKING:
    import duckdb
    import geopandas as gpd
    import pyarrow as pa
    import shapely.geometry
    import shapely.geometry.base
    from arro3.core.types import ArrowArrayExportable, ArrowStreamExportable
    from numpy.typing import NDArray

    from lonboard.types.layer import (
        PathLayerKwargs,
        PolygonLayerKwargs,
        ScatterplotLayerKwargs,
    )
    from lonboard.types.map import MapKwargs

    class GeoInterfaceProtocol(Protocol):
        @property
        def __geo_interface__(self) -> dict: ...

    VizDataInput: TypeAlias = (
        gpd.GeoDataFrame
        | gpd.GeoSeries
        | pa.Table
        | NDArray[np.object_]
        | shapely.geometry.base.BaseGeometry
        | ArrowArrayExportable
        | ArrowStreamExportable
        | GeoInterfaceProtocol
        | dict[str, Any]
        | duckdb.DuckDBPyRelation
    )
    """A type definition for allowed data inputs to the `viz` function."""


# From mbview
# https://github.com/mapbox/mbview/blob/e64bd86cfe4a63e6af4ea1d310bd49be4f162a43/views/vector.ejs#L75-L87
COLORS = [
    "#FC49A3",  # pink
    "#CC66FF",  # purple-ish
    "#66CCFF",  # sky blue
    "#66FFCC",  # teal
    "#00FF00",  # lime green
    "#FFCC66",  # light orange
    "#FF6666",  # salmon
    "#FF0000",  # red
    "#FF8000",  # orange
    "#FFFF66",  # yellow
    "#00FFFF",  # turquoise
]
COLOR_COUNTER = 0
DEFAULT_POLYGON_LINE_COLOR = [0, 0, 0, 200]


def viz(
    data: VizDataInput | list[VizDataInput] | tuple[VizDataInput, ...],
    *,
    scatterplot_kwargs: ScatterplotLayerKwargs | None = None,
    path_kwargs: PathLayerKwargs | None = None,
    polygon_kwargs: PolygonLayerKwargs | None = None,
    map_kwargs: MapKwargs | None = None,
    con: duckdb.DuckDBPyConnection | None = None,
) -> Map:
    """Plot your data easily.

    The goal of this function is to make it simple to get _something_ showing on a map.
    For more control over rendering, construct `Map` and `Layer` objects directly.

    This function accepts a variety of geospatial inputs:

    - GeoPandas `GeoDataFrame`.
    - GeoPandas `GeoSeries`.
    - numpy array of Shapely objects.
    - Single Shapely object.
    - A DuckDB query with a spatial column from DuckDB Spatial.

        !!! warning

            The DuckDB query must be run with
            [`duckdb.sql()`](https://duckdb.org/docs/api/python/reference/#duckdb.sql)
            or
            [`duckdb.DuckDBPyConnection.sql()`](https://duckdb.org/docs/api/python/reference/#duckdb.DuckDBPyConnection.sql)
            and not with `duckdb.execute()` or `duckdb.DuckDBPyConnection.execute()`.

            For example

            ```py
            import duckdb
            from lonboard import viz

            sql = "SELECT * FROM spatial_table;"
            query = duckdb.sql(sql)
            viz(query)
            ```

            You can also render an entire table by using the `table()` method:

            ```py
            import duckdb
            from lonboard import viz

            con = duckdb.connect()
            con.execute("CREATE TABLE spatial_table AS ...;")
            viz(con.table("spatial_table"))
            ```

        !!! warning

            DuckDB Spatial does not currently expose coordinate reference system
            information, so the user must ensure that data has been reprojected to
            EPSG:4326.

    - Any Python class with a `__geo_interface__` property conforming to the
        [Geo Interface protocol](https://gist.github.com/sgillies/2217756).
    - `dict` holding GeoJSON-like data.
    - pyarrow `Table` with a geometry column marked with a
        [GeoArrow](https://geoarrow.org/) extension type.
    - pyarrow `Array` or `ChunkedArray` marked with a [GeoArrow extension type defined by geoarrow-pyarrow](https://geoarrow.org/geoarrow-python/main/pyarrow.html#geoarrow.pyarrow.GeometryExtensionType).
    - Arrow-compatible Array, ChunkedArray, Table, or RecordBatch objects that have associated GeoArrow metadata. An object is "Arrow-compatible" if it implements the [Arrow PyCapsule Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html) and has either an `__arrow_c_array__` or `__arrow_c_stream__` method. The provided Arrow data must be or have a geometry column marked with a GeoArrow extension type.

        Some examples of these sources include pyogrio's [`open_arrow`][pyogrio.open_arrow], DuckDB Spatial, [GeoArrow-Rust's Python bindings](https://geoarrow.org/geoarrow-rs/python/latest/), [GeoDataFusion database connections](https://github.com/datafusion-contrib/datafusion-geo), and, soon, [GeoPolars DataFrames](https://github.com/geopolars/geopolars).

    Alternatively, you can pass a `list` or `tuple` of any of the above inputs.

    If you want to easily add more data, to an existing map, you can pass the output of
    `viz` into [`Map.add_layer`][lonboard.Map.add_layer].

    Args:
        data: a data object of any supported type.

    Keyword Args:
        scatterplot_kwargs: a `dict` of parameters to pass down to all generated
            [`ScatterplotLayer`][lonboard.ScatterplotLayer]s.
        path_kwargs: a `dict` of parameters to pass down to all generated
            [`PathLayer`][lonboard.PathLayer]s.
        polygon_kwargs: a `dict` of parameters to pass down to all generated
            [`PolygonLayer`][lonboard.PolygonLayer]s.
        map_kwargs: a `dict` of parameters to pass down to the generated
            [`Map`][lonboard.Map].
        con: Deprecated: the active DuckDB connection. This argument has no effect and
            might be removed in the future.

    For more control over rendering, construct [`Map`][lonboard.Map] and `Layer` objects
    directly.

    Returns:
        widget visualizing the provided data.

    """
    global COLOR_COUNTER  # noqa: PLW0603 Using the global statement to update `COLOR_COUNTER` is discouraged

    if con is not None:
        warnings.warn(
            "The 'con' argument is deprecated and may be removed in a future version. "
            "It has no effect.",
            category=DeprecationWarning,
            stacklevel=2,
        )

    if isinstance(data, (list, tuple)):
        layers: list[ScatterplotLayer | PathLayer | PolygonLayer] = []
        for i, item in enumerate(data):
            ls = create_layers_from_data_input(
                item,
                _viz_color=COLORS[(COLOR_COUNTER + i) % len(COLORS)],
                scatterplot_kwargs=scatterplot_kwargs,
                path_kwargs=path_kwargs,
                polygon_kwargs=polygon_kwargs,
            )
            layers.extend(ls)

        COLOR_COUNTER += len(layers)
    else:
        layers = create_layers_from_data_input(
            data,
            _viz_color=COLORS[COLOR_COUNTER % len(COLORS)],
            scatterplot_kwargs=scatterplot_kwargs,
            path_kwargs=path_kwargs,
            polygon_kwargs=polygon_kwargs,
        )
        COLOR_COUNTER += 1

    map_kwargs = map_kwargs if map_kwargs else {}

    if "basemap_style" not in map_kwargs:
        map_kwargs["basemap_style"] = CartoBasemap.DarkMatter

    return Map(layers=layers, **map_kwargs)


DUCKDB_PY_CONN_ERROR = dedent("""\
    Must pass in DuckDBPyRelation object, not DuckDBPyConnection.

    Instead of using `duckdb.execute()` or `con.execute()`, use `duckdb.sql()`,
    `con.sql()` or `con.table()`.
    """)


def create_layers_from_data_input(
    data: VizDataInput,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    """Create one or more renderable layers from data input.

    This helper function can create multiple layers in the case of mixed input.
    """
    # geopandas GeoDataFrame
    if (
        data.__class__.__module__.startswith("geopandas")
        and data.__class__.__name__ == "GeoDataFrame"
    ):
        return _viz_geopandas_geodataframe(data, **kwargs)  # type: ignore

    # geopandas GeoSeries
    if (
        data.__class__.__module__.startswith("geopandas")
        and data.__class__.__name__ == "GeoSeries"
    ):
        return _viz_geopandas_geoseries(data, **kwargs)  # type: ignore

    # duckdb DuckDBPyRelation
    if (
        data.__class__.__module__.startswith("duckdb")
        and data.__class__.__name__ == "DuckDBPyRelation"
    ):
        return _viz_duckdb_relation(data, **kwargs)  # type: ignore

    if (
        data.__class__.__module__.startswith("duckdb")
        and data.__class__.__name__ == "DuckDBPyConnection"
    ):
        raise TypeError(DUCKDB_PY_CONN_ERROR)

    # Shapely array
    if isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.object_):
        return _viz_shapely_array(data, **kwargs)

    # Shapely scalar
    if data.__class__.__module__.startswith("shapely") and any(
        cls.__name__ == "BaseGeometry" for cls in data.__class__.__mro__
    ):
        return _viz_shapely_scalar(data, **kwargs)  # type: ignore

    # Anything with __arrow_c_array__
    if hasattr(data, "__arrow_c_array__"):
        data = cast("ArrowArrayExportable", data)
        array = Array.from_arrow(data)
        ca = ChunkedArray([array])
        return _viz_geoarrow_chunked_array(ca, **kwargs)

    # Anything with __arrow_c_stream__
    if hasattr(data, "__arrow_c_stream__"):
        data = cast("ArrowStreamExportable", data)
        imported_stream = import_arrow_c_stream(data)
        if isinstance(imported_stream, Table):
            return _viz_geoarrow_table(imported_stream, **kwargs)

        assert isinstance(imported_stream, ChunkedArray)
        return _viz_geoarrow_chunked_array(imported_stream, **kwargs)

    # Anything with __geo_interface__
    if hasattr(data, "__geo_interface__"):
        data = cast("GeoInterfaceProtocol", data)
        return _viz_geo_interface(data.__geo_interface__, **kwargs)

    # GeoJSON dict
    if isinstance(data, dict):
        if data.get("type") in [
            "Point",
            "LineString",
            "Polygon",
            "MultiPoint",
            "MultiLineString",
            "MultiPolygon",
            "GeometryCollection",
            "Feature",
            "FeatureCollection",
        ]:
            return _viz_geo_interface(data, **kwargs)

        raise ValueError(
            "If passing a dict, must be a GeoJSON "
            "Geometry, Feature, or FeatureCollection.",
        )

    raise ValueError


def _viz_geopandas_geodataframe(
    data: gpd.GeoDataFrame,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    layers: list[ScatterplotLayer | PathLayer | PolygonLayer] = []
    for partial_gdf in split_mixed_gdf(data):
        table = geopandas_to_geoarrow(partial_gdf)
        layers.extend(_viz_geoarrow_table(table, **kwargs))

    return layers


def _viz_geopandas_geoseries(
    data: gpd.GeoSeries,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(geometry=data)  # type: ignore
    return _viz_geopandas_geodataframe(gdf, **kwargs)


def _viz_duckdb_relation(
    data: duckdb.DuckDBPyRelation,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    from lonboard._geoarrow._duckdb import from_duckdb

    table = from_duckdb(data)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_shapely_scalar(
    data: shapely.geometry.base.BaseGeometry,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    return _viz_shapely_array(np.array([data]), **kwargs)


def _viz_shapely_array(
    data: NDArray[np.object_],
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    layers: list[ScatterplotLayer | PathLayer | PolygonLayer] = []
    for partial_geometry_array in split_mixed_shapely_array(data):
        field, geom_arr = construct_geometry_array(
            partial_geometry_array,
        )
        table = Table.from_arrays([geom_arr], schema=Schema([field]))
        layers.extend(_viz_geoarrow_table(table, **kwargs))

    return layers


def _viz_geo_interface(
    data: dict,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    try:
        import pyarrow as pa
    except ImportError as e:
        raise ImportError(
            "pyarrow required for visualizing __geo_interface__ objects.\n"
            "Run `pip install pyarrow`.",
        ) from e

    try:
        import shapely
    except ImportError as e:
        raise ImportError(
            "shapely required for visualizing __geo_interface__ objects.\n"
            "Run `pip install shapely`.",
        ) from e

    if data["type"] in [
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    ]:
        return _viz_shapely_scalar(shapely.from_geojson(json.dumps(data)), **kwargs)

    if data["type"] == "Feature":
        attribute_columns = {k: [v] for k, v in data["properties"].items()}
        table = pa.table(attribute_columns)
        shapely_geom = shapely.from_geojson(json.dumps(data["geometry"]))
        field, geom_arr = construct_geometry_array(np.array([shapely_geom]))
        return _viz_geoarrow_table(table.append_column(field, geom_arr), **kwargs)

    if data["type"] == "FeatureCollection":
        # We currently take a FeatureCollection through GeoPandas so that we can handle
        # mixed-geometry type collections
        import geopandas as gpd
        import pandas as pd

        check_pandas_version()

        attribute_columns_struct = pa.array(
            [feature["properties"] for feature in data["features"]],
        )

        fields = []
        arrays = []
        for field_idx in range(attribute_columns_struct.type.num_fields):
            fields.append(attribute_columns_struct.type.field(field_idx))
            arrays.append(struct_field(attribute_columns_struct, field_idx))  # type: ignore

        table = pa.Table.from_arrays(arrays, schema=pa.schema(fields))
        df = table.to_pandas(types_mapper=pd.ArrowDtype)

        shapely_geom_arr = shapely.from_geojson(
            [json.dumps(feature["geometry"]) for feature in data["features"]],
        )
        gdf = gpd.GeoDataFrame(df, geometry=shapely_geom_arr)  # type: ignore
        return _viz_geopandas_geodataframe(gdf, **kwargs)

    geo_interface_type = data["type"]
    raise ValueError(f"type '{geo_interface_type}' not supported.")


def _viz_geoarrow_chunked_array(
    ca: ChunkedArray,
    **kwargs: Any,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    field = ca.field.with_name("geometry")
    schema = Schema([field])
    table = Table.from_arrays([ca], schema=schema)
    table = add_positional_row_index(table)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geoarrow_table(
    table: Table,
    *,
    _viz_color: str,
    scatterplot_kwargs: ScatterplotLayerKwargs | None = None,
    path_kwargs: PathLayerKwargs | None = None,
    polygon_kwargs: PolygonLayerKwargs | None = None,
) -> list[ScatterplotLayer | PathLayer | PolygonLayer]:
    parsed_tables = parse_serialized_table(table)
    if len(parsed_tables) > 1:
        output: list[ScatterplotLayer | PathLayer | PolygonLayer] = []
        for parsed_table in parsed_tables:
            output.extend(
                _viz_geoarrow_table(
                    parsed_table,
                    _viz_color=_viz_color,
                    scatterplot_kwargs=scatterplot_kwargs,
                    path_kwargs=path_kwargs,
                    polygon_kwargs=polygon_kwargs,
                ),
            )

        return output
    table = parsed_tables[0]

    geometry_column_index = get_geometry_column_index(table.schema)
    assert geometry_column_index is not None, (
        "One column must have GeoArrow extension metadata"
    )

    geometry_field = table.schema.field(geometry_column_index)
    geometry_ext_type = geometry_field.metadata.get(b"ARROW:extension:name")

    if geometry_ext_type in [EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT]:
        scatterplot_kwargs = scatterplot_kwargs if scatterplot_kwargs else {}

        if "get_fill_color" not in scatterplot_kwargs:
            scatterplot_kwargs["get_fill_color"] = _viz_color

        if "radius_min_pixels" not in scatterplot_kwargs:
            if len(table) <= 10_000:
                scatterplot_kwargs["radius_min_pixels"] = 2
            elif len(table) <= 100_000:
                scatterplot_kwargs["radius_min_pixels"] = 1
            elif len(table) <= 1_000_000:
                scatterplot_kwargs["radius_min_pixels"] = 0.5
            else:
                scatterplot_kwargs["radius_min_pixels"] = 0.2

        if "opacity" not in scatterplot_kwargs:
            if len(table) <= 10_000:
                scatterplot_kwargs["opacity"] = 0.9
            elif len(table) <= 100_000:
                scatterplot_kwargs["opacity"] = 0.7
            elif len(table) <= 1_000_000:
                scatterplot_kwargs["opacity"] = 0.5

        return [ScatterplotLayer(table=table, **scatterplot_kwargs)]

    if geometry_ext_type in [
        EXTENSION_NAME.LINESTRING,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        path_kwargs = path_kwargs if path_kwargs else {}

        if "get_color" not in path_kwargs:
            path_kwargs["get_color"] = _viz_color

        if "width_min_pixels" not in path_kwargs:
            if len(table) <= 1_000:
                path_kwargs["width_min_pixels"] = 1.5
            elif len(table) <= 10_000:
                path_kwargs["width_min_pixels"] = 1
            elif len(table) <= 100_000:
                path_kwargs["width_min_pixels"] = 0.7
            else:
                path_kwargs["width_min_pixels"] = 0.5

        if "opacity" not in path_kwargs:
            if len(table) <= 1_000:
                path_kwargs["opacity"] = 0.9
            elif len(table) <= 10_000:
                path_kwargs["opacity"] = 0.7
            elif len(table) <= 100_000:
                path_kwargs["opacity"] = 0.5

        return [PathLayer(table=table, **path_kwargs)]

    if geometry_ext_type in [
        EXTENSION_NAME.POLYGON,
        EXTENSION_NAME.MULTIPOLYGON,
        EXTENSION_NAME.BOX,
    ]:
        polygon_kwargs = polygon_kwargs if polygon_kwargs else {}

        if "get_fill_color" not in polygon_kwargs:
            polygon_kwargs["get_fill_color"] = _viz_color

        if "get_line_color" not in polygon_kwargs:
            polygon_kwargs["get_line_color"] = DEFAULT_POLYGON_LINE_COLOR

        if "opacity" not in polygon_kwargs:
            polygon_kwargs["opacity"] = 0.5

        if "line_width_min_pixels" not in polygon_kwargs:
            if len(table) <= 100:
                polygon_kwargs["line_width_min_pixels"] = 0.5
            if len(table) <= 1_000:
                polygon_kwargs["line_width_min_pixels"] = 0.45
            if len(table) <= 5_000:
                polygon_kwargs["line_width_min_pixels"] = 0.4
            elif len(table) <= 10_000:
                polygon_kwargs["line_width_min_pixels"] = 0.3
            elif len(table) <= 100_000:
                polygon_kwargs["line_width_min_pixels"] = 0.25
            else:
                polygon_kwargs["line_width_min_pixels"] = 0.2

        return [PolygonLayer(table=table, **polygon_kwargs)]

    raise ValueError(f"Unsupported extension type: '{geometry_ext_type!r}'.")
