import type {
  FirstPersonViewProps,
  FirstPersonViewState,
  GlobeViewProps,
  GlobeViewState,
  MapViewProps,
  MapViewState,
  OrbitViewProps,
  OrbitViewState,
  OrthographicViewProps,
  OrthographicViewState,
  View,
} from "@deck.gl/core";
import {
  FirstPersonView,
  _GlobeView as GlobeView,
  MapView,
  OrbitView,
  OrthographicView,
} from "@deck.gl/core";
import type { CommonViewProps } from "@deck.gl/core/dist/views/view";
import { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../util";
import { BaseModel } from "./base";

export abstract class BaseViewModel<ViewState> extends BaseModel {
  protected x: CommonViewProps<ViewState>["x"] | null;
  protected y: CommonViewProps<ViewState>["y"] | null;
  protected width: CommonViewProps<ViewState>["width"] | null;
  protected height: CommonViewProps<ViewState>["height"] | null;
  protected padding: CommonViewProps<ViewState>["padding"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("x", "x");
    this.initRegularAttribute("y", "y");
    this.initRegularAttribute("width", "width");
    this.initRegularAttribute("height", "height");
    this.initRegularAttribute("padding", "padding");
  }

  baseViewProps<T>(): CommonViewProps<T> {
    return {
      id: this.model.model_id,
      ...(isDefined(this.x) && { x: this.x }),
      ...(isDefined(this.y) && { y: this.y }),
      ...(isDefined(this.width) && { width: this.width }),
      ...(isDefined(this.height) && { height: this.height }),
      ...(isDefined(this.padding) && { padding: this.padding }),
    };
  }

  abstract viewProps(): Omit<CommonViewProps<ViewState>, "id">;

  abstract build(): View;
}

export class FirstPersonViewModel extends BaseViewModel<FirstPersonViewState> {
  static viewType = "first-person-view";

  protected projectionMatrix: FirstPersonViewProps["projectionMatrix"] | null;
  protected fovy: FirstPersonViewProps["fovy"] | null;
  protected near: FirstPersonViewProps["near"] | null;
  protected far: FirstPersonViewProps["far"] | null;
  protected focalDistance: FirstPersonViewProps["focalDistance"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("projection_matrix", "projectionMatrix");
    this.initRegularAttribute("fovy", "fovy");
    this.initRegularAttribute("near", "near");
    this.initRegularAttribute("far", "far");
    this.initRegularAttribute("focal_distance", "focalDistance");
  }

  viewProps(): Omit<FirstPersonViewProps, "id"> {
    return {
      ...(isDefined(this.projectionMatrix) && {
        projectionMatrix: this.projectionMatrix,
      }),
      ...(isDefined(this.fovy) && { fovy: this.fovy }),
      ...(isDefined(this.near) && { near: this.near }),
      ...(isDefined(this.far) && { far: this.far }),
      ...(isDefined(this.focalDistance) && {
        focalDistance: this.focalDistance,
      }),
    };
  }

  build(): FirstPersonView {
    return new FirstPersonView({
      ...this.baseViewProps(),
      ...this.viewProps(),
    });
  }
}

export class GlobeViewModel extends BaseViewModel<GlobeViewState> {
  static viewType = "globe-view";

  protected resolution: GlobeViewProps["resolution"] | null;
  protected nearZMultiplier: GlobeViewProps["nearZMultiplier"] | null;
  protected farZMultiplier: GlobeViewProps["farZMultiplier"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("resolution", "resolution");
    this.initRegularAttribute("near_z_multiplier", "nearZMultiplier");
    this.initRegularAttribute("far_z_multiplier", "farZMultiplier");
  }

  viewProps(): Omit<GlobeViewProps, "id"> {
    return {
      ...(isDefined(this.resolution) && { resolution: this.resolution }),
      ...(isDefined(this.nearZMultiplier) && {
        nearZMultiplier: this.nearZMultiplier,
      }),
      ...(isDefined(this.farZMultiplier) && {
        farZMultiplier: this.farZMultiplier,
      }),
    };
  }

  build(): GlobeView {
    return new GlobeView({
      ...this.baseViewProps(),
      ...this.viewProps(),
    });
  }
}

export class MapViewModel extends BaseViewModel<MapViewState> {
  static viewType = "map-view";

  protected repeat: MapViewProps["repeat"] | null;
  protected nearZMultiplier: MapViewProps["nearZMultiplier"] | null;
  protected farZMultiplier: MapViewProps["farZMultiplier"] | null;
  protected projectionMatrix: MapViewProps["projectionMatrix"] | null;
  protected fovy: MapViewProps["fovy"] | null;
  protected altitude: MapViewProps["altitude"] | null;
  protected orthographic: MapViewProps["orthographic"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("repeat", "repeat");
    this.initRegularAttribute("near_z_multiplier", "nearZMultiplier");
    this.initRegularAttribute("far_z_multiplier", "farZMultiplier");
    this.initRegularAttribute("projection_matrix", "projectionMatrix");
    this.initRegularAttribute("fovy", "fovy");
    this.initRegularAttribute("altitude", "altitude");
    this.initRegularAttribute("orthographic", "orthographic");
  }

  viewProps(): Omit<MapViewProps, "id"> {
    return {
      ...(isDefined(this.repeat) && { repeat: this.repeat }),
      ...(isDefined(this.nearZMultiplier) && {
        nearZMultiplier: this.nearZMultiplier,
      }),
      ...(isDefined(this.farZMultiplier) && {
        farZMultiplier: this.farZMultiplier,
      }),
      ...(isDefined(this.projectionMatrix) && {
        projectionMatrix: this.projectionMatrix,
      }),
      ...(isDefined(this.fovy) && { fovy: this.fovy }),
      ...(isDefined(this.altitude) && { altitude: this.altitude }),
      ...(isDefined(this.orthographic) && { orthographic: this.orthographic }),
    };
  }

  build(): MapView {
    return new MapView({
      ...this.baseViewProps(),
      ...this.viewProps(),
    });
  }
}

export class OrbitViewModel extends BaseViewModel<OrbitViewState> {
  static viewType = "orbit-view";

  protected orbitAxis: OrbitViewProps["orbitAxis"] | null;
  protected projectionMatrix: OrbitViewProps["projectionMatrix"] | null;
  protected fovy: OrbitViewProps["fovy"] | null;
  protected near: OrbitViewProps["near"] | null;
  protected far: OrbitViewProps["far"] | null;
  protected orthographic: OrbitViewProps["orthographic"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("orbit_axis", "orbitAxis");
    this.initRegularAttribute("projection_matrix", "projectionMatrix");
    this.initRegularAttribute("fovy", "fovy");
    this.initRegularAttribute("near", "near");
    this.initRegularAttribute("far", "far");
    this.initRegularAttribute("orthographic", "orthographic");
  }

  viewProps(): Omit<OrbitViewProps, "id"> {
    return {
      ...(isDefined(this.orbitAxis) && { orbitAxis: this.orbitAxis }),
      ...(isDefined(this.projectionMatrix) && {
        projectionMatrix: this.projectionMatrix,
      }),
      ...(isDefined(this.fovy) && { fovy: this.fovy }),
      ...(isDefined(this.near) && { near: this.near }),
      ...(isDefined(this.far) && { far: this.far }),
      ...(isDefined(this.orthographic) && { orthographic: this.orthographic }),
    };
  }

  build(): OrbitView {
    return new OrbitView({
      ...this.baseViewProps(),
      ...this.viewProps(),
    });
  }
}

export class OrthographicViewModel extends BaseViewModel<OrthographicViewState> {
  static viewType = "orthographic-view";

  protected flipY: OrthographicViewProps["flipY"] | null;
  protected near: OrthographicViewProps["near"] | null;
  protected far: OrthographicViewProps["far"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("flip_y", "flipY");
    this.initRegularAttribute("near", "near");
    this.initRegularAttribute("far", "far");
  }

  viewProps(): Omit<OrthographicViewProps, "id"> {
    return {
      ...(isDefined(this.flipY) && { flipY: this.flipY }),
      ...(isDefined(this.near) && { near: this.near }),
      ...(isDefined(this.far) && { far: this.far }),
    };
  }

  build(): OrthographicView {
    return new OrthographicView({
      ...this.baseViewProps(),
      ...this.viewProps(),
    });
  }
}

export async function initializeView(
  model: WidgetModel,
  updateStateCallback: () => void,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
): Promise<BaseViewModel<any>> {
  const viewType = model.get("_view_type");
  switch (viewType) {
    case FirstPersonViewModel.viewType:
      return new FirstPersonViewModel(model, updateStateCallback);

    case GlobeViewModel.viewType:
      return new GlobeViewModel(model, updateStateCallback);

    case MapViewModel.viewType:
      return new MapViewModel(model, updateStateCallback);

    case OrbitViewModel.viewType:
      return new OrbitViewModel(model, updateStateCallback);

    case OrthographicViewModel.viewType:
      return new OrthographicViewModel(model, updateStateCallback);

    default:
      throw new Error(`no view supported for ${viewType}`);
  }
}
