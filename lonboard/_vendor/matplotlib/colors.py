# Vendored from matplotlib at
# https://github.com/matplotlib/matplotlib/blob/6166e5b990b32c7f46847782c0354653e483560d/lib/matplotlib/colors.py#L75

from __future__ import annotations

import re
from numbers import Real
from typing import Tuple

import numpy as np

from ._color_data import BASE_COLORS, CSS4_COLORS, TABLEAU_COLORS, XKCD_COLORS


class _ColorMapping(dict):
    def __init__(self, mapping):
        super().__init__(mapping)
        self.cache = {}

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.cache.clear()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.cache.clear()


_colors_full_map = {}
# Set by reverse priority order.
_colors_full_map.update(XKCD_COLORS)
_colors_full_map.update(
    {k.replace("grey", "gray"): v for k, v in XKCD_COLORS.items() if "grey" in k}
)
_colors_full_map.update(CSS4_COLORS)
_colors_full_map.update(TABLEAU_COLORS)
_colors_full_map.update(
    {k.replace("gray", "grey"): v for k, v in TABLEAU_COLORS.items() if "gray" in k}
)
_colors_full_map.update(BASE_COLORS)
_colors_full_map = _ColorMapping(_colors_full_map)


def _to_rgba_no_colorcycle(c, alpha: int | float | None = None) -> Tuple[float, ...]:
    """
    Convert *c* to an RGBA color, with no support for color-cycle syntax.

    If *alpha* is given, force the alpha value of the returned RGBA tuple
    to *alpha*. Otherwise, the alpha value from *c* is used, if it has alpha
    information, or defaults to 1.

    *alpha* is ignored for the color value ``"none"`` (case-insensitive),
    which always maps to ``(0, 0, 0, 0)``.
    """
    if alpha is not None and not 0 <= alpha <= 1:
        raise ValueError("'alpha' must be between 0 and 1, inclusive")
    orig_c = c
    if c is np.ma.masked:
        return (0.0, 0.0, 0.0, 0.0)
    if isinstance(c, str):
        if c.lower() == "none":
            return (0.0, 0.0, 0.0, 0.0)
        # Named color.
        try:
            # This may turn c into a non-string, so we check again below.
            c = _colors_full_map[c]
        except KeyError:
            if len(orig_c) != 1:
                try:
                    c = _colors_full_map[c.lower()]
                except KeyError:
                    pass
    if isinstance(c, str):
        # hex color in #rrggbb format.
        match = re.match(r"\A#[a-fA-F0-9]{6}\Z", c)
        if match:
            return tuple(int(n, 16) / 255 for n in [c[1:3], c[3:5], c[5:7]]) + (
                alpha if alpha is not None else 1.0,
            )
        # hex color in #rgb format, shorthand for #rrggbb.
        match = re.match(r"\A#[a-fA-F0-9]{3}\Z", c)
        if match:
            return tuple(int(n, 16) / 255 for n in [c[1] * 2, c[2] * 2, c[3] * 2]) + (
                alpha if alpha is not None else 1.0,
            )
        # hex color with alpha in #rrggbbaa format.
        match = re.match(r"\A#[a-fA-F0-9]{8}\Z", c)
        if match:
            color = [int(n, 16) / 255 for n in [c[1:3], c[3:5], c[5:7], c[7:9]]]
            if alpha is not None:
                color[-1] = alpha
            return tuple(color)
        # hex color with alpha in #rgba format, shorthand for #rrggbbaa.
        match = re.match(r"\A#[a-fA-F0-9]{4}\Z", c)
        if match:
            color = [int(n, 16) / 255 for n in [c[1] * 2, c[2] * 2, c[3] * 2, c[4] * 2]]
            if alpha is not None:
                color[-1] = alpha
            return tuple(color)
        # string gray.
        try:
            c = float(c)
        except ValueError:
            pass
        else:
            if not (0 <= c <= 1):
                raise ValueError(
                    f"Invalid string grayscale value {orig_c!r}. "
                    f"Value must be within 0-1 range"
                )
            return c, c, c, alpha if alpha is not None else 1.0
        raise ValueError(f"Invalid RGBA argument: {orig_c!r}")
    # turn 2-D array into 1-D array
    if isinstance(c, np.ndarray):
        if c.ndim == 2 and c.shape[0] == 1:
            c = c.reshape(-1)
    # tuple color.
    if not np.iterable(c):
        raise ValueError(f"Invalid RGBA argument: {orig_c!r}")
    if len(c) not in [3, 4]:  # type: ignore
        raise ValueError("RGBA sequence should have length 3 or 4")
    if not all(isinstance(x, Real) for x in c):
        # Checks that don't work: `map(float, ...)`, `np.array(..., float)` and
        # `np.array(...).astype(float)` would all convert "0.5" to 0.5.
        raise ValueError(f"Invalid RGBA argument: {orig_c!r}")
    # Return a tuple to prevent the cached value from being modified.
    c = tuple(map(float, c))
    if len(c) == 3 and alpha is None:
        alpha = 1
    if alpha is not None:
        c = c[:3] + (alpha,)
    if any(elem < 0 or elem > 1 for elem in c):
        raise ValueError("RGBA values should be within 0-1 range")
    return c
