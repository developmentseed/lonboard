"""Shared fixtures for UI tests."""

import sys
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point

from lonboard import Map
from lonboard.layer import ScatterplotLayer

# Add project root and tests/ui directories to path
project_root = Path(__file__).parent.parent.parent
tests_ui_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_ui_dir))


@pytest.fixture
def sample_geodataframe():
    """Simple GeoDataFrame for testing."""
    return gpd.GeoDataFrame(
        {"name": ["test_point"], "value": [1]},
        geometry=[Point(0, 0)],
        crs="EPSG:4326",
    )


@pytest.fixture
def sample_layer(sample_geodataframe):
    """Scatterplot layer for testing."""
    return ScatterplotLayer.from_geopandas(
        sample_geodataframe,
        get_fill_color=[255, 0, 0],
        get_radius=5000,
    )


@pytest.fixture
def sample_map(sample_layer):
    """Lonboard map for testing."""
    return Map(sample_layer)


@pytest.fixture
def sample_map_with_side_panel(sample_layer):
    """Lonboard map with side panel enabled for testing."""
    return Map(sample_layer, show_side_panel=True)
