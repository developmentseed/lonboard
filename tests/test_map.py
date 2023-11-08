import geopandas as gpd
import pytest
import shapely

from lonboard import Map, ScatterplotLayer


def test_map_fails_with_unexpected_argument():
    points = shapely.points([1, 2], [3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)

    layer = ScatterplotLayer.from_geopandas(gdf)

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        Map(layers=[layer], unknown_keyword="foo")
