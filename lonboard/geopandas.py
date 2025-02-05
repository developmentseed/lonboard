from typing import Any, Dict, List, Optional, Union

import geopandas as gpd
import numpy as np
import pandas as pd

from . import Map, basemap, viz
from .colormap import apply_categorical_cmap, apply_continuous_cmap

__all__ = ["LonboardAccessor"]


@pd.api.extensions.register_dataframe_accessor("lb")
class LonboardAccessor:
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        if not isinstance(obj, gpd.GeoDataFrame):
            raise AttributeError("must be a geodataframe")

    def explore(
        self,
        column: Optional[str] = None,
        cmap: Optional[str] = None,
        scheme: Optional[str] = None,
        k: Optional[int] = 6,
        categorical: bool = False,
        elevation: Union[str, np.ndarray] = None,
        extruded: bool = False,
        elevation_scale: Optional[float] = 1,
        alpha: Optional[float] = 1,
        layer_kwargs: Optional[Dict[str, Any]] = None,
        map_kwargs: Optional[Dict[str, Any]] = None,
        classification_kwds: Optional[Dict[str, Any]] = None,
        nan_color: Optional[Union[List[int], np.ndarray[int]]] = [255, 255, 255, 255],
        color: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        wireframe: bool = False,
        tiles: Optional[str] = None,
        highlight: bool = False,
        m: Optional[Map] = None,
    ) -> Map:
        """explore a dataframe using lonboard and deckgl

        Keyword Args:
            column : Name of column on dataframe to visualize on map.
            cmap : Name of matplotlib colormap to use.
            scheme : Name of a classification scheme defined by mapclassify.Classifier.
            k : Number of classes to generate. Defaults to 6.
            categorical : Whether the data should be treated as categorical or
                continuous.
            elevation : Name of column on the dataframe used to extrude each geometry or
                an array-like in the same order as observations. Defaults to None.
            extruded : Whether to extrude geometries using the z-dimension.
            elevation_scale : Constant scaler multiplied by elevation value.
            alpha : Alpha (opacity) parameter in the range (0,1) passed to
                mapclassify.util.get_color_array.
            layer_kwargs : Additional keyword arguments passed to lonboard.viz layer
                arguments (either polygon_kwargs, scatterplot_kwargs, or path_kwargs,
                depending on input geometry type).
            map_kwargs : Additional keyword arguments passed to lonboard.viz map_kwargs.
            classification_kwds : Additional keyword arguments passed to
                `mapclassify.classify`.
            nan_color : Color used to shade NaN observations formatted as an RGBA list.
                Defaults to [255, 255, 255, 255]. If no alpha channel is passed it is
                assumed to be 255.
            color : Either a known string {"CartoDB Positron",
                "CartoDB Positron No Label", "CartoDB Darkmatter",
                "CartoDB Darkmatter No Label", "CartoDB Voyager",
                "CartoDB Voyager No Label"}
                or a lonboard.basemap object, or a string to a maplibre style basemap.
            vmin : Minimum value for color mapping.
            vmax : Maximum value for color mapping.
            wireframe : Whether to use wireframe styling in deckgl.
            tiles : An existing Map object to plot onto.
            highlight : Whether to highlight each feature on mouseover (passed to
                lonboard.Layer's auto_highlight). Defaults to False.

        Returns:
        lonboard.Map
            a lonboard map with geodataframe included as a Layer object.
        """
        return _dexplore(
            self._obj,
            column,
            cmap,
            scheme,
            k,
            categorical,
            elevation,
            extruded,
            elevation_scale,
            alpha,
            layer_kwargs,
            map_kwargs,
            classification_kwds,
            nan_color,
            color,
            vmin,
            vmax,
            wireframe,
            tiles,
            highlight,
            m,
        )


def _dexplore(
    gdf,
    column=None,
    cmap=None,
    scheme=None,
    k=6,
    categorical=False,
    elevation=None,
    extruded=False,
    elevation_scale=1,
    alpha=1,
    layer_kwargs=None,
    map_kwargs=None,
    classification_kwds=None,
    nan_color=[255, 255, 255, 255],
    color=None,
    vmin=None,
    vmax=None,
    wireframe=False,
    tiles="CartoDB Darkmatter",
    highlight=False,
    m=None,
):
    """explore a dataframe using lonboard and deckgl.

    See the public docstring for detailed parameter information

    Returns
    -------
    lonboard.Map
        a lonboard map with geodataframe included as a Layer object.

    """

    providers = {
        "CartoDB Positron": basemap.CartoBasemap.Positron,
        "CartoDB Positron No Label": basemap.CartoBasemap.PositronNoLabels,
        "CartoDB Darkmatter": basemap.CartoBasemap.DarkMatter,
        "CartoDB Darkmatter No Label": basemap.CartoBasemap.DarkMatterNoLabels,
        "CartoDB Voyager": basemap.CartoBasemap.Voyager,
        "CartoDB Voyager No Label": basemap.CartoBasemap.VoyagerNoLabels,
    }

    if map_kwargs is None:
        map_kwargs = dict()
    if classification_kwds is None:
        classification_kwds = dict()
    if layer_kwargs is None:
        layer_kwargs = dict()
    if isinstance(elevation, str):
        if elevation in gdf.columns:
            elevation = gdf[elevation]
        else:
            raise ValueError(
                f"the designated height column {elevation} is not in the dataframe"
            )
        if not pd.api.types.is_numeric_dtype(elevation):
            raise ValueError("elevation must be a numeric data type")

    if not pd.api.types.is_list_like(nan_color):
        raise ValueError("nan_color must be an iterable of 3 or 4 values")

    if len(nan_color) != 4:
        if len(nan_color) == 3:
            nan_color = np.append(nan_color, [255])
        else:
            raise ValueError("nan_color must be an iterable of 3 or 4 values")

    # only polygons have z
    if ["Polygon", "MultiPolygon"] in gdf.geometry.geom_type.unique():
        layer_kwargs["get_elevation"] = elevation
        layer_kwargs["extruded"] = extruded
        layer_kwargs["elevation_scale"] = elevation_scale
        layer_kwargs["wireframe"] = wireframe
        layer_kwargs["auto_highlight"] = highlight

    LINE = False  # set color of lines, not fill_color
    if ["LineString", "MultiLineString"] in gdf.geometry.geom_type.unique():
        LINE = True
    if color:
        if LINE:
            layer_kwargs["get_color"] = color
        else:
            layer_kwargs["get_fill_color"] = color
    if column is not None:
        try:
            from matplotlib import colormaps
            from matplotlib.colors import
        except ImportError as e:
            raise ImportError(
                "you must have matplotlib installed to style by a column"
            ) from e

        if column not in gdf.columns:
            raise ValueError(f"the designated column {column} is not in the dataframe")
        if gdf[column].dtype in ["O", "category"]:
            categorical = True
        if cmap is not None and cmap not in colormaps:
            raise ValueError(
                f"`cmap` must be one of {list(colormaps.keys())} but {cmap} was passed"
            )
        if cmap is None:
            cmap = "tab20" if categorical else "viridis"
        if categorical:
            color_array = _get_categorical_cmap(gdf[column], cmap, nan_color, alpha)
        elif scheme is None:
            if vmin is None:
                vmin = np.nanmin(gdf[column])
            if vmax is None:
                vmax = np.nanmax(gdf[column])
            # minmax scale the column first, matplotlib needs 0-1
            transformed = (gdf[column] - vmin) / (
                vmax - vmin)
            color_array = apply_continuous_cmap(
                values=transformed, cmap=colormaps[cmap], alpha=alpha
            )
        else:
            try:
                from mapclassify._classify_API import _classifiers
                from mapclassify.util import get_color_array

                _klasses = list(_classifiers.keys())
                _klasses.append("userdefined")
            except ImportError as e:
                raise ImportError(
                    "you must have the `mapclassify` package installed to use the "
                    "`scheme` keyword"
                ) from e
            if scheme.replace("_", "") not in _klasses:
                raise ValueError(
                    "the classification scheme must be a valid mapclassify"
                    f"classifier in {_klasses},"
                    f"but {scheme} was passed instead"
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

        if LINE:
            layer_kwargs["get_color"] = color_array

        else:
            layer_kwargs["get_fill_color"] = color_array
    if tiles:
        map_kwargs["basemap_style"] = providers[tiles]
    new_m = viz(
        gdf,
        polygon_kwargs=layer_kwargs,
        scatterplot_kwargs=layer_kwargs,
        path_kwargs=layer_kwargs,
        map_kwargs=map_kwargs,
    )
    if m is not None:
        new_m = m.add_layer(new_m)

    return new_m


def _get_categorical_cmap(categories, cmap, nan_color, alpha):
    try:
        from matplotlib import colormaps
    except ImportError as e:
        raise ImportError(
            "this function requres the lonboard package to be installed"
        ) from e

    cat_codes = pd.Series(pd.Categorical(categories).codes, dtype="category")
    # nans are encoded as -1 OR largest category depending on input type
    # re-encode to always be last category
    cat_codes = cat_codes.cat.rename_categories({-1: len(cat_codes.unique()) - 1})
    unique_cats = categories.dropna().unique()
    n_cats = len(unique_cats)
    colors = colormaps[cmap].resampled(n_cats)(list(range(n_cats)), alpha, bytes=True)
    colors = np.vstack([colors, nan_color])
    temp_cmap = dict(zip(range(n_cats + 1), colors))
    fill_color = apply_categorical_cmap(cat_codes, temp_cmap)
    return fill_color
