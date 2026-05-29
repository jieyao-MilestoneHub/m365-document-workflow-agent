import Link from "next/link";

/** Microsoft 365-style brand command bar shared across console pages. */
export function AppHeader({ compact = false }: { compact?: boolean }) {
  return (
    <header className="sticky top-0 z-20 border-b border-stroke bg-surface/85 backdrop-blur-md">
      <div
        className={`mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 sm:px-6 lg:px-8 ${
          compact ? "" : ""
        }`}
      >
        <Link href="/" className="flex items-center gap-2.5">
          <BrandMark />
          <span className="flex flex-col leading-tight">
            <span className="font-display text-sm font-semibold text-ink">
              AP Three-Way Match
            </span>
            <span className="hidden text-[11px] font-medium text-muted sm:block">
              Microsoft 365 Copilot · Finance Operations
            </span>
          </span>
        </Link>
        <div className="ml-auto flex items-center gap-2">
          <span className="hidden items-center gap-1.5 rounded-full bg-surface-muted px-2.5 py-1 text-[11px] font-semibold text-muted ring-1 ring-inset ring-stroke sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-success" aria-hidden="true" />
            Agent runtime
          </span>
        </div>
      </div>
    </header>
  );
}

/** The Microsoft "four squares" inspired brand tile, in the product blue. */
function BrandMark() {
  return (
    <span className="grid h-8 w-8 place-items-center rounded-md bg-gradient-to-br from-brand to-brand-pressed shadow-sm">
      <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
        <rect x="3" y="3" width="6.2" height="6.2" rx="1" fill="#fff" opacity="0.95" />
        <rect x="10.8" y="3" width="6.2" height="6.2" rx="1" fill="#fff" opacity="0.7" />
        <rect x="3" y="10.8" width="6.2" height="6.2" rx="1" fill="#fff" opacity="0.7" />
        <rect x="10.8" y="10.8" width="6.2" height="6.2" rx="1" fill="#fff" opacity="0.95" />
      </svg>
    </span>
  );
}

/** Page chrome: sticky header + a responsive max-width content container. */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        {children}
      </main>
    </div>
  );
}

/** Standard page heading block (title + description + optional actions / breadcrumb). */
export function PageHeading({
  title,
  description,
  actions,
  eyebrow,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  eyebrow?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-1">
        {eyebrow}
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink sm:text-[28px]">
          {title}
        </h1>
        {description && <p className="max-w-2xl text-sm text-muted">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
