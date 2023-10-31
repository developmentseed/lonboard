from typing import Union

import numpy as np
from numpy.typing import NDArray
from palettable.palette import Palette


def apply_continuous_cmap(
    values: NDArray[np.floating],
    cmap: Palette,
    *,
    alpha: Union[float, int, NDArray[np.floating], None] = None,
) -> NDArray[np.uint8]:
    """Apply a colormap to a set of values.

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
