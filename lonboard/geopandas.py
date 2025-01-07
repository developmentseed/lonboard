import geopandas as gpd
import numpy as np
import pandas as pd

from . import basemap, viz
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
        wireframe=False,
        tiles="CartoDB Darkmatter",
        m=None,
    ):
        """explore a dataframe using lonboard and deckgl

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            dataframe to visualize
        column : str, optional
            name of column on dataframe to visualize on map, by default None
        cmap : str, optional
            name of matplotlib colormap to use, by default None
        scheme : str, optional
            name of a classification scheme defined by mapclassify.Classifier, by default
            None
        k : int, optional
            number of classes to generate, by default 6
        categorical : bool, optional
            whether the data should be treated as categorical or continuous, by default
            False
        elevation : str or array, optional
            name of column on the dataframe used to extrude each geometry or  an array-like
            in the same order as observations, by default None
        extruded : bool, optional
            whether to extrude geometries using the z-dimension, by default False
        elevation_scale : float, optional
            constant scaler multiplied by elevation valuer, by default 1
        alpha : float, optional
            alpha (opacity) parameter in the range (0,1) passed to
            mapclassify.util.get_color_array, by default 1
        layer_kwargs : dict, optional
            additional keyword arguments passed to lonboard.viz layer arguments (either
            polygon_kwargs, scatterplot_kwargs, or path_kwargs, depending on input
            geometry type), by default None
        map_kwargs : dict, optional
            additional keyword arguments passed to lonboard.viz map_kwargs, by default
            None
        classification_kwds : dict, optional
            additional keyword arguments passed to `mapclassify.classify`, by default
            None
        nan_color : list-like, optional
            color used to shade NaN observations formatted as an RGBA list, by
            default [255, 255, 255, 255]. If no alpha channel is passed it is assumed to
            be 255.
        color : str or array-like, optional
            single or array of colors passed to `lonboard.Layer` object (get_color if
            input dataframe is linestring, or get_fill_color otherwise. By default None
        wireframe : bool, optional
            whether to use wireframe styling in deckgl, by default False
        tiles : str or lonboard.basemap
            either a known string {"CartoDB Positron", "CartoDB Positron No Label",
            "CartoDB Darkmatter", "CartoDB Darkmatter No Label", "CartoDB Voyager",
            "CartoDB Voyager No Label"} or a lonboard.basemap object, or a string to a
            maplibre style basemap.

        Returns
        -------
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
            wireframe,
            tiles,
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
    wireframe=False,
    tiles="CartoDB Darkmatter",
    m=None,
):
    """explore a dataframe using lonboard and deckgl

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        dataframe to visualize
    column : str, optional
        name of column on dataframe to visualize on map, by default None
    cmap : str, optional
        name of matplotlib colormap to , by default None
    scheme : str, optional
        name of a classification scheme defined by mapclassify.Classifier, by default
        None
    k : int, optional
        number of classes to generate, by default 6
    categorical : bool, optional
        whether the data should be treated as categorical or continuous, by default
        False
    elevation : str or array, optional
        name of column on the dataframe used to extrude each geometry or an array-like
        in the same order as observations, by default None
    extruded : bool, optional
        whether to extrude geometries using the z-dimension, by default False
    elevation_scale : int, optional
        constant scaler multiplied by elevation valuer, by default 1
    alpha : float, optional
        alpha (opacity) parameter in the range (0,1) passed to
        mapclassify.util.get_color_array, by default 1
    layer_kwargs : dict, optional
        additional keyword arguments passed to lonboard.viz layer arguments (either
        polygon_kwargs, scatterplot_kwargs, or path_kwargs, depending on input
        geometry type), by default None
    map_kwargs : dict, optional
        additional keyword arguments passed to lonboard.viz map_kwargs, by default None
    classification_kwds : dict, optional
        additional keyword arguments passed to `mapclassify.classify`, by default None
    nan_color : list-like, optional
        color used to shade NaN observations formatted as an RGBA list, by
        default [255, 255, 255, 255]. If no alpha channel is passed it is assumed to be
        255.
    color : str or array-like, optional
        _description_, by default None
    wireframe : bool, optional
        whether to use wireframe styling in deckgl, by default False
    m : lonboard.Map
        a lonboard.Map instance to render the new layer on. If None (default), a new Map
        will be generated.

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
            # minmax scale the column first, matplotlib needs 0-1
            transformed = (gdf[column] - np.nanmin(gdf[column])) / (
                np.nanmax(gdf[column]) - np.nanmin(gdf[column])
            )
            color_array = apply_continuous_cmap(
                values=transformed, cmap=colormaps[cmap], alpha=alpha
            )
        else:
            try:
                from mapclassify.util import get_color_array
            except ImportError as e:
                raise ImportError(
                    "you must have the `mapclassify` package installed to use this function"
                ) from e
            if k is not None and 'k' in classification_kwds:
                # k passed directly takes precedence
                classification_kwds.pop('k')
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
