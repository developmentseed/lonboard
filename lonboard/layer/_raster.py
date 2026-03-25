# ruff: noqa: SLF001, ERA001

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Generic, Literal, Protocol, TypeVar, Unpack

from pyproj.transformer import Transformer

import lonboard.traits as t
from lonboard._geoarrow.ops import Bbox, WeightedCentroid
from lonboard.layer._base import BaseLayer
from lonboard.raster import EncodedImage
from lonboard.traits import ProjectionTrait, TileMatrixSetTrait

if TYPE_CHECKING:
    import sys

    from async_geotiff import GeoTIFF, Overview, Tile
    from async_pmtiles import PMTilesReader
    from morecantile import TileMatrixSet
    from pyproj import CRS

    from lonboard.types.layer import RasterLayerKwargs

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


# These must be kept in sync with src/model/layer/raster.ts
MSG_KIND = "raster-get-tile-data"
MSG_KIND_CANCEL = f"{MSG_KIND}-cancel"

Tile_co = TypeVar("Tile_co", covariant=True)
"""Covariant generic type for type that FetchTile can return."""

Tile_contra = TypeVar("Tile_contra", contravariant=True)
"""Contravariant generic type for type that RenderTile can receive."""

T = TypeVar("T")


class FetchTile(Protocol[Tile_co]):
    """Protocol for user-defined fetch_tile function."""

    async def __call__(self, x: int, y: int, z: int) -> Tile_co:
        """Fetch a tile asynchronously.

        Args:
            x: The x coordinate of the tile.
            y: The y coordinate of the tile.
            z: The zoom level of the tile.

        Returns:
            A Tile object representing the fetched tile.

        """
        ...


class RenderTile(Protocol[Tile_contra]):
    """Protocol for user-defined render_tile function."""

    def __call__(self, tile: Tile_contra) -> EncodedImage | None:
        """Render a tile.

        Args:
            tile: A tile object returned by FetchTile.

        Returns:
            An RGBA numpy array representing the rendered tile.

        """
        ...


def handle_anywidget_dispatch(
    widget: RasterLayer,
    msg: str | list | dict,
    buffers: list[bytes],
) -> None:
    if not isinstance(msg, dict):
        return

    kind = msg.get("kind")

    if kind == MSG_KIND_CANCEL:
        task_id = msg.get("id")
        if not isinstance(task_id, str):
            return
        task = widget._pending_tasks.pop(task_id, None)
        if task is not None:
            task.cancel()
        return

    if kind != MSG_KIND:
        return

    # Schedule the async handler on the event loop
    task_id = msg["id"]
    task = asyncio.create_task(_handle_tile_request(widget, msg, buffers))
    widget._pending_tasks[task_id] = task
    task.add_done_callback(lambda _: widget._pending_tasks.pop(task_id, None))


async def _handle_tile_request(
    widget: RasterLayer,
    msg: dict,
    buffers: list[bytes],  # noqa: ARG001
) -> None:
    """Async handler for tile data requests from the frontend."""
    output = widget._error_output

    try:
        if widget.debug:
            output.append_stdout(f"Received tile request: {msg}")

        content = msg["msg"]
        tile = content["tile"]
        index = tile["index"]
        x = index["x"]
        y = index["y"]
        z = index["z"]

        if widget.debug:
            output.append_stdout(f"Fetching tile at x={x}, y={y}, z={z}\n")

        tile = await widget._fetch_tile(x=x, y=y, z=z)
        # TODO: put rendering in thread pool?
        rendered = widget._render_tile(tile)
        if rendered is None:
            widget.send(
                {
                    "id": msg["id"],
                    "kind": f"{MSG_KIND}-response",
                    "response": {
                        "type": "empty",
                    },
                },
            )
            return

        response_buffers = [rendered.data]

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": {
                    "type": "encoded-image",
                    "media_type": rendered.media_type,
                },
            },
            response_buffers,
        )
    except Exception:  # noqa: BLE001
        error_msg = traceback.format_exc()
        output.append_stderr(f"Error handling tile request: {error_msg}\n")

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": {"error": error_msg},
            },
        )


class RasterLayer(BaseLayer, Generic[T]):
    """The RasterLayer renders raster imagery.

    This layer expects input such as Cloud-Optimized GeoTIFFs (COGs) that can be
    efficiently accessed by internal tiles.
    """

    # Prevent garbage collection of async tasks before they complete.
    # Tasks are keyed by their UUID so they can be cancelled by ID when JS
    # fires an AbortSignal. Entries are removed automatically on completion.
    _pending_tasks: dict[str, asyncio.Task[None]]

    _fetch_tile: FetchTile[T]
    _render_tile: RenderTile[T]
    _bounds: Bbox | None
    _center: tuple[float, float] | None

    def __init__(
        self,
        *,
        _tile_matrix_set: TileMatrixSet | None,
        _crs: CRS,
        _fetch_tile: FetchTile[T],
        _render_tile: RenderTile[T],
        _bounds: Bbox | None = None,
        _center: tuple[float, float] | None = None,
        **kwargs: Unpack[RasterLayerKwargs],
    ) -> None:
        self._pending_tasks = {}
        self._fetch_tile = _fetch_tile
        self._render_tile = _render_tile
        self.on_msg(handle_anywidget_dispatch)
        self._bounds = _bounds
        self._center = _center
        super().__init__(_tile_matrix_set=_tile_matrix_set, _crs=_crs, **kwargs)  # type: ignore

    @property
    def _bbox(self) -> Bbox:
        # TODO: compute bounds from TMS if not explicitly set
        assert self._bounds is not None
        return self._bounds

    @property
    def _weighted_centroid(self) -> WeightedCentroid:
        assert self._center is not None
        return WeightedCentroid(x=self._center[0], y=self._center[1], num_items=100)

    # Note: this is a staticmethod because it always returns a concrete instance of
    # RasterLayer[Tile]
    # The typing doesn't work out if this is `@classmethod` because the type checker
    # tries and fails to associate `T` with `Tile`.
    @staticmethod
    def from_pmtiles(
        reader: PMTilesReader,
        **kwargs: Unpack[RasterLayerKwargs],
    ) -> RasterLayer[Buffer | None]:
        """Create a RasterLayer from a PMTiles archive.

        **Example:**

        Using [`obstore.store.HTTPStore`][obstore.store.HTTPStore] to read a PMTiles
        file over HTTP:

        ```py
        from async_pmtiles import PMTilesReader
        from lonboard import Map, RasterLayer
        from obstore.store import HTTPStore

        store = HTTPStore("https://air.mtn.tw")
        reader = await PMTilesReader.open("flowers.pmtiles", store=store)
        layer = RasterLayer.from_pmtiles(reader)
        m = Map(layer)
        ```

        Args:
            reader: A PMTilesReader instance from [`async-pmtiles`](https://github.com/developmentseed/async-pmtiles). Refer to the `async-pmtiles` documentation for how to create a PMTilesReader from various input sources.

        Keyword Args:
            kwargs: parameters passed on to `__init__`

        Raises:
            ValueError: if the PMTiles tile type is not a supported raster format (i.e.
                PNG, JPEG, WEBP, or AVIF).

        Returns:
            A new RasterLayer instance.

        """
        from pmtiles.tile import TileType

        media_type: Literal["image/png", "image/jpeg", "image/webp", "image/avif"]
        match reader.tile_type:
            case TileType.PNG:
                media_type = "image/png"
            case TileType.JPEG:
                media_type = "image/jpeg"
            case TileType.WEBP:
                media_type = "image/webp"
            case TileType.AVIF:
                media_type = "image/avif"
            case _:
                raise ValueError(
                    f"PMTiles tile type {reader.tile_type} is not supported by RasterLayer. "
                    "Only raster tile types are supported.",
                )

        async def fetch_tile(
            x: int,
            y: int,
            z: int,
        ) -> Buffer | None:
            """Fetch a specific tile from the PMTiles archive."""
            buffer = await reader.get_tile(x=x, y=y, z=z)
            if buffer is None:
                return None

            return buffer

        def render_tile(tile: Buffer | None) -> EncodedImage | None:
            """Render a tile using the user-provided render_tile function."""
            if tile is None:
                return None

            return EncodedImage(data=tile, media_type=media_type)

        # Remove the kwargs that we override
        kwargs.pop("min_zoom", None)
        kwargs.pop("max_zoom", None)
        kwargs.pop("extent", None)

        return RasterLayer(
            _fetch_tile=fetch_tile,
            _render_tile=render_tile,
            min_zoom=reader.minzoom,
            max_zoom=reader.maxzoom,
            extent=reader.bounds,
            _bounds=Bbox(*reader.bounds),
            _center=reader.center[:2],
            **kwargs,  # type: ignore
        )

    # Note: this is a staticmethod because it always returns a concrete instance of
    # RasterLayer[Tile]
    # The typing doesn't work out if this is `@classmethod` because the type checker
    # tries and fails to associate `T` with `Tile`.
    @staticmethod
    def from_geotiff(
        geotiff: GeoTIFF,
        /,
        *,
        render_tile: RenderTile[Tile],
        **kwargs: Unpack[RasterLayerKwargs],
    ) -> RasterLayer[Tile]:
        """Create a RasterLayer from a GeoTIFF instance from async-geotiff.

        **Example:**

        Args:
            geotiff: A GeoTIFF instance from [`async-geotiff`](https://github.com/developmentseed/async-geotiff). Refer to the `async-geotiff` documentation for how to create a GeoTIFF from various input sources.

        Keyword Args:
            render_tile:
            TODO: reword
            A function that takes a tile from the GeoTIFF and renders it into an RGBA image. The input tile will be in the format returned by `async-geotiff`'s `fetch_tile` method, which includes metadata and a method to access the pixel data as a NumPy array.
            kwargs: parameters passed on to `__init__`

        Returns:
            A new RasterLayer instance.

        """
        from async_geotiff.tms import generate_tms

        tms = generate_tms(geotiff)

        async def geotiff_fetch_tile(
            x: int,
            y: int,
            z: int,
        ) -> Tile:
            """Fetch a specific tile from the GeoTIFF."""
            images: list[GeoTIFF | Overview] = [geotiff, *geotiff.overviews]
            image = images[len(images) - 1 - z]
            return await image.fetch_tile(x, y, boundless=False)

        transformer = Transformer.from_crs(geotiff.crs, "EPSG:4326", always_xy=True)
        wgs84_bounds = transformer.transform_bounds(*geotiff.bounds)
        wgs84_center = (
            wgs84_bounds[0] + (wgs84_bounds[2] - wgs84_bounds[0]) / 2,
            wgs84_bounds[1] + (wgs84_bounds[3] - wgs84_bounds[1]) / 2,
        )

        return RasterLayer(
            _tile_matrix_set=tms,
            _crs=geotiff.crs,
            _fetch_tile=geotiff_fetch_tile,
            _render_tile=render_tile,
            # min_zoom=0,
            # max_zoom=len(tms.tileMatrices) - 1,
            _bounds=Bbox(*wgs84_bounds),
            _center=wgs84_center,
            **kwargs,
        )

    _layer_type = t.Unicode("raster")

    _tile_matrix_set: TileMatrixSet = TileMatrixSetTrait(allow_none=True).tag(sync=True)  # type: ignore

    _crs: CRS = ProjectionTrait().tag(sync=True)  # type: ignore

    _tile_size = t.Int(512)
    """The pixel dimension of the tiles, usually a power of 2.

    For geospatial viewports, tile size represents the target pixel width and height of each tile when rendered. Smaller tile sizes display the content at higher resolution, while the layer needs to load more tiles to fill the same viewport.

    For non-geospatial viewports, the tile size should correspond to the true pixel size of the tiles.

    - Default: `512`
    """

    zoom_offset = t.Int(0)
    """This offset changes the zoom level at which the tiles are fetched.  Needs to be an integer.

    - Default: `0`
    """

    max_zoom = t.Int(allow_none=True, default_value=None)
    """The max zoom level of the layer's data.

    When overzoomed (i.e. `zoom > maxZoom`), tiles from this level will be displayed.

    - Default: `null`
    """

    min_zoom = t.Int(0)
    """The min zoom level of the layer's data.

    When underzoomed (i.e. `zoom < minZoom`), the layer will not display any tiles
    unless `extent` is defined, to avoid issuing too many tile requests.

    - Default: 0
    """

    extent = t.List(
        t.Float(),
        allow_none=True,
        default_value=None,
        minlen=4,
        maxlen=4,
    )
    """The bounding box of the layer's data, in the form of `[minX, minY, maxX, maxY]`.

    If provided, the layer will only load and render the tiles that are needed to fill
    this box.

    - Default: `null`
    """

    max_cache_size = t.Int(allow_none=True, default_value=None)
    """The maximum number of tiles that can be cached.

    The tile cache keeps loaded tiles in memory even if they are no longer visible. It
    reduces the need to re-download the same data over and over again when the user
    pan/zooms around the map, providing a smoother experience.

    If not supplied, the `max_cache_size` is calculated as `5` times the number of tiles
    in the current viewport.

    - Default: `null`
    """

    # max_requests = t.Int(6)
    """Maximum number of concurrent getTileData calls. Default: 6."""

    debounce_time = t.Int(0)
    """Queue tile requests until no new tiles have been added for at least `debounceTime` milliseconds.

    If `debounceTime == 0`, tile requests are issued as quickly as the `maxRequests` concurrent request limit allows.

    If `debounceTime > 0`, tile requests are queued until a period of at least `debounceTime` milliseconds has passed without any new tiles being added to the queue. May reduce bandwidth usage and total loading time during interactive view transitions.

    - Default: `0`
    """
