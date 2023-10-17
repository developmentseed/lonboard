"""High-level, super-simple API for visualizing GeoDataFrames
"""
from __future__ import annotations

import json
import warnings
from typing import TYPE_CHECKING, Any, Dict, Protocol, Union, cast

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import shapely.geometry
from numpy.typing import NDArray

from lonboard.constants import EPSG_4326, EXTENSION_NAME, OGC_84
from lonboard.geoarrow.extension_types import construct_geometry_array
from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard.layer import BaseLayer, PathLayer, ScatterplotLayer, SolidPolygonLayer

if TYPE_CHECKING:
    import geopandas as gpd


class GeoInterfaceProtocol(Protocol):
    @property
    def __geo_interface__(self) -> dict:
        ...


def viz(
    data: Union[
        gpd.GeoDataFrame,
        gpd.GeoSeries,
        pa.Table,
        NDArray[np.object_],
        shapely.geometry.base.BaseGeometry,
        GeoInterfaceProtocol,
        Dict[str, Any],
    ],
    **kwargs,
) -> Union[ScatterplotLayer, PathLayer, SolidPolygonLayer]:
    """A high-level function to plot your data easily.

    This function accepts a variety of geospatial inputs:

    - geopandas `GeoDataFrame`
    - geopandas `GeoSeries`
    - numpy array of Shapely objects
    - Single Shapely object
    - Any Python class with a `__geo_interface__` property conforming to the
        [Geo Interface protocol](https://gist.github.com/sgillies/2217756).
    - `dict` holding GeoJSON-like data.
    - pyarrow `Table` with a geometry column marked with a GeoArrow extension type

    Args:
        data: a data object of any supported type.

    Named args:
        Any other keyword arguments will be passed onto the relevant layer, either a
        `ScatterplotLayer`, `PathLayer`, or `SolidPolygonLayer`.

    Returns:
        widget visualizing the provided data.
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

    # pyarrow table
    if isinstance(data, pa.Table):
        return _viz_geoarrow_table(data, **kwargs)

    # Shapely array
    if isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.object_):
        return _viz_shapely_array(data, **kwargs)

    # Shapely scalar
    if isinstance(data, shapely.geometry.base.BaseGeometry):
        return _viz_shapely_scalar(data, **kwargs)

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


# TODO: check CRS in geopandas methods
def _viz_geopandas_geodataframe(data: gpd.GeoDataFrame, **kwargs) -> BaseLayer:
    if data.crs and data.crs not in [EPSG_4326, OGC_84]:
        warnings.warn("GeoDataFrame being reprojected to EPSG:4326")
        data = data.to_crs(OGC_84)

    table = geopandas_to_geoarrow(data)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geopandas_geoseries(data: gpd.GeoSeries, **kwargs) -> BaseLayer:
    import geopandas as gpd

    if data.crs and data.crs not in [EPSG_4326, OGC_84]:
        warnings.warn("GeoSeries being reprojected to EPSG:4326")
        data = data.to_crs(OGC_84)

    gdf = gpd.GeoDataFrame(geometry=data)
    table = geopandas_to_geoarrow(gdf)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_shapely_scalar(
    data: shapely.geometry.base.BaseGeometry, **kwargs
) -> BaseLayer:
    return _viz_shapely_array(np.array([data]), **kwargs)


def _viz_shapely_array(data: NDArray[np.object_], **kwargs) -> BaseLayer:
    # TODO: pass include_z?
    field, geom_arr = construct_geometry_array(data)
    schema = pa.schema([field])
    table = pa.Table.from_arrays([geom_arr], schema=schema)
    return _viz_geoarrow_table(table, **kwargs)


def _viz_geo_interface(data: dict, **kwargs) -> BaseLayer:
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


def _viz_geoarrow_table(table: pa.Table, **kwargs) -> BaseLayer:
    geometry_ext_type = table.schema.field("geometry").metadata.get(
        b"ARROW:extension:name"
    )

    if geometry_ext_type in [EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT]:
        return ScatterplotLayer(table, **kwargs)

    elif geometry_ext_type in [
        EXTENSION_NAME.LINESTRING,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        return PathLayer(table, **kwargs)

    elif geometry_ext_type in [EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON]:
        return SolidPolygonLayer(table, **kwargs)

    raise ValueError(f"Unsupported extension type: '{geometry_ext_type}'.")
