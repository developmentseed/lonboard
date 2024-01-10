"""High-level, super-simple API for visualizing GeoDataFrames
"""
from __future__ import annotations

import json
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
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

from lonboard._constants import EPSG_4326, EXTENSION_NAME, OGC_84
from lonboard._geoarrow.extension_types import construct_geometry_array
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._layer import PathLayer, ScatterplotLayer, SolidPolygonLayer
from lonboard._map import Map

if TYPE_CHECKING:
    import geopandas as gpd

    class GeoInterfaceProtocol(Protocol):
        @property
        def __geo_interface__(self) -> dict:
            ...

    class ArrowStreamExportable(Protocol):
        def __arrow_c_stream__(self, requested_schema: object | None = None) -> object:
            ...

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


def viz(
    data: Union[VizDataInput, List[VizDataInput], Tuple[VizDataInput, ...]],
    **kwargs,
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

    Named args:
        Any other keyword arguments will be passed onto the relevant layer, either a
        `ScatterplotLayer`, `PathLayer`, or `SolidPolygonLayer`.

        If you pass a `list` or `tuple` of data objects, `kwargs` will be passed to
        _all_ layers. For more control over rendering, construct `Map` and `Layer`
        objects directly.

    Returns:
        widget visualizing the provided data.
    """
    if isinstance(data, (list, tuple)):
        layers = [create_layer_from_data_input(item, **kwargs) for item in data]
    else:
        layers = [create_layer_from_data_input(data, **kwargs)]

    return Map(layers=layers)


def create_layer_from_data_input(
    data: VizDataInput, **kwargs
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
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

    # Anything with __arrow_c_stream__
    if hasattr(data, "__arrow_c_stream__"):
        data = cast(ArrowStreamExportable, data)
        return _viz_geoarrow_table(pa.table(data.__arrow_c_stream__()), **kwargs)

    # Anything with __geo_interface__
    if hasattr(data, "__geo_interface__"):
        data = cast(GeoInterfaceProtocol, data)
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
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
    if data.crs and data.crs not in [EPSG_4326, OGC_84]:
        warnings.warn("GeoDataFrame being reprojected to EPSG:4326")
        data = data.to_crs(OGC_84)

    table = geopandas_to_geoarrow(data)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geopandas_geoseries(
    data: gpd.GeoSeries, **kwargs
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
    import geopandas as gpd

    if data.crs and data.crs not in [EPSG_4326, OGC_84]:
        warnings.warn("GeoSeries being reprojected to EPSG:4326")
        data = data.to_crs(OGC_84)

    gdf = gpd.GeoDataFrame(geometry=data)
    table = geopandas_to_geoarrow(gdf)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_shapely_scalar(
    data: shapely.geometry.base.BaseGeometry, **kwargs
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
    return _viz_shapely_array(np.array([data]), **kwargs)


def _viz_shapely_array(
    data: NDArray[np.object_], **kwargs
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
    # TODO: pass include_z?
    field, geom_arr = construct_geometry_array(data)
    schema = pa.schema([field])
    table = pa.Table.from_arrays([geom_arr], schema=schema)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geo_interface(
    data: dict, **kwargs
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
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


def _viz_geoarrow_table(
    table: pa.Table, **kwargs
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
    # TODO: don't hard-code "geometry"
    geometry_ext_type = table.schema.field("geometry").metadata.get(
        b"ARROW:extension:name"
    )

    if geometry_ext_type in [EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT]:
        return ScatterplotLayer(table=table, **kwargs)

    elif geometry_ext_type in [
        EXTENSION_NAME.LINESTRING,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        return PathLayer(table=table, **kwargs)

    elif geometry_ext_type in [EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON]:
        return SolidPolygonLayer(table=table, **kwargs)

    raise ValueError(f"Unsupported extension type: '{geometry_ext_type}'.")
