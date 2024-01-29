import json
from enum import Enum
from typing import Dict, Optional, Tuple

import numpy as np
import pyarrow as pa
import shapely
from numpy.typing import NDArray
from shapely import GeometryType


class CoordinateDimension(str, Enum):
    XY = "xy"
    XYZ = "xyz"
    XYM = "xym"
    XYZM = "xyzm"


class BaseGeometryType(pa.ExtensionType):
    extension_name: str
    coord_dimension: CoordinateDimension


def coord_storage_type(*, interleaved: bool, dims: CoordinateDimension) -> pa.DataType:
    """Generate the storage type of a geoarrow coordinate array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
    """
    if interleaved:
        return pa.list_(pa.field(dims, pa.float64()), len(dims))

    else:
        if dims == CoordinateDimension.XY:
            return pa.struct(
                [
                    ("x", pa.float64()),
                    ("y", pa.float64()),
                ]
            )
        if dims == CoordinateDimension.XYZ:
            return pa.struct(
                [
                    ("x", pa.float64()),
                    ("y", pa.float64()),
                    ("z", pa.float64()),
                ]
            )
        if dims == CoordinateDimension.XYM:
            return pa.struct(
                [
                    ("x", pa.float64()),
                    ("y", pa.float64()),
                    ("m", pa.float64()),
                ]
            )
        if dims == CoordinateDimension.XYZM:
            return pa.struct(
                [
                    ("x", pa.float64()),
                    ("y", pa.float64()),
                    ("z", pa.float64()),
                    ("m", pa.float64()),
                ]
            )


def linestring_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> pa.DataType:
    """Generate the storage type of a geoarrow.linestring array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    vertices_type = coord_storage_type(interleaved=interleaved, dims=dims)
    if large_list:
        return pa.large_list(pa.field("vertices", vertices_type))
    else:
        return pa.list_(pa.field("vertices", vertices_type))


def polygon_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> pa.DataType:
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
        return pa.large_list(pa.field("rings", rings_type))
    else:
        return pa.list_(pa.field("rings", rings_type))


def multipoint_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> pa.DataType:
    """Generate the storage type of a geoarrow.multipoint array

    Args:
        interleaved: Whether coordinates should be interleaved or separated
        dims: The number of dimensions
        large_list: Whether to use a large list with int64 offsets for the inner type
    """
    points_type = coord_storage_type(interleaved=interleaved, dims=dims)
    if large_list:
        return pa.large_list(pa.field("points", points_type))
    else:
        return pa.list_(pa.field("points", points_type))


def multilinestring_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> pa.DataType:
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
        return pa.large_list(pa.field("linestrings", linestrings_type))
    else:
        return pa.list_(pa.field("linestrings", linestrings_type))


def multipolygon_storage_type(
    *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
) -> pa.DataType:
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
        return pa.large_list(pa.field("polygons", polygons_type))
    else:
        return pa.list_(pa.field("polygons", polygons_type))


class PointType(BaseGeometryType):
    extension_name = "geoarrow.point"

    def __init__(self, *, interleaved: bool, dims: CoordinateDimension):
        self.coord_dimension = dims

        storage_type = coord_storage_type(interleaved=interleaved, dims=dims)
        super().__init__(storage_type, self.extension_name)

    def __arrow_ext_serialize__(self):
        return b""

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes):
        return cls(interleaved=True, dims=CoordinateDimension.XY)


class LineStringType(BaseGeometryType):
    extension_name = "geoarrow.linestring"

    def __init__(
        self, *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
    ):
        self.coord_dimension = dims

        storage_type = linestring_storage_type(
            interleaved=interleaved, dims=dims, large_list=large_list
        )
        super().__init__(storage_type, self.extension_name)

    def __arrow_ext_serialize__(self):
        return b""

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes):
        return cls(interleaved=True, dims=CoordinateDimension.XY)


class PolygonType(BaseGeometryType):
    extension_name = "geoarrow.polygon"

    def __init__(
        self, *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
    ):
        self.coord_dimension = dims

        storage_type = polygon_storage_type(
            interleaved=interleaved, dims=dims, large_list=large_list
        )
        super().__init__(storage_type, self.extension_name)

    def __arrow_ext_serialize__(self):
        return b""

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes):
        return cls(interleaved=True, dims=CoordinateDimension.XY)


class MultiPointType(BaseGeometryType):
    extension_name = "geoarrow.multipoint"

    def __init__(
        self, *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
    ):
        self.coord_dimension = dims

        storage_type = multipoint_storage_type(
            interleaved=interleaved, dims=dims, large_list=large_list
        )
        super().__init__(storage_type, self.extension_name)

    def __arrow_ext_serialize__(self):
        return b""

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes):
        return cls(interleaved=True, dims=CoordinateDimension.XY)


class MultiLineStringType(BaseGeometryType):
    extension_name = "geoarrow.multilinestring"

    def __init__(
        self, *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
    ):
        self.coord_dimension = dims

        storage_type = multilinestring_storage_type(
            interleaved=interleaved, dims=dims, large_list=large_list
        )
        super().__init__(storage_type, self.extension_name)

    def __arrow_ext_serialize__(self):
        return b""

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes):
        return cls(interleaved=True, dims=CoordinateDimension.XY)


class MultiPolygonType(BaseGeometryType):
    extension_name = "geoarrow.multipolygon"

    def __init__(
        self, *, interleaved: bool, dims: CoordinateDimension, large_list: bool = False
    ):
        self.coord_dimension = dims

        storage_type = multipolygon_storage_type(
            interleaved=interleaved, dims=dims, large_list=large_list
        )
        super().__init__(storage_type, self.extension_name)

    def __arrow_ext_serialize__(self):
        return b""

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes):
        return cls(interleaved=True, dims=CoordinateDimension.XY)


def construct_geometry_array(
    shapely_arr: NDArray[np.object_],
    include_z: Optional[bool] = None,
    *,
    crs_str: Optional[str] = None,
) -> Tuple[pa.Field, pa.Array]:
    # NOTE: this implementation returns a (field, array) pair so that it can set the
    # extension metadata on the field without instantiating extension types into the
    # global pyarrow registry
    geom_type, coords, offsets = shapely.to_ragged_array(
        shapely_arr, include_z=include_z
    )

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
        parr = pa.FixedSizeListArray.from_arrays(coords.flatten(), len(dims))
        extension_metadata["ARROW:extension:name"] = "geoarrow.point"
        field = pa.field(
            "geometry",
            parr.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, parr

    elif geom_type == GeometryType.LINESTRING:
        assert len(offsets) == 1, "Expected one offsets array"
        (geom_offsets,) = offsets
        _parr = pa.FixedSizeListArray.from_arrays(coords.flatten(), len(dims))
        parr = pa.ListArray.from_arrays(pa.array(geom_offsets), _parr)
        extension_metadata["ARROW:extension:name"] = "geoarrow.linestring"
        field = pa.field(
            "geometry",
            parr.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, parr

    elif geom_type == GeometryType.POLYGON:
        assert len(offsets) == 2, "Expected two offsets arrays"
        ring_offsets, geom_offsets = offsets
        _parr = pa.FixedSizeListArray.from_arrays(coords.flatten(), len(dims))
        _parr1 = pa.ListArray.from_arrays(pa.array(ring_offsets), _parr)
        parr = pa.ListArray.from_arrays(pa.array(geom_offsets), _parr1)
        extension_metadata["ARROW:extension:name"] = "geoarrow.polygon"
        field = pa.field(
            "geometry",
            parr.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, parr

    elif geom_type == GeometryType.MULTIPOINT:
        assert len(offsets) == 1, "Expected one offsets array"
        (geom_offsets,) = offsets
        _parr = pa.FixedSizeListArray.from_arrays(coords.flatten(), len(dims))
        parr = pa.ListArray.from_arrays(pa.array(geom_offsets), _parr)
        extension_metadata["ARROW:extension:name"] = "geoarrow.multipoint"
        field = pa.field(
            "geometry",
            parr.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, parr

    elif geom_type == GeometryType.MULTILINESTRING:
        assert len(offsets) == 2, "Expected two offsets arrays"
        ring_offsets, geom_offsets = offsets
        _parr = pa.FixedSizeListArray.from_arrays(coords.flatten(), len(dims))
        _parr1 = pa.ListArray.from_arrays(pa.array(ring_offsets), _parr)
        parr = pa.ListArray.from_arrays(pa.array(geom_offsets), _parr1)
        extension_metadata["ARROW:extension:name"] = "geoarrow.multilinestring"
        field = pa.field(
            "geometry",
            parr.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, parr

    elif geom_type == GeometryType.MULTIPOLYGON:
        assert len(offsets) == 3, "Expected three offsets arrays"
        ring_offsets, polygon_offsets, geom_offsets = offsets
        _parr = pa.FixedSizeListArray.from_arrays(coords.flatten(), len(dims))
        _parr1 = pa.ListArray.from_arrays(pa.array(ring_offsets), _parr)
        _parr2 = pa.ListArray.from_arrays(pa.array(polygon_offsets), _parr1)
        parr = pa.ListArray.from_arrays(pa.array(geom_offsets), _parr2)
        extension_metadata["ARROW:extension:name"] = "geoarrow.multipolygon"
        field = pa.field(
            "geometry",
            parr.type,
            nullable=True,
            metadata=extension_metadata,
        )
        return field, parr

    else:
        raise ValueError(f"Unsupported type for geoarrow: {geom_type}")
