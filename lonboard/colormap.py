from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
from numpy.typing import NDArray
from palettable.palette import Palette

__all__ = (
    "apply_continuous_cmap",
    "apply_categorical_cmap",
)

RGBColor = Union[Tuple[int, int, int], Tuple[int, int, int, int], Sequence[int]]
"""A type definition for an RGB or RGBA color value

All values must range between 0 and 255 (inclusive). If only three values are provided,
the fourth (alpha) channel will be inferred as 255 (meaning full opacity, no
transparency).
"""

DiscreteColormap = Dict[Any, RGBColor]
"""A type definition for a discrete colormap.

For example, for a land cover colormap, you may want to use the following dict:

```py
color_map = {
    "Open Water": [70, 107, 159],
    "Perennial Snow/Ice": [209, 222, 248],
    "Developed, Open Space": [222, 197, 197],
    "Developed, Low Intensity": [217, 146, 130],
    "Developed, Medium Intensity": [235, 0, 0],
    "Developed, High Intensity": [171, 0, 0],
    "Barren Land": [179, 172, 159],
    "Deciduous Forest": [104, 171, 95],
    "Evergreen Forest": [28, 95, 44],
    "Mixed Forest": [181, 197, 143],
    "Shrub/Scrub": [204, 184, 121],
    "Herbaceous": [223, 223, 194],
    "Hay/Pasture": [220, 217, 57],
    "Cultivated Crops": [171, 108, 40],
    "Woody Wetlands": [184, 217, 235],
    "Emergent Herbaceous Wetlands": [108, 159, 184],
}
```

This corresponds to the following well-known color palette from the [National Land Cover
Database](https://www.mrlc.gov/data/legends/national-land-cover-database-class-legend-and-description).

<a href="https://grasswiki.osgeo.org/wiki/NLCD_Land_Cover">
    <img
        src="https://grasswiki.osgeo.org/w/images/NLCD_Colour_Classification_Update.jpg"
        alt="NLCD Land Cover Legend"
        width="300px"
    />
</a>

Keep in mind that the type of the key of the `color_map` dictionary is important. If
your data is represented as a string, the keys of the `color_map` must also be
represented as strings. If your data is represented as an integer, the keys of the
colormap should be integers.
"""


def apply_continuous_cmap(
    values: NDArray[np.floating],
    cmap: Palette,
    *,
    alpha: Union[float, int, NDArray[np.floating], None] = None,
) -> NDArray[np.uint8]:
    """Apply a colormap to a column of continuous values.

    This is described as "continuous" because it uses matplotlib's
    [LinearSegmentedColormap][matplotlib.colors.LinearSegmentedColormap] under the hood.
    As described in Matplotlib's referenced docstring:

    > The lookup table is generated using linear interpolation for each primary color,
    > with the 0-1 domain divided into any number of segments.

    This means that input values are linearly combined from the two nearest colormap
    colors.

    If you want to snap to the "nearest" colormap value, you should use another function
    (not yet implemented) to snap to the strictly nearest color value.

    Args:
        values: A numpy array of floating point values ranging from 0 to 1.
        cmap: Any `Palette` object from the
            [`palettable`](https://github.com/jiffyclub/palettable) package.

    Other Args:
        alpha: Alpha must be a scalar between 0 and 1, a sequence of such floats with
            shape matching `values`, or None.

    Returns:
        A two dimensional numpy array with data type [np.uint8][numpy.uint8]. The second
            dimension will have a length of either `3` if `alpha` is `None`, or `4` is
            each color has an alpha value.
    """
    assert isinstance(cmap, Palette), "Expected cmap to be a palettable colormap."

    # Note: we can remove the matplotlib dependency in the future if we vendor
    # matplotlib.colormap
    colors: NDArray[np.uint8] = cmap.mpl_colormap(values, alpha=alpha, bytes=True)  # type: ignore

    # If the alpha values are all 255, don't serialize
    if (colors[:, 3] == 255).all():
        return colors[:, :3]

    return colors


def apply_categorical_cmap(
    values: Union[NDArray, pd.Series, pa.Array, pa.ChunkedArray],
    cmap: DiscreteColormap,
    *,
    alpha: Optional[int] = None,
) -> NDArray[np.uint8]:
    """Apply a colormap to a column of categorical values.

    If you're working with categorical data in Pandas or GeoPandas, and **especially**
    when those categories are strings, you should use the [pandas Categorical
    type](https://pandas.pydata.org/docs/user_guide/categorical.html). This
    will use much less memory and be faster to operate on. `apply_categorical_cmap` will
    be 2-3x faster (and use less memory itself) when your data is already represented as
    a categorical data type.

    The key of the colormap must be the same as the data type of the column of values
    you pass in. _Usually_ this will be string, when you perform the lookup on a string
    column of data.

    Args:
        values: A numpy array, pandas Series, pyarrow Array or pyarrow ChunkedArray of
            data. The data type of this column must match the keys of the colormap.
        cmap: A dictionary mapping keys to colors. See [DiscreteColormap] for more
            information.

    Other Args:
        alpha: The _default_ alpha value for entries in the colormap that do not have an
            alpha value defined. Alpha must be an integer between 0 and 255 (inclusive).

    Returns:
        A two dimensional numpy array with data type [np.uint8][numpy.uint8]. The second
            dimension will have a length of either `3` if `alpha` is `None`, or `4` is
            each color has an alpha value.
    """

    if not isinstance(values, (pa.Array, pa.ChunkedArray)):
        values = pa.array(values)

    if not pa.types.is_dictionary(values.type):
        values = pc.dictionary_encode(values)

    # Build lookup table
    lut = np.zeros((len(values.dictionary), 4), dtype=np.uint8)
    if alpha is not None:
        assert isinstance(alpha, int), "alpha must be an integer"
        assert 0 <= alpha <= 255, "alpha must be between 0-255 (inclusive)."

        lut[:, 3] = alpha
    else:
        lut[:, 3] = 255

    for i, key in enumerate(values.dictionary):
        color = cmap[key.as_py()]
        if len(color) == 3:
            lut[i, :3] = color
        elif len(color) == 4:
            lut[i] = color
        else:
            raise ValueError(
                "Expected color to be 3 or 4 values representing RGB or RGBA."
            )

    colors = lut[values.indices]

    # If the alpha values are all 255, don't serialize
    if (colors[:, 3] == 255).all():
        return colors[:, :3]

    return colors
