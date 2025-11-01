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
    """The `H3HexagonLayer` renders hexagons from the [H3](https://h3geo.org/) geospatial indexing system.

    **Example:**

    From Pandas:

    ```py
    import pandas as pd
    from lonboard import Map, H3HexagonLayer

    # A DataFrame with H3 cell identifiers
    df = pd.DataFrame({
        "h3_index": ["8928308280fffff", "8928308280bffff", ...],
        "other_attributes": [...],
    })
    layer = H3HexagonLayer.from_pandas(
        df,
        get_hexagon=df["h3_index"],
    )
    m = Map(layer)
    ```

    Or, you can pass in an Arrow table directly

    ```py
    from lonboard import Map, H3HexagonLayer

    # Example: An Arrow table with H3 identifiers as a column
    layer = H3HexagonLayer(
        table,
        get_hexagon=table["h3_index"],
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
            table: An Arrow table with properties to associate with the H3 hexagons.

        Keyword Args:
            get_hexagon: The cell identifier of each H3 hexagon.
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
            df: a Pandas DataFrame with properties to associate with H3 hexagons.

        Keyword Args:
            get_hexagon: H3 cell identifier of each H3 hexagon.
            auto_downcast: Whether to save memory on input by casting to smaller types. Defaults to True.
            kwargs: Extra args passed down as H3HexagonLayer attributes.

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
    """An Arrow table with properties to associate with the H3 hexagons.

    If you have a Pandas `DataFrame`, use
    [`from_pandas`][lonboard.H3HexagonLayer.from_pandas] instead.
    """

    get_hexagon = H3Accessor()
    """The cell identifier of each H3 hexagon.

    Accepts either an array of strings or uint64 integers representing H3 cell IDs.

    - Type: [H3Accessor][lonboard.traits.H3Accessor]
    """

    high_precision = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to render H3 hexagons in high-precision mode.

    Each hexagon in the H3 indexing system is [slightly different in shape](https://h3geo.org/docs/core-library/coordsystems). To draw a large number of hexagons efficiently, the `H3HexagonLayer` may choose to use instanced drawing by assuming that all hexagons within the current viewport have the same shape as the one at the center of the current viewport. The discrepancy is usually too small to be visible.

    There are several cases in which high-precision mode is required. In these cases, `H3HexagonLayer` may choose to switch to high-precision mode, where it trades performance for accuracy:

    * The input set contains a pentagon. There are 12 pentagons world wide at each resolution, and these cells and their immediate neighbors have significant differences in shape.
    * The input set is at a coarse resolution (res `0` through res `5`). These cells have larger differences in shape, particularly when using a Mercator projection.
    * The input set contains hexagons with different resolutions.

    Possible values:

    * `None`: The layer chooses the mode automatically. High-precision rendering is only used if an edge case is encountered in the data.
    * `True`: Always use high-precision rendering.
    * `False`: Always use instanced rendering, regardless of the characteristics of the data.

    - Type: `bool | None`, optional
    - Default: `None`
    """

    coverage = t.Float(None, allow_none=True, min=0, max=1).tag(sync=True)
    """Hexagon radius multiplier, between 0 - 1.

    When coverage = 1, hexagon is rendered with actual size, by specifying a different value (between 0 and 1) hexagon can be scaled down.

    - Type: `float`, optional
    - Default: `1`
    """
