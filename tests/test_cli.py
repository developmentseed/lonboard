from pathlib import Path

import pytest

import lonboard._compat as compat
from lonboard import PathLayer, viz
from lonboard._cli import read_pyogrio

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(not compat.HAS_SHAPELY, reason="shapely not available")
def test_viz_gpkg():
    table = read_pyogrio(fixtures_dir / "West_Devon_rail.gpkg")
    map_ = viz(table)
    assert isinstance(map_.layers[0], PathLayer)
