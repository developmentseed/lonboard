from enum import Enum

import pyproj

EPSG_4326 = pyproj.CRS("epsg:4326")
OGC_84 = pyproj.CRS("ogc:84")


class EXTENSION_NAME(bytes, Enum):
    """GeoArrow extension name"""

    POINT = b"geoarrow.point"
    LINESTRING = b"geoarrow.linestring"
    POLYGON = b"geoarrow.polygon"
    MULTIPOINT = b"geoarrow.multipoint"
    MULTILINESTRING = b"geoarrow.multilinestring"
    MULTIPOLYGON = b"geoarrow.multipolygon"


class Environment(str, Enum):
    Azure = "azure"
    """Azure notebook"""

    Cocalc = "cocalc"
    Colab = "colab"
    """Colab notebook"""

    Databricks = "databricks"

    IPythonTerminal = "ipython_terminal"

    Kaggle = "kaggle"
    """Kaggle notebook"""

    Nteract = "nteract"
    Unknown = "unknown"
    Vscode = "vscode"
