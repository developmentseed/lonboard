import numpy as np
import pyarrow as pa
from arro3.core import Table
from geoarrow.rust.core import point, points

from lonboard import ArcLayer, Map


def test_arc_layer_geoarrow_interleaved():
    start_coords = np.array([[1, 4], [2, 5], [3, 6]], dtype=np.float64)
    end_coords = np.array([[7, 4], [8, 5], [9, 6]], dtype=np.float64)
    start_array = points(start_coords).cast(point("XY", coord_type="interleaved"))
    end_array = points(end_coords).cast(point("XY", coord_type="interleaved"))

    string_col = pa.array(["a", "b", "c"], type=pa.string())
    table = Table.from_arrays([string_col], names=["string"])

    layer = ArcLayer(
        table,
        get_source_position=start_array,
        get_target_position=end_array,
    )
    m = Map(layer)
    assert isinstance(m.layers[0], ArcLayer)


def test_arc_layer_geoarrow_separated():
    start_coords = np.array([[1, 4], [2, 5], [3, 6]], dtype=np.float64)
    end_coords = np.array([[7, 4], [8, 5], [9, 6]], dtype=np.float64)
    start_array = points(start_coords).cast(point("XY", coord_type="separated"))
    end_array = points(end_coords).cast(point("XY", coord_type="separated"))

    string_col = pa.array(["a", "b", "c"], type=pa.string())
    table = Table.from_arrays([string_col], names=["string"])

    layer = ArcLayer(
        table,
        get_source_position=start_array,
        get_target_position=end_array,
    )
    m = Map(layer)
    assert isinstance(m.layers[0], ArcLayer)
