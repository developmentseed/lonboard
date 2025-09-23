import ibis
import pyarrow as pa
from arro3.core import Schema
from ibis import _

con = ibis.duckdb.connect()

schema = pa.schema(
    [pa.field("some_int", pa.int32()), pa.field("some_string", pa.string())],
)
Schema(schema)

ibis.table(Schema(schema), "table")


schema = {
    "carat": "float64",
    "cut": "string",
    "color": "string",
    "clarity": "string",
    "depth": "float64",
    "table": "float64",
    "price": "int64",
    "x": "float64",
    "y": "float64",
    "z": "float64",
}
diamonds = ibis.table(schema, name="diamonds")
diamonds

diamonds.col

expr = (
    diamonds.group_by(["cut", "color"])
    .agg(carat=_.carat.mean())
    .pivot_wider(
        names=("Premium", "Ideal"),
        names_from="cut",
        values_from="carat",
        names_sort=True,
        values_agg="mean",
    )
)

parquet_dir = "diamonds.parquet"
ibis.examples.diamonds.fetch().to_parquet(parquet_dir)

con = ibis.duckdb.connect()
con.read_parquet(parquet_dir, table_name="diamonds")

con.to_pandas(expr)
expr.to_sql("duckdb")


diamonds.columns

dir(expr.columns)
