from __future__ import annotations

import json
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from arro3.core import Array, DataType, Field, fixed_size_list_array, list_array

from lonboard._geoarrow.crs import serialize_crs

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray
    from pyproj import CRS


class CoordinateDimension(str, Enum):
    XY = "xy"
    XYZ = "xyz"
    XYM = "xym"
    XYZM = "xyzm"


def coord_storage_type(*, interleaved: bool, dims: CoordinateDimension) -> DataType:
    """Generate the storage type of a geoarrow coordinate array.

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions

    """
    if interleaved:
        return DataType.list(Field(dims, DataType.float64()), len(dims))

    if dims == CoordinateDimension.XY:
        return DataType.struct(
            [
                Field("x", DataType.float64()),
                Field("y", DataType.float64()),
            ],
        )
    if dims == CoordinateDimension.XYZ:
        return DataType.struct(
            [
                Field("x", DataType.float64()),
                Field("y", DataType.float64()),
                Field("z", DataType.float64()),
            ],
        )
    if dims == CoordinateDimension.XYM:
        return DataType.struct(
            [
                Field("x", DataType.float64()),
                Field("y", DataType.float64()),
                Field("m", DataType.float64()),
            ],
        )
    if dims == CoordinateDimension.XYZM:
        return DataType.struct(
            [
                Field("x", DataType.float64()),
                Field("y", DataType.float64()),
                Field("z", DataType.float64()),
                Field("m", DataType.float64()),
            ],
        )

    raise ValueError("Unreachable")


def linestring_storage_type(
    *,
    interleaved: bool,
    dims: CoordinateDimension,
    large_list: bool = False,
) -> DataType:
    """Generate the storage type of a geoarrow.linestring array.

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type

    """
    vertices_type = coord_storage_type(interleaved=interleaved, dims=dims)
    if large_list:
        return DataType.large_list(Field("vertices", vertices_type))
    return DataType.list(Field("vertices", vertices_type))


def polygon_storage_type(
    *,
    interleaved: bool,
    dims: CoordinateDimension,
    large_list: bool = False,
) -> DataType:
    """Generate the storage type of a geoarrow.polygon array.

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type

    """
    rings_type = linestring_storage_type(
        large_list=large_list,
        interleaved=interleaved,
        dims=dims,
    )
    if large_list:
        return DataType.large_list(Field("rings", rings_type))
    return DataType.list(Field("rings", rings_type))


def multipoint_storage_type(
    *,
    interleaved: bool,
    dims: CoordinateDimension,
    large_list: bool = False,
) -> DataType:
    """Generate the storage type of a geoarrow.multipoint array.

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type

    """
    points_type = coord_storage_type(interleaved=interleaved, dims=dims)
    if large_list:
        return DataType.large_list(Field("points", points_type))
    return DataType.list(Field("points", points_type))


def multilinestring_storage_type(
    *,
    interleaved: bool,
    dims: CoordinateDimension,
    large_list: bool = False,
) -> DataType:
    """Generate the storage type of a geoarrow.multilinestring array.

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type

    """
    linestrings_type = linestring_storage_type(
        large_list=large_list,
        interleaved=interleaved,
        dims=dims,
    )
    if large_list:
        return DataType.large_list(Field("linestrings", linestrings_type))
    return DataType.list(Field("linestrings", linestrings_type))


def multipolygon_storage_type(
    *,
    interleaved: bool,
    dims: CoordinateDimension,
    large_list: bool = False,
) -> DataType:
    """Generate the storage type of a geoarrow.multipolygon array.

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type

    """
    polygons_type = polygon_storage_type(
        large_list=large_list,
        interleaved=interleaved,
        dims=dims,
    )
    if large_list:
        return DataType.large_list(Field("polygons", polygons_type))
    return DataType.list(Field("polygons", polygons_type))


def offsets_to_arrow(
    offsets: tuple[NDArray[np.int32], ...] | tuple[NDArray[np.int64], ...],
) -> tuple[Sequence[Array], bool]:
    """Return a tuple of Arrow arrays from offsets.

    Returns:
        Arrays; whether they're large.

    """
    # Shapely historically produced int64 offset arrays in `to_ragged_array`, but as of
    # a recent version (2.1? 2.1.1?) switched to producing `int32` arrays where
    # possible. In the case that we receive `int64` arrays, we downcast them to int32 if
    # possible
    if all(offset_arr.dtype == np.int32 for offset_arr in offsets):
        return [Array(offset_arr) for offset_arr in offsets], False

    if any(offset_arr[-1] >= np.iinfo(np.int32).max for offset_arr in offsets):
        return [Array(offset_arr) for offset_arr in offsets], True

    return [Array(offset_arr.astype(np.int32)) for offset_arr in offsets], False


def construct_geometry_array(  # noqa: PLR0915
    shapely_arr: NDArray[np.object_],
    include_z: bool | None = None,  # noqa: FBT001
    *,
    field_name: str = "geometry",
    crs: CRS | None = None,
) -> tuple[Field, Array]:
    import shapely
    from shapely import GeometryType

    geom_type, coords, np_offsets = shapely.to_ragged_array(
        shapely_arr,
        include_z=include_z,
    )
    offsets, is_large_offset = offsets_to_arrow(np_offsets)

    if coords.shape[-1] == 2:
        dims = CoordinateDimension.XY
    elif coords.shape[-1] == 3:
        dims = CoordinateDimension.XYZ
    else:
        raise ValueError(f"Unexpected coords dimensions: {coords.shape}")

    extension_metadata: dict[str, str] = {}
    if crs is not None:
        extension_metadata["ARROW:extension:metadata"] = json.dumps(serialize_crs(crs))

    if geom_type == GeometryType.POINT:
        arrow_coords = fixed_size_list_array(coords.ravel("C"), len(dims)).cast(
            coord_storage_type(interleaved=True, dims=dims),
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.point"
        field = Field(
            field_name,
            arrow_coords.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_coords

    if geom_type == GeometryType.LINESTRING:
        assert len(offsets) == 1, "Expected one offsets array"
        (geom_offsets,) = offsets
        arrow_coords = fixed_size_list_array(coords.ravel("C"), len(dims))
        arrow_geoms = list_array(geom_offsets, arrow_coords).cast(
            linestring_storage_type(
                interleaved=True,
                dims=dims,
                large_list=is_large_offset,
            ),
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.linestring"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    if geom_type == GeometryType.POLYGON:
        assert len(offsets) == 2, "Expected two offsets arrays"
        ring_offsets, geom_offsets = offsets
        arrow_coords = fixed_size_list_array(coords.ravel("C"), len(dims))
        arrow_rings = list_array(ring_offsets, arrow_coords)
        arrow_geoms = list_array(geom_offsets, arrow_rings).cast(
            polygon_storage_type(
                interleaved=True,
                dims=dims,
                large_list=is_large_offset,
            ),
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.polygon"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    if geom_type == GeometryType.MULTIPOINT:
        assert len(offsets) == 1, "Expected one offsets array"
        (geom_offsets,) = offsets
        arrow_coords = fixed_size_list_array(coords.ravel("C"), len(dims))
        arrow_geoms = list_array(geom_offsets, arrow_coords).cast(
            multipoint_storage_type(
                interleaved=True,
                dims=dims,
                large_list=is_large_offset,
            ),
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.multipoint"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    if geom_type == GeometryType.MULTILINESTRING:
        assert len(offsets) == 2, "Expected two offsets arrays"
        ring_offsets, geom_offsets = offsets
        arrow_coords = fixed_size_list_array(coords.ravel("C"), len(dims))
        arrow_rings = list_array(ring_offsets, arrow_coords)
        arrow_geoms = list_array(geom_offsets, arrow_rings).cast(
            multilinestring_storage_type(
                interleaved=True,
                dims=dims,
                large_list=is_large_offset,
            ),
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.multilinestring"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    if geom_type == GeometryType.MULTIPOLYGON:
        assert len(offsets) == 3, "Expected three offsets arrays"
        ring_offsets, polygon_offsets, geom_offsets = offsets
        arrow_coords = fixed_size_list_array(coords.ravel("C"), len(dims))
        arrow_rings = list_array(ring_offsets, arrow_coords)
        arrow_polygons = list_array(polygon_offsets, arrow_rings)
        arrow_geoms = list_array(geom_offsets, arrow_polygons).cast(
            multipolygon_storage_type(
                interleaved=True,
                dims=dims,
                large_list=is_large_offset,
            ),
        )
        extension_metadata["ARROW:extension:name"] = "geoarrow.multipolygon"
        field = Field(
            field_name,
            arrow_geoms.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, arrow_geoms

    raise ValueError(f"Unsupported type for geoarrow: {geom_type}")
