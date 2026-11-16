from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from pyproj import CRS

if TYPE_CHECKING:
    import sys
    from collections.abc import Sequence

    from affine import Affine
    from morecantile import TileMatrixSet

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


@dataclass
class EncodedImage:
    """An encoded image in a specific format."""

    # Keep the raw bytes out of the repr; a single tile's repr would otherwise
    # run to megabytes when displayed in a notebook.
    data: Buffer = field(repr=False)
    """Image data as a bytes-like object, such as bytes or memoryview."""

    media_type: Literal["image/png", "image/jpeg", "image/webp", "image/avif"]
    """The media type of the image, indicating its format."""

    def __post_init__(self) -> None:
        if self.media_type not in (
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/avif",
        ):
            raise ValueError(
                f"Invalid media_type {self.media_type!r}. Must be one of 'image/png', 'image/jpeg', 'image/webp', or 'image/avif'.",
            )

        if not isinstance(self.data, (bytes, memoryview)):
            # Check if the input is bytes-like by trying to create a memoryview.
            try:
                memoryview(self.data)
            except TypeError as e:
                raise TypeError(
                    f"data must be a bytes-like object such as bytes or memoryview, not {type(self.data).__name__!r}",
                ) from e

    def _repr_mimebundle_(self, **kwargs: Any) -> dict[str, bytes]:  # noqa: ARG002
        data = self.data if isinstance(self.data, bytes) else bytes(self.data)
        return {self.media_type: data}


@dataclass(frozen=True)
class AffineLevel:
    """One resolution level of a raster grid, from pixel edges to CRS coordinates."""

    transform: Affine
    """Affine transform from pixel `(col, row)` at the array's top-left edge to CRS `(x, y)`."""

    width: int
    """Array width in pixels."""

    height: int
    """Array height in pixels."""

    tile_width: int
    """Tile width in pixels."""

    tile_height: int
    """Tile height in pixels."""

    def __post_init__(self) -> None:
        for name in ("width", "height", "tile_width", "tile_height"):
            value = getattr(self, name)
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive int, got {value!r}")


Bounds = tuple[float, float, float, float]
"""`(min_x, min_y, max_x, max_y)` in a tileset's CRS."""


def _level_bounds(level: AffineLevel) -> Bounds:
    t = level.transform
    corners = [
        t * (0, 0),
        t * (level.width, 0),
        t * (0, level.height),
        t * (level.width, level.height),
    ]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys))


@runtime_checkable
class RasterTileset(Protocol):
    """A tile grid in a source CRS.

    Mirrors deck.gl-raster's `RasterTilesetDescriptor`, with the CRS in place
    of its projection functions.
    """

    @property
    def levels(self) -> Sequence[AffineLevel]:
        """The resolution levels, in any order."""
        ...

    @property
    def crs(self) -> CRS:
        """The coordinate reference system of the levels."""
        ...

    @property
    def bounds(self) -> Bounds:
        """`(min_x, min_y, max_x, max_y)` of the data in `crs`."""
        ...


@dataclass(frozen=True)
class AffineTileset:
    """A tileset whose levels are given as affine transforms.

    Mirrors deck.gl-raster's `AffineTileset`.
    """

    levels: Sequence[AffineLevel]
    """The resolution levels, in any order."""

    crs: CRS
    """The coordinate reference system of the levels."""

    def __post_init__(self) -> None:
        if len(self.levels) == 0:
            raise ValueError("AffineTileset needs at least one level")
        if not isinstance(self.crs, CRS):
            object.__setattr__(self, "crs", CRS.from_user_input(self.crs))

    @property
    def bounds(self) -> Bounds:
        """The union of the levels' arrays, in `crs`."""
        boxes = [_level_bounds(level) for level in self.levels]
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )


@dataclass(frozen=True)
class TileMatrixSetAdaptor:
    """A morecantile `TileMatrixSet` as a tileset, one level per tile matrix.

    Mirrors deck.gl-raster's `TileMatrixSetAdaptor`. Tile matrices with
    `variableMatrixWidths` are not supported.
    """

    tms: TileMatrixSet
    """The tile matrix set."""

    @property
    def levels(self) -> Sequence[AffineLevel]:
        """One level per tile matrix, in the tile matrix set's order."""
        from affine import Affine

        levels = []
        for matrix in self.tms.tileMatrices:
            if matrix.variableMatrixWidths:
                raise ValueError(
                    f"Tile matrix {matrix.id!r} has variableMatrixWidths, which an "
                    "affine level cannot describe",
                )
            x0, y0 = matrix.pointOfOrigin
            sign = 1.0 if matrix.cornerOfOrigin == "bottomLeft" else -1.0
            levels.append(
                AffineLevel(
                    transform=Affine(
                        matrix.cellSize,
                        0.0,
                        x0,
                        0.0,
                        sign * matrix.cellSize,
                        y0,
                    ),
                    width=matrix.matrixWidth * matrix.tileWidth,
                    height=matrix.matrixHeight * matrix.tileHeight,
                    tile_width=matrix.tileWidth,
                    tile_height=matrix.tileHeight,
                ),
            )
        return levels

    @property
    def crs(self) -> CRS:
        """The tile matrix set's CRS."""
        return CRS.from_user_input(self.tms.crs.root)

    @property
    def bounds(self) -> Bounds:
        """The tile matrix set's bounding box in its CRS."""
        box = self.tms.xy_bbox
        return (box.left, box.bottom, box.right, box.top)
