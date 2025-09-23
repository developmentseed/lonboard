export interface RendererProps {
  mapStyle: string;
  showTooltip: boolean;
  pickingRadius: number;
  useDevicePixels: number | boolean;
  parameters: object;
  customAttribution: string;
}