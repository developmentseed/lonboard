from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
import traitlets as t

from lonboard._geoarrow.ops import Bbox, WeightedCentroid
from lonboard._utils import auto_downcast as _auto_downcast
from lonboard.layer._polygon import PolygonLayer
from lonboard.traits import ArrowTableTrait, H3Accessor

if TYPE_CHECKING:
    import sys

    import pandas as pd
    from arro3.core import ChunkedArray
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import H3AccessorInput, H3HexagonLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack

SEED_VALUE = 42
RNG = np.random.default_rng(SEED_VALUE)
MAX_SAMPLE_N = 10000


def default_h3_viewport(ca: ChunkedArray) -> tuple[Bbox, WeightedCentroid] | None:
    try:
        import h3.api.numpy_int as h3
    except ImportError:
        warnings.warn(
            "h3-py is not installed, cannot compute default H3 viewport.",
            ImportWarning,
        )
        return None

    sample_n = min(MAX_SAMPLE_N, len(ca))
    sample_h3 = RNG.choice(ca.to_numpy(), size=sample_n, replace=False)

    if not hasattr(h3, "cells_to_geo"):
        warnings.warn(
            "h3-py v4 is not installed, cannot compute default H3 viewport.",
            ImportWarning,
        )
        return None

    geo_dict = h3.cells_to_geo(sample_h3)

    geom_type = geo_dict.get("type")
    if geom_type == "Polygon":
        polygons = [geo_dict["coordinates"]]
    elif geom_type == "MultiPolygon":
        polygons = geo_dict["coordinates"]
    else:
        # I think it should always be Polygon/MultiPolygon
        return None

    coords = np.array(
        [pt for polygon in polygons for ring in polygon for pt in ring],
        dtype=np.float64,
    )
    centroid = coords.mean(axis=0)

    minx, miny = coords.min(axis=0)
    maxx, maxy = coords.max(axis=0)

    return (
        Bbox(minx=float(minx), miny=float(miny), maxx=float(maxx), maxy=float(maxy)),
        # Still give it the weight of the full input dataset
        WeightedCentroid(x=float(centroid[0]), y=float(centroid[1]), num_items=len(ca)),
    )


class H3HexagonLayer(PolygonLayer):
    """The `H3HexagonLayer` renders H3 hexagons.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, H3HexagonLayer

    # A GeoDataFrame with Polygon or MultiPolygon geometries
    gdf = gpd.GeoDataFrame()
    layer = H3HexagonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, H3HexagonLayer

    # Example: A FlatGeobuf file with Polygon or MultiPolygon geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = H3HexagonLayer(
        table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        get_hexagon: H3AccessorInput,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[H3HexagonLayerKwargs],
    ) -> None:
        """Create a new H3HexagonLayer.

        Args:
            table: _description_

        Keyword Args:
            get_hexagon: _description_
            kwargs: Extra args passed down as H3HexagonLayer attributes.

        """
        super().__init__(
            table=table,
            get_hexagon=get_hexagon,
            _rows_per_chunk=_rows_per_chunk,
            **kwargs,
        )

        # Assign viewport after get_hexagon has already been validated to be uint64
        # array
        default_viewport = default_h3_viewport(self.get_hexagon)
        if default_viewport is not None:
            self._bbox = default_viewport[0]
            self._weighted_centroid = default_viewport[1]

    @classmethod
    def from_pandas(
        cls,
        df: pd.DataFrame,
        *,
        get_hexagon: H3AccessorInput,
        auto_downcast: bool = True,
        **kwargs: Unpack[H3HexagonLayerKwargs],
    ) -> Self:
        """Create a new H3HexagonLayer from a pandas DataFrame.

        Args:
            df: _description_

        Keyword Args:
            get_hexagon: _description_
            auto_downcast: _description_. Defaults to True.
            kwargs: Extra args passed down as H3HexagonLayer attributes.

        Raises:
            ImportError: _description_

        Returns:
            _description_

        """
        try:
            import pyarrow as pa
        except ImportError as e:
            raise ImportError(
                "pyarrow required for converting GeoPandas to arrow.\n"
                "Run `pip install pyarrow`.",
            ) from e

        if auto_downcast:
            # Note: we don't deep copy because we don't need to clone geometries
            df = _auto_downcast(df.copy())  # type: ignore

        table = pa.Table.from_pandas(df)
        return cls(table, get_hexagon=get_hexagon, **kwargs)

    _layer_type = t.Unicode("h3-hexagon").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)

    get_hexagon = H3Accessor()
    """
    todo
    """

    high_precision = t.Bool(None, allow_none=True).tag(sync=True)
