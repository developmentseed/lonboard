import numpy as np
import pandas as pd
import pyarrow as pa

from lonboard import H3HexagonLayer, Map
from lonboard._h3 import h3_to_str

VALID_INDICES = np.array(
    [
        0x8075FFFFFFFFFFF,
        0x81757FFFFFFFFFF,
        0x82754FFFFFFFFFF,
        0x83754EFFFFFFFFF,
        0x84754A9FFFFFFFF,
        0x85754E67FFFFFFF,
        0x86754E64FFFFFFF,
        0x87754E64DFFFFFF,
        0x88754E6499FFFFF,
        0x89754E64993FFFF,
        0x8A754E64992FFFF,
        0x8B754E649929FFF,
        0x8C754E649929DFF,
        0x8D754E64992D6FF,
        0x8E754E64992D6DF,
        0x8F754E64992D6D8,
    ],
    dtype=np.uint64,
)


def test_from_geopandas():
    hex_str = h3_to_str(VALID_INDICES)
    hex_str_pa_arr = pa.array(hex_str).cast(pa.string())

    df = pd.DataFrame({"h3": VALID_INDICES, "h3_str": hex_str})

    layer = H3HexagonLayer.from_pandas(df, get_hexagon=hex_str_pa_arr)
    m = Map(layer)
    assert isinstance(m.layers[0], H3HexagonLayer)
