from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import pyarrow as pa

from lonboard._constants import EXTENSION_NAME

if TYPE_CHECKING:
    import duckdb


def from_duckdb(
    rel: duckdb.DuckDBPyRelation,
    *,
    con: Optional[duckdb.DuckDBPyConnection] = None,
    crs: Any = None,
) -> pa.Table:
    import duckdb

    # TODO: also check for WKB_BLOB (and don't cast that)
    geom_cols = [i for i, t in enumerate(rel.types) if t == "GEOMETRY"]

    if len(geom_cols) == 0:
        raise ValueError("No geometry column found in table")

    if len(geom_cols) > 1:
        raise ValueError("Multiple geometry columns found in table")

    geom_col_idx = geom_cols[0]
    other_col_names = [name for i, name in enumerate(rel.columns) if i != geom_col_idx]
    non_geo_table = rel.select(*other_col_names).arrow()
    geom_col_name = rel.columns[geom_col_idx]

    # TODO: remove string formatting!!
    if con is not None:
        geom_table = con.sql(f"""
        SELECT ST_AsWKB( {geom_col_name} ) as {geom_col_name} FROM rel;
        """).arrow()
    else:
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

    geom_field = geom_table.schema.field(0).with_metadata(
        {b"ARROW:extension:name": EXTENSION_NAME.WKB}
    )
    return non_geo_table.append_column(geom_field, geom_table.column(0))
