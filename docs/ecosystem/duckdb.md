# DuckDB Spatial

[DuckDB](https://duckdb.org/) is a fast, self-contained analytical database. [DuckDB Spatial](https://duckdb.org/docs/extensions/spatial.html) is an extension to DuckDB that adds geospatial support.

You can pass a DuckDB query into the top-level [`viz`](../api/viz.md#viz) function to quickly inspect data:

```py
import duckdb
from lonboard import viz

sql = "SELECT * FROM spatial_table;"
query = duckdb.sql(sql)
viz(query)
```

Additionally, all relevant Lonboard layer classes have a [`from_duckdb`](../api/layers/base-layer.md#lonboard.BaseArrowLayer.from_duckdb) method for DuckDB query input.

```py
import duckdb
from lonboard import Map, PolygonLayer

sql = "SELECT * FROM polygon_table;"
query = duckdb.sql(sql)
layer = PolygonLayer.from_duckdb(
    query,
    get_fill_color=[255, 0, 0],
)
m = Map(layer)
m
```

!!! warning

    The DuckDB query must be run with
    [`duckdb.sql()`](https://duckdb.org/docs/api/python/reference/#duckdb.sql)
    or
    [`duckdb.DuckDBPyConnection.sql()`](https://duckdb.org/docs/api/python/reference/#duckdb.DuckDBPyConnection.sql)
    and not with `duckdb.execute()` or `duckdb.DuckDBPyConnection.execute()`.

    For example

    ```py
    import duckdb
    from lonboard import viz

    sql = "SELECT * FROM spatial_table;"
    query = duckdb.sql(sql)
    viz(query)
    ```

!!! warning

    DuckDB Spatial does not currently expose coordinate reference system
    information, so the user must ensure that data has been reprojected to
    EPSG:4326.

You can also render an entire table by using the `table()` method:

```py
import duckdb
from lonboard import viz

duckdb.sql("CREATE TABLE spatial_table AS ...;")
viz(duckdb.table("spatial_table"))
```

## Custom Connection

If y you're using a custom DuckDB connection (not the global default connection), such as `con = duckdb.connect()`, then instead of `duckdb.sql()` and `duckdb.table()`, you can use `con.sql()` and `con.table()`.

## Directly passing a query string to `from_duckdb` of a layer class

The `from_duckdb` method of Lonboard layer classes supports directly passing a SQL string, but then you need to also pass the connection object into the `con` named parameter of `from_duckdb`:

```py
import duckdb
from lonboard import Map, PolygonLayer

con = duckdb.connect()
layer = PolygonLayer.from_duckdb(
    "SELECT * FROM polygon_table;",
    con=con,
    get_fill_color=[255, 0, 0],
)
m = Map(layer)
m
```

### Implementation Notes

Lonboard integrates with DuckDB by using its [Arrow export support](https://duckdb.org/docs/guides/python/export_arrow).

As of DuckDB Spatial version 0.10.2, DuckDB Spatial's primary `GEOMETRY` type [uses a custom, non-stable binary format](https://github.com/duckdb/duckdb_spatial/blob/v0.10.2/docs/internals.md#multi-tiered-geometry-type-system). When exported to Python via an Arrow table, this `GEOMETRY` type is maintained as a binary blob that is impossible to reliably parse in Python. The only way to interpret this column in Python-based tools is to get DuckDB to cast this column to a standardized format like Well-Known Binary (WKB).

We could require that users always call `ST_AsWKB` on the geometry column on every query, but this is unwieldy and easy to forget. Instead, by requiring that the user pass in a `DuckDBPyRelation` object instead of a `DuckDBPyConnection`, we're able to use the [replacement scan feature](https://duckdb.org/docs/api/python/relational_api#sql-queries) of `DuckDBPyRelation` to call _back_ into DuckDB and perform our _own_ `ST_AsWKB` call on the data, before it's left DuckDB memory, and then export the WKB geometries out to Arrow.
