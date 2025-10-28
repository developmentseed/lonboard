# ruff: noqa: D205, ERA001

from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard._geoarrow.ops import Bbox, WeightedCentroid
from lonboard.layer._base import BaseLayer
from lonboard.traits import (
    VariableLengthTuple,
)

if TYPE_CHECKING:
    import sys

    from lonboard.types.layer import BitmapLayerKwargs, BitmapTileLayerKwargs

    if sys.version_info >= (3, 11):
        pass
    else:
        pass

    if sys.version_info >= (3, 12):
        pass
    else:
        pass


class BitmapLayer(BaseLayer):
    """The `BitmapLayer` renders a bitmap (e.g. PNG, JPEG, or WebP) at specified
    boundaries.

    **Example:**

    ```py
    from lonboard import Map, BitmapLayer

    layer = BitmapLayer(
        image='https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/sf-districts.png',
        bounds=[-122.5190, 37.7045, -122.355, 37.829]
    )
    m = Map(layer)
    m
    ```
    """

    def __init__(self, **kwargs: BitmapLayerKwargs) -> None:
        super().__init__(**kwargs)  # type: ignore

    _layer_type = t.Unicode("bitmap").tag(sync=True)

    image = t.Unicode().tag(sync=True)
    """The URL to an image to display.

    - Type: `str`
    """

    bounds = t.Union(
        [
            VariableLengthTuple(t.Float(), minlen=4, maxlen=4),
            VariableLengthTuple(
                VariableLengthTuple(t.Float(), minlen=2, maxlen=2),
                minlen=4,
                maxlen=4,
            ),
        ],
    ).tag(sync=True)
    """The bounds of the image.

    Supported formats:

        - Coordinates of the bounding box of the bitmap `[left, bottom, right, top]`
        - Coordinates of four corners of the bitmap, should follow the sequence of
          `[[left, bottom], [left, top], [right, top], [right, bottom]]`.
    """

    desaturate = t.Float(0, min=0, max=1).tag(sync=True)
    """The desaturation of the bitmap. Between `[0, 1]`.

    - Type: `float`, optional
    - Default: `0`
    """

    transparent_color = VariableLengthTuple(
        t.Float(),
        default_value=None,
        allow_none=True,
        minlen=3,
        maxlen=4,
    )
    """The color to use for transparent pixels, in `[r, g, b, a]`.

    - Type: `List[float]`, optional
    - Default: `[0, 0, 0, 0]`
    """

    tint_color = VariableLengthTuple(
        t.Float(),
        default_value=None,
        allow_none=True,
        minlen=3,
        maxlen=4,
    )
    """The color to tint the bitmap by, in `[r, g, b]`.

    - Type: `List[float]`, optional
    - Default: `[255, 255, 255]`
    """

    @property
    def _bbox(self) -> Bbox:
        a, b, c, d = self.bounds

        # Four corners
        if isinstance(a, tuple):
            bbox = Bbox()
            bbox.update(Bbox(a[0], a[1], a[0], a[1]))
            bbox.update(Bbox(b[0], b[1], b[0], b[1]))
            bbox.update(Bbox(c[0], c[1], c[0], c[1]))
            bbox.update(Bbox(d[0], d[1], d[0], d[1]))
            return bbox

        return Bbox(a, b, c, d)

    @property
    def _weighted_centroid(self) -> WeightedCentroid:
        bbox = self._bbox
        center_x = (bbox.minx + bbox.maxx) / 2
        center_y = (bbox.miny + bbox.maxy) / 2
        # no idea what weight to put on this; we don't know how many "objects" this
        # image should represent.
        return WeightedCentroid(x=center_x, y=center_y, num_items=100)


class BitmapTileLayer(BaseLayer):
    """The BitmapTileLayer renders image tiles (e.g. PNG, JPEG, or WebP) in the web
    mercator tiling system. Only the tiles visible in the current viewport are loaded
    and rendered.

    **Example:**

    ```py
    from lonboard import Map, BitmapTileLayer

    # We set `max_requests < 0` because `tile.openstreetmap.org` supports HTTP/2.
    layer = BitmapTileLayer(
        data="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        tile_size=256,
        max_requests=-1,
        min_zoom=0,
        max_zoom=19,
    )
    m = Map(layer)
    ```
    """

    def __init__(self, **kwargs: BitmapTileLayerKwargs) -> None:
        super().__init__(**kwargs)  # type: ignore

    _layer_type = t.Unicode("bitmap-tile").tag(sync=True)

    data = t.Union([t.Unicode(), VariableLengthTuple(t.Unicode(), minlen=1)]).tag(
        sync=True,
    )
    """
    Either a URL template or an array of URL templates from which the tile data should
    be loaded.

    If the value is a string: a URL template. Substrings {x} {y} and {z}, if present,
    will be replaced with a tile's actual index when it is requested.

    If the value is an array: multiple URL templates. Each endpoint must return the same
    content for the same tile index. This can be used to work around domain sharding,
    allowing browsers to download more resources simultaneously. Requests made are
    balanced among the endpoints, based on the tile index.
    """

    tile_size = t.Int(None, allow_none=True).tag(sync=True)
    """
    The pixel dimension of the tiles, usually a power of 2.

    Tile size represents the target pixel width and height of each tile when rendered.
    Smaller tile sizes display the content at higher resolution, while the layer needs
    to load more tiles to fill the same viewport.

    - Type: `int`, optional
    - Default: `512`
    """

    zoom_offset = t.Int(None, allow_none=True).tag(sync=True)
    """
    This offset changes the zoom level at which the tiles are fetched. Needs to be an
    integer.

    - Type: `int`, optional
    - Default: `0`
    """

    max_zoom = t.Int(None, allow_none=True).tag(sync=True)
    """
    The max zoom level of the layer's data. When overzoomed (i.e. `zoom > max_zoom`),
    tiles from this level will be displayed.

    - Type: `int`, optional
    - Default: `None`
    """

    min_zoom = t.Int(None, allow_none=True).tag(sync=True)
    """
    The min zoom level of the layer's data. When underzoomed (i.e. `zoom < min_zoom`),
    the layer will not display any tiles unless `extent` is defined, to avoid issuing
    too many tile requests.

    - Type: `int`, optional
    - Default: `None`
    """

    extent = VariableLengthTuple(
        t.Float(),
        minlen=4,
        maxlen=4,
        allow_none=True,
        default_value=None,
    ).tag(sync=True)
    """
    The bounding box of the layer's data, in the form of `[min_x, min_y, max_x, max_y]`.
    If provided, the layer will only load and render the tiles that are needed to fill
    this box.

    - Type: `List[float]`, optional
    - Default: `None`
    """

    max_cache_size = t.Int(None, allow_none=True).tag(sync=True)
    """
    The maximum number of tiles that can be cached. The tile cache keeps loaded tiles in
    memory even if they are no longer visible. It reduces the need to re-download the
    same data over and over again when the user pan/zooms around the map, providing a
    smoother experience.

    If not supplied, the `max_cache_size` is calculated as 5 times the number of tiles
    in the current viewport.

    - Type: `int`, optional
    - Default: `None`
    """

    # TODO: Not sure if `getTileData` returns a `byteLength`?
    # max_cache_byte_size = t.Int(None, allow_none=True).tag(sync=True)
    # """
    # """

    refinement_strategy = t.Unicode(None, allow_none=True).tag(sync=True)
    """How the tile layer refines the visibility of tiles.

    When zooming in and out, if the layer only shows tiles from the current zoom level,
    then the user may observe undesirable flashing while new data is loading. By setting
    `refinement_strategy` the layer can attempt to maintain visual continuity by
    displaying cached data from a different zoom level before data is available.

    This prop accepts one of the following:

    - `"best-available"`: If a tile in the current viewport is waiting for its data to
      load, use cached content from the closest zoom level to fill the empty space. This
      approach minimizes the visual flashing due to missing content.
    - `"no-overlap"`: Avoid showing overlapping tiles when backfilling with cached
      content. This is usually favorable when tiles do not have opaque backgrounds.
    - `"never"`: Do not display any tile that is not selected.

    - Type: `str`, optional
    - Default: `"best-available"`
    """

    max_requests = t.Int(None, allow_none=True).tag(sync=True)
    """The maximum number of concurrent data fetches.

    If <= 0, no throttling will occur, and `get_tile_data` may be called an unlimited
    number of times concurrently regardless of how long that tile is or was visible.

    If > 0, a maximum of `max_requests` instances of `get_tile_data` will be called
    concurrently. Requests may never be called if the tile wasn't visible long enough to
    be scheduled and started. Requests may also be aborted (through the signal passed to
    `get_tile_data`) if there are more than `max_requests` ongoing requests and some of
    those are for tiles that are no longer visible.

    If `get_tile_data` makes fetch requests against an HTTP 1 web server, then
    max_requests should correlate to the browser's maximum number of concurrent fetch
    requests. For Chrome, the max is 6 per domain. If you use the data prop and specify
    multiple domains, you can increase this limit. For example, with Chrome and 3
    domains specified, you can set max_requests=18.

    If the web server supports HTTP/2 (Open Chrome dev tools and look for "h2" in the
    Protocol column), then you can make an unlimited number of concurrent requests (and
    can set max_requests=-1). Note that this will request data for every tile, no matter
    how long the tile was visible, and may increase server load.
    """

    desaturate = t.Float(0, min=0, max=1).tag(sync=True)
    """The desaturation of the bitmap. Between `[0, 1]`.

    - Type: `float`, optional
    - Default: `0`
    """

    transparent_color = VariableLengthTuple(
        t.Float(),
        default_value=None,
        allow_none=True,
        minlen=3,
        maxlen=4,
    )
    """The color to use for transparent pixels, in `[r, g, b, a]`.

    - Type: `List[float]`, optional
    - Default: `[0, 0, 0, 0]`
    """

    tint_color = VariableLengthTuple(
        t.Float(),
        default_value=None,
        allow_none=True,
        minlen=3,
        maxlen=4,
    )
    """The color to tint the bitmap by, in `[r, g, b]`.

    - Type: `List[float]`, optional
    - Default: `[255, 255, 255]`
    """
