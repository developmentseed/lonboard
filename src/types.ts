export type FlyToMessage = {
  type: "fly-to";
  longitude: number;
  latitude: number;
  zoom: number;
  pitch?: number | undefined;
  bearing?: number | undefined;
  transitionDuration?: number | "auto" | undefined;
  curve?: number | undefined;
  speed?: number | undefined;
  screenSpeed?: number | undefined;
};

export type Message = FlyToMessage;
