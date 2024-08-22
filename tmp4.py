from datetime import datetime

import geodatasets
import geopandas as gpd
import numpy as np
import quak
import sqlglot
from arro3.core import Array, ChunkedArray, DataType, Table

from lonboard import PolygonLayer, viz

gdf = gpd.read_file(geodatasets.get_path("nybb"))
layer = PolygonLayer.from_geopandas(gdf)
self = layer
self.extensions


def quak_fn(self: PolygonLayer) -> quak.Widget:
    table: Table = self.table
    num_rows = table.num_rows
    if num_rows <= np.iinfo(np.uint8).max:
        row_index = Array.from_numpy(np.arange(num_rows, dtype=np.uint8))
        filter_arr = np.zeros(num_rows, dtype=np.uint8)
    elif num_rows <= np.iinfo(np.uint16).max:
        row_index = Array.from_numpy(np.arange(num_rows, dtype=np.uint16))
        filter_arr = np.zeros(num_rows, dtype=np.uint16)
    elif num_rows <= np.iinfo(np.uint32).max:
        row_index = Array.from_numpy(np.arange(num_rows, dtype=np.uint32))
        filter_arr = np.zeros(num_rows, dtype=np.uint32)
    else:
        row_index = Array.from_numpy(np.arange(num_rows, dtype=np.uint64))
        filter_arr = np.zeros(num_rows, dtype=np.uint64)

    table_with_row_index = table.append_column("_row_index", ChunkedArray(row_index))
    quak_widget = quak.Widget(table_with_row_index)

    test = None

    def row_index_callback(change):
        global test
        test = change

        sql = sqlglot.parse_one(quak_widget.sql, dialect="duckdb")
        sql.set("expressions", [sqlglot.column("_row_index")])
        row_index_table = quak_widget._conn.query(sql.sql(dialect="duckdb")).arrow()

        # Reset all to zero
        filter_arr[:] = 0

        # Set the desired _row_index to 1
        filter_arr[row_index_table["_row_index"]] = 1

    quak_widget.observe(row_index_callback, names="sql")

    test


m = viz(gdf)
m
table = m.layers[0].table
