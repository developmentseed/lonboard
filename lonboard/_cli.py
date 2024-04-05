import json
import webbrowser
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

import click
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import CRS

from lonboard import viz


def read_pyogrio(path: Path) -> pa.Table:
    """Read path using pyogrio and convert field metadata to geoarrow

    Args:
        path: Path to file readable by pyogrio
    """
    try:
        from pyogrio.raw import read_arrow
    except ImportError as e:
        raise ImportError(
            "pyogrio is a required dependency for the CLI. "
            "Install with `pip install pyogrio`."
        ) from e

    meta, table = read_arrow(path)
    # The `geometry_name` key always exists but can be an empty string. In the case of
    # an empty string, we want to default to `wkb_geometry`
    geometry_column_name = meta.get("geometry_name") or "wkb_geometry"
    # TODO: assert there are not two column names of wkb_geometry, nor an existing
    # column named "geometry"

    # Rename wkb_geometry to geometry
    geometry_column_index = [
        i for (i, name) in enumerate(table.column_names) if name == geometry_column_name
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
    return pa.Table.from_arrays(table.columns, schema=new_schema)


def read_geoparquet(path: Path):
    """Read GeoParquet file at path using pyarrow

    Args:
        path: Path to GeoParquet file
    """
    file = pq.ParquetFile(path)
    geo_meta = file.metadata.metadata.get(b"geo")
    if not geo_meta:
        raise ValueError("Expected geo metadata in Parquet file")

    table = file.read()

    geo_meta = json.loads(geo_meta)
    geometry_column_name = geo_meta["primary_column"]
    geometry_column_index = [
        i for (i, name) in enumerate(table.schema.names) if name == geometry_column_name
    ][0]

    metadata = {
        b"ARROW:extension:name": b"geoarrow.wkb",
    }
    crs_dict = geo_meta["columns"][geometry_column_name].get("crs")
    if crs_dict:
        # Parse CRS and create PROJJSON
        ext_meta = {"crs": crs_dict}
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    new_field = table.schema.field(geometry_column_index).with_metadata(metadata)
    new_schema = table.schema.set(geometry_column_index, new_field)
    return pa.Table.from_arrays(table.columns, schema=new_schema)


@click.command()
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "The output path for the generated HTML file. "
        "If not provided, will save to a temporary file."
    ),
)
@click.option(
    "--open/--no-open",
    "open_browser",
    default=None,
    help=(
        "Whether to open a web browser tab with the generated map. "
        "By default, the web browser is not opened when --output is provided, "
        "but is in other cases."
    ),
)
@click.argument("files", nargs=-1, type=click.Path(path_type=Path))
def main(output: Optional[Path], open_browser: Optional[bool], files: List[Path]):
    """Interactively visualize geospatial data using Lonboard.

    This CLI can be used either to quickly view local files or to create static HTML
    files.
    """

    tables = []
    for path in files:
        if path.suffix == ".parquet":
            table = read_geoparquet(path)
        else:
            table = read_pyogrio(path)

        tables.append(table)

    map_ = viz(tables)

    # If -o flag passed, write to file; otherwise write to temporary file
    if output:
        map_.to_html(output)

        # Default to not opening browser when None
        if open_browser is True:
            webbrowser.open_new_tab(f"file://{output.absolute()}")
    else:
        with NamedTemporaryFile("wt", suffix=".html", delete=False) as f:
            map_.to_html(f)

            # Default to opening browser when None
            if open_browser is not False:
                webbrowser.open_new_tab(f"file://{f.name}")
