"""Manage the display of exceptions raised by JavaScript code."""

from ipywidgets import Output


class OutputProxy:
    """A file-like proxy that routes writes to an ErrorOutput's stdout or stderr."""

    def __init__(self, output: "ErrorOutput", *, is_stderr: bool) -> None:
        self._output = output
        self._is_stderr = is_stderr

    def write(self, text: str) -> int:
        if text:
            if self._is_stderr:
                self._output.append_stderr(text)
            else:
                self._output.append_stdout(text)
        return len(text)

    def flush(self) -> None:
        pass


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

    def open_stdout(self) -> OutputProxy:
        """Return a file-like object that writes to this widget's stdout."""
        return OutputProxy(self, is_stderr=False)

    def open_stderr(self) -> OutputProxy:
        """Return a file-like object that writes to this widget's stderr."""
        return OutputProxy(self, is_stderr=True)
