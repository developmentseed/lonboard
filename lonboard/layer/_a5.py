from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard._utils import auto_downcast as _auto_downcast

# Important to import from ._polygon to avoid circular imports
from lonboard.layer._polygon import PolygonLayer
from lonboard.traits import A5Accessor, ArrowTableTrait

if TYPE_CHECKING:
    import sys

    import pandas as pd
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import A5AccessorInput, A5LayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class A5Layer(PolygonLayer):
    """The `A5Layer` renders filled and/or stroked polygons based on the [A5](https://a5geo.org) geospatial indexing system.

    !!! warning
        This layer does not currently support auto-centering the map view based on the
        extent of the input.
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        get_pentagon: A5AccessorInput,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[A5LayerKwargs],
    ) -> None:
        """Create a new A5Layer.

        Args:
            table: An Arrow table with properties to associate with the A5 pentagons.

        Keyword Args:
            get_pentagon: The cell identifier of each A5 pentagon.
            kwargs: Extra args passed down as A5Layer attributes.

        """
        super().__init__(
            table=table,
            get_pentagon=get_pentagon,
            _rows_per_chunk=_rows_per_chunk,
            **kwargs,
        )

    @classmethod
    def from_pandas(
        cls,
        df: pd.DataFrame,
        *,
        get_pentagon: A5AccessorInput,
        auto_downcast: bool = True,
        **kwargs: Unpack[A5LayerKwargs],
    ) -> Self:
        """Create a new A5Layer from a pandas DataFrame.

        Args:
            df: a Pandas DataFrame with properties to associate with A5 pentagons.

        Keyword Args:
            get_pentagon: A5 cell identifier of each A5 hexagon.
            auto_downcast: Whether to save memory on input by casting to smaller types. Defaults to True.
            kwargs: Extra args passed down as A5Layer attributes.

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
        return cls(table, get_pentagon=get_pentagon, **kwargs)

    _layer_type = t.Unicode("a5").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)
    """An Arrow table with properties to associate with the A5 pentagons.

    If you have a Pandas `DataFrame`, use
    [`from_pandas`][lonboard.A5Layer.from_pandas] instead.
    """

    get_pentagon = A5Accessor()
    """The cell identifier of each A5 pentagon.

    Accepts either an array of strings or uint64 integers representing A5 cell IDs.

    - Type: [A5Accessor][lonboard.traits.A5Accessor]
    """
