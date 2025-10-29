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
    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        get_pentagon: A5AccessorInput,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[A5LayerKwargs],
    ) -> None:
        """Create a new H3HexagonLayer.

        Args:
            table: _description_

        Keyword Args:
            get_pentagon: _description_
            kwargs: Extra args passed down as H3HexagonLayer attributes.

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
        """Create a new H3HexagonLayer from a pandas DataFrame.

        Args:
            df: _description_

        Keyword Args:
            get_pentagon: _description_
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
        return cls(table, get_pentagon=get_pentagon, **kwargs)

    _layer_type = t.Unicode("a5").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)

    get_pentagon = A5Accessor()
    """
    todo
    """
