from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t
from arro3.core import DataType

from lonboard._layer import BaseLayer
from lonboard.experimental.traits import MeshAccessor, TextureTrait

if TYPE_CHECKING:
    from typing import Any


class SurfaceLayer(BaseLayer):
    """SurfaceLayer."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # type: ignore

    _layer_type = t.Unicode("surface").tag(sync=True)

    positions = MeshAccessor(
        list_size=3,
        expected_arrow_type=DataType.list(
            DataType.float32(),
            3,
        ),
    )
    tex_coords = MeshAccessor(
        list_size=2,
        expected_arrow_type=DataType.list(
            DataType.float32(),
            2,
        ),
    )
    triangles = MeshAccessor(
        list_size=3,
        expected_arrow_type=DataType.list(
            DataType.uint32(),
            3,
        ),
    )

    texture = TextureTrait().tag(sync=True)

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to render the mesh in wireframe mode.

    - Type: `bool`, optional
    - Default: `False`
    """
