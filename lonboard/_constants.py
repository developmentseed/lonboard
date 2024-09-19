from enum import Enum

import pyproj

EPSG_4326 = pyproj.CRS("epsg:4326")

# In pyodide, the pyproj PROJ data directory is much smaller, and it currently
# hard-crashes on the line `pyproj.CRS("ogc:84")`. Instead, we vendor the PROJJSON
# representation of this CRS, which works in pyodide.
OGC_84_dict = {
    "$schema": "https://proj.org/schemas/v0.7/projjson.schema.json",
    "type": "GeographicCRS",
    "name": "WGS 84 (CRS84)",
    "datum_ensemble": {
        "name": "World Geodetic System 1984 ensemble",
        "members": [
            {
                "name": "World Geodetic System 1984 (Transit)",
                "id": {"authority": "EPSG", "code": 1166},
            },
            {
                "name": "World Geodetic System 1984 (G730)",
                "id": {"authority": "EPSG", "code": 1152},
            },
            {
                "name": "World Geodetic System 1984 (G873)",
                "id": {"authority": "EPSG", "code": 1153},
            },
            {
                "name": "World Geodetic System 1984 (G1150)",
                "id": {"authority": "EPSG", "code": 1154},
            },
            {
                "name": "World Geodetic System 1984 (G1674)",
                "id": {"authority": "EPSG", "code": 1155},
            },
            {
                "name": "World Geodetic System 1984 (G1762)",
                "id": {"authority": "EPSG", "code": 1156},
            },
            {
                "name": "World Geodetic System 1984 (G2139)",
                "id": {"authority": "EPSG", "code": 1309},
            },
        ],
        "ellipsoid": {
            "name": "WGS 84",
            "semi_major_axis": 6378137,
            "inverse_flattening": 298.257223563,
        },
        "accuracy": "2.0",
        "id": {"authority": "EPSG", "code": 6326},
    },
    "coordinate_system": {
        "subtype": "ellipsoidal",
        "axis": [
            {
                "name": "Geodetic longitude",
                "abbreviation": "Lon",
                "direction": "east",
                "unit": "degree",
            },
            {
                "name": "Geodetic latitude",
                "abbreviation": "Lat",
                "direction": "north",
                "unit": "degree",
            },
        ],
    },
    "scope": "Not known.",
    "area": "World.",
    "bbox": {
        "south_latitude": -90,
        "west_longitude": -180,
        "north_latitude": 90,
        "east_longitude": 180,
    },
    "id": {"authority": "OGC", "code": "CRS84"},
}

OGC_84 = pyproj.CRS.from_json_dict(OGC_84_dict)


class EXTENSION_NAME(bytes, Enum):
    """GeoArrow extension name"""

    POINT = b"geoarrow.point"
    LINESTRING = b"geoarrow.linestring"
    POLYGON = b"geoarrow.polygon"
    MULTIPOINT = b"geoarrow.multipoint"
    MULTILINESTRING = b"geoarrow.multilinestring"
    MULTIPOLYGON = b"geoarrow.multipolygon"
    WKB = b"geoarrow.wkb"
    WKT = b"geoarrow.wkt"
    OGC_WKB = b"ogc.wkb"

    def __str__(self):
        return self.value.decode()


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
