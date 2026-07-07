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
  emerald: "text-emerald-700 hover:text-emerald-900",
  amber: "text-amber-800 hover:text-amber-950",
  gray: "text-gray-700 hover:text-gray-900",
  blue: "text-blue-700 hover:text-blue-900",
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
    inactive ? "pointer-events-none opacity-40 no-underline cursor-not-allowed" : "",
    className,
  ].filter(Boolean).join(" ");

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
