from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import traitlets

from lonboard._environment import DEFAULT_HEIGHT
from lonboard._serialization import serialize_view_state
from lonboard.models import ViewState
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets import HasTraits
    from traitlets.traitlets import TraitType

    from lonboard._map import Map

DEFAULT_INITIAL_VIEW_STATE = {
    "latitude": 10,
    "longitude": 0,
    "zoom": 0.5,
    "bearing": 0,
    "pitch": 0,
}


class BasemapUrl(traitlets.Unicode):
    """Validation for basemap url."""

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

    def validate(self, obj: HasTraits | None, value: Any) -> Any:
        value = super().validate(obj, value)

        try:
            parsed = urlparse(value)
        except:  # noqa: E722
            self.error(obj, value, info="to be a URL")

        if not parsed.scheme.startswith("http"):
            self.error(obj, value, info="to be a HTTP(s) URL")

        return value


class HeightTrait(FixedErrorTraitType):
    """Trait to validate map height input."""

    allow_none = True
    default_value = DEFAULT_HEIGHT

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True)

    def validate(self, obj: Any, value: Any) -> str:
        if isinstance(value, int):
            return f"{value}px"

        if isinstance(value, str):
            return value

        self.error(obj, value)
        assert False


class ViewStateTrait(FixedErrorTraitType):
    """Trait to validate view state input."""

    allow_none = True
    default_value = DEFAULT_INITIAL_VIEW_STATE

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True, to_json=serialize_view_state)

    def validate(self, obj: Map, value: Any) -> None | ViewState:
        if value is None:
            return None

        if isinstance(value, ViewState):
            return value

        if isinstance(value, dict):
            value = {**DEFAULT_INITIAL_VIEW_STATE, **value}
            return ViewState(**value)

        self.error(obj, value)
        assert False
