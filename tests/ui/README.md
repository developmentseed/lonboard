# UI Testing with pytest-ipywidgets

Browser-based testing for Lonboard's UI interaction workflows.

## Install playwright browser

```bash
uv run playwright install chromium
```

## Run UI tests

```bash
# Run UI tests
uv run pytest tests/ui/

# Run with headed browser for debugging
uv run pytest tests/ui/ --headed -v -s
```
