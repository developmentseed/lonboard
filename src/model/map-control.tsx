import { ControlPosition } from "@deck.gl/mapbox/dist/types";
import {
  CompassWidget,
  FullscreenWidget,
  _ScaleWidget as ScaleWidget,
  ZoomWidget,
} from "@deck.gl/react";
import {
  _GoogleGeocoder as GoogleGeocoder,
  _MapboxGeocoder as MapboxGeocoder,
  _OpenCageGeocoder as OpenCageGeocoder,
  _CoordinatesGeocoder as CoordinatesGeocoder,
} from "@deck.gl/widgets";
import type { Geocoder } from "@deck.gl/widgets";
import type { WidgetModel } from "@jupyter-widgets/base";
import MaplibreGeocoder, {
  CarmenGeojsonFeature,
  MaplibreGeocoderApi,
  MaplibreGeocoderOptions,
} from "@maplibre/maplibre-gl-geocoder";
import React from "react";
import {
  FullscreenControl,
  NavigationControl,
  ScaleControl,
  useControl,
} from "react-map-gl/maplibre";

import { isDefined } from "../util";
import { BaseModel } from "./base";

export abstract class BaseMapControlModel extends BaseModel {
  static controlType: string;

  protected position?:
    | "top-left"
    | "top-right"
    | "bottom-left"
    | "bottom-right";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("position", "position");
  }

  baseDeckProps() {
    return {
      ...(isDefined(this.position) ? { placement: this.position } : {}),
    };
  }

  baseMaplibreProps() {
    return {
      ...(isDefined(this.position) ? { position: this.position } : {}),
    };
  }

  abstract renderDeck(): React.JSX.Element | null;
  abstract renderMaplibre(): React.JSX.Element | null;
}

export class FullscreenControlModel extends BaseMapControlModel {
  static controlType = "fullscreen";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
  }

  renderDeck() {
    const { placement, ...otherProps } = this.baseDeckProps();
    const props = { placement: placement || "top-right", ...otherProps };
    console.log(placement);
    return <div>{<FullscreenWidget {...props} />}</div>;
  }

  renderMaplibre() {
    return <div>{<FullscreenControl {...this.baseMaplibreProps()} />}</div>;
  }
}

export class NavigationControlModel extends BaseMapControlModel {
  static controlType = "navigation";

  protected showCompass?: boolean;
  protected showZoom?: boolean;
  protected visualizePitch?: boolean;
  protected visualizeRoll?: boolean;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("show_compass", "showCompass");
    this.initRegularAttribute("show_zoom", "showZoom");
    this.initRegularAttribute("visualize_pitch", "visualizePitch");
    this.initRegularAttribute("visualize_roll", "visualizeRoll");
  }

  renderDeck() {
    return (
      <div>
        {this.showZoom && <ZoomWidget {...this.baseDeckProps()} />}
        {this.showCompass && <CompassWidget {...this.baseDeckProps()} />}
      </div>
    );
  }

  renderMaplibre() {
    const props = {
      ...this.baseMaplibreProps(),
      ...(isDefined(this.showCompass) && { showCompass: this.showCompass }),
      ...(isDefined(this.showZoom) && { showZoom: this.showZoom }),
      ...(isDefined(this.visualizePitch) && {
        visualizePitch: this.visualizePitch,
      }),
      ...(isDefined(this.visualizeRoll) && {
        visualizeRoll: this.visualizeRoll,
      }),
    };
    return <NavigationControl {...props} />;
  }
}

export class ScaleControlModel extends BaseMapControlModel {
  static controlType = "scale";

  protected maxWidth?: number;
  protected unit?: "imperial" | "metric" | "nautical";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("max_width", "maxWidth");
    this.initRegularAttribute("unit", "unit");
  }

  renderDeck() {
    return <ScaleWidget {...this.baseDeckProps()} />;
  }

  renderMaplibre() {
    const props = {
      ...this.baseMaplibreProps(),
      ...(isDefined(this.maxWidth) && { maxWidth: this.maxWidth }),
      ...(isDefined(this.unit) && { unit: this.unit }),
    };
    return <div>{<ScaleControl {...props} />}</div>;
  }
}

function MaplibreGeocoderControl(
  api: MaplibreGeocoderApi,
  props: MaplibreGeocoderOptions,
  opts?: ControlOptions,
) {
  useControl(() => new MaplibreGeocoder(api, props), opts);

  return null;
}

export class GeocoderControlModel extends BaseMapControlModel {
  static controlType = "geocoder";

  protected provider?: string;
  protected apiKey?: string;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
  }

  providerInstance(): Geocoder | null {
    switch (this.provider) {
      case "google":
        return GoogleGeocoder;
      case "mapbox":
        return MapboxGeocoder;
      case "opencage":
        return OpenCageGeocoder;
      case "coordinates":
        return CoordinatesGeocoder;
      default:
        return null;
    }
  }

  maplibreApi(): MaplibreGeocoderApi | null {
    const provider = this.providerInstance();
    if (provider instanceof MaplibreGeocoder) {
      return {
        forwardGeocode: async (config) => {
          const queryString = config.query?.toString() || "";
          const result = await provider.geocode(queryString, this.apiKey || "");
          const feature: CarmenGeojsonFeature = {
            id: "",
            text: queryString,
            place_name: "",
            place_type: [],
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [result?.longitude || 0, result?.longitude || 0],
            },
            properties: {},
          };
          return {
            type: "FeatureCollection",
            features: [feature],
          };
        },
      };
    }
    return null;
  }

  renderDeck() {
    return null;
  }

  renderMaplibre() {
    const api = this.maplibreApi();
    if (api) {
      return (
        <MaplibreGeocoderControl
          api={api}
          props={{ accessToken: this.apiKey || "" }}
          opts={this.baseMaplibreProps()}
        />
      );
    }
    return null;
  }
}

type ControlOptions = {
  position?: ControlPosition;
};

export async function initializeControl(
  model: WidgetModel,
  updateStateCallback: () => void,
): Promise<BaseMapControlModel> {
  const controlType = model.get("_control_type");
  let controlModel: BaseMapControlModel;
  switch (controlType) {
    case FullscreenControlModel.controlType:
      controlModel = new FullscreenControlModel(model, updateStateCallback);
      break;

    case NavigationControlModel.controlType:
      controlModel = new NavigationControlModel(model, updateStateCallback);
      break;

    case ScaleControlModel.controlType:
      controlModel = new ScaleControlModel(model, updateStateCallback);
      break;

    default:
      throw new Error(`no control supported for ${controlType}`);
  }

  return controlModel;
}
