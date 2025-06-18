from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from arro3.core import ChunkedArray, Table

from lonboard._geoarrow.extension_types import construct_geometry_array

if TYPE_CHECKING:
    import geopandas as gpd


def geopandas_to_geoarrow(
    gdf: gpd.GeoDataFrame,
    columns: list[str] | None = None,
    preserve_index: bool | None = None,  # noqa: FBT001
) -> Table:
    try:
        import pyarrow as pa
    except ImportError as e:
        raise ImportError(
            "pyarrow required for converting GeoPandas to arrow.\n"
            "Run `pip install pyarrow`.",
        ) from e

    df_attr = gdf.drop(columns=[gdf._geometry_column_name])  # noqa: SLF001

    if columns is not None:
        df_attr = df_attr[columns]

    pyarrow_table = pa.Table.from_pandas(df_attr, preserve_index=preserve_index)
    field, geom_arr = construct_geometry_array(
        np.array(gdf.geometry),
        crs=gdf.crs,
    )
    return Table.from_arrow(pyarrow_table).append_column(
        field,
        ChunkedArray([geom_arr]),
    )
