from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    T = TypeVar("T", bound=np.generic)


# Note: it's important for the np.ma.MaskedArray overload to be first
@overload
def reshape_as_image(arr: np.ma.MaskedArray) -> np.ma.MaskedArray: ...
@overload
def reshape_as_image(arr: NDArray[T]) -> NDArray[T]: ...
def reshape_as_image(
    arr: NDArray[T] | np.ma.MaskedArray,
) -> NDArray[T] | np.ma.MaskedArray:
    """Return the source array reshaped into standard image axis ordering.

    Libraries like async-geotiff and rasterio return arrays in `(bands, rows, columns)`
    order, while image processing and visualization software like Lonboard require
    `(rows, columns, bands)` order.

    This function performs this reshaping by swapping the axes order from (bands, rows,
    columns) to (rows, columns, bands).

    Args:
        arr : array-like of shape (bands, rows, columns)
            image to reshape

    """
    # This is vendored from rasterio:
    # https://github.com/rasterio/rasterio/blob/1e03dc98d7b63b62fe2f5e34eaeb488be38dfcb7/rasterio/plot.py#L227-L241

    # swap the axes order from (bands, rows, columns) to (rows, columns, bands)
    return np.ma.transpose(arr, [1, 2, 0])
