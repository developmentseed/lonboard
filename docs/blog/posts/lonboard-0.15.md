---
draft: false
date: 2026-03-13
categories:
  - Release
authors:
  - kylebarron
links:
  - CHANGELOG.md#0130-2025-11-05
---

# Releasing lonboard 0.15!

Lonboard enables fast, interactive geospatial data visualization in Jupyter.

This post gives an overview of what's new in Lonboard version 0.15.

<!-- more -->

Refer to the [changelog] for all updates.

## New logo!

Lonboard has a new logo!

<img src="../../assets/lonboard-logo.png" width="400" />

This logo was designed by [Gus Becker], and continues with the pun behind Lonboard:

[Gus Becker]: https://gusbus.space/

Lonboard connects to the [deck.gl] geospatial data visualization library. A "deck" is the part of a skateboard you ride on. What's a fast, geospatial skateboard? A <em>lon</em>board.

[deck.gl]: https://deck.gl

## Geocoder control

Lonboard introduced [_map controls_][lonboard.controls] in [version 0.14](lonboard-0.14.md) to extend client-side map functionality. Lonboard is now adding support for a [`GeocoderControl`][lonboard.controls.GeocoderControl]!

This allows you to include a drop-down element on the map for easily finding locations of interest on the map.

![](../../assets/geocoder-control.jpg)

> Screenshot from [Geocoding with GeoPy](../../../../../examples/geocoder-control) example

To use, create a [`GeocoderControl`][lonboard.controls.GeocoderControl] and add it to your `Map` via the `controls` parameter.

### Using with GeoPy

The `GeocoderControl` has integration with [GeoPy](https://geopy.readthedocs.io/en/stable/), a Python library that [supports many geocoder providers](https://geopy.readthedocs.io/en/stable/#module-geopy.geocoders).

In order to use the GeoPy integration, create a geocoder of your choice in [async mode](https://geopy.readthedocs.io/en/stable/#async-mode). Then pass to [`GeocoderControl.from_geopy`][lonboard.controls.GeocoderControl.from_geopy].

```py
from geopy.adapters import AioHTTPAdapter
from geopy.geocoders import Nominatim
from lonboard import Map
from lonboard.controls import GeocoderControl

geocoder = Nominatim(user_agent="lonboard-app", adapter_factory=AioHTTPAdapter)
geocoder_control = GeocoderControl.from_geopy(geocoder)
m = Map([], controls=controls)
```

### Custom geocoder

The GeoPy integration is provided for easy use, but it's possible to customize the `GeocoderControl` to use _any_ provider you could think of. Just provide an async function that implements the [GeocoderHandler][lonboard.controls.GeocoderHandler] protocol.

```py
from lonboard import Map
from lonboard.controls import (
    GeocoderControl,
    GeocoderFeature,
    GeocoderFeatureCollection,
)

async def my_custom_geocoder(
    query: str,
) -> GeocoderFeatureCollection | GeocoderFeature | None:
    # Implement your custom geocoding logic here, e.g. by querying an API.
    # This is just a placeholder implementation that returns a fixed location.
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": (-122.4194, 37.7749),
                },
                "text": "San Francisco, CA, USA",
                "place_name": "San Francisco, CA, USA",
                "place_type": ["custom-result"],
                "center": (-122.4194, 37.7749),
            },
        ],
    }

geocoder_control = GeocoderControl(client=my_custom_geocoder)
m = Map([], controls=[geocoder_control])
```

### Limitations

This integration works by message passing between the browser and Python, using the Jupyter communication mechanism.

When you perform a search in the geocoder UI element on the map, that fires off a request to Python, which routes the query string to the Python async callback. When that callback returns, Lonboard sends the result back to the browser, which displays the available results from the geocoder service.

So all queries are proxied _through Python_. This makes the maintenance of this feature much simpler, because Lonboard doesn't have to connect to any geocoder providers itself. It also means that the end user has full control over which geocoder API they use, and any relevant API keys never leave the Python environment.

The one downside here, is that, for now, if you export a map with a geocoder control to a static HTML file using the [HTML export functionality][lonboard.Map.to_html], the geocoder will no longer function, as there's no running Python service for it to connect to.

## All updates

Refer to the [changelog] for all updates.

[changelog]: ../../CHANGELOG.md/#0150-2026-03-13
