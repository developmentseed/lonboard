# ruff: noqa: SLF001, ERA001

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, Unpack

import traitlets.traitlets as t
from pyproj.transformer import Transformer

from lonboard._geoarrow.ops import Bbox, WeightedCentroid
from lonboard.layer._base import BaseLayer
from lonboard.raster import IMAGE_MIME_TYPES, EncodedImage
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


# This must be kept in sync with src/model/layer/raster.ts
MSG_KIND = "raster-get-tile-data"

Tile_co = TypeVar("Tile_co", covariant=True)
"""Covariant generic type for type that FetchTile can return."""

Tile_contra = TypeVar("Tile_contra", contravariant=True)
"""Contravariant generic type for type that RenderTile can receive."""

T = TypeVar("T")


class FetchTile(Protocol[Tile_co]):
    """Protocol for user-defined fetch_tile function."""

    async def __call__(self, *, x: int, y: int, z: int) -> Tile_co:
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
    """Protocol for user-defined render function."""

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
    if not isinstance(msg, dict) or msg.get("kind") != MSG_KIND:
        return

    # Schedule the async handler on the event loop
    task = asyncio.create_task(_handle_tile_request(widget, msg, buffers))
    widget._pending_tasks.add(task)
    task.add_done_callback(widget._pending_tasks.discard)


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

        tile = await widget.fetch_tile(x=x, y=y, z=z)
        # TODO: put rendering in thread pool?
        rendered = widget.render(tile)
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
                    "mime_type": rendered.mime_type,
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
    # Tasks are removed automatically via add_done_callback when they finish.
    #
    # TODO: ensure JS AbortSignal propagates to cancel these tasks
    _pending_tasks: set[asyncio.Task[None]]

    fetch_tile: FetchTile[T]
    render: RenderTile[T]
    _bounds: Bbox | None
    _center: tuple[float, float] | None

    def __init__(
        self,
        tile_matrix_set: TileMatrixSet | None,
        crs: CRS,
        *,
        fetch_tile: FetchTile[T],
        render: RenderTile[T],
        debug: bool = False,
        _bounds: Bbox | None = None,
        _center: tuple[float, float] | None = None,
        **kwargs: Unpack[RasterLayerKwargs],
    ) -> None:
        self._pending_tasks = set()
        self.fetch_tile = fetch_tile
        self.render = render
        self.debug = debug
        self.on_msg(handle_anywidget_dispatch)
        self._bounds = _bounds
        self._center = _center
        super().__init__(tile_matrix_set=tile_matrix_set, crs=crs, **kwargs)  # type: ignore

    @property
    def _bbox(self) -> Bbox:
        # TODO: compute bounds from TMS if not explicitly set
        assert self._bounds is not None
        return self._bounds

    @property
    def _weighted_centroid(self) -> WeightedCentroid:
        assert self._center is not None
        return WeightedCentroid(x=self._center[0], y=self._center[1], num_items=100)

    @classmethod
    def from_pmtiles(
        cls,
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

        mime_type: IMAGE_MIME_TYPES
        match reader.tile_type:
            case TileType.PNG:
                mime_type = "image/png"
            case TileType.JPEG:
                mime_type = "image/jpeg"
            case TileType.WEBP:
                mime_type = "image/webp"
            case TileType.AVIF:
                mime_type = "image/avif"
            case _:
                raise ValueError(
                    f"PMTiles tile type {reader.tile_type} is not supported by RasterLayer. "
                    "Only raster tile types are supported.",
                )

        async def fetch_tile(
            *,
            x: int,
            y: int,
            z: int,
        ) -> Buffer | None:
            """Fetch a specific tile from the PMTiles archive."""
            buffer = await reader.get_tile(x=x, y=y, z=z)
            if buffer is None:
                return None

            return buffer

        def render(tile: Buffer | None) -> EncodedImage | None:
            """Render a tile using the user-provided render function."""
            if tile is None:
                return None

            return EncodedImage(data=tile, mime_type=mime_type)

        # Remove the kwargs that we override
        kwargs.pop("min_zoom", None)
        kwargs.pop("max_zoom", None)
        kwargs.pop("extent", None)

        return RasterLayer(
            fetch_tile=fetch_tile,
            render=render,
            min_zoom=reader.minzoom,
            max_zoom=reader.maxzoom,
            extent=reader.bounds,
            _bounds=Bbox(*reader.bounds),
            _center=reader.center[:2],
            **kwargs,  # type: ignore
        )

    @classmethod
    def from_geotiff(
        cls,
        geotiff: GeoTIFF,
        /,
        *,
        render: RenderTile[Tile],
        **kwargs: Any,
        # TODO: can this return type specify RasterLayer[T] where T is the type of the
        # GeoTIFF?
        # Ideally, in a typed context, render should receive the correct tile type
    ) -> RasterLayer[Tile]:
        """Create a RasterLayer from a GeoTIFF instance from async-geotiff."""
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
            tile_matrix_set=tms,
            crs=geotiff.crs,
            fetch_tile=geotiff_fetch_tile,
            render=render,
            # min_zoom=0,
            # max_zoom=len(tms.tileMatrices) - 1,
            _bounds=Bbox(*wgs84_bounds),
            _center=wgs84_center,
            **kwargs,
        )  # type: ignore[call-arg]

    _layer_type = t.Unicode("raster").tag(sync=True)

    tile_matrix_set: TileMatrixSet = TileMatrixSetTrait(allow_none=True).tag(sync=True)  # type: ignore

    crs: CRS = ProjectionTrait().tag(sync=True)  # type: ignore

    tile_size = t.Int(512).tag(sync=True)
    """The pixel dimension of the tiles, usually a power of 2.

    For geospatial viewports, tile size represents the target pixel width and height of each tile when rendered. Smaller tile sizes display the content at higher resolution, while the layer needs to load more tiles to fill the same viewport.

    For non-geospatial viewports, the tile size should correspond to the true pixel size of the tiles.

    - Default: `512`
    """

    zoom_offset = t.Int(0).tag(sync=True)
    """This offset changes the zoom level at which the tiles are fetched.  Needs to be an integer.

    - Default: `0`
    """

    max_zoom = t.Int(allow_none=True, default_value=None).tag(sync=True)
    """The max zoom level of the layer's data.

    When overzoomed (i.e. `zoom > maxZoom`), tiles from this level will be displayed.

    - Default: `null`
    """

    min_zoom = t.Int(0).tag(sync=True)
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
    ).tag(sync=True)
    """The bounding box of the layer's data, in the form of `[minX, minY, maxX, maxY]`.

    If provided, the layer will only load and render the tiles that are needed to fill
    this box.

    - Default: `null`
    """

    max_cache_size = t.Int(allow_none=True, default_value=None).tag(sync=True)
    """The maximum number of tiles that can be cached.

    The tile cache keeps loaded tiles in memory even if they are no longer visible. It
    reduces the need to re-download the same data over and over again when the user
    pan/zooms around the map, providing a smoother experience.

    If not supplied, the `max_cache_size` is calculated as `5` times the number of tiles
    in the current viewport.

    - Default: `null`
    """

    # max_requests = t.Int(6).tag(sync=True)
    """Maximum number of concurrent getTileData calls. Default: 6."""

    debounce_time = t.Int(0).tag(sync=True)
    """Queue tile requests until no new tiles have been added for at least `debounceTime` milliseconds.

    If `debounceTime == 0`, tile requests are issued as quickly as the `maxRequests` concurrent request limit allows.

    If `debounceTime > 0`, tile requests are queued until a period of at least `debounceTime` milliseconds has passed without any new tiles being added to the queue. May reduce bandwidth usage and total loading time during interactive view transitions.

    - Default: `0`
    """
