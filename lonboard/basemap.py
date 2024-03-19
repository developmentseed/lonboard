from enum import Enum


class CartoBasemap(str, Enum):
    """Basemap styles provided by Carto.

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
    """A dark map style without labels."""

    Positron = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    """A light map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/positron_labels.png)
    """

    PositronNoLabels = (
        "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json"
    )
    """A light map style without labels."""

    Voyager = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
    """A light, colored map style with labels.

    ![](https://carto.com/help/images/building-maps/basemaps/voyager_labels.png)
    """

    VoyagerNoLabels = (
        "https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json"
    )
    """A light, colored map style without labels."""
