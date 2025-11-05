from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import traitlets

from lonboard._environment import DEFAULT_HEIGHT
from lonboard._serialization import serialize_view_state
from lonboard.traits._base import FixedErrorTraitType
from lonboard.view_state import BaseViewState, MapViewState

if TYPE_CHECKING:
    from traitlets import HasTraits
    from traitlets.traitlets import TraitType

    from lonboard._map import Map


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


class MapHeightTrait(FixedErrorTraitType):
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
    default_value = None

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True, to_json=serialize_view_state)

    def validate(self, obj: Map, value: Any) -> None | BaseViewState:
        if value is None:
            return None

        if isinstance(value, BaseViewState):
            return value

        # Otherwise dict input
        view = obj.view
        validator = view._view_state_type if view is not None else MapViewState  # noqa: SLF001

        # The frontend currently sends back data in camelCase
        snake_case_kwargs = {_camel_to_snake(k): v for k, v in value.items()}
        return validator(**snake_case_kwargs)  # type: ignore


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
