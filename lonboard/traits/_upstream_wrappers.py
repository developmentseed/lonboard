from typing import Any as TypingAny

import traitlets.traitlets as t


class Any(t.Any):
    """A subclass of [Any][traitlets.Any] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Bool(t.Bool):
    """A subclass of [Bool][traitlets.Bool] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Enum(t.Enum):
    """A subclass of [Enum][traitlets.Enum] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Float(t.Float):
    """A subclass of [Float][traitlets.Float] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Int(t.Int):
    """A subclass of [Int][traitlets.Int] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class List(t.List):
    """A subclass of [List][traitlets.List] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Tuple(t.Tuple):
    """A subclass of [Tuple][traitlets.Tuple] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Unicode(t.Unicode):
    """A subclass of [Unicode][traitlets.Unicode] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)


class Union(t.Union):
    """A subclass of [Union][traitlets.Union] tagged with `sync=True`."""

    def __init__(self, *args: TypingAny, **kwargs: TypingAny) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True)
