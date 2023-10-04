from typing import Union

import numpy as np
from numpy.typing import NDArray
from palettable.palette import Palette


def apply_continuous_cmap(
    values: NDArray[np.floating],
    cmap: Palette,
    *,
    alpha: Union[float, int, NDArray[np.floating], None] = None
) -> NDArray[np.uint8]:
    """_summary_

    Args:
        values: _description_
        cmap: _description_
        alpha: Alpha must be a scalar between 0 and 1, a sequence of such floats with
            shape matching `values`, or None.

    Returns:
        _description_
    """
    assert isinstance(cmap, Palette), "Expected cmap to be a palettable colormap."

    # Note: we can remove the matplotlib dependency in the future if we vendor
    # matplotlib.colormap
    colors: NDArray[np.uint8] = cmap.mpl_colormap(
        values, alpha=alpha, bytes=True
    )  # type: ignore

    # If the alpha values are all 255, don't serialize
    if (colors[:, 3] == 255).all():
        return colors[:, :3]

    return colors
