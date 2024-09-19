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
