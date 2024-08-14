from __future__ import annotations

import json
from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Sequence, Tuple

import numpy as np
from arro3.core import Array, DataType, Field, fixed_size_list_array, list_array

if TYPE_CHECKING:
    from numpy.typing import NDArray


class CoordinateDimension(str, Enum):
    XY = "xy"
    XYZ = "xyz"
    XYM = "xym"
    XYZM = "xyzm"


def coord_storage_type(*, interleaved: bool, dims: CoordinateDimension) -> DataType:
    """Generate the storage type of a geoarrow coordinate array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
    """
    if interleaved:
        return DataType.list(Field(dims, DataType.float64()), len(dims))

    else:
        if dims == CoordinateDimension.XY:
            return DataType.struct(
                [
                    Field("x", DataType.float64()),
                    Field("y", DataType.float64()),
                ]
            )
        if dims == CoordinateDimension.XYZ:
            return DataType.struct(
                [
                    Field("x", DataType.float64()),
                    Field("y", DataType.float64()),
                    Field("z", DataType.float64()),
                ]
            )
        if dims == CoordinateDimension.XYM:
            return DataType.struct(
                [
                    Field("x", DataType.float64()),
                    Field("y", DataType.float64()),
                    Field("m", DataType.float64()),
                ]
            )
        if dims == CoordinateDimension.XYZM:
            return DataType.struct(
                [
                    Field("x", DataType.float64()),
                    Field("y", DataType.float64()),
                    Field("z", DataType.float64()),
                    Field("m", DataType.float64()),
                ]
            )


def linestring_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> DataType:
    """Generate the storage type of a geoarrow.linestring array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    vertices_type = coord_storage_type(interleaved=interleaved, dims=dims)
    if large_list:
        return DataType.large_list(Field("vertices", vertices_type))
    else:
        return DataType.list(Field("vertices", vertices_type))


def polygon_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> DataType:
    """Generate the storage type of a geoarrow.polygon array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    rings_type = linestring_storage_type(
        large_list=large_list, interleaved=interleaved, dims=dims
    )
    if large_list:
        return DataType.large_list(Field("rings", rings_type))
    else:
        return DataType.list(Field("rings", rings_type))


def multipoint_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> DataType:
    """Generate the storage type of a geoarrow.multipoint array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    points_type = coord_storage_type(interleaved=interleaved, dims=dims)
    if large_list:
        return DataType.large_list(Field("points", points_type))
    else:
        return DataType.list(Field("points", points_type))


def multilinestring_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> DataType:
    """Generate the storage type of a geoarrow.multilinestring array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    linestrings_type = linestring_storage_type(
        large_list=large_list, interleaved=interleaved, dims=dims
    )
    if large_list:
        return DataType.large_list(Field("linestrings", linestrings_type))
    else:
        return DataType.list(Field("linestrings", linestrings_type))


def multipolygon_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> DataType:
    """Generate the storage type of a geoarrow.multipolygon array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    polygons_type = polygon_storage_type(
        large_list=large_list, interleaved=interleaved, dims=dims
    )
    if large_list:
        return DataType.large_list(Field("polygons", polygons_type))
    else:
        return DataType.list(Field("polygons", polygons_type))


def offsets_to_arrow(
    offsets: Tuple[NDArray[np.int64], ...],
) -> Sequence[Array]:
    # Shapely produces int64 offset arrays. We downcast those to int32 if possible
    if any(offset_arr[-1] >= np.iinfo(np.int32).max for offset_arr in offsets):
        return [Array.from_numpy(offset_arr) for offset_arr in offsets]

    return [Array.from_numpy(offset_arr.astype(np.int32)) for offset_arr in offsets]


def construct_geometry_array(
    shapely_arr: NDArray[np.object_],
    include_z: Optional[bool] = None,
    *,
    field_name: str = "geometry",
    crs_str: Optional[str] = None,
) -> Tuple[Field, Array]:
    import shapely
    from shapely import GeometryType

    geom_type, coords, offsets = shapely.to_ragged_array(
        shapely_arr, include_z=include_z
    )
    offsets = offsets_to_arrow(offsets)

    if coords.shape[-1] == 2:
        dims = CoordinateDimension.XY
    elif coords.shape[-1] == 3:
        dims = CoordinateDimension.XYZ
    else:
        raise ValueError(f"Unexpected coords dimensions: {coords.shape}")

    extension_metadata: Dict[str, str] = {}
    if crs_str is not None:
        extension_metadata["ARROW:extension:metadata"] = json.dumps({"crs": crs_str})

    if geom_type == GeometryType.POINT:
        arrow_coords = fixed_size_list_array(
            Array.from_numpy(coords.ravel("C")), len(dims)
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.point"
        field = Field(
            field_name,
            arrow_coords.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_coords

    elif geom_type == GeometryType.LINESTRING:
        assert len(offsets) == 1, "Expected one offsets array"
        (geom_offsets,) = offsets
        arrow_coords = fixed_size_list_array(
            Array.from_numpy(coords.ravel("C")), len(dims)
        )
        arrow_geoms = list_array(geom_offsets, arrow_coords)
        extension_metadata["ARROW:extension:name"] = "geoarrow.linestring"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    elif geom_type == GeometryType.POLYGON:
        assert len(offsets) == 2, "Expected two offsets arrays"
        ring_offsets, geom_offsets = offsets
        arrow_coords = fixed_size_list_array(
            Array.from_numpy(coords.ravel("C")), len(dims)
        )
        arrow_rings = list_array(ring_offsets, arrow_coords)
        arrow_geoms = list_array(geom_offsets, arrow_rings)
        extension_metadata["ARROW:extension:name"] = "geoarrow.polygon"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    elif geom_type == GeometryType.MULTIPOINT:
        assert len(offsets) == 1, "Expected one offsets array"
        (geom_offsets,) = offsets
        arrow_coords = fixed_size_list_array(
            Array.from_numpy(coords.ravel("C")), len(dims)
        )
        arrow_geoms = list_array(geom_offsets, arrow_coords)
        extension_metadata["ARROW:extension:name"] = "geoarrow.multipoint"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    elif geom_type == GeometryType.MULTILINESTRING:
        assert len(offsets) == 2, "Expected two offsets arrays"
        ring_offsets, geom_offsets = offsets
        arrow_coords = fixed_size_list_array(
            Array.from_numpy(coords.ravel("C")), len(dims)
        )
        arrow_rings = list_array(ring_offsets, arrow_coords)
        arrow_geoms = list_array(geom_offsets, arrow_rings)
        extension_metadata["ARROW:extension:name"] = "geoarrow.multilinestring"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    elif geom_type == GeometryType.MULTIPOLYGON:
        assert len(offsets) == 3, "Expected three offsets arrays"
        ring_offsets, polygon_offsets, geom_offsets = offsets
        arrow_coords = fixed_size_list_array(
            Array.from_numpy(coords.ravel("C")), len(dims)
        )
        arrow_rings = list_array(ring_offsets, arrow_coords)
        arrow_polygons = list_array(polygon_offsets, arrow_rings)
        arrow_geoms = list_array(geom_offsets, arrow_polygons)
        extension_metadata["ARROW:extension:name"] = "geoarrow.multipolygon"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    else:
        raise ValueError(f"Unsupported type for geoarrow: {geom_type}")
