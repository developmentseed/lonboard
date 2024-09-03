from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, List, Optional, Union

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

from lonboard._constants import EXTENSION_NAME

if TYPE_CHECKING:
    import duckdb
    import pyproj

DUCKDB_SPATIAL_TYPES = {
    "GEOMETRY",
    "WKB_BLOB",
    "POINT_2D",
    "LINESTRING_2D",
    "POLYGON_2D",
    "BOX_2D",
}


def from_duckdb(
    rel: duckdb.DuckDBPyRelation,
    *,
    con: Optional[duckdb.DuckDBPyConnection] = None,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> Table:
    geom_col_idxs = [
        i for i, t in enumerate(rel.types) if str(t) in DUCKDB_SPATIAL_TYPES
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
    geom_type = rel.types[geom_col_idx]
    if geom_type == "WKB_BLOB":
        return _from_geoarrow(
            rel, extension_type=EXTENSION_NAME.WKB, geom_col_idx=geom_col_idx, crs=crs
        )
    elif geom_type == "GEOMETRY":
        return _from_geometry(rel, con=con, geom_col_idx=geom_col_idx, crs=crs)
    elif geom_type == "POINT_2D":
        return _from_geoarrow(
            rel, extension_type=EXTENSION_NAME.POINT, geom_col_idx=geom_col_idx, crs=crs
        )
    elif geom_type == "LINESTRING_2D":
        return _from_geoarrow(
            rel,
            extension_type=EXTENSION_NAME.LINESTRING,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    elif geom_type == "POLYGON_2D":
        return _from_geoarrow(
            rel,
            extension_type=EXTENSION_NAME.POLYGON,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    elif geom_type == "BOX_2D":
        return _from_box2d(
            rel,
            geom_col_idx=geom_col_idx,
            crs=crs,
        )
    else:
        raise ValueError(f"Unsupported geometry type: {geom_type}")


def _from_geometry(
    rel: duckdb.DuckDBPyRelation,
    *,
    con: Optional[duckdb.DuckDBPyConnection] = None,
    geom_col_idx: int,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> Table:
    other_col_names = [name for i, name in enumerate(rel.columns) if i != geom_col_idx]
    if other_col_names:
        non_geo_table = Table.from_arrow(rel.select(*other_col_names).arrow())
    else:
        non_geo_table = None
    geom_col_name = rel.columns[geom_col_idx]

    # A poor-man's string interpolation check
    # We can't pass in SQL-templated strings for the column name
    re_match = r"[a-zA-Z][a-zA-Z0-9_]*"
    assert re.match(
        re_match, geom_col_name
    ), f"Expected geometry column name to match regex: {re_match}"

    if con is not None:
        geom_table = Table.from_arrow(
            con.sql(f"""
        SELECT ST_AsWKB( {geom_col_name} ) as {geom_col_name} FROM rel;
        """).arrow()
        )
    else:
        import duckdb

        # We need to re-import the spatial extension because this is a different context
        # as the user's context.
        # It would be nice to re-use the user's context, but in the case of `viz` where
        # we want to visualize a single input object, we want to accept a
        # DuckDBPyRelation as input.
        sql = f"""
            INSTALL spatial;
            LOAD spatial;
            SELECT ST_AsWKB( {geom_col_name} ) as {geom_col_name} FROM rel;
            """
        try:
            geom_table = Table.from_arrow(
                duckdb.execute(sql, connection=duckdb.default_connection).arrow()
            )
        except duckdb.CatalogException as err:
            msg = (
                "Could not coerce type GEOMETRY to WKB.\n"
                "This often happens from using a custom DuckDB connection object.\n"
                "Either pass in a `con` object containing the DuckDB connection or "
                "cast to WKB manually with `ST_AsWKB`."
            )
            raise ValueError(msg) from err

    metadata = _make_geoarrow_field_metadata(EXTENSION_NAME.WKB, crs)
    geom_field = geom_table.schema.field(0).with_metadata(metadata)
    if non_geo_table is not None:
        return non_geo_table.append_column(geom_field, geom_table.column(0))
    else:
        # Need to set geospatial metadata onto the Arrow table, because the table
        # returned from duckdb has none.
        new_schema = geom_table.schema.set(0, geom_field)
        return geom_table.with_schema(new_schema)


def _from_geoarrow(
    rel: duckdb.DuckDBPyRelation,
    *,
    extension_type: EXTENSION_NAME,
    geom_col_idx: int,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> Table:
    table = Table.from_arrow(rel.arrow())
    metadata = _make_geoarrow_field_metadata(extension_type, crs)
    geom_field = table.schema.field(geom_col_idx).with_metadata(metadata)
    return table.set_column(geom_col_idx, geom_field, table.column(geom_col_idx))


def _from_box2d(
    rel: duckdb.DuckDBPyRelation,
    *,
    geom_col_idx: int,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> Table:
    table = Table.from_arrow(rel.arrow())
    geom_col = table.column(geom_col_idx)

    polygon_chunks: List[Array] = []
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
    """
    This is a manual conversion of the duckdb box_2d type to a GeoArrow Polygon array.

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
    flat_coords: Array = Array.from_numpy(coords.ravel("C"))
    coords = fixed_size_list_array(flat_coords, 2)
    ring_array = list_array(Array.from_numpy(ring_offsets), coords)
    polygon_array = list_array(Array.from_numpy(geom_offsets), ring_array)
    return polygon_array


# TODO: refactor, put helper in lonboard._geoarrow.crs?
def _make_geoarrow_field_metadata(
    extension_type: EXTENSION_NAME,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> dict[bytes, bytes]:
    import pyproj

    metadata: dict[bytes, bytes] = {b"ARROW:extension:name": extension_type}

    if crs is not None:
        if isinstance(crs, str):
            crs = pyproj.CRS.from_user_input(crs)

        ext_meta = {"crs": crs.to_json_dict()}
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    return metadata
