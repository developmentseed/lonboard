from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard._utils import auto_downcast as _auto_downcast

# Important to import from ._polygon to avoid circular imports
from lonboard.layer._polygon import PolygonLayer
from lonboard.traits import ArrowTableTrait, TextAccessor

if TYPE_CHECKING:
    import sys

    import pandas as pd
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import S2LayerKwargs, TextAccessorInput

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class S2Layer(PolygonLayer):
    """The `S2Layer` renders filled and/or stroked polygons based on the [S2](http://s2geometry.io/) geospatial indexing system.

    !!! warning
        This layer does not currently support auto-centering the map view based on the
        extent of the input.
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        get_s2_token: TextAccessorInput,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[S2LayerKwargs],
    ) -> None:
        """Create a new S2Layer.

        Args:
            table: An Arrow table with properties to associate with the S2 cells.

        Keyword Args:
            get_s2_token: The identifier of each S2 cell.
            kwargs: Extra args passed down as S2Layer attributes.

        """
        super().__init__(
            table=table,
            get_s2_token=get_s2_token,
            _rows_per_chunk=_rows_per_chunk,
            **kwargs,
        )

    @classmethod
    def from_pandas(
        cls,
        df: pd.DataFrame,
        *,
        get_s2_token: TextAccessorInput,
        auto_downcast: bool = True,
        **kwargs: Unpack[S2LayerKwargs],
    ) -> Self:
        """Create a new S2Layer from a pandas DataFrame.

        Args:
            df: a Pandas DataFrame with properties to associate with S2 cells.

        Keyword Args:
            get_s2_token: S2 cell identifier of each S2 hexagon.
            auto_downcast: Whether to save memory on input by casting to smaller types. Defaults to True.
            kwargs: Extra args passed down as S2Layer attributes.

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
        return cls(table, get_s2_token=get_s2_token, **kwargs)

    _layer_type = t.Unicode("s2").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)
    """An Arrow table with properties to associate with the S2 cells.

    If you have a Pandas `DataFrame`, use
    [`from_pandas`][lonboard.S2Layer.from_pandas] instead.
    """

    get_s2_token = TextAccessor()
    """The cell identifier of each S2 cell.

    Accepts either an array of strings or uint64 integers representing S2 cell IDs.

    - Type: [TextAccessor][lonboard.traits.TextAccessor]
    """
