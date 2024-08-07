from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import numpy as np
import pyarrow as pa

if TYPE_CHECKING:
    import geopandas as gpd


def geopandas_to_geoarrow(
    gdf: gpd.GeoDataFrame,
    columns: Optional[List[str]] = None,
    preserve_index: Optional[bool] = None,
):
    from lonboard._geoarrow.extension_types import construct_geometry_array

    df_attr = gdf.drop(columns=[gdf._geometry_column_name])

    if columns is not None:
        df_attr = df_attr[columns]

    table = pa.Table.from_pandas(df_attr, preserve_index=preserve_index)
    field, geom_arr = construct_geometry_array(
        np.array(gdf.geometry),
        crs_str=gdf.crs.to_json() if gdf.crs is not None else None,
    )

    return table.append_column(field, geom_arr)
