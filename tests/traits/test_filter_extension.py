from collections.abc import Callable

import arro3
import geopandas as gpd
import numpy as np
import pyarrow as pa
import pytest
from shapely.geometry import Point
from traitlets import TraitError

import lonboard
from lonboard.layer_extension import DataFilterExtension


@pytest.fixture
def dfe_test_df() -> gpd.GeoDataFrame:
    """GeoDataframe for testing DataFilterExtension."""
    d = {
        "int_col": [0, 1, 2, 3, 4, 5],
        "float_col": [0.0, 1.5, 0.0, 1.5, 0.0, 1.5],
        "str_col": ["even", "odd", "even", "odd", "even", "odd"],
        "bool_col": [True, False, True, False, True, False],
        "geometry": [
            Point(0, 0),
            Point(1, 1),
            Point(2, 2),
            Point(3, 3),
            Point(4, 4),
            Point(5, 5),
        ],
    }
    return gpd.GeoDataFrame(d, crs="EPSG:4326")


def test_dfe_no_args_no_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE without args, no get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(),
        ],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size is None
    assert layer.get_filter_value is None
    assert layer.get_filter_category is None


def test_dfe_no_args_and_int_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE without args and int get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(),
        ],
        get_filter_value=dfe_test_df["int_col"],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size is None
    assert isinstance(layer.get_filter_value, arro3.core.ChunkedArray)
    assert layer.get_filter_category is None


def test_dfe_no_args_and_float_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE without args and float get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(),
        ],
        get_filter_value=dfe_test_df["float_col"],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size is None
    assert isinstance(layer.get_filter_value, arro3.core.ChunkedArray)
    assert layer.get_filter_category is None


def test_dfe_filter_size_no_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size, no get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=1),
        ],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size is None
    assert layer.get_filter_value is None
    assert layer.get_filter_category is None


def test_dfe_filter_size_and_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size and get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=1),
        ],
        get_filter_value=dfe_test_df["int_col"],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size is None
    assert isinstance(layer.get_filter_value, arro3.core.ChunkedArray)
    assert layer.get_filter_category is None


def test_dfe_filter_size2_no_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size 2, no get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=2),
        ],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 2
    assert dfe.category_size is None
    assert layer.get_filter_value is None
    assert layer.get_filter_category is None


def test_dfe_filter_size2_and_get_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size 2 and get_filter_value
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=2),
        ],
        get_filter_value=dfe_test_df[["int_col", "float_col"]].values,
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 2
    assert dfe.category_size is None
    assert isinstance(layer.get_filter_value, arro3.core.ChunkedArray)
    assert layer.get_filter_category is None


def test_dfe_cat_no_get_filter_cat(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size None category_size=1, no get_filter_category
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=None, category_size=1),
        ],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size is None
    assert dfe.category_size == 1
    assert layer.get_filter_value is None
    assert layer.get_filter_category is None


def test_dfe_cat_and_int_get_filter_cat(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size None category_size=1 and get_filter_category
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=None, category_size=1),
        ],
        get_filter_category=dfe_test_df["int_col"],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size is None
    assert dfe.category_size == 1
    assert layer.get_filter_value is None
    assert isinstance(layer.get_filter_category, arro3.core.ChunkedArray)


def test_dfe_cat_and_float_get_filter_cat(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size None category_size=1 and get_filter_category
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=None, category_size=1),
        ],
        get_filter_category=dfe_test_df["float_col"],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size is None
    assert dfe.category_size == 1
    assert layer.get_filter_value is None
    assert isinstance(layer.get_filter_category, arro3.core.ChunkedArray)


def test_dfe_cat2_get_filter_cat(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size None category_size=2 and get_filter_category
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=None, category_size=2),
        ],
        get_filter_category=dfe_test_df[["int_col", "float_col"]].values,
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size is None
    assert dfe.category_size == 2
    assert layer.get_filter_value is None
    assert isinstance(layer.get_filter_category, arro3.core.ChunkedArray)


def test_dfe_value_and_cat_no_get_filter_value_or_category(
    dfe_test_df: gpd.GeoDataFrame,
):
    ## Test DFE with filter_size=1 category_size=1 and no get_filter_value or get_filter_category
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=1, category_size=1),
        ],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size == 1
    assert layer.get_filter_value is None
    assert layer.get_filter_category is None


def test_dfe_value_and_cat_and_get_filter_value_category(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size=1 category_size=1 and get_filter_value/get_filter_category
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=1, category_size=1),
        ],
        get_filter_value=dfe_test_df["int_col"],
        get_filter_category=dfe_test_df["float_col"],
    )
    assert len(layer.extensions) == 1
    dfe = layer.extensions[0]
    assert isinstance(dfe, DataFilterExtension)
    assert dfe.filter_size == 1
    assert dfe.category_size == 1
    assert isinstance(layer.get_filter_value, arro3.core.ChunkedArray)
    assert isinstance(layer.get_filter_category, arro3.core.ChunkedArray)


def test_dfe_filter_size_none_with_filter_value(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size=None category_size=1 and get_filter_value provided raises
    with pytest.raises(TraitError):
        lonboard.ScatterplotLayer.from_geopandas(
            dfe_test_df,
            extensions=[
                DataFilterExtension(filter_size=None, category_size=1),
            ],
            get_filter_value=dfe_test_df["float_col"],
        )


def test_dfe_category_size_none_with_filter_category(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size=1 category_size=None and get_filter_category provided raises
    with pytest.raises(TraitError):
        lonboard.ScatterplotLayer.from_geopandas(
            dfe_test_df,
            extensions=[
                DataFilterExtension(filter_size=1, category_size=None),
            ],
            get_filter_category=dfe_test_df["float_col"],
        )


def test_dfe_wrong_get_filter_value_size(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size=2 and get_filter_value with 1-D array raises
    with pytest.raises(TraitError):
        lonboard.ScatterplotLayer.from_geopandas(
            dfe_test_df,
            extensions=[
                DataFilterExtension(filter_size=2, category_size=None),
            ],
            get_filter_value=dfe_test_df["float_col"],
        )


def test_dfe_wrong_get_filter_value_size2(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with filter_size=1 and get_filter_value with 2-D array raises
    with pytest.raises(TraitError):
        lonboard.ScatterplotLayer.from_geopandas(
            dfe_test_df,
            extensions=[
                DataFilterExtension(filter_size=1, category_size=None),
            ],
            get_filter_value=dfe_test_df[["int_col", "float_col"]].values,
        )


def test_dfe_wrong_get_filter_category_size(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with category_size=2 and get_filter_category with 1-D array raises
    with pytest.raises(TraitError):
        lonboard.ScatterplotLayer.from_geopandas(
            dfe_test_df,
            extensions=[
                DataFilterExtension(filter_size=None, category_size=2),
            ],
            get_filter_category=dfe_test_df["float_col"],
        )


def test_dfe_wrong_get_filter_category_size2(dfe_test_df: gpd.GeoDataFrame):
    ## Test DFE with category_size=1 and get_filter_category with 2-D array raises
    with pytest.raises(TraitError):
        lonboard.ScatterplotLayer.from_geopandas(
            dfe_test_df,
            extensions=[
                DataFilterExtension(filter_size=None, category_size=1),
            ],
            get_filter_category=dfe_test_df[["int_col", "float_col"]].values,
        )


# The ways of passing a boolean column to an accessor
BOOL_INPUTS = {
    "numpy": np.asarray,
    "pandas": lambda series: series,
    "arrow-array": pa.array,
    "arrow-chunked-array": lambda series: pa.chunked_array([pa.array(series)]),
}

# The ways of passing two boolean columns, as a 2D numpy array, to an accessor
BOOL_2D_INPUTS = {
    "numpy": lambda values: values,
    "arrow-fixed-size-list": lambda values: pa.FixedSizeListArray.from_arrays(
        pa.array(values.ravel()),
        2,
    ),
}


@pytest.mark.parametrize("as_input", BOOL_INPUTS.values(), ids=BOOL_INPUTS.keys())
def test_dfe_bool_get_filter_value(dfe_test_df: gpd.GeoDataFrame, as_input: Callable):
    ## Test DFE with boolean get_filter_value, which is cast to float32
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=1),
        ],
        get_filter_value=as_input(dfe_test_df["bool_col"]),
    )
    filter_value = pa.chunked_array(layer.get_filter_value)
    assert filter_value.type == pa.float32()
    assert filter_value.to_pylist() == [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]


@pytest.mark.parametrize(
    "as_input",
    BOOL_2D_INPUTS.values(),
    ids=BOOL_2D_INPUTS.keys(),
)
def test_dfe_bool_filter_size2_get_filter_value(
    dfe_test_df: gpd.GeoDataFrame,
    as_input: Callable,
):
    ## Test DFE with filter_size 2 and boolean get_filter_value
    bool_col = dfe_test_df["bool_col"].to_numpy()
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=2),
        ],
        get_filter_value=as_input(np.column_stack([bool_col, ~bool_col])),
    )
    filter_value = pa.chunked_array(layer.get_filter_value)
    assert filter_value.type.value_type == pa.float32()
    assert filter_value.to_pylist() == [
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [0.0, 1.0],
    ]


@pytest.mark.parametrize("as_input", BOOL_INPUTS.values(), ids=BOOL_INPUTS.keys())
def test_dfe_bool_get_filter_cat(dfe_test_df: gpd.GeoDataFrame, as_input: Callable):
    ## Test DFE with boolean get_filter_category, which is cast to uint8
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=None, category_size=1),
        ],
        get_filter_category=as_input(dfe_test_df["bool_col"]),
    )
    filter_category = pa.chunked_array(layer.get_filter_category)
    # In a fixed size list, because the frontend doesn't render a plain integer array
    assert filter_category.type.value_type == pa.uint8()
    assert filter_category.to_pylist() == [[1], [0], [1], [0], [1], [0]]


@pytest.mark.parametrize(
    "as_input",
    BOOL_2D_INPUTS.values(),
    ids=BOOL_2D_INPUTS.keys(),
)
def test_dfe_bool_cat2_get_filter_cat(
    dfe_test_df: gpd.GeoDataFrame,
    as_input: Callable,
):
    ## Test DFE with category_size=2 and boolean get_filter_category
    bool_col = dfe_test_df["bool_col"].to_numpy()
    layer = lonboard.ScatterplotLayer.from_geopandas(
        dfe_test_df,
        extensions=[
            DataFilterExtension(filter_size=None, category_size=2),
        ],
        get_filter_category=as_input(np.column_stack([bool_col, ~bool_col])),
    )
    filter_category = pa.chunked_array(layer.get_filter_category)
    assert filter_category.type.value_type == pa.uint8()
    assert filter_category.to_pylist() == [
        [1, 0],
        [0, 1],
        [1, 0],
        [0, 1],
        [1, 0],
        [0, 1],
    ]
