"""High-level, super-simple API for visualizing GeoDataFrames"""

from __future__ import annotations

import json
from random import shuffle
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
import pyarrow as pa
import pyarrow.compute as pc
import shapely.geometry
import shapely.geometry.base
from numpy.typing import NDArray

from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.extension_types import construct_geometry_array
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.parse_wkb import parse_wkb_table
from lonboard._geoarrow.sanitize import remove_extension_classes
from lonboard._layer import PathLayer, PolygonLayer, ScatterplotLayer
from lonboard._map import Map
from lonboard._utils import get_geometry_column_index
from lonboard.basemap import CartoBasemap
from lonboard.types.layer import (
    PathLayerKwargs,
    PolygonLayerKwargs,
    ScatterplotLayerKwargs,
)
from lonboard.types.map import MapKwargs

if TYPE_CHECKING:
    import geopandas as gpd

    class GeoInterfaceProtocol(Protocol):
        @property
        def __geo_interface__(self) -> dict: ...

    class ArrowArrayExportable(Protocol):
        def __arrow_c_array__(
            self, requested_schema: object | None = None
        ) -> Tuple[object, object]: ...

    class ArrowStreamExportable(Protocol):
        def __arrow_c_stream__(
            self, requested_schema: object | None = None
        ) -> object: ...

    VizDataInput = Union[
        gpd.GeoDataFrame,
        gpd.GeoSeries,
        pa.Table,
        NDArray[np.object_],
        shapely.geometry.base.BaseGeometry,
        ArrowStreamExportable,
        GeoInterfaceProtocol,
        Dict[str, Any],
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
DEFAULT_POLYGON_LINE_COLOR = [0, 0, 0, 200]


def viz(
    data: Union[VizDataInput, List[VizDataInput], Tuple[VizDataInput, ...]],
    *,
    scatterplot_kwargs: Optional[ScatterplotLayerKwargs] = None,
    path_kwargs: Optional[PathLayerKwargs] = None,
    polygon_kwargs: Optional[PolygonLayerKwargs] = None,
    map_kwargs: Optional[MapKwargs] = None,
) -> Map:
    """A high-level function to plot your data easily.

    The goal of this function is to make it simple to get _something_ showing on a map.
    For more control over rendering, construct `Map` and `Layer` objects directly.

    This function accepts a variety of geospatial inputs:

    - geopandas `GeoDataFrame`
    - geopandas `GeoSeries`
    - numpy array of Shapely objects
    - Single Shapely object
    - Any Python class with a `__geo_interface__` property conforming to the
        [Geo Interface protocol](https://gist.github.com/sgillies/2217756).
    - `dict` holding GeoJSON-like data.
    - pyarrow `Table` with a geometry column marked with a GeoArrow extension type

    Alternatively, you can pass a `list` or `tuple` of any of the above inputs.

    Args:
        data: a data object of any supported type.

    Other args:
        scatterplot_kwargs: a `dict` of parameters to pass down to all generated
          [`ScatterplotLayer`][lonboard.ScatterplotLayer]s.
        path_kwargs: a `dict` of parameters to pass down to all generated
          [`PathLayer`][lonboard.PathLayer]s.
        polygon_kwargs: a `dict` of parameters to pass down to all generated
          [`PolygonLayer`][lonboard.PolygonLayer]s.
        map_kwargs: a `dict` of parameters to pass down to the generated
          [`Map`][lonboard.Map].

    For more control over rendering, construct `Map` and `Layer` objects directly.

    Returns:
        widget visualizing the provided data.
    """
    color_ordering = COLORS.copy()
    shuffle(color_ordering)

    if isinstance(data, (list, tuple)):
        layers = [
            create_layer_from_data_input(
                item,
                _viz_color=color_ordering[i % len(color_ordering)],
                scatterplot_kwargs=scatterplot_kwargs,
                path_kwargs=path_kwargs,
                polygon_kwargs=polygon_kwargs,
            )
            for i, item in enumerate(data)
        ]
    else:
        layers = [
            create_layer_from_data_input(
                data,
                _viz_color=color_ordering[0],
                scatterplot_kwargs=scatterplot_kwargs,
                path_kwargs=path_kwargs,
                polygon_kwargs=polygon_kwargs,
            )
        ]

    map_kwargs = {} if not map_kwargs else map_kwargs

    if "basemap_style" not in map_kwargs.keys():
        map_kwargs["basemap_style"] = CartoBasemap.DarkMatter

    return Map(layers=layers, **map_kwargs)


def create_layer_from_data_input(
    data: VizDataInput, **kwargs
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
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

    # pyarrow table
    if isinstance(data, pa.Table):
        return _viz_geoarrow_table(data, **kwargs)

    # Shapely array
    if isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.object_):
        return _viz_shapely_array(data, **kwargs)

    # Shapely scalar
    if isinstance(data, shapely.geometry.base.BaseGeometry):
        return _viz_shapely_scalar(data, **kwargs)

    # Anything with __arrow_c_array__
    if hasattr(data, "__arrow_c_array__"):
        data = cast("ArrowArrayExportable", data)
        return _viz_geoarrow_array(data, **kwargs)

    # Anything with __arrow_c_stream__
    if hasattr(data, "__arrow_c_stream__"):
        data = cast("ArrowStreamExportable", data)
        return _viz_geoarrow_table(pa.table(data), **kwargs)

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
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
    table = geopandas_to_geoarrow(data)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geopandas_geoseries(
    data: gpd.GeoSeries, **kwargs
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(geometry=data)
    table = geopandas_to_geoarrow(gdf)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_shapely_scalar(
    data: shapely.geometry.base.BaseGeometry, **kwargs
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
    return _viz_shapely_array(np.array([data]), **kwargs)


def _viz_shapely_array(
    data: NDArray[np.object_], **kwargs
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
    # TODO: pass include_z?
    field, geom_arr = construct_geometry_array(data)
    schema = pa.schema([field])
    table = pa.Table.from_arrays([geom_arr], schema=schema)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geo_interface(
    data: dict, **kwargs
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
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
        attribute_columns_struct = pa.array(
            [feature["properties"] for feature in data["features"]]
        )

        fields = []
        arrays = []
        for field_idx in range(attribute_columns_struct.type.num_fields):
            fields.append(attribute_columns_struct.type.field(field_idx))
            arrays.append(pc.struct_field(attribute_columns_struct, field_idx))

        table = pa.Table.from_arrays(arrays, schema=pa.schema(fields))

        shapely_geom_arr = shapely.from_geojson(
            [json.dumps(feature["geometry"]) for feature in data["features"]]
        )
        field, geom_arr = construct_geometry_array(shapely_geom_arr)
        return _viz_geoarrow_table(table.append_column(field, geom_arr), **kwargs)

    geo_interface_type = data["type"]
    raise ValueError(f"type '{geo_interface_type}' not supported.")


def _viz_geoarrow_array(
    data: ArrowArrayExportable,
    **kwargs,
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
    schema_capsule, array_capsule = data.__arrow_c_array__()

    # If the user doesn't have pyarrow extension types registered for geoarrow types,
    # `pa.array()` will lose the extension metadata. Instead, we manually persist the
    # extension metadata by extracting both the field and the array.

    class ArrayHolder:
        schema_capsule: object
        array_capsule: object

        def __init__(self, schema_capsule, array_capsule) -> None:
            self.schema_capsule = schema_capsule
            self.array_capsule = array_capsule

        def __arrow_c_array__(self, requested_schema):
            return self.schema_capsule, self.array_capsule

    if not hasattr(pa.Field, "_import_from_c_capsule"):
        raise KeyError(
            "Incompatible version of pyarrow: pa.Field does not have"
            "  _import_from_c_capsule method"
        )

    field = pa.Field._import_from_c_capsule(schema_capsule)
    array = pa.array(ArrayHolder(field.__arrow_c_schema__(), array_capsule))
    schema = pa.schema([field.with_name("geometry")])
    table = pa.Table.from_arrays([array], schema=schema)

    num_rows = len(array)
    if num_rows <= np.iinfo(np.uint8).max:
        arange_col = np.arange(num_rows, dtype=np.uint8)
    elif num_rows <= np.iinfo(np.uint16).max:
        arange_col = np.arange(num_rows, dtype=np.uint16)
    elif num_rows <= np.iinfo(np.uint32).max:
        arange_col = np.arange(num_rows, dtype=np.uint32)
    else:
        arange_col = np.arange(num_rows, dtype=np.uint64)

    table = table.append_column("row_index", pa.array(arange_col))
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geoarrow_table(
    table: pa.Table,
    *,
    _viz_color: str,
    scatterplot_kwargs: Optional[ScatterplotLayerKwargs] = None,
    path_kwargs: Optional[PathLayerKwargs] = None,
    polygon_kwargs: Optional[PolygonLayerKwargs] = None,
) -> Union[ScatterplotLayer, PathLayer, PolygonLayer]:
    table = remove_extension_classes(table)
    table = parse_wkb_table(table)

    geometry_column_index = get_geometry_column_index(table.schema)
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

        return ScatterplotLayer(table=table, **scatterplot_kwargs)

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

        return PathLayer(table=table, **path_kwargs)

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

        return PolygonLayer(table=table, **polygon_kwargs)

    raise ValueError(f"Unsupported extension type: '{geometry_ext_type}'.")
