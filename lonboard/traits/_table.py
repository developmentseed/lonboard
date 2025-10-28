# ruff: noqa: SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from typing import cast as type_cast

from arro3.core import DataType, Table

from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.box_to_polygon import parse_box_encoded_table
from lonboard._serialization import TABLE_SERIALIZATION
from lonboard._utils import get_geometry_column_index
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class ArrowTableTrait(FixedErrorTraitType):
    """A trait to validate input for a geospatial Arrow-backed table.

    Allowed input includes:

    - A pyarrow [`Table`][pyarrow.Table] or containing a geometry column with [GeoArrow metadata](https://geoarrow.org/extension-types).
    - Any GeoArrow table from a library that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = None
    info_text = (
        "a table-like Arrow object, such as a pyarrow or arro3 Table or "
        "RecordBatchReader"
    )

    def __init__(
        self: TraitType,
        *args: Any,
        allowed_geometry_types: set[EXTENSION_NAME] | None = None,
        allowed_dimensions: set[int] | None = None,
        geometry_required: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(
            sync=True,
            allowed_geometry_types=allowed_geometry_types,
            allowed_dimensions=allowed_dimensions,
            geometry_required=geometry_required,
            **TABLE_SERIALIZATION,
        )

    def validate(self, obj: BaseArrowLayer, value: Any) -> Table:
        if not isinstance(value, Table):
            self.error(obj, value)

        allowed_geometry_types = self.metadata.get("allowed_geometry_types")
        allowed_geometry_types = type_cast(
            "set[bytes] | None",
            allowed_geometry_types,
        )

        allowed_dimensions = self.metadata.get("allowed_dimensions")
        allowed_dimensions = type_cast("set[int] | None", allowed_dimensions)

        geom_col_idx = get_geometry_column_index(value.schema)

        geometry_required = self.metadata.get("geometry_required")
        if geometry_required and geom_col_idx is None:
            return self.error(obj, value, info="geometry column in table")

        # No restriction on the allowed geometry types in this table
        if allowed_geometry_types:
            # If we allow polygons as input, then we also allow geoarrow.box.
            # Convert boxes to Polygons
            if EXTENSION_NAME.POLYGON in allowed_geometry_types:
                value = parse_box_encoded_table(value)

            geometry_extension_type = value.schema.field(geom_col_idx).metadata.get(
                b"ARROW:extension:name",
            )

            if (
                allowed_geometry_types
                and geometry_extension_type not in allowed_geometry_types
            ):
                allowed_types_str = ", ".join(map(str, allowed_geometry_types))
                msg = (
                    f"Expected one of {allowed_types_str} geometry types, "
                    f"got {geometry_extension_type}."
                )
                self.error(obj, value, info=msg)

        if allowed_dimensions:
            typ = value.column(geom_col_idx).type
            while DataType.is_list(typ):
                value_type = typ.value_type
                assert value_type is not None
                typ = value_type

            assert DataType.is_fixed_size_list(typ)
            if typ.list_size not in allowed_dimensions:
                msg = " or ".join(map(str, list(allowed_dimensions)))
                self.error(obj, value, info=f"{msg}-dimensional points")

        return value.rechunk(max_chunksize=obj._rows_per_chunk)
