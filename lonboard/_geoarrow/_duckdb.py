from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Optional, Union

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

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
) -> pa.Table:
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
) -> pa.Table:
    other_col_names = [name for i, name in enumerate(rel.columns) if i != geom_col_idx]
    non_geo_table = rel.select(*other_col_names).arrow()
    geom_col_name = rel.columns[geom_col_idx]

    # A poor-man's string interpolation check
    # We can't pass in SQL-templated strings for the column name
    re_match = r"[a-zA-Z][a-zA-Z0-9_]*"
    assert re.match(
        re_match, geom_col_name
    ), f"Expected geometry column name to match regex: {re_match}"

    if con is not None:
        geom_table = con.sql(f"""
        SELECT ST_AsWKB( {geom_col_name} ) as {geom_col_name} FROM rel;
        """).arrow()
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
            geom_table = duckdb.execute(sql).arrow()
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
    return non_geo_table.append_column(geom_field, geom_table.column(0))


def _from_geoarrow(
    rel: duckdb.DuckDBPyRelation,
    *,
    extension_type: EXTENSION_NAME,
    geom_col_idx: int,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> pa.Table:
    table = rel.arrow()
    metadata = _make_geoarrow_field_metadata(extension_type, crs)
    geom_field = table.schema.field(geom_col_idx).with_metadata(metadata)
    return table.set_column(geom_col_idx, geom_field, table.column(geom_col_idx))


def _from_box2d(
    rel: duckdb.DuckDBPyRelation,
    *,
    geom_col_idx: int,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> pa.Table:
    table = rel.arrow()
    geom_col = table.column(geom_col_idx)

    polygon_array = _convert_box2d_to_geoarrow_polygon_array(geom_col)

    metadata = _make_geoarrow_field_metadata(EXTENSION_NAME.POLYGON, crs)
    prev_field = table.schema.field(geom_col_idx)
    geom_field = pa.field(prev_field.name, polygon_array.type, metadata=metadata)
    return table.set_column(geom_col_idx, geom_field, polygon_array)


def _convert_box2d_to_geoarrow_polygon_array(
    geom_col: pa.StructArray,
) -> pa.ListArray:
    """
    This is a manual conversion of the duckdb box_2d type to a GeoArrow Polygon array.

    We don't wish to add dependencies so we reimplement this here using numpy.
    """

    # Extract the bounding box columns from the Arrow struct
    # NOTE: this assumes that the box ordering is minx, miny, maxx, maxy
    # Note sure whether the positional ordering or the named fields is more stable
    min_x = pc.struct_field(geom_col, 0)
    min_y = pc.struct_field(geom_col, 1)
    max_x = pc.struct_field(geom_col, 2)
    max_y = pc.struct_field(geom_col, 3)

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
    coords = pa.FixedSizeListArray.from_arrays(coords.flatten("C"), 2)
    ring_array = pa.ListArray.from_arrays(ring_offsets, coords)
    polygon_array = pa.ListArray.from_arrays(geom_offsets, ring_array)
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
