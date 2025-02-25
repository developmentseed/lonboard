from packaging.version import Version

try:
    import pandas as pd

    if not Version(pd.__version__) >= Version("2.0.0"):
        raise ValueError("Pandas v2 or later is required.")

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


try:
    import geopandas as gpd

    if not Version(gpd.__version__) >= Version("0.13"):
        raise ValueError("GeoPandas v0.13 or later is required.")

    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    import shapely

    if not Version(shapely.__version__) >= Version("2.0.0"):
        raise ValueError("Shapely v2 or later is required.")

    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False
