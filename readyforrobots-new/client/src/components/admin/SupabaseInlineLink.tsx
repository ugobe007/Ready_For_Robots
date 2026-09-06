/**
 * Supabase-style admin action: plain underlined text, no padding/border.
 * onClick actions use <button> (reliable); route/hash links use <a>.
 */
type Props = {
  children: React.ReactNode;
  onClick?: () => void;
  href?: string;
  onNavigate?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
  disabled?: boolean;
  busy?: boolean;
  tone?: "emerald" | "amber" | "gray" | "blue";
  className?: string;
};

const TONE: Record<NonNullable<Props["tone"]>, string> = {
  emerald: "text-emerald-400 hover:text-emerald-300",
  amber: "text-amber-400 hover:text-amber-300",
  gray: "text-slate-400 hover:text-slate-200",
  blue: "text-sky-400 hover:text-sky-300",
};

export default function SupabaseInlineLink({
  children,
  onClick,
  href,
  onNavigate,
  disabled,
  busy,
  tone = "emerald",
  className = "",
}: Props) {
  const inactive = disabled || busy;
  const cls = [
    "cursor-pointer font-medium underline underline-offset-2 bg-transparent border-0 p-0 inline",
    TONE[tone],
    inactive
      ? "pointer-events-none opacity-40 no-underline cursor-not-allowed"
      : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (href && onNavigate) {
    return (
      <a href={href} onClick={onNavigate} className={cls}>
        {busy ? "Working…" : children}
      </a>
    );
  }

  if (href && !onClick) {
    return (
      <a href={href} className={cls} aria-disabled={inactive || undefined}>
        {busy ? "Working…" : children}
      </a>
    );
  }

  return (
    <button
      type="button"
      disabled={inactive}
      className={cls}
      onClick={() => {
        if (!inactive) onClick?.();
      }}
    >
      {busy ? "Working…" : children}
    </button>
  );
}
