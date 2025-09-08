import React from 'react';

type IconProps = React.SVGProps<SVGSVGElement> & { size?: number };

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export const HomeIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 10.5V21h14V10.5" />
  </svg>
);

export const BookOpenIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M3 5h7a4 4 0 0 1 4 4v12H7a4 4 0 0 0-4-4V5Z" />
    <path d="M21 5h-7a4 4 0 0 0-4 4v12h7a4 4 0 0 1 4-4V5Z" />
  </svg>
);

export const ListChecksIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M11 6h10" />
    <path d="M11 12h10" />
    <path d="M11 18h10" />
    <path d="m3 6 2 2 3-3" />
    <path d="m3 12 2 2 3-3" />
    <path d="m3 18 2 2 3-3" />
  </svg>
);

export const GaugeIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M12 13V8" />
    <path d="M7.5 4.2A10 10 0 1 0 20 16" />
  </svg>
);

export const RotateCcwIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M1 4v6h6" />
    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
  </svg>
);

export const MessageSquareIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M21 15a4 4 0 0 1-4 4H7l-4 4V5a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z" />
  </svg>
);

export const PlusIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </svg>
);

export const SaveIcon: React.FC<IconProps> = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M7 21h10a2 2 0 0 0 2-2V7l-4-4H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2Z" />
    <path d="M7 3v8h10" />
  </svg>
);


