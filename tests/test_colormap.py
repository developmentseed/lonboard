import numpy as np
import pyarrow as pa
import pytest
from arro3.core import Array, DataType

from lonboard.colormap import apply_categorical_cmap


def test_discrete_cmap():
    str_values = ["red", "green", "blue", "blue", "red"]
    values = Array(str_values, type=DataType.string())
    cmap = {
        "red": [255, 0, 0],
        "green": [0, 255, 0],
        "blue": [0, 0, 255],
    }
    colors = apply_categorical_cmap(values, cmap)

    for i, val in enumerate(str_values):
        assert list(colors[i]) == cmap[val]


def pandas_series(values):
    pd = pytest.importorskip("pandas")
    return pd.Series(values)


@pytest.mark.parametrize(
    "constructor",
    [
        np.array,
        pandas_series,
        pa.array,
        lambda values: pa.chunked_array([values]),
    ],
    ids=["numpy", "pandas", "pyarrow_array", "pyarrow_chunked_array"],
)
def test_discrete_cmap_bool(constructor):
    bool_values = [True, False, False, True, True]
    values = constructor(bool_values)
    cmap = {
        False: [255, 0, 0],
        True: [0, 255, 0],
    }
    colors = apply_categorical_cmap(values, cmap)

    for i, val in enumerate(bool_values):
        assert list(colors[i]) == cmap[val]


def test_discrete_cmap_bool_single_value():
    values = np.array([True, True])
    cmap = {True: [0, 255, 0]}
    colors = apply_categorical_cmap(values, cmap)

    assert colors.tolist() == [[0, 255, 0], [0, 255, 0]]


def test_discrete_cmap_bool_missing_key():
    values = np.array([True, False])
    cmap = {True: [0, 255, 0]}

    with pytest.raises(KeyError):
        apply_categorical_cmap(values, cmap)
