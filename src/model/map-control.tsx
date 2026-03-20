import {
  CompassWidget,
  FullscreenWidget,
  _ScaleWidget as ScaleWidget,
  ZoomWidget,
} from "@deck.gl/react";
import type { Geocoder } from "@deck.gl/widgets";
import type { WidgetModel } from "@jupyter-widgets/base";
import type {
  CarmenGeojsonFeature,
  MaplibreGeocoderApi,
  MaplibreGeocoderFeatureResults,
  MaplibreGeocoderOptions,
} from "@maplibre/maplibre-gl-geocoder";
import MaplibreGeocoder from "@maplibre/maplibre-gl-geocoder";
import type React from "react";
import type { ControlPosition } from "react-map-gl/maplibre";
import {
  FullscreenControl,
  NavigationControl,
  ScaleControl,
  useControl,
} from "react-map-gl/maplibre";

import { isDefined } from "../util";
import { BaseModel } from "./base";
import { invoke } from "./dispatch";

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

const GEOCODER_MSG_KIND = "geocoder-query";

type ControlOptions = {
  position?: ControlPosition;
};

function MaplibreGeocoderControl({
  api,
  props = {},
  opts = {},
}: {
  api: MaplibreGeocoderApi;
  props?: MaplibreGeocoderOptions;
  opts?: ControlOptions;
}) {
  useControl(() => new MaplibreGeocoder(api, props), opts);

  return null;
}

export class GeocoderControlModel extends BaseMapControlModel {
  static controlType = "geocoder";

  async invokePythonGeocode(
    query: string,
  ): Promise<MaplibreGeocoderFeatureResults | null> {
    const [message] = await invoke<
      MaplibreGeocoderFeatureResults | CarmenGeojsonFeature | null
    >(
      this.model,
      {
        query,
      },
      GEOCODER_MSG_KIND,
      { timeout: 10000 },
    );

    if (!message) {
      return null;
    }

    if ("features" in message) {
      return message;
    }

    return {
      type: "FeatureCollection",
      features: [message],
    };
  }

  emptyFeature(): CarmenGeojsonFeature {
    return {
      id: "",
      text: "",
      place_name: "",
      place_type: [],
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [0, 0],
      },
      properties: {},
    };
  }

  emptyFeatureCollection(): MaplibreGeocoderFeatureResults {
    return {
      type: "FeatureCollection",
      features: [this.emptyFeature()],
    };
  }

  deckGeocoder(): Geocoder {
    return {
      name: "python-geocoder",
      requiresApiKey: false,
      geocode: async (address: string) => {
        const features = await this.invokePythonGeocode(address);

        if (!features) {
          return null;
        }

        const feature = features.features[0];

        if (!feature) {
          return null;
        }

        const { center } = feature;
        if (!center || center.length < 2) {
          return null;
        }
        return {
          longitude: center[0],
          latitude: center[1],
        };
      },
    };
  }

  maplibreApi(): MaplibreGeocoderApi | null {
    return {
      forwardGeocode: async (config) => {
        const queryString = config.query?.toString();
        const features = queryString
          ? ((await this.invokePythonGeocode(queryString)) ??
            this.emptyFeatureCollection())
          : this.emptyFeatureCollection();
        return features;
      },
    };
  }

  // deck.gl's GeocoderWidget appeared to not work well in testing
  renderDeck() {
    return null;

    // const { placement, ...otherProps } = this.baseDeckProps();
    // console.log(placement);
    // return (
    //   <div>
    //     {
    //       <GeocoderWidget
    //         placement={placement || "top-left"}
    //         label="Geocoder"
    //         geocoder="custom"
    //         customGeocoder={this.deckGeocoder()}
    //         {...otherProps}
    //       />
    //     }
    //   </div>
    // );
  }

  renderMaplibre() {
    const api = this.maplibreApi();
    if (api) {
      return (
        <MaplibreGeocoderControl api={api} opts={this.baseMaplibreProps()} />
      );
    }
    return null;
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

    case GeocoderControlModel.controlType:
      controlModel = new GeocoderControlModel(model, updateStateCallback);
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
