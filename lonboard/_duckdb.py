from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Union

import pyarrow as pa

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
    geom_col_idxs = [i for i, t in enumerate(rel.types) if t in DUCKDB_SPATIAL_TYPES]

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
        return _from_wkb_blob(rel, geom_col_idx=geom_col_idx, crs=crs)
    elif geom_type == "GEOMETRY":
        return _from_geometry(rel, con=con, geom_col_idx=geom_col_idx, crs=crs)
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

    # TODO: remove string formatting!!
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
        geom_table = duckdb.execute(f"""
            INSTALL spatial;
            LOAD spatial;
            SELECT ST_AsWKB( {geom_col_name} ) as {geom_col_name} FROM rel;
            """).arrow()

    metadata = _make_geoarrow_field_metadata(crs)
    geom_field = geom_table.schema.field(0).with_metadata(metadata)
    return non_geo_table.append_column(geom_field, geom_table.column(0))


def _from_wkb_blob(
    rel: duckdb.DuckDBPyRelation,
    geom_col_idx: int,
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> pa.Table:
    table = rel.arrow()
    metadata = _make_geoarrow_field_metadata(crs)
    geom_field = table.schema.field(geom_col_idx).with_metadata(metadata)
    return table.set_column(geom_col_idx, geom_field, table.column(geom_col_idx))


# TODO: refactor, put helper in lonboard._geoarrow.crs?
def _make_geoarrow_field_metadata(
    crs: Optional[Union[str, pyproj.CRS]] = None,
) -> dict[bytes, bytes]:
    import pyproj

    metadata: dict[bytes, bytes] = {b"ARROW:extension:name": EXTENSION_NAME.WKB}

    if crs is not None:
        if isinstance(crs, str):
            crs = pyproj.CRS.from_user_input(crs)

        ext_meta = {"crs": crs.to_json_dict()}
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    return metadata
