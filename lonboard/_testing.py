"""Utilities for exporting data to test in the JS @geoarrow/deck.gl-layers package
"""
import pyarrow.feather as feather

from lonboard._layer import BaseLayer


def export_widget(widget: BaseLayer, path: str):
    feather.write_feather(widget.table, path, compression="uncompressed")
