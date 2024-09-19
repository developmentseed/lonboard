from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import numpy as np
from arro3.core import ChunkedArray, Table

from lonboard._geoarrow.extension_types import construct_geometry_array

if TYPE_CHECKING:
    import geopandas as gpd


def geopandas_to_geoarrow(
    gdf: gpd.GeoDataFrame,
    columns: Optional[List[str]] = None,
    preserve_index: Optional[bool] = None,
) -> Table:
    try:
        import pyarrow
    except ImportError as e:
        raise ImportError(
            "pyarrow required for converting GeoPandas to arrow.\n"
            "Run `pip install pyarrow`."
        ) from e

    df_attr = gdf.drop(columns=[gdf._geometry_column_name])

    if columns is not None:
        df_attr = df_attr[columns]

    pyarrow_table = pyarrow.Table.from_pandas(df_attr, preserve_index=preserve_index)
    field, geom_arr = construct_geometry_array(
        np.array(gdf.geometry),
        crs_str=gdf.crs.to_json() if gdf.crs is not None else None,
    )
    return Table.from_arrow(pyarrow_table).append_column(
        field, ChunkedArray([geom_arr])
    )
