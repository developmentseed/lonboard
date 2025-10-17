from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from lonboard import Map
    from lonboard._validators.types import TraitProposal
    from lonboard.traits import ViewStateTrait


def validate_view_state(
    proposal: TraitProposal[ViewStateTrait, dict[str, Any], Map],
) -> dict[str, Any] | None:
    """Validate the view_state trait of a Map instance."""
    return proposal["value"]
