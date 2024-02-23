import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
import pyarrow as pa
import pyarrow.parquet as pq
from pyogrio.raw import read_arrow
from pyproj import CRS

from lonboard import viz

# path = Path("/Users/kyle/github/developmentseed/lonboard/DC_Wetlands.parquet")
# path = Path("/Users/kyle/Downloads/UScounties.geojson")


def read_pyogrio(path: Path) -> pa.Table:
    """Read path using pyogrio and convert field metadata to geoarrow

    Args:
        path: Path to file readable by pyogrio
    """
    meta, table = read_arrow(path)
    # TODO: assert there are not two column names of wkb_geometry

    # Rename wkb_geometry to geometry
    geometry_column_index = [
        i for (i, name) in enumerate(table.column_names) if name == "wkb_geometry"
    ][0]

    schema = table.schema
    field = schema.field(geometry_column_index)

    metadata: Dict[bytes, bytes] = field.metadata
    if metadata.get(b"ARROW:extension:name") == b"ogc.wkb":
        # Parse CRS and create PROJJSON
        ext_meta = {"crs": CRS.from_user_input(meta["crs"]).to_json_dict()}

        # Replace metadata
        metadata[b"ARROW:extension:name"] = b"geoarrow.wkb"
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    new_field = field.with_name("geometry").with_metadata(metadata)
    new_schema = schema.set(geometry_column_index, new_field)
    return pa.Table.from_arrays(table.columns, new_schema)


def read_geoparquet(path: Path):
    """Read GeoParquet file at path using pyarrow

    Args:
        path: Path to GeoParquet file
    """
    meta = pq.ParquetFile(path)
    geo_meta = meta.metadata.metadata[b"geo"]

    table = pq.read_table(path)
    pass


@click.command()
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None)
@click.argument("files", nargs=-1, type=click.Path(path_type=Path))
def main(output: Optional[Path], files: List[Path]):
    """Interactively view geospatial data using kepler.gl"""

    tables = []
    for path in files:
        if path.suffix == ".parquet":
            table = read_geoparquet(path)
        else:
            table = read_pyogrio(path)

        tables.append(table)

    map_ = viz(tables)

    # If -o flag passed, write to file; otherwise write to stdout
    if output:
        map_.to_html(output)
    else:
        map_.to_html(sys.stdout)


if __name__ == "__main__":
    main()
