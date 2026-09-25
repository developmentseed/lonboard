from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from warnings import warn

import numpy as np
from arro3.core import (
    Array,
    ChunkedArray,
    Field,
    Table,
    fixed_size_list_array,
    list_array,
    struct_field,
)
from pyproj import CRS

from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.crs import get_field_crs

if TYPE_CHECKING:
    import duckdb

DUCKDB_SPATIAL_TYPES = {
    "GEOMETRY",
    "WKB_BLOB",
    "POINT_2D",
    "LINESTRING_2D",
    "POLYGON_2D",
    "BOX_2D",
}


def _base_type_name(duckdb_type: duckdb.typing.DuckDBPyType) -> str:
    """Return the name of a DuckDB type without any type parameters.

    As of DuckDB 1.5, the spatial extension's GEOMETRY type is parameterized
    with a CRS, e.g. `GEOMETRY('EPSG:4326')`, so an exact string comparison
    against `"GEOMETRY"` no longer matches.

    String parsing is the only way to do this: `DuckDBPyType` exposes only
    `id` and `children`, where `id` omits the type parameters (and is
    `'blob'` for both GEOMETRY and WKB_BLOB on DuckDB 1.4, so it can't be
    used for detection either) and `children` raises for non-nested types.
    """
    return str(duckdb_type).split("(", 1)[0]


def from_duckdb(
    rel: duckdb.DuckDBPyRelation,
    *,
    crs: str | CRS | None = None,
) -> Table:
    geom_col_idxs = [
        i for i, t in enumerate(rel.types) if _base_type_name(t) in DUCKDB_SPATIAL_TYPES
    ]

    if len(geom_col_idxs) == 0:
        raise ValueError("No geometry column found in query.")

    if len(geom_col_idxs) > 1:
        msg = "Multiple geometry columns found in query.\n\n"
        for geom_col_idx in geom_col_idxs:
            msg += (
                f"- name: {rel.columns[geom_col_idx]}, "
                f"type: {rel.types[geom_col_idx]} \n"
            )

        raise ValueError(msg)

    geom_col_idx = geom_col_idxs[0]
    geom_type = _base_type_name(rel.types[geom_col_idx])
    if geom_type == "WKB_BLOB":
        return _from_geoarrow(
            rel,
            extension_type=EXTENSION_NAME.WKB,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    if geom_type == "GEOMETRY":
        return _from_geometry(rel, geom_col_idx=geom_col_idx, crs=crs)
    if geom_type == "POINT_2D":
        return _from_geoarrow(
            rel,
            extension_type=EXTENSION_NAME.POINT,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    if geom_type == "LINESTRING_2D":
        return _from_geoarrow(
            rel,
            extension_type=EXTENSION_NAME.LINESTRING,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    if geom_type == "POLYGON_2D":
        return _from_geoarrow(
            rel,
            extension_type=EXTENSION_NAME.POLYGON,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    if geom_type == "BOX_2D":
        return _from_box2d(
            rel,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    raise ValueError(f"Unsupported geometry type: {geom_type}")


def _from_geometry(
    rel: duckdb.DuckDBPyRelation,
    *,
    geom_col_idx: int,
    crs: str | CRS | None = None,
) -> Table:
    table = Table.from_arrow(rel.arrow())
    geom_field = table.schema.field(geom_col_idx)
    field_metadata = geom_field.metadata or {}

    # DuckDB >= 1.5 exports GEOMETRY columns as spec-compliant GeoArrow WKB,
    # including the PROJJSON CRS when the type has one encoded
    # (e.g. `GEOMETRY('EPSG:4326')`). DuckDB 1.4 exports plain binary with no
    # field metadata, so fall back to converting via `ST_AsWKB`.
    if field_metadata.get(b"ARROW:extension:name") == EXTENSION_NAME.WKB:
        return _reconcile_crs(table, geom_col_idx=geom_col_idx, crs=crs)

    return _from_geometry_st_aswkb(rel, geom_col_idx=geom_col_idx, crs=crs)


def _reconcile_crs(
    table: Table,
    *,
    geom_col_idx: int,
    crs: str | CRS | None,
) -> Table:
    """Apply the `crs` parameter to a GeoArrow table exported from DuckDB.

    - If the column has a CRS and `crs` matches it: warn that `crs` is
      unnecessary.
    - If the column has a CRS and `crs` conflicts with it: raise `ValueError`.
    - If the column has no CRS: attach `crs` (if provided) like before
      DuckDB 1.5.
    """
    geom_field = table.schema.field(geom_col_idx)
    column_crs = get_field_crs(geom_field)

    if column_crs is None:
        if crs is not None:
            metadata = _make_geoarrow_field_metadata(EXTENSION_NAME.WKB, crs)
            geom_field = geom_field.with_metadata(metadata)
            return table.set_column(
                geom_col_idx,
                geom_field,
                table.column(geom_col_idx),
            )

        return table

    if crs is not None:
        param_crs = CRS.from_user_input(crs)
        if param_crs != column_crs:
            raise ValueError(
                f"crs parameter ({param_crs.to_string()}) does not match the "
                "CRS encoded in the DuckDB GEOMETRY column "
                f"({column_crs.to_string()}).",
            )

        warn(
            "Passing `crs` is no longer needed with DuckDB >= 1.5 when using "
            "a GEOMETRY type with a CRS encoded; the CRS is read from the "
            "DuckDB column type automatically.",
            UserWarning,
            stacklevel=2,
        )

    return table


def _from_geometry_st_aswkb(
    rel: duckdb.DuckDBPyRelation,
    *,
    geom_col_idx: int,
    crs: str | CRS | None = None,
) -> Table:
    from duckdb import ColumnExpression, FunctionExpression

    other_col_names = [name for i, name in enumerate(rel.columns) if i != geom_col_idx]
    if other_col_names:
        non_geo_table = Table.from_arrow(rel.select(*other_col_names).arrow())
    else:
        non_geo_table = None
    geom_col_name = rel.columns[geom_col_idx]

    # A poor-man's string interpolation check
    # We can't pass in SQL-templated strings for the column name
    re_match = r"[a-zA-Z][a-zA-Z0-9_]*"
    assert re.fullmatch(
        re_match,
        geom_col_name,
    ), f"Expected geometry column name to match regex: {re_match}"

    geom_table = Table.from_arrow(
        rel.select(
            FunctionExpression("st_aswkb", ColumnExpression(geom_col_name)).alias(
                geom_col_name,
            ),
        ).arrow(),
    )

    metadata = _make_geoarrow_field_metadata(EXTENSION_NAME.WKB, crs)
    geom_field = geom_table.schema.field(0).with_metadata(metadata)
    if non_geo_table is not None:
        return non_geo_table.append_column(geom_field, geom_table.column(0))
    # Need to set geospatial metadata onto the Arrow table, because the table
    # returned from duckdb has none.
    new_schema = geom_table.schema.set(0, geom_field)
    return geom_table.with_schema(new_schema)


def _from_geoarrow(
    rel: duckdb.DuckDBPyRelation,
    *,
    extension_type: EXTENSION_NAME,
    geom_col_idx: int,
    crs: str | CRS | None = None,
) -> Table:
    table = Table.from_arrow(rel.arrow())
    metadata = _make_geoarrow_field_metadata(extension_type, crs)
    geom_field = table.schema.field(geom_col_idx).with_metadata(metadata)
    return table.set_column(geom_col_idx, geom_field, table.column(geom_col_idx))


def _from_box2d(
    rel: duckdb.DuckDBPyRelation,
    *,
    geom_col_idx: int,
    crs: str | CRS | None = None,
) -> Table:
    table = Table.from_arrow(rel.arrow())
    geom_col = table.column(geom_col_idx)

    polygon_chunks: list[Array] = []
    for geom_chunk in geom_col.chunks:
        polygon_array = _convert_box2d_to_geoarrow_polygon_array(geom_chunk)
        polygon_chunks.append(polygon_array)

    metadata = _make_geoarrow_field_metadata(EXTENSION_NAME.POLYGON, crs)
    prev_field = table.schema.field(geom_col_idx)
    geom_field = Field(prev_field.name, polygon_chunks[0].type, metadata=metadata)
    return table.set_column(geom_col_idx, geom_field, ChunkedArray(polygon_chunks))


def _convert_box2d_to_geoarrow_polygon_array(
    geom_col: Array,
) -> Array:
    """Manual conversion of the duckdb box_2d type to a GeoArrow Polygon array.

    We don't wish to add dependencies so we reimplement this here using numpy.
    """
    # Extract the bounding box columns from the Arrow struct
    # NOTE: this assumes that the box ordering is minx, miny, maxx, maxy
    # Note sure whether the positional ordering or the named fields is more stable
    min_x = struct_field(geom_col, 0)
    min_y = struct_field(geom_col, 1)
    max_x = struct_field(geom_col, 2)
    max_y = struct_field(geom_col, 3)

    # Provision memory for the output coordinates. For closed polygons, each input box
    # becomes 5 coordinates.
    # The first dimension is length and the second dimension allows for x and y
    coords = np.zeros(((len(geom_col) * 5), 2), dtype=np.float64)

    # Compute the insertion indexes for each corner of the box.
    # Start at bottom left
    bottom_left_idxs = np.arange(0, len(geom_col) * 5, 5)
    bottom_right_idxs = bottom_left_idxs + 1
    upper_right_idxs = bottom_right_idxs + 1
    upper_left_idxs = upper_right_idxs + 1
    bottom_left_idxs_again = upper_left_idxs + 1

    # Insert each corner into the coordinate array at these specified indexes
    coords[bottom_left_idxs, :] = np.column_stack([min_x, min_y])
    coords[bottom_right_idxs, :] = np.column_stack([max_x, min_y])
    coords[upper_right_idxs, :] = np.column_stack([max_x, max_y])
    coords[upper_left_idxs, :] = np.column_stack([min_x, max_y])
    coords[bottom_left_idxs_again, :] = np.column_stack([min_x, min_y])

    # Create the geoarrow Polygon offset arrays
    # Each ring has 5 coordinates
    ring_offsets = np.arange(0, (len(geom_col) + 1) * 5, 5, dtype=np.int32)
    # Each geometry has a single ring
    geom_offsets = np.arange(0, len(ring_offsets), dtype=np.int32)

    # Construct the final PolygonArray
    coords = fixed_size_list_array(coords.ravel("C"), 2)
    ring_array = list_array(ring_offsets, coords)
    polygon_array = list_array(geom_offsets, ring_array)
    return polygon_array  # noqa: RET504


# TODO: refactor, put helper in lonboard._geoarrow.crs?
def _make_geoarrow_field_metadata(
    extension_type: EXTENSION_NAME,
    crs: str | CRS | None = None,
) -> dict[bytes, bytes]:
    metadata: dict[bytes, bytes] = {b"ARROW:extension:name": extension_type}

    if crs is not None:
        if isinstance(crs, str):
            crs = CRS.from_user_input(crs)

        ext_meta = {"crs": crs.to_json_dict()}
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    return metadata
