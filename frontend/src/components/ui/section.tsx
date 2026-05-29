type IconCmp = (props: { className?: string }) => React.ReactNode;

/**
 * Standard Fluent surface card with an optional titled header (icon + title + aside).
 * Every console section uses this so spacing, borders and elevation stay consistent.
 */
export function Section({
  title,
  icon: Icon,
  aside,
  children,
  className,
  bodyClassName,
}: {
  title?: string;
  icon?: IconCmp;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={`overflow-hidden rounded-card border border-stroke bg-surface shadow-card ${className ?? ""}`}
    >
      {title && (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-stroke px-4 py-3 sm:px-5">
          <h3 className="flex items-center gap-2 font-display text-sm font-semibold text-ink">
            {Icon && (
              <span className="text-brand">
                <Icon className="h-[18px] w-[18px]" />
              </span>
            )}
            {title}
          </h3>
          {aside && <div className="flex items-center gap-2">{aside}</div>}
        </header>
      )}
      <div className={bodyClassName ?? "p-4 sm:p-5"}>{children}</div>
    </section>
  );
}
