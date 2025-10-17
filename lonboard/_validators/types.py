from __future__ import annotations

from typing import Generic, TypedDict, TypeVar

from traitlets import HasTraits, TraitType

Trait = TypeVar("Trait", bound=TraitType)
Value = TypeVar("Value")
Owner = TypeVar("Owner", bound=HasTraits)


class TraitProposal(TypedDict, Generic[Trait, Value, Owner]):
    """The type of a traitlets proposal.

    The input into a `@validate` method.
    """

    trait: Trait
    value: Value
    owner: Owner
