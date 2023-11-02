from typing import TypeVar

import numpy as np
import pandas as pd
import pyarrow as pa

from lonboard._constants import EXTENSION_NAME

DF = TypeVar("DF", bound=pd.DataFrame)

GEOARROW_EXTENSION_TYPE_NAMES = {e.value for e in EXTENSION_NAME}


def get_geometry_column_index(schema: pa.Schema) -> int:
    """Get the positional index of the geometry column in a pyarrow Schema"""
    for field_idx in range(len(schema)):
        field_metadata = schema.field(field_idx).metadata
        if (
            field_metadata
            and field_metadata.get(b"ARROW:extension:name")
            in GEOARROW_EXTENSION_TYPE_NAMES
        ):
            return field_idx

    raise ValueError("No geometry column in table schema.")


def auto_downcast(df: DF) -> DF:
    """Automatically downcast types to smallest data size

    Args:
        df: pandas DataFrame or geopandas GeoDataFrame

    Returns:
        DataFrame with downcasted data types
    """
    # Convert objects to numeric types where possible.
    # Note: we have to exclude geometry because
    # `convert_dtypes(dtype_backend="pyarrow")` fails on the geometory column, but we
    # also have to manually cast to a non-geo data frame because it'll fail to convert
    # dtypes on a GeoDataFrame without a geom col
    casted_df = pd.DataFrame(df.select_dtypes(exclude="geometry")).convert_dtypes(
        infer_objects=True,
        convert_string=True,
        convert_integer=True,
        convert_boolean=True,
        convert_floating=True,
        dtype_backend="pyarrow",
    )
    df[casted_df.columns] = casted_df

    # Try to convert _all_ integer columns to unsigned integer columns, but use
    # errors='ignore' to return signed integer data types for columns with negative
    # integers.
    for col_name in df.select_dtypes(np.integer).columns:  # type: ignore
        df[col_name] = pd.to_numeric(
            df[col_name], errors="ignore", downcast="unsigned", dtype_backend="pyarrow"
        )

    # For any integer columns that are still signed integer, downcast those to smaller
    # signed types
    for col_name in df.select_dtypes(np.signedinteger).columns:  # type: ignore
        df[col_name] = pd.to_numeric(
            df[col_name], errors="ignore", downcast="signed", dtype_backend="pyarrow"
        )

    for col_name in df.select_dtypes(np.floating).columns:  # type: ignore
        df[col_name] = pd.to_numeric(
            df[col_name], errors="ignore", downcast="float", dtype_backend="pyarrow"
        )

    return df
