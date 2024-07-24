import React from "react";

interface SquareIconProps extends React.SVGProps<SVGSVGElement> {
  fill?: string;
  filled?: boolean;
  size?: number;
  height?: number;
  width?: number;
  label?: string;
}

export const SquareIcon: React.FC<SquareIconProps> = ({
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
