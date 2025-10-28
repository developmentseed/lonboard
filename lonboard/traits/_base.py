# ruff: noqa: SLF001, UP031

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

import traitlets
from traitlets import TraitError, Undefined
from traitlets.utils.descriptions import class_of, describe

if TYPE_CHECKING:
    from traitlets import HasTraits
    from traitlets.utils.sentinel import Sentinel

DEFAULT_INITIAL_VIEW_STATE = {
    "latitude": 10,
    "longitude": 0,
    "zoom": 0.5,
    "bearing": 0,
    "pitch": 0,
}


class FixedErrorTraitType(traitlets.TraitType):
    """A custom subclass of traitlets.TraitType.

    This is because its `error` method ignores the `info` passed in. See
    https://github.com/developmentseed/lonboard/issues/71 and
    https://github.com/ipython/traitlets/pull/884.
    """

    def error(
        self,
        obj: HasTraits | None,
        value: Any,
        error: Exception | None = None,
        info: str | None = None,
    ) -> NoReturn:
        """Raise a TraitError.

        Parameters
        ----------
        obj : HasTraits or None
            The instance which owns the trait. If not
            object is given, then an object agnostic
            error will be raised.
        value : any
            The value that caused the error.
        error : Exception (default: None)
            An error that was raised by a child trait.
            The arguments of this exception should be
            of the form ``(value, info, *traits)``.
            Where the ``value`` and ``info`` are the
            problem value, and string describing the
            expected value. The ``traits`` are a series
            of :class:`TraitType` instances that are
            "children" of this one (the first being
            the deepest).
        info : str (default: None)
            A description of the expected value. By
            default this is infered from this trait's
            ``info`` method.

        """
        if error is not None:
            # handle nested error
            error.args += (self,)
            if self.name is not None:
                # this is the root trait that must format the final message
                chain = " of ".join(describe("a", t) for t in error.args[2:])
                if obj is not None:
                    error.args = (
                        "The '{}' trait of {} instance contains {} which "
                        "expected {}, not {}.".format(
                            self.name,
                            describe("an", obj),
                            chain,
                            error.args[1],
                            describe("the", error.args[0]),
                        ),
                    )
                else:
                    error.args = (
                        "The '{}' trait contains {} which expected {}, not {}.".format(
                            self.name,
                            chain,
                            error.args[1],
                            describe("the", error.args[0]),
                        ),
                    )
            raise error
        # this trait caused an error
        if self.name is None:
            # this is not the root trait
            raise TraitError(value, info or self.info(), self)
        # this is the root trait
        if obj is not None:
            e = "The '{}' trait of {} instance expected {}, not {}.".format(
                self.name,
                class_of(obj),
                # CHANGED:
                # Use info if provided
                info or self.info(),
                describe("the", value),
            )
        else:
            e = "The '{}' trait expected {}, not {}.".format(
                self.name,
                # CHANGED:
                # Use info if provided
                info or self.info(),
                describe("the", value),
            )
        raise TraitError(e)


T = TypeVar("T")


# TODO: switch to
# class VariableLengthTuple(traitlets.Container[tuple[T, ...]])
# When we can upgrade to traitlets 5.10 (depends on Colab upgrading)
class VariableLengthTuple(traitlets.Container):
    """An instance of a Python tuple with variable numbers of elements of the same type."""

    klass = list  # type:ignore[assignment]
    _cast_types: Any = (tuple,)

    def __init__(
        self,
        trait: T | Sentinel = None,
        default_value: tuple[T, ...] | Sentinel | None = Undefined,
        minlen: int = 0,
        maxlen: int = sys.maxsize,
        **kwargs: Any,
    ) -> None:
        """Create a tuple trait type.

        The default value is created by doing ``list(default_value)``,
        which creates a copy of the ``default_value``.

        ``trait`` can be specified, which restricts the type of elements
        in the container to that TraitType.

        If only one arg is given and it is not a Trait, it is taken as
        ``default_value``:

        ``c = List([1, 2, 3])``

        Parameters
        ----------
        trait : TraitType [ optional ]
            the type for restricting the contents of the Container.
            If unspecified, types are not checked.
        default_value : SequenceType [ optional ]
            The default value for the Trait.  Must be list/tuple/set, and
            will be cast to the container type.
        minlen : Int [ default 0 ]
            The minimum length of the input list
        maxlen : Int [ default sys.maxsize ]
            The maximum length of the input list
        kwargs:
            passed on to traitlets.Container.

        """
        self._maxlen = maxlen
        self._minlen = minlen
        super().__init__(trait=trait, default_value=default_value, **kwargs)

    def length_error(self, obj: Any, value: Any) -> None:
        e = "The '%s' trait of %s instance must be of length %i <= L <= %i" % (
            self.name,
            class_of(obj),
            self._minlen,
            self._maxlen,
        )
        e += f", but a value of {value} was specified."
        raise TraitError(e)

    def validate_elements(self, obj: Any, value: Any) -> Any:
        length = len(value)
        if length < self._minlen or length > self._maxlen:
            self.length_error(obj, value)

        trait = self._trait

        validated = []
        for v in value:
            try:
                v = trait._validate(obj, v)  # noqa: PLW2901
            except TraitError as error:  # noqa: PERF203
                self.error(obj, v, error)
            else:
                validated.append(v)

        return tuple(validated)
