import numpy as np
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


def test_discrete_cmap_boolean():
    """Test that boolean values work with categorical colormap."""
    bool_values = np.array([True, False, True, False])
    cmap = {
        True: [0, 255, 0],   # Green for True
        False: [255, 0, 0],  # Red for False
    }
    colors = apply_categorical_cmap(bool_values, cmap)
    
    expected_colors = np.array([
        [0, 255, 0],    # True -> green
        [255, 0, 0],    # False -> red  
        [0, 255, 0],    # True -> green
        [255, 0, 0],    # False -> red
    ], dtype=np.uint8)
    
    np.testing.assert_array_equal(colors, expected_colors)
