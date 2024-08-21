from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

import click
from arro3.core import Table
from pyproj import CRS

from lonboard import viz
from lonboard._constants import EXTENSION_NAME


def read_pyogrio(path: Path) -> Table:
    """Read path using pyogrio and convert field metadata to geoarrow

    Args:
        path: Path to file readable by pyogrio
    """
    try:
        from pyogrio.raw import open_arrow
    except ImportError as e:
        raise ImportError(
            "pyogrio is a required dependency for the CLI for reading data sources \n"
            "other than GeoParquet.\n"
            "Install with `pip install pyogrio`."
        ) from e

    with open_arrow(path, use_pyarrow=False) as source:
        meta, stream = source
        table = Table.from_arrow(stream)

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
    if metadata.get(b"ARROW:extension:name") == EXTENSION_NAME.OGC_WKB:
        # Parse CRS and create PROJJSON
        ext_meta = {"crs": CRS.from_user_input(meta["crs"]).to_json_dict()}

        # Replace metadata
        metadata[b"ARROW:extension:name"] = EXTENSION_NAME.WKB
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    new_field = field.with_name("geometry").with_metadata(metadata)
    new_schema = schema.set(geometry_column_index, new_field)
    return table.with_schema(new_schema)


def read_parquet(path: Path) -> tuple[Table, dict]:
    """Read Parquet file using either pyarrow or arro3.

    arro3.io.read_parquet is not multi-threaded (as of arro3 0.2.1), so pyarrow can be
    up to 4x faster on an 8-core machine. Because of this, we prefer pyarrow if it's
    installed, and fall back to arro3 otherwise.

    Args:
        path: path to Parquet file.

    Raises:
        ValueError: if there's no GeoParquet metadata in the file

    Returns:
        arro3 Table
    """
    try:
        import pyarrow.parquet as pq

        file = pq.ParquetFile(path)
        if b"geo" not in file.metadata.metadata:
            raise ValueError("Expected geo metadata in Parquet file")
        geo_meta = json.loads(file.metadata.metadata.get(b"geo"))

        table = Table.from_arrow(file.read())

        return table, geo_meta

    except ImportError:
        from arro3.io import read_parquet

        reader = read_parquet(path)

        if "geo" not in reader.schema.metadata_str.keys():
            raise ValueError("Expected geo metadata in Parquet file")

        table = reader.read_all()
        geo_meta = json.loads(table.schema.metadata_str["geo"])

        return table, geo_meta


def read_geoparquet(path: Path) -> Table:
    """Read GeoParquet file at path using pyarrow or arro3.io

    Args:
        path: Path to GeoParquet file
    """
    table, geo_meta = read_parquet(path)
    geometry_column_name = geo_meta["primary_column"]
    geometry_column_index = [
        i for (i, name) in enumerate(table.schema.names) if name == geometry_column_name
    ][0]

    metadata: dict[bytes, bytes] = {
        b"ARROW:extension:name": EXTENSION_NAME.WKB,
    }
    crs_dict = geo_meta["columns"][geometry_column_name].get("crs")
    if crs_dict:
        # Parse CRS and create PROJJSON
        ext_meta = {"crs": crs_dict}
        metadata[b"ARROW:extension:metadata"] = json.dumps(ext_meta).encode()

    new_field = table.schema.field(geometry_column_index).with_metadata(metadata)
    new_schema = table.schema.set(geometry_column_index, new_field)
    return table.with_schema(new_schema)


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
