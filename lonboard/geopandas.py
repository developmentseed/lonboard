from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
import numpy as np
import pandas as pd
from numpy import uint8

from lonboard import Map, viz
from lonboard.basemap import CartoStyle
from lonboard.colormap import apply_categorical_cmap, apply_continuous_cmap

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

    from lonboard.types.layer import (
        IntFloat,
        PathLayerKwargs,
        PolygonLayerKwargs,
        ScatterplotLayerKwargs,
    )
    from lonboard.types.map import MapKwargs

__all__ = ["LonboardAccessor"]

_QUERY_NAME_TRANSLATION = str.maketrans(dict.fromkeys("., -_/", ""))
_basemap_providers = {
    "CartoDB Positron": CartoStyle.Positron,
    "CartoDB Positron No Label": CartoStyle.PositronNoLabels,
    "CartoDB Darkmatter": CartoStyle.DarkMatter,
    "CartoDB Darkmatter No Label": CartoStyle.DarkMatterNoLabels,
    "CartoDB Voyager": CartoStyle.Voyager,
    "CartoDB Voyager No Label": CartoStyle.VoyagerNoLabels,
}
# Convert keys to lower case without spaces
_BASEMAP_PROVIDERS = {
    k.translate(_QUERY_NAME_TRANSLATION).lower(): v
    for k, v in _basemap_providers.items()
}


@pd.api.extensions.register_dataframe_accessor("lb")
class LonboardAccessor:
    """Geopandas Extension class to provide the `explore` method."""

    def __init__(self, pandas_obj: gpd.GeoDataFrame) -> None:
        """Initialize geopandas extension."""
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj: gpd.GeoDataFrame) -> None:
        if not isinstance(obj, gpd.GeoDataFrame):
            raise TypeError("Input Must be a geodataframe")

    def explore(  # noqa: C901, PLR0912, PLR0913, PLR0915
        self,
        column: str | None = None,
        *,
        cmap: str | None = None,
        color: str | None = None,
        m: Map | None = None,
        tiles: str | None = None,
        attr: str | list[str] | None = None,
        tooltip: bool = False,
        highlight: bool = False,
        categorical: bool = False,
        scheme: str | None = None,
        k: int | None = 5,
        vmin: float | None = None,
        vmax: float | None = None,
        classification_kwds: dict[str, str | IntFloat | ArrayLike | bool] | None = None,
        layer_kwargs: ScatterplotLayerKwargs
        | PathLayerKwargs
        | PolygonLayerKwargs
        | None = None,
        map_kwargs: MapKwargs | None = None,
        nan_color: list[int] | NDArray[np.uint8] | None = None,
        alpha: float | None = 1,
    ) -> Map:
        """Explore a dataframe using lonboard and deckgl.

        Keyword Args:
            column : Name of column on dataframe to visualize on map.
            cmap : Name of matplotlib colormap to use.
            color : single or array of colors passed to Layer.get_fill_color
                or a lonboard.basemap object, or a string to a maplibre style basemap.
            m: An existing Map object to plot onto.
            tiles : Either a known string {"CartoDB Positron",
                "CartoDB Positron No Label", "CartoDB Darkmatter",
                "CartoDB Darkmatter No Label", "CartoDB Voyager",
                "CartoDB Voyager No Label"}
            attr : Map tile attribution; only required if passing custom tile URL.
            tooltip : Whether to render a tooltip on hover on the map.
            highlight : Whether to highlight each feature on mouseover (passed to
                lonboard.Layer's auto_highlight). Defaults to False.
            categorical : Whether the data should be treated as categorical or
                continuous.
            scheme : Name of a classification scheme defined by mapclassify.Classifier.
            k : Number of classes to generate. Defaults to 5.
            vmin : Minimum value for color mapping.
            vmax : Maximum value for color mapping.
            classification_kwds : Additional keyword arguments passed to
                `mapclassify.classify`.
            layer_kwargs : Additional keyword arguments passed to lonboard.viz layer
                arguments (either `polygon_kwargs`, `scatterplot_kwargs`, or `path_kwargs`,
                depending on input geometry type).
            map_kwargs : Additional keyword arguments passed to lonboard.viz map_kwargs.
            nan_color : Color used to shade NaN observations formatted as an RGBA list.
                Defaults to [255, 255, 255, 255]. If no alpha channel is passed it is
                assumed to be 255.
            alpha : Alpha (opacity) parameter in the range (0,1) passed to
                mapclassify.util.get_color_array.

        Returns:
        lonboard.Map
            a lonboard map with geodataframe included as a Layer object.

        """
        gdf = self._obj

        if map_kwargs is None:
            map_kwargs = {}
        if classification_kwds is None:
            classification_kwds = {}
        if layer_kwargs is None:
            layer_kwargs = {}
        if nan_color is None:
            nan_color = [255, 255, 255, 255]
        if not pd.api.types.is_list_like(nan_color):
            raise ValueError("nan_color must be an iterable of 3 or 4 values")
        if len(nan_color) != 4:
            if len(nan_color) == 3:
                nan_color = np.append(nan_color, [255])
            else:
                raise ValueError("nan_color must be an iterable of 3 or 4 values")

        line = False  # set color of lines, not fill_color
        if ["LineString", "MultiLineString"] in gdf.geometry.geom_type.unique():
            line = True
        if color:
            if line:
                layer_kwargs["get_color"] = color
            else:
                layer_kwargs["get_fill_color"] = color
        if column is not None:
            try:
                from matplotlib import colormaps
            except ImportError as e:
                raise ImportError(
                    "you must have matplotlib installed to style by a column",
                ) from e

            if column not in gdf.columns:
                raise ValueError(
                    f"the designated column {column} is not in the dataframe",
                )
            if gdf[column].dtype in ["O", "category"]:
                categorical = True
            if cmap is not None and cmap not in colormaps:
                raise ValueError(
                    f"`cmap` must be one of {list(colormaps.keys())} but {cmap} was passed",
                )
            if cmap is None:
                cmap = "tab20" if categorical else "viridis"
            if categorical:
                color_array = _get_categorical_cmap(gdf[column], cmap, nan_color, alpha)
            elif scheme is None:
                if vmin is None:
                    vmin: int | float = np.nanmin(gdf[column])
                if vmax is None:
                    vmax: int | float = np.nanmax(gdf[column])
                # minmax scale the column first, matplotlib needs 0-1
                transformed = (gdf[column] - vmin) / (vmax - vmin)
                color_array = apply_continuous_cmap(
                    values=transformed,
                    cmap=colormaps[cmap],
                    alpha=alpha,
                )
            else:
                try:
                    from mapclassify._classify_API import _classifiers
                    from mapclassify.util import get_color_array

                    _klasses = list(_classifiers.keys())
                    _klasses.append("userdefined")
                except ImportError as e:
                    raise ImportError(
                        "You must have the package `mapclassify` >=2.7 installed to use the `scheme` keyword",
                    ) from e
                if scheme.replace("_", "") not in _klasses:
                    raise ValueError(
                        f"The classification scheme must be a valid mapclassify classifier in {_klasses}, but {scheme} was passed instead",
                    )
                if k is not None and "k" in classification_kwds:
                    # k passed directly takes precedence
                    classification_kwds.pop("k")
                color_array = get_color_array(
                    gdf[column],
                    scheme=scheme,
                    k=k,
                    cmap=cmap,
                    alpha=alpha,
                    nan_color=nan_color,
                    **classification_kwds,
                )

            if line:
                layer_kwargs["get_color"] = color_array

            else:
                layer_kwargs["get_fill_color"] = color_array
        if tiles:
            map_kwargs["basemap_style"] = _query_name(tiles)
        if attr:
            map_kwargs["custom_attribution"] = attr

        layer_kwargs["auto_highlight"] = highlight
        map_kwargs["show_tooltip"] = tooltip

        """
        additional loboard-specific arguments to consider

        # only polygons have z
        if ["Polygon", "MultiPolygon"] in gdf.geometry.geom_type.unique():
            layer_kwargs["get_elevation"] = elevation
            layer_kwargs["elevation_scale"] = elevation_scale
            layer_kwargs["wireframe"] = wireframe
                if isinstance(elevation, str):
            if elevation in gdf.columns:
                elevation: Series = gdf[elevation]
            else:
                raise ValueError(
                    f"the designated height column {elevation} is not in the dataframe",
                )
            if not pd.api.types.is_numeric_dtype(elevation):
                raise ValueError("elevation must be a numeric data type")
        if elevation is not None:
            layer_kwargs["extruded"] = True
        """

        new_m: Map = viz(
            gdf,
            polygon_kwargs=layer_kwargs,
            scatterplot_kwargs=layer_kwargs,
            path_kwargs=layer_kwargs,
            map_kwargs=map_kwargs,
        )
        if m is not None:
            new_m = m.add_layer(new_m)

        return new_m


def _get_categorical_cmap(
    categories: pd.Series,
    cmap: str,
    nan_color: str | NDArray[np.uint8] | NDArray[np.float64] | list[int],
    alpha: float | None,
) -> NDArray[uint8]:
    try:
        from matplotlib import colormaps
    except ImportError as e:
        raise ImportError(
            "this function requires the `matplotlib` package to be installed",
        ) from e

    cat_codes = pd.Series(pd.Categorical(categories).codes, dtype="category")
    # nans are encoded as -1 OR largest category depending on input type
    # re-encode to always be last category
    cat_codes = cat_codes.cat.rename_categories({-1: len(cat_codes.unique()) - 1})
    unique_cats = categories.dropna().unique()
    n_cats = len(unique_cats)
    colors = colormaps[cmap].resampled(n_cats)(list(range(n_cats)), alpha, bytes=True)
    colors = np.vstack([colors, nan_color])
    temp_cmap = dict(zip(range(n_cats + 1), colors, strict=True))
    return apply_categorical_cmap(cat_codes, temp_cmap)


def _query_name(name: str) -> CartoStyle:
    """Return basemap URL based on the name query (mimicking behavior from xyzservices).

    Returns a matching basemap from name contains the same letters in the same
    order as the provider's name irrespective of the letter case, spaces, dashes
    and other characters. See examples for details.

    Parameters
    ----------
    name : str
        Name of the tile provider. Formatting does not matter.

    Returns
    -------
    match: lonboard.basemap

    Examples
    --------
    >>> import xyzservices.providers as xyz

    All these queries return the same ``CartoDB.Positron`` TileProvider:

    >>> xyz._query_name("CartoDB Positron")
    >>> xyz._query_name("cartodbpositron")
    >>> xyz._query_name("cartodb-positron")
    >>> xyz._query_name("carto db/positron")
    >>> xyz._query_name("CARTO_DB_POSITRON")
    >>> xyz._query_name("CartoDB.Positron")

    """
    name_clean = name.translate(_QUERY_NAME_TRANSLATION).lower()
    if name_clean in _BASEMAP_PROVIDERS:
        return _BASEMAP_PROVIDERS[name_clean]

    raise ValueError(f"No matching provider found for the query '{name}'.")
