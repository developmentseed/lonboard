"""Reproject a GeoArrow array
"""
import json
import warnings
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache, partial
from typing import Callable, Optional, Tuple, Union

import numpy as np
import pyarrow as pa
from pyproj import CRS, Transformer

from lonboard._constants import EXTENSION_NAME, OGC_84
from lonboard._geoarrow.extension_types import CoordinateDimension
from lonboard._utils import get_geometry_column_index

TransformerFromCRS = lru_cache(Transformer.from_crs)


def reproject_table(
    table: pa.Table,
    *,
    to_crs: Union[str, CRS] = OGC_84,
    max_workers: Optional[int] = None,
) -> pa.Table:
    """Reproject a GeoArrow table to a new CRS

    Args:
        table: The table to reproject.
        to_crs: The target CRS. Defaults to OGC_84.
        max_workers: The maximum number of threads to use. Defaults to None.

    Returns:
        A new table.
    """
    geom_col_idx = get_geometry_column_index(table.schema)
    # No geometry column in table
    if geom_col_idx is None:
        return table

    geom_field = table.schema.field(geom_col_idx)
    geom_column = table.column(geom_col_idx)

    # geometry column exists in table but is not assigned a CRS
    if b"ARROW:extension:metadata" not in geom_field.metadata:
        return table

    new_field, new_column = reproject_column(
        field=geom_field, column=geom_column, to_crs=to_crs, max_workers=max_workers
    )
    return table.set_column(geom_col_idx, new_field, new_column)


def reproject_column(
    *,
    field: pa.Field,
    column: pa.ChunkedArray,
    to_crs: Union[str, CRS] = OGC_84,
    max_workers: Optional[int] = None,
) -> Tuple[pa.Field, pa.ChunkedArray]:
    """Reproject a GeoArrow array to a new CRS

    Args:
        field: The field describing the column
        column: A ChunkedArray
        to_crs: The target CRS. Defaults to OGC_84.
        max_workers: The maximum number of threads to use. Defaults to None.
    """
    extension_type_name = field.metadata[b"ARROW:extension:name"]
    extension_metadata = json.loads(field.metadata[b"ARROW:extension:metadata"])
    crs_str = extension_metadata["crs"]
    existing_crs = CRS(crs_str)

    if existing_crs == to_crs:
        return field, column

    # NOTE: Not sure the best place to put this warning
    warnings.warn("Input being reprojected to EPSG:4326 CRS")

    transformer = TransformerFromCRS(existing_crs, to_crs, always_xy=True)

    # Metadata inside metadata, bad naming
    new_extension_meta_meta = {"crs": CRS(to_crs).to_json()}
    new_extension_metadata = {
        b"ARROW:extension:name": extension_type_name,
        b"ARROW:extension:metadata": json.dumps(new_extension_meta_meta),
    }

    new_chunked_array = _reproject_column(
        column,
        extension_type_name=extension_type_name,
        transformer=transformer,
        max_workers=max_workers,
    )
    return field.with_metadata(new_extension_metadata), new_chunked_array


def _reproject_column(
    column: pa.ChunkedArray,
    *,
    extension_type_name: EXTENSION_NAME,
    transformer: Transformer,
    max_workers: Optional[int] = None,
) -> pa.ChunkedArray:
    if extension_type_name == EXTENSION_NAME.POINT:
        func = partial(_reproject_chunk_nest_0, transformer=transformer)
    elif extension_type_name in [EXTENSION_NAME.LINESTRING, EXTENSION_NAME.MULTIPOINT]:
        func = partial(_reproject_chunk_nest_1, transformer=transformer)
    elif extension_type_name in [
        EXTENSION_NAME.POLYGON,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        func = partial(_reproject_chunk_nest_2, transformer=transformer)

    elif extension_type_name == EXTENSION_NAME.MULTIPOLYGON:
        func = partial(_reproject_chunk_nest_3, transformer=transformer)
    else:
        raise ValueError(f"Unexpected extension type name {extension_type_name}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return pa.chunked_array(executor.map(func, column.chunks))


def _reproject_coords(arr: pa.FixedSizeListArray, transformer: Transformer):
    list_size = arr.type.list_size
    np_arr = arr.flatten().to_numpy().reshape(-1, list_size)

    if list_size == 2:
        output_np_arr = np.column_stack(
            transformer.transform(np_arr[:, 0], np_arr[:, 1])
        )
        dims = CoordinateDimension.XY
    elif list_size == 3:
        output_np_arr = np.column_stack(
            transformer.transform(np_arr[:, 0], np_arr[:, 1], np_arr[:, 2])
        )
        dims = CoordinateDimension.XYZ
    else:
        raise ValueError(f"Unexpected list size {list_size}")

    coord_field = pa.list_(pa.field(dims, pa.float64()), len(dims))
    return pa.FixedSizeListArray.from_arrays(
        output_np_arr.flatten("C"), type=coord_field
    )


def _reproject_chunk_nest_0(arr: pa.ListArray, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_0(arr, callback)


def _reproject_chunk_nest_1(arr: pa.ListArray, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_1(arr, callback)


def _reproject_chunk_nest_2(arr: pa.ListArray, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_2(arr, callback)


def _reproject_chunk_nest_3(arr: pa.ListArray, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_3(arr, callback)


def _map_coords_nest_0(
    arr: pa.FixedSizeListArray,
    callback: Callable[[pa.FixedSizeListArray], pa.FixedSizeListArray],
):
    new_coords = callback(arr)
    return new_coords


def _map_coords_nest_1(
    arr: pa.ListArray,
    callback: Callable[[pa.FixedSizeListArray], pa.FixedSizeListArray],
):
    geom_offsets = arr.offsets
    coords = arr.flatten()
    new_coords = callback(coords)
    new_geometry_array = pa.ListArray.from_arrays(geom_offsets, new_coords)
    return new_geometry_array


def _map_coords_nest_2(
    arr: pa.ListArray,
    callback: Callable[[pa.FixedSizeListArray], pa.FixedSizeListArray],
):
    geom_offsets = arr.offsets
    ring_offsets = arr.flatten().offsets
    coords = arr.flatten().flatten()
    new_coords = callback(coords)
    new_ring_array = pa.ListArray.from_arrays(ring_offsets, new_coords)
    new_geometry_array = pa.ListArray.from_arrays(geom_offsets, new_ring_array)
    return new_geometry_array


def _map_coords_nest_3(
    arr: pa.ListArray,
    callback: Callable[[pa.FixedSizeListArray], pa.FixedSizeListArray],
):
    geom_offsets = arr.offsets
    polygon_offsets = arr.flatten().offsets
    ring_offsets = arr.flatten().flatten().offsets
    coords = arr.flatten().flatten().flatten()
    new_coords = callback(coords)
    new_ring_array = pa.ListArray.from_arrays(ring_offsets, new_coords)
    new_polygon_array = pa.ListArray.from_arrays(polygon_offsets, new_ring_array)
    new_geometry_array = pa.ListArray.from_arrays(geom_offsets, new_polygon_array)
    return new_geometry_array
