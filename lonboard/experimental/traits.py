# ruff: noqa

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import (
    Array,
    ChunkedArray,
    DataType,
    fixed_size_list_array,
)
from traitlets.traitlets import TraitType

from lonboard._serialization import (
    serialize_pyarrow_column,
)
from lonboard.traits import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer
    from lonboard.experimental._surface import SurfaceLayer


class MeshAccessor(FixedErrorTraitType):
    """A representation of a deck.gl mesh accessor."""

    default_value = None
    info_text = "a Arrow ListArray representing a nested array of 3D positions"
    list_size: int
    expected_arrow_type: DataType

    def __init__(
        self: TraitType,
        *args: Any,
        list_size: int,
        expected_arrow_type: DataType,
        **kwargs: Any,
    ) -> None:
        self.list_size = list_size
        self.expected_arrow_type = expected_arrow_type
        super().__init__(*args, **kwargs)
        self.tag(
            sync=True,
            to_json=lambda data, obj: serialize_pyarrow_column(
                data,
                max_chunksize=len(data),
            ),
        )

    def numpy_to_arrow(self, obj: SurfaceLayer, value: np.ndarray) -> Array:
        values_array = Array.from_numpy(
            value.ravel("C").astype(np.float32),
        )
        return fixed_size_list_array(values_array, self.list_size)

    def validate(self, obj: SurfaceLayer, value) -> ChunkedArray:
        if isinstance(value, np.ndarray):
            value = self.numpy_to_arrow(obj, value)

        if hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        return value.cast(self.expected_arrow_type)


class TextureTrait(FixedErrorTraitType):
    """A representation of a deck.gl texture trait."""

    default_value = None
    allow_none = True
    info_text = "a URL string or numpy array representing image data"

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        # This uses the default traitlet serialization for bytes (inside of a dict) and
        # strings
        self.tag(sync=True)

    def numpy_to_value(
        self,
        obj: BaseArrowLayer,
        value: np.ndarray,
    ) -> dict[str, Any]:
        # Should be an array of uint8, shape (height, width, channels)
        if value.dtype != np.uint8:
            self.error(
                obj,
                value,
                info="a numpy array of dtype uint8 representing image data",
            )

        if len(value.shape) != 3:
            self.error(
                obj,
                value,
                info="a 3-dimensional numpy array representing image data",
            )

        if value.shape[-1] not in (3, 4):
            self.error(
                obj,
                value,
                info="a numpy array with 3 (RGB) or 4 (RGBA) channels representing image data",
            )

        if value.shape[-1] == 3:
            rgba = np.empty((*value.shape[:2], 4), dtype=np.uint8)
            rgba[..., :3] = value
            rgba[..., 3] = 255
            value = rgba

        assert value.shape[-1] == 4

        # Ensure array is C-contiguous (copies only if needed)
        value = np.ascontiguousarray(value)

        return {
            "height": value.shape[0],
            "width": value.shape[1],
            "data": memoryview(value),
        }

    def validate(self, obj: BaseArrowLayer, value) -> Any:
        # Pre-validated input from existing layer state
        if isinstance(value, dict) and set(value.keys()) == {"height", "width", "data"}:
            return value

        # str input can be an image to a remote URL
        if isinstance(value, str):
            return value

        # bytes input can be raw image data (e.g. as a PNG)
        if isinstance(value, bytes):
            return value

        if isinstance(value, np.ndarray):
            return self.numpy_to_value(obj, value)

        self.error(
            obj,
            value,
            info="a URL string or a numpy ndarray array representing image data",
        )
