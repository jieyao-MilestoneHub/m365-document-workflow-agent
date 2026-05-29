/**
 * Minimal Fluent-style line icons (inline SVG — no external deps, CSP-safe, no <img>).
 * 20px grid, 1.6 stroke, rounded joins.
 */
type IconProps = { className?: string };

function svg(path: React.ReactNode, extra?: { fill?: boolean }) {
  return function Icon({ className }: IconProps) {
    return (
      <svg
        viewBox="0 0 20 20"
        className={className ?? "h-5 w-5"}
        fill={extra?.fill ? "currentColor" : "none"}
        stroke={extra?.fill ? "none" : "currentColor"}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        {path}
      </svg>
    );
  };
}

export const InboxIcon = svg(
  <>
    <path d="M3 11.5 5 4.5a1.5 1.5 0 0 1 1.45-1.1h7.1A1.5 1.5 0 0 1 15 4.5l2 7" />
    <path d="M3 11.5h4l1 2h4l1-2h4v3.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 3 15z" />
  </>,
);

export const ScaleIcon = svg(
  <>
    <path d="M10 3v14" />
    <path d="M5 6h10M6 17h8" />
    <path d="M5 6 3 11h4zM15 6l-2 5h4z" />
  </>,
);

export const ChartIcon = svg(
  <>
    <path d="M3.5 16.5h13" />
    <path d="M6 16.5v-4M10 16.5v-8M14 16.5v-6" />
  </>,
);

export const LedgerIcon = svg(
  <>
    <rect x="4" y="3.5" width="12" height="13" rx="1.5" />
    <path d="M7 7h6M7 10h6M7 13h3.5" />
  </>,
);

export const SparkleIcon = svg(
  <>
    <path d="M10 3.5c.4 2.8 1.7 4.1 4.5 4.5-2.8.4-4.1 1.7-4.5 4.5-.4-2.8-1.7-4.1-4.5-4.5C8.3 7.6 9.6 6.3 10 3.5Z" />
    <path d="M15 12.5c.2 1.2.7 1.7 1.9 1.9-1.2.2-1.7.7-1.9 1.9-.2-1.2-.7-1.7-1.9-1.9 1.2-.2 1.7-.7 1.9-1.9Z" />
  </>,
);

export const HistoryIcon = svg(
  <>
    <path d="M3.6 9a6.5 6.5 0 1 1 .8 4" />
    <path d="M3.2 13.2 4 12.7l-.6 1.1M10 6.5V10l2.5 1.6" />
  </>,
);

export const BuildingIcon = svg(
  <>
    <path d="M4.5 16.5V5a1 1 0 0 1 1-1H11a1 1 0 0 1 1 1v11.5" />
    <path d="M12 8h3a1 1 0 0 1 1 1v7.5M3.5 16.5h13" />
    <path d="M7 7h2M7 10h2M7 13h2" />
  </>,
);

export const CheckIcon = svg(<path d="m4.5 10.5 3.2 3.2 7.8-7.4" />);

export const ShieldIcon = svg(
  <>
    <path d="M10 3.2 5 5v4.2c0 3 2.1 5.3 5 6.6 2.9-1.3 5-3.6 5-6.6V5z" />
    <path d="m7.8 9.7 1.6 1.6 3-3.2" />
  </>,
);

export const QuoteIcon = svg(
  <path d="M8 6.5c-2 .6-3 2-3 4.3 0 .9.6 1.7 1.6 1.7s1.6-.7 1.6-1.6c0-.8-.5-1.4-1.3-1.5.1-1 .8-1.7 2-2zm6 0c-2 .6-3 2-3 4.3 0 .9.6 1.7 1.6 1.7s1.6-.7 1.6-1.6c0-.8-.5-1.4-1.3-1.5.1-1 .8-1.7 2-2z" />,
  { fill: true },
);
