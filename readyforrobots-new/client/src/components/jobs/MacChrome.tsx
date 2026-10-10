/**
 * Dark ReadyForRobots window chrome for /jobs employment office.
 * Dense System-1 composition, RFR navy + emerald palette.
 */
import type { ReactNode } from "react";

export const macInk = "#e2e8f0";
export const macPaper = "#0b162f";
export const macPaperHi = "#0b162f";
export const macMuted = "#94a3b8";
export const macRule = "#334155";
export const macAccent = "#10b981";

/** Compact title strip for nested panels. */
export function MacTitleBar({
  title,
  trailing,
}: {
  title: string;
  trailing?: ReactNode;
  showClose?: boolean;
}) {
  return (
    <div
      className="flex h-7 shrink-0 items-center justify-between border-b px-3"
      style={{ borderColor: macRule, background: "#0a1327", color: macInk }}
    >
      <span className="truncate font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-300">
        {title}
      </span>
      <div className="flex items-center gap-2">{trailing}</div>
    </div>
  );
}

export function MacWindow({
  title,
  trailing,
  children,
  className = "",
}: {
  title: string;
  trailing?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`flex min-h-0 flex-col border bg-[#0b162f] ${className}`}
      style={{ borderColor: macRule }}
    >
      <MacTitleBar title={title} trailing={trailing} />
      <div className="min-h-0 flex-1 text-slate-100">{children}</div>
    </div>
  );
}
