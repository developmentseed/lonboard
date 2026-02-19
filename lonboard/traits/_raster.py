from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyproj import CRS

from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from morecantile import TileMatrixSet
    from traitlets.traitlets import HasTraits, TraitType


def serialize_crs(crs: CRS, _obj: Any) -> dict:
    """Serialize a pyproj CRS object to a dict."""
    return crs.to_json_dict()


class ProjectionTrait(FixedErrorTraitType):
    """Validation for Projection.

    This allows as input:

    - a pyproj CRS object
    - a rasterio CRS object
    - any input that pyproj.CRS.from_user_input can parse (e.g. "EPSG:4326")

    Internally, it gets serialized as PROJJSON to send to JS.
    """

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True, to_json=serialize_crs)

    def validate(self, obj: HasTraits | None, value: Any) -> Any:
        if isinstance(value, CRS):
            return value

        if value.__class__.__module__.startswith("rasterio"):
            return CRS(value)

        try:
            return CRS.from_user_input(value)
        except:  # noqa: E722
            self.error(obj, value, info="to be a valid CRS input (e.g. EPSG:4326)")


def serialize_tile_matrix_set(tms: TileMatrixSet, _obj: Any) -> dict:
    """Serialize a TileMatrixSet object to a dict."""
    return tms.model_dump(mode="json", exclude_none=True)


class TileMatrixSetTrait(FixedErrorTraitType):
    """Validation for TileMatrixSet.

    This allows as input:

    - a morecantile [TileMatrixSet][morecantile.models.TileMatrixSet] object
    - Python `dict` representing a TileMatrixSet.
    """

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True, to_json=serialize_tile_matrix_set)

    def validate(self, obj: HasTraits | None, value: Any) -> Any:
        from morecantile.models import TileMatrixSet

        if isinstance(value, TileMatrixSet):
            return value

        try:
            return TileMatrixSet(**value)
        except:  # noqa: E722
            self.error(obj, value, info="to be a valid TileMatrixSet dict")
