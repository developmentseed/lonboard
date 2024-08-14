import pytest

from lonboard.colormap import apply_categorical_cmap


def test_discrete_cmap():
    pd = pytest.importorskip("pandas")

    values = ["red", "green", "blue", "blue", "red"]
    df = pd.DataFrame({"val": values})
    cmap = {
        "red": [255, 0, 0],
        "green": [0, 255, 0],
        "blue": [0, 0, 255],
    }
    colors = apply_categorical_cmap(df["val"], cmap)

    for i, val in enumerate(values):
        assert list(colors[i]) == cmap[val]
