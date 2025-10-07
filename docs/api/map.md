# Map

<!-- Note: filters is set to an empty filter to include private methods.
https://mkdocstrings.github.io/python/usage/configuration/members/#filters
-->
::::: lonboard.Map
    options:
      group_by_category: false
      show_bases: false
      filters:
::::: lonboard.models.ViewState

## Projection

Lonboard supports selecting the base map projection via the `projection` trait on `Map`:

```python
from lonboard import Map

m = Map(layers=[], projection="globe")  # or "mercator" (default)
```

- When `projection="globe"`, Lonboard renders a 3D globe using MapLibre GL JS (v5+).
- The initial globe support is minimal by design: basemap + data layers only.
- Interactive features and UI controls are equivalent to the default map where applicable, but globe-specific interactions may differ.
