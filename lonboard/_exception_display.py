"""Manage the display of exceptions raised by JavaScript code."""

from ipywidgets import Output


class ErrorOutput(Output):
    """An Output widget that captures and displays error messages."""

    name: str | None

    def __init__(self, *, name: str | None = None) -> None:
        self.name = name

        super().__init__()

    def _prepare_text(self, text: str) -> str:
        if self.name is not None:
            return f"[{self.name}] {text}\n"

        return text + "\n"

    def append_stdout(self, text: str) -> None:
        return super().append_stdout(self._prepare_text(text))

    def append_stderr(self, text: str) -> None:
        return super().append_stderr(self._prepare_text(text))
