# Layer Extensions

Layer extensions are bonus features that you can optionally add to the core deck.gl layers.

Layer extensions are in an experimental state. Some things are known to not yet work:

- Modifying the extensions on a layer by mutating its `extensions` list via `append` or `pop`. It should work, however, by creating a new list and assigning `layer.extensions = new_extensions_list`.

If you encounter issues, please [create an issue](https://github.com/developmentseed/lonboard/issues/new) with reproducible steps.
