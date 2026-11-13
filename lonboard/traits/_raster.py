from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from pyproj import CRS

from lonboard.raster import AffineLevel
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


def serialize_tile_matrix_set(tms: TileMatrixSet | None, _obj: Any) -> dict | None:
    """Serialize a TileMatrixSet object to a dict."""
    if tms is None:
        return None

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


def meters_per_unit(crs: CRS) -> float:
    """Meters per horizontal CRS unit, as a TileMatrixSet's `metersPerUnit`."""
    unit_name = crs.axis_info[0].unit_name
    if unit_name == "metre":
        return 1.0
    if unit_name == "degree":
        return 2 * math.pi * crs.ellipsoid.semi_major_metre / 360.0
    if unit_name == "foot":
        return 0.3048
    if unit_name == "US survey foot":
        return 0.30480060960121924
    raise ValueError(f"Unsupported CRS unit {unit_name!r}")


def serialize_affine_levels(
    levels: list[AffineLevel] | None,
    obj: Any,
) -> list[dict] | None:
    """Serialize affine levels as deck.gl-raster `AffineTilesetLevelOptions`.

    `obj` is the widget; its `_crs` gives the meters per unit.
    """
    if levels is None:
        return None

    mpu = meters_per_unit(obj._crs)  # noqa: SLF001
    return [
        {
            "affine": [float(v) for v in tuple(level.transform)[:6]],
            "arrayWidth": level.width,
            "arrayHeight": level.height,
            "tileWidth": level.tile_width,
            "tileHeight": level.tile_height,
            "mpu": mpu,
        }
        for level in levels
    ]


class AffineLevelsTrait(FixedErrorTraitType):
    """Validation for a raster grid given as affine levels, coarsest first.

    This allows as input a non-empty list of [AffineLevel][lonboard.raster.AffineLevel].
    """

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True, to_json=serialize_affine_levels)

    def validate(self, obj: HasTraits | None, value: Any) -> Any:
        if (
            isinstance(value, list)
            and len(value) > 0
            and all(isinstance(level, AffineLevel) for level in value)
        ):
            return value

        return self.error(obj, value, info="to be a non-empty list of AffineLevel")
