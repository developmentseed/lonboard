"""Basemap helpers."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

import traitlets as t
from typing_extensions import deprecated

from lonboard._base import BaseWidget
from lonboard.traits import BasemapUrl

if TYPE_CHECKING:
    from typing import Literal


class CartoStyle(str, Enum):
    """Maplibre-supported vector basemap styles provided by Carto.

    Refer to [Carto
    documentation](https://docs.carto.com/carto-for-developers/carto-for-react/guides/basemaps)
    for information on styles.
    """

    DarkMatter = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
    """A dark map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/dark_labels.png)
    """

    DarkMatterNoLabels = (
        "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json"
    )
    """A dark map style without labels.

    ![](https://carto.com/help/images/building-maps/basemaps/dark_no_labels.png)
    """

    Positron = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    """A light map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/positron_labels.png)
    """

    PositronNoLabels = (
        "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json"
    )
    """A light map style without labels.

    ![](https://carto.com/help/images/building-maps/basemaps/positron_no_labels.png)
    """

    Voyager = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
    """A light, colored map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/voyager_labels.png)
    """

    VoyagerNoLabels = (
        "https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json"
    )
    """A light, colored map style without labels.

    ![](https://carto.com/help/images/building-maps/basemaps/voyager_no_labels.png)
    """


# NOTE: this is fully duplicated because you can't subclass enums, and I don't see any
# other way to provide a deprecation warning
@deprecated(
    "CartoBasemap is deprecated, use CartoStyle instead. Will be removed in v0.14",
)
class CartoBasemap(str, Enum):
    """Maplibre-supported vector basemap styles provided by Carto.

    Refer to [Carto
    documentation](https://docs.carto.com/carto-for-developers/carto-for-react/guides/basemaps)
    for information on styles.
    """

    DarkMatter = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
    """A dark map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/dark_labels.png)
    """

    DarkMatterNoLabels = (
        "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json"
    )
    """A dark map style without labels.

    ![](https://carto.com/help/images/building-maps/basemaps/dark_no_labels.png)
    """

    Positron = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    """A light map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/positron_labels.png)
    """

    PositronNoLabels = (
        "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json"
    )
    """A light map style without labels.

    ![](https://carto.com/help/images/building-maps/basemaps/positron_no_labels.png)
    """

    Voyager = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
    """A light, colored map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/voyager_labels.png)
    """

    VoyagerNoLabels = (
        "https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json"
    )
    """A light, colored map style without labels.

    ![](https://carto.com/help/images/building-maps/basemaps/voyager_no_labels.png)
    """


class MaplibreBasemap(BaseWidget):
    """A MapLibre GL JS basemap."""

    def __init__(
        self,
        *,
        mode: Literal[
            "interleaved",
            "overlaid",
            "reverse-controlled",
        ] = "reverse-controlled",
        style: str | CartoStyle = CartoStyle.PositronNoLabels,
    ) -> None:
        """Create a MapLibre GL JS basemap."""
        super().__init__(mode=mode, style=style)

    mode = t.Enum(
        [
            "interleaved",
            "overlaid",
            "reverse-controlled",
        ],
        default_value="reverse-controlled",
    ).tag(sync=True)
    """The basemap integration mode.

    - **`"interleaved"`**:

        The interleaved mode renders deck.gl layers into the same context created by MapLibre. If you need to mix deck.gl layers with MapLibre layers, e.g. having deck.gl surfaces below text labels, or objects occluding each other correctly in 3D, then you have to use this option.

    - **`"overlaid"`**:

        The overlaid mode renders deck.gl in a separate canvas inside the MapLibre's controls container. If your use case does not require interleaving, but you still want to use certain features of maplibre-gl, such as globe view, then you should use this option.

    - **`"reverse-controlled"`**:

        The reverse-controlled mode renders deck.gl above the MapLibre container and blocks any interaction to the base map.

        If you need to have multiple views, you should use this option.

    **Default**: `"reverse-controlled"`
    """

    style = BasemapUrl(CartoStyle.PositronNoLabels).tag(sync=True)
    """
    A URL to a MapLibre-compatible basemap style.

    Various styles are provided in [`lonboard.basemap`](https://developmentseed.org/lonboard/latest/api/basemap/).

    - Type: `str`, holding a URL hosting a basemap style.
    - Default
      [`lonboard.basemap.CartoStyle.PositronNoLabels`][lonboard.basemap.CartoStyle.PositronNoLabels]
    """
