"""High-level, super-simple API for visualizing GeoDataFrames"""

from __future__ import annotations

import json
from textwrap import dedent
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Union,
    cast,
)

import numpy as np
from arro3.core import Array, ChunkedArray, Schema, Table, struct_field

from lonboard._compat import check_pandas_version
from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.extension_types import construct_geometry_array
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.parse_wkb import parse_serialized_table
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
    import pyarrow
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

    VizDataInput = Union[
        gpd.GeoDataFrame,
        gpd.GeoSeries,
        pyarrow.Table,
        NDArray[np.object_],
        shapely.geometry.base.BaseGeometry,
        ArrowArrayExportable,
        ArrowStreamExportable,
        GeoInterfaceProtocol,
        Dict[str, Any],
        duckdb.DuckDBPyRelation,
    ]
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
    data: Union[VizDataInput, List[VizDataInput], Tuple[VizDataInput, ...]],
    *,
    scatterplot_kwargs: Optional[ScatterplotLayerKwargs] = None,
    path_kwargs: Optional[PathLayerKwargs] = None,
    polygon_kwargs: Optional[PolygonLayerKwargs] = None,
    map_kwargs: Optional[MapKwargs] = None,
    con: Optional[duckdb.DuckDBPyConnection] = None,
) -> Map:
    """A high-level function to plot your data easily.

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

            If you're using a custom connection, ensure you pass in the `con` parameter:

            ```py
            import duckdb
            from lonboard import viz

            con = duckdb.connect()
            sql = "SELECT * FROM spatial_table;"
            query = con.sql(sql)
            viz(query, con=con)
            ```

            You can also render an entire table by using the `table()` method:

            ```py
            import duckdb
            from lonboard import viz

            con = duckdb.connect()
            con.execute("CREATE TABLE spatial_table AS ...;")
            viz(con.table(), con=con)
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
    - pyarrow `Array` marked with a [GeoArrow extension type defined by geoarrow-pyarrow](https://geoarrow.org/geoarrow-python/main/pyarrow.html#geoarrow.pyarrow.GeometryExtensionType).

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
        con: the active DuckDB connection. This is necessary in some cases when passing
            in a DuckDB query. In particular, if you're using a non-global DuckDB
            connection and if your SQL query outputs the default `GEOMETRY` type.

    For more control over rendering, construct [`Map`][lonboard.Map] and `Layer` objects
    directly.

    Returns:
        widget visualizing the provided data.
    """
    global COLOR_COUNTER

    if isinstance(data, (list, tuple)):
        layers: List[Union[ScatterplotLayer, PathLayer, PolygonLayer]] = []
        for i, item in enumerate(data):
            ls = create_layers_from_data_input(
                item,
                _viz_color=COLORS[(COLOR_COUNTER + i) % len(COLORS)],
                scatterplot_kwargs=scatterplot_kwargs,
                path_kwargs=path_kwargs,
                polygon_kwargs=polygon_kwargs,
                con=con,
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
            con=con,
        )
        COLOR_COUNTER += 1

    map_kwargs = {} if not map_kwargs else map_kwargs

    if "basemap_style" not in map_kwargs.keys():
        map_kwargs["basemap_style"] = CartoBasemap.DarkMatter

    return Map(layers=layers, **map_kwargs)


DUCKDB_PY_CONN_ERROR = dedent("""\
    Must pass in DuckDBPyRelation object, not DuckDBPyConnection.

    Instead of using `duckdb.execute()` or `con.execute()`, use `duckdb.sql()` or
    `con.sql()`.

    If using `con.sql()`, ensure you pass the `con` into the `viz()` function:

    ```
    viz(con.sql("SELECT * FROM table;", con=con))
    ```

    Alternatively, you can call the `table()` method of `con`:

    ```
    viz(con.table("table_name", con=con))
    ```
    """)


def create_layers_from_data_input(
    data: VizDataInput, *, con: Optional[duckdb.DuckDBPyConnection] = None, **kwargs
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
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
        return _viz_duckdb_relation(data, con=con, **kwargs)  # type: ignore

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
        (cls.__name__ == "BaseGeometry" for cls in data.__class__.__mro__)
    ):
        return _viz_shapely_scalar(data, **kwargs)  # type: ignore

    # Anything with __arrow_c_array__
    if hasattr(data, "__arrow_c_array__"):
        data = cast("ArrowArrayExportable", data)
        return _viz_geoarrow_array(data, **kwargs)

    # Anything with __arrow_c_stream__
    if hasattr(data, "__arrow_c_stream__"):
        data = cast("ArrowStreamExportable", data)
        return _viz_geoarrow_table(Table.from_arrow(data), **kwargs)

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
            "Geometry, Feature, or FeatureCollection."
        )

    raise ValueError


def _viz_geopandas_geodataframe(
    data: gpd.GeoDataFrame, **kwargs
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    layers: List[Union[ScatterplotLayer, PathLayer, PolygonLayer]] = []
    for partial_gdf in split_mixed_gdf(data):
        table = geopandas_to_geoarrow(partial_gdf)
        layers.extend(_viz_geoarrow_table(table, **kwargs))

    return layers


def _viz_geopandas_geoseries(
    data: gpd.GeoSeries, **kwargs
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(geometry=data)  # type: ignore
    return _viz_geopandas_geodataframe(gdf, **kwargs)


def _viz_duckdb_relation(
    data: duckdb.DuckDBPyRelation,
    con: Optional[duckdb.DuckDBPyConnection] = None,
    **kwargs,
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    from lonboard._geoarrow._duckdb import from_duckdb

    table = from_duckdb(data, con=con)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_shapely_scalar(
    data: shapely.geometry.base.BaseGeometry, **kwargs
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    return _viz_shapely_array(np.array([data]), **kwargs)


def _viz_shapely_array(
    data: NDArray[np.object_], **kwargs
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    layers: List[Union[ScatterplotLayer, PathLayer, PolygonLayer]] = []
    for partial_geometry_array in split_mixed_shapely_array(data):
        field, geom_arr = construct_geometry_array(
            partial_geometry_array,
        )
        table = Table.from_arrays([geom_arr], schema=Schema([field]))
        layers.extend(_viz_geoarrow_table(table, **kwargs))

    return layers


def _viz_geo_interface(
    data: dict, **kwargs
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    try:
        import pyarrow as pa
    except ImportError as e:
        raise ImportError(
            "pyarrow required for visualizing __geo_interface__ objects.\n"
            "Run `pip install pyarrow`."
        ) from e

    try:
        import shapely
    except ImportError as e:
        raise ImportError(
            "shapely required for visualizing __geo_interface__ objects.\n"
            "Run `pip install shapely`."
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
            [feature["properties"] for feature in data["features"]]
        )

        fields = []
        arrays = []
        for field_idx in range(attribute_columns_struct.type.num_fields):
            fields.append(attribute_columns_struct.type.field(field_idx))
            arrays.append(struct_field(attribute_columns_struct, field_idx))  # type: ignore

        table = pa.Table.from_arrays(arrays, schema=pa.schema(fields))
        df = table.to_pandas(types_mapper=pd.ArrowDtype)

        shapely_geom_arr = shapely.from_geojson(
            [json.dumps(feature["geometry"]) for feature in data["features"]]
        )
        gdf = gpd.GeoDataFrame(df, geometry=shapely_geom_arr)  # type: ignore
        return _viz_geopandas_geodataframe(gdf, **kwargs)

    geo_interface_type = data["type"]
    raise ValueError(f"type '{geo_interface_type}' not supported.")


def _viz_geoarrow_array(
    data: ArrowArrayExportable,
    **kwargs,
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    array = Array.from_arrow(data)
    field = array.field.with_name("geometry")
    schema = Schema([field])
    table = Table.from_arrays([array], schema=schema)

    num_rows = len(array)
    if num_rows <= np.iinfo(np.uint8).max:
        arange_col = Array.from_numpy(np.arange(num_rows, dtype=np.uint8))
    elif num_rows <= np.iinfo(np.uint16).max:
        arange_col = Array.from_numpy(np.arange(num_rows, dtype=np.uint16))
    elif num_rows <= np.iinfo(np.uint32).max:
        arange_col = Array.from_numpy(np.arange(num_rows, dtype=np.uint32))
    else:
        arange_col = Array.from_numpy(np.arange(num_rows, dtype=np.uint64))

    table = table.append_column("row_index", ChunkedArray([arange_col]))
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geoarrow_table(
    table: Table,
    *,
    _viz_color: str,
    scatterplot_kwargs: Optional[ScatterplotLayerKwargs] = None,
    path_kwargs: Optional[PathLayerKwargs] = None,
    polygon_kwargs: Optional[PolygonLayerKwargs] = None,
) -> List[Union[ScatterplotLayer, PathLayer, PolygonLayer]]:
    parsed_tables = parse_serialized_table(table)
    if len(parsed_tables) > 1:
        output: List[Union[ScatterplotLayer, PathLayer, PolygonLayer]] = []
        for parsed_table in parsed_tables:
            output.extend(
                _viz_geoarrow_table(
                    parsed_table,
                    _viz_color=_viz_color,
                    scatterplot_kwargs=scatterplot_kwargs,
                    path_kwargs=path_kwargs,
                    polygon_kwargs=polygon_kwargs,
                )
            )

        return output
    else:
        table = parsed_tables[0]

    geometry_column_index = get_geometry_column_index(table.schema)
    assert (
        geometry_column_index is not None
    ), "One column must have GeoArrow extension metadata"

    geometry_field = table.schema.field(geometry_column_index)
    geometry_ext_type = geometry_field.metadata.get(b"ARROW:extension:name")

    if geometry_ext_type in [EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT]:
        scatterplot_kwargs = {} if not scatterplot_kwargs else scatterplot_kwargs

        if "get_fill_color" not in scatterplot_kwargs.keys():
            scatterplot_kwargs["get_fill_color"] = _viz_color

        if "radius_min_pixels" not in scatterplot_kwargs.keys():
            if len(table) <= 10_000:
                scatterplot_kwargs["radius_min_pixels"] = 2
            elif len(table) <= 100_000:
                scatterplot_kwargs["radius_min_pixels"] = 1
            elif len(table) <= 1_000_000:
                scatterplot_kwargs["radius_min_pixels"] = 0.5
            else:
                scatterplot_kwargs["radius_min_pixels"] = 0.2

        if "opacity" not in scatterplot_kwargs.keys():
            if len(table) <= 10_000:
                scatterplot_kwargs["opacity"] = 0.9
            elif len(table) <= 100_000:
                scatterplot_kwargs["opacity"] = 0.7
            elif len(table) <= 1_000_000:
                scatterplot_kwargs["opacity"] = 0.5

        return [ScatterplotLayer(table=table, **scatterplot_kwargs)]

    elif geometry_ext_type in [
        EXTENSION_NAME.LINESTRING,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        path_kwargs = {} if not path_kwargs else path_kwargs

        if "get_color" not in path_kwargs.keys():
            path_kwargs["get_color"] = _viz_color

        if "width_min_pixels" not in path_kwargs.keys():
            if len(table) <= 1_000:
                path_kwargs["width_min_pixels"] = 1.5
            elif len(table) <= 10_000:
                path_kwargs["width_min_pixels"] = 1
            elif len(table) <= 100_000:
                path_kwargs["width_min_pixels"] = 0.7
            else:
                path_kwargs["width_min_pixels"] = 0.5

        if "opacity" not in path_kwargs.keys():
            if len(table) <= 1_000:
                path_kwargs["opacity"] = 0.9
            elif len(table) <= 10_000:
                path_kwargs["opacity"] = 0.7
            elif len(table) <= 100_000:
                path_kwargs["opacity"] = 0.5

        return [PathLayer(table=table, **path_kwargs)]

    elif geometry_ext_type in [EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON]:
        polygon_kwargs = {} if not polygon_kwargs else polygon_kwargs

        if "get_fill_color" not in polygon_kwargs.keys():
            polygon_kwargs["get_fill_color"] = _viz_color

        if "get_line_color" not in polygon_kwargs.keys():
            polygon_kwargs["get_line_color"] = DEFAULT_POLYGON_LINE_COLOR

        if "opacity" not in polygon_kwargs.keys():
            polygon_kwargs["opacity"] = 0.5

        if "line_width_min_pixels" not in polygon_kwargs.keys():
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

    raise ValueError(f"Unsupported extension type: '{geometry_ext_type}'.")
