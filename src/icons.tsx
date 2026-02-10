import type React from "react";

// SVG elements are from Collecticons
// https://collecticons.io/

interface IconProps extends React.SVGProps<SVGSVGElement> {
  fill?: string;
  filled?: boolean;
  size?: number;
  height?: number;
  width?: number;
  label?: string;
}

export const XMarkIcon: React.FC<IconProps> = ({
  fill = "currentColor",
  filled = false,
  size,
  height,
  width,
  label,
  ...props
}) => {
  const computedSize = size || width || height || 16;

  return (
    <svg
      width={computedSize}
      height={computedSize}
      viewBox="0 0 16 16"
      fill={filled ? fill : "none"}
      xmlns="http://www.w3.org/2000/svg"
      aria-label={label}
      {...props}
    >
      <polygon
        points="14.707,2.707 13.293,1.293 8,6.586 2.707,1.293 1.293,2.707 6.586,8 1.293,13.293 2.707,14.707 8,9.414 13.293,14.707 14.707,13.293 9.414,8 "
        fill={fill}
      />
    </svg>
  );
};

export const SquareIcon: React.FC<IconProps> = ({
  fill = "currentColor",
  filled = false,
  size,
  height,
  width,
  label,
  ...props
}) => {
  const computedSize = size || width || height || 24;

  return (
    <svg
      width={computedSize}
      height={computedSize}
      viewBox="0 0 24 24"
      fill={filled ? fill : "none"}
      xmlns="http://www.w3.org/2000/svg"
      aria-label={label}
      {...props}
    >
      <rect x="6" y="6" width="12" height="12" fill={fill} />
    </svg>
  );
};
