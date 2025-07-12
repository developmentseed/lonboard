import json

from arro3.core import Field
from pyproj import CRS

from lonboard._geoarrow.crs import get_field_crs
from lonboard._geoarrow.extension_types import CoordinateDimension, coord_storage_type


def parse_geoarrow_projjson_crs():
    expected = CRS.from_epsg(4326)
    meta = {
        "crs": expected.to_json_dict(),
        "crs_type": "projjson",
    }
    geoarrow_meta = {
        "ARROW:extension:name": "geoarrow.point",
        "ARROW:extension:metadata": json.dumps(meta),
    }
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) == expected


def parse_geoarrow_wkt_crs():
    expected = CRS.from_epsg(4326)
    meta = {
        "crs": expected.to_wkt(version="WKT2:2019"),
        "crs_type": "wkt2:2019",
    }
    geoarrow_meta = {
        "ARROW:extension:name": "geoarrow.point",
        "ARROW:extension:metadata": json.dumps(meta),
    }
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) == expected


def parse_geoarrow_authority_crs():
    expected = CRS.from_epsg(4326)
    meta = {
        "crs": ":".join(expected.to_authority()),
        "crs_type": "authority_code",
    }
    geoarrow_meta = {
        "ARROW:extension:name": "geoarrow.point",
        "ARROW:extension:metadata": json.dumps(meta),
    }
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) == expected


def parse_geoarrow_srid_crs():
    expected = CRS.from_epsg(4326)
    meta = {
        "crs": str(expected.to_epsg()),
        "crs_type": "srid",
    }
    geoarrow_meta = {
        "ARROW:extension:name": "geoarrow.point",
        "ARROW:extension:metadata": json.dumps(meta),
    }
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) == expected


def parse_geoarrow_unknown_crs_type():
    expected = CRS.from_epsg(4326)
    meta = {
        "crs": expected.to_wkt(),
    }
    geoarrow_meta = {
        "ARROW:extension:name": "geoarrow.point",
        "ARROW:extension:metadata": json.dumps(meta),
    }
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) == expected


def parse_geoarrow_no_crs():
    geoarrow_meta = {
        "ARROW:extension:name": "geoarrow.point",
        "ARROW:extension:metadata": json.dumps({}),
    }
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) is None

    geoarrow_meta = {"ARROW:extension:name": "geoarrow.point"}
    field = Field(
        name="geometry",
        type=coord_storage_type(interleaved=True, dims=CoordinateDimension.XY),
        nullable=True,
        metadata=geoarrow_meta,
    )
    assert get_field_crs(field) is None
