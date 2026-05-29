import { TONE_CLASSES, TONE_DOT, type Tone } from "@/lib/registry";

/** Tone-styled pill. Text is rendered as children (plain text) — never HTML. */
export function Badge({
  tone = "neutral",
  children,
  title,
  dot = false,
}: {
  tone?: Tone;
  children: React.ReactNode;
  title?: string;
  /** show a leading status dot */
  dot?: boolean;
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${TONE_CLASSES[tone]}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${TONE_DOT[tone]}`} aria-hidden="true" />}
      {children}
    </span>
  );
}
