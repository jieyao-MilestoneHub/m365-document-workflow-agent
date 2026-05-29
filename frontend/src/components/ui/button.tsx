import Link from "next/link";

type Variant = "primary" | "default" | "subtle" | "danger" | "success";
type Size = "sm" | "md";

const BASE =
  "inline-flex items-center justify-center gap-1.5 rounded-md font-semibold transition-colors duration-100 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50";

const VARIANT: Record<Variant, string> = {
  primary: "bg-brand text-white hover:bg-brand-hover active:bg-brand-pressed",
  default:
    "bg-surface text-ink ring-1 ring-inset ring-stroke-strong hover:bg-surface-muted active:bg-surface-muted",
  subtle: "bg-transparent text-brand hover:bg-brand-tint active:bg-brand-tint-strong",
  danger: "bg-danger text-white hover:brightness-95 active:brightness-90",
  success: "bg-success text-white hover:brightness-95 active:brightness-90",
};

const SIZE: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
};

function classes(variant: Variant, size: Size, className?: string) {
  return `${BASE} ${VARIANT[variant]} ${SIZE[size]} ${className ?? ""}`;
}

/** Fluent-style button. */
export function Button({
  variant = "default",
  size = "md",
  className,
  ...props
}: {
  variant?: Variant;
  size?: Size;
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={classes(variant, size, className)} {...props} />;
}

/** Same styling as Button, rendered as a Next.js link. */
export function ButtonLink({
  variant = "default",
  size = "md",
  className,
  href,
  children,
}: {
  variant?: Variant;
  size?: Size;
  className?: string;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link href={href} className={classes(variant, size, className)}>
      {children}
    </Link>
  );
}
