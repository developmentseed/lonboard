from __future__ import annotations

import json
from typing import TYPE_CHECKING

import numpy as np
from arro3.core import (
    Array,
    ChunkedArray,
    DataType,
    Field,
    RecordBatch,
    Schema,
    Table,
    fixed_size_list_array,
    list_array,
)

if TYPE_CHECKING:
    import movingpandas as mpd
    import pandas as pd
    import pyarrow as pa
    from movingpandas import TrajectoryCollection


def movingpandas_to_geoarrow(  # noqa: PLR0915
    traj_collection: TrajectoryCollection,
) -> tuple[Table, ChunkedArray]:
    """Convert a MovingPandas TrajectoryCollection to GeoArrow.

    Args:
        traj_collection: _description_

    Returns:
        _description_

    """
    import pyarrow as pa
    import shapely

    crs = traj_collection.get_crs()
    crs_json = crs.to_json_dict() if crs is not None else None

    num_coords = 0
    num_trajectories = len(traj_collection)
    offsets = np.zeros(num_trajectories + 1, dtype=np.int32)
    datetime_dtypes = set()
    attr_schemas: list[pa.Schema] = []

    # Loop the first time to infer offsets for each trajectory
    for i, traj in enumerate(traj_collection.trajectories):
        traj: mpd.Trajectory

        num_coords += traj.size()
        offsets[i + 1] = num_coords
        datetime_dtypes.add(traj.df.index.dtype)

        geom_col_name = traj.get_geom_col()
        df_attr = traj.df.drop(columns=[geom_col_name])

        # Explicitly drop index because the index is a DatetimeIndex that we convert
        # manually later.
        arrow_schema = pa.Schema.from_pandas(df_attr, preserve_index=False)
        attr_schemas.append(arrow_schema)

    assert len(datetime_dtypes) == 1, (
        "Expected only one datetime dtype across all trajectories."
    )
    datetime_dtype = list(datetime_dtypes)[0]

    # We currently always provision space for XYZ coordinates, and then only use 2d if
    # the Z dimension is always NaN
    coords = np.zeros((num_coords, 3), dtype=np.float64)

    arrow_timestamp_dtype = infer_timestamp_dtype(datetime_dtype)
    timestamps = np.zeros(num_coords, dtype=np.int64)

    attr_schema = pa.unify_schemas(attr_schemas, promote_options="permissive")
    attr_tables: list[pa.Table] = []

    # Loop second time to fill timestamps and coords
    for i, traj in enumerate(traj_collection.trajectories):
        start_offset = offsets[i]
        end_offset = offsets[i + 1]

        timestamps[start_offset:end_offset] = traj.df.index
        coords[start_offset:end_offset] = shapely.get_coordinates(
            traj.df.geometry.array,  # type: ignore
            include_z=True,
        )

        geom_col_name = traj.get_geom_col()
        df_attr = traj.df.drop(columns=[geom_col_name])

        attr_table = pa.Table.from_pandas(
            traj.df,
            schema=attr_schema,
            preserve_index=False,
        )
        attr_tables.append(attr_table)

    attr_table = pa.concat_tables(attr_tables, promote_options="none")
    attr_table = Table.from_arrow(attr_table)

    offsets = Array.from_numpy(offsets)

    nested_attr_table = apply_offsets_to_table(attr_table, offsets=offsets)

    if np.all(np.isnan(coords[:, 2])):
        coord_list_size = 2
        # Cast to 2D coords
        coords = coords[:, :2]
    else:
        assert not np.any(
            np.isnan(coords[:, 2]),
        ), "Mixed 2D and 3D coordinates not currently supported"
        coord_list_size = 3

    coords_arr = Array.from_numpy(coords.ravel("C"))
    coords_fixed_size_list = fixed_size_list_array(coords_arr, coord_list_size)
    linestrings_arr = list_array(offsets, coords_fixed_size_list)

    extension_metadata: dict[str, str] = {"ARROW:extension:name": "geoarrow.linestring"}
    if crs_json is not None:
        extension_metadata["ARROW:extension:metadata"] = json.dumps({"crs": crs_json})

    linestrings_field = Field(
        "geometry",
        linestrings_arr.type,
        nullable=True,
        metadata=extension_metadata,
    )

    timestamp_values = Array.from_numpy(timestamps).cast(arrow_timestamp_dtype)
    timestamp_arr = list_array(offsets, timestamp_values)
    timestamp_col = ChunkedArray([timestamp_arr])

    table = nested_attr_table.append_column(
        linestrings_field,
        ChunkedArray([linestrings_arr]),
    )
    return table, timestamp_col


def infer_timestamp_dtype(dtype: np.dtype | pd.DatetimeTZDtype) -> DataType:
    """Infer an arrow time unit from the numpy data type.

    Raises:
        ValueError: If not a known numpy datetime dtype

    """
    import pandas as pd

    if isinstance(dtype, pd.DatetimeTZDtype):
        return DataType.timestamp(dtype.unit, tz=str(dtype.tz))

    if dtype.name == "datetime64[s]":
        return DataType.timestamp("s")

    if dtype.name == "datetime64[ms]":
        return DataType.timestamp("ms")

    if dtype.name == "datetime64[us]":
        return DataType.timestamp("us")

    if dtype.name == "datetime64[ns]":
        return DataType.timestamp("ns")

    raise ValueError(f"Unexpected datetime type: {dtype}")


def apply_offsets_to_table(table: Table, offsets: Array) -> Table:
    batch = table.combine_chunks().to_batches()[0]

    new_fields = []
    new_arrays = []

    for field_idx in range(batch.num_columns):
        field = batch.schema.field(field_idx)
        new_field = field.with_type(DataType.list(field))
        new_array = list_array(offsets, batch[field_idx], type=new_field)

        new_fields.append(new_field)
        new_arrays.append(new_array)

    new_schema = Schema(new_fields, metadata=batch.schema.metadata)
    new_batch = RecordBatch(new_arrays, schema=new_schema)
    return Table.from_batches([new_batch])
