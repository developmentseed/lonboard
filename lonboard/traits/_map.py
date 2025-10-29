from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import traitlets

from lonboard._environment import DEFAULT_HEIGHT
from lonboard.models import BaseViewState, _serialize_view_state
from lonboard.traits._base import FixedErrorTraitType

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
    default_value = None

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tag(sync=True, to_json=_serialize_view_state)

    def validate(self, obj: Map, value: Any) -> None | BaseViewState:
        view = obj.views
        if view is None:
            return None
        else:  # noqa: RET505 (typing issue)
            validator = view._view_state_type  # noqa: SLF001
            return validator(value)  # type: ignore
        #     view

        # reveal_type(view)
        # view

        # if isinstance(view, MapView) or view is None:
        #     if value is None:
        #         return MapViewState()

        #     if isinstance(value, MapViewState):
        #         return value

        #     if isinstance(value, dict):
        #         return MapViewState(**value)

        # elif isinstance(view, GlobeView):
        #     if isinstance(value, GlobeViewState):
        #         return value

        #     if isinstance(value, dict):
        #         return GlobeViewState(**value)

        # elif isinstance(view, FirstPersonView):
        #     if isinstance(value, FirstPersonViewState):
        #         return value

        #     if isinstance(value, dict):
        #         return FirstPersonViewState(**value)

        # elif isinstance(view, OrbitView):
        #     if isinstance(value, OrbitViewState):
        #         return value

        #     if isinstance(value, dict):
        #         return OrbitViewState(**value)

        # elif isinstance(view, OrthographicView):
        #     if isinstance(value, OrthographicViewState):
        #         return value

        #     if isinstance(value, dict):
        #         return OrthographicViewState(**value)

        # if value is None:
        #     return None

        # self.error(obj, value)
        # assert False
