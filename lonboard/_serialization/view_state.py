from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lonboard.models import ViewState


def serialize_view_state(data: ViewState | None, obj: Any) -> None | dict[str, Any]:  # noqa: ARG001
    """Serialize ViewState for the frontend."""
    if data is None:
        return None

    return data._asdict()
