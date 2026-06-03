import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { RR } from "@/lib/humanoidReportTheme";

export function ReportKicker({ children }: { children: ReactNode }) {
  return (
    <p
      className="text-[10px] font-bold uppercase tracking-[0.24em]"
      style={{ color: RR.teal }}
    >
      {children}
    </p>
  );
}

export function ReportTitle({ children, id }: { children: ReactNode; id?: string }) {
  return (
    <h2
      id={id}
      className="mt-1 text-lg font-bold tracking-tight sm:text-xl"
      style={{ fontFamily: RR.fontDisplay, color: RR.text }}
    >
      {children}
    </h2>
  );
}

export function ReportSectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3
      className="text-[11px] font-bold uppercase tracking-[0.18em] mb-2.5"
      style={{ color: RR.purple }}
    >
      {children}
    </h3>
  );
}

type PanelProps = {
  children: ReactNode;
  accent?: "purple" | "teal" | "none";
  className?: string;
};

export function ReportPanel({ children, accent = "purple", className = "" }: PanelProps) {
  const borderLeft =
    accent === "teal"
      ? `3px solid ${RR.teal}`
      : accent === "purple"
        ? `3px solid ${RR.purple}`
        : "3px solid transparent";
  return (
    <div
      className={`rounded-lg border px-4 py-3.5 ${className}`}
      style={{
        borderColor: RR.border,
        borderLeft,
        background: RR.bgElevated,
      }}
    >
      {children}
    </div>
  );
}

export function ReportBtnDownload({
  href,
  label = "Download PDF",
  compact,
}: {
  href: string;
  label?: string;
  compact?: boolean;
}) {
  return (
    <a
      href={href}
      download
      className={
        compact
          ? "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-bold transition-opacity hover:opacity-90"
          : "inline-flex shrink-0 items-center gap-2 rounded-md px-3.5 py-2 text-[12px] font-bold transition-opacity hover:opacity-90"
      }
      style={{
        background: RR.teal,
        color: RR.bg,
      }}
    >
      {label}
    </a>
  );
}

export function ReportLink({
  href,
  children,
  external,
}: {
  href: string;
  children: ReactNode;
  external?: boolean;
}) {
  return (
    <a
      href={href}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="font-medium underline underline-offset-4 decoration-white/20 hover:decoration-violet-400/50"
      style={{ color: "rgba(167,139,250,0.95)" }}
    >
      {children}
    </a>
  );
}

export function ReportBodyText({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <p className={`text-[13px] leading-relaxed ${className}`} style={{ color: RR.textMuted }}>
      {children}
    </p>
  );
}

export function ReportFindingCard({ title, body }: { title: string; body: string }) {
  return (
    <div
      className="rounded-md border px-3 py-2.5"
      style={{ borderColor: RR.border, background: "rgba(255,255,255,0.02)" }}
    >
      <p className="text-[12px] font-bold" style={{ color: RR.teal }}>
        {title}
      </p>
      <p className="mt-1 text-[13px] leading-snug" style={{ color: RR.textMuted }}>
        {body}
      </p>
    </div>
  );
}

export function ReportMetric({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="rounded-md border px-3 py-2 text-center"
      style={{ borderColor: RR.border, background: "rgba(124,58,237,0.06)" }}
    >
      <p className="text-[9px] font-bold uppercase tracking-wider" style={{ color: RR.textDim }}>
        {label}
      </p>
      <p className="mt-0.5 text-lg font-black tabular-nums" style={{ color: RR.teal }}>
        {value}
      </p>
    </div>
  );
}

type TableProps = {
  headers: string[];
  rows: ReactNode[][];
  minWidth?: string;
};

export function ReportTable({ headers, rows, minWidth = "480px" }: TableProps) {
  return (
    <div className="overflow-x-auto rounded-md border" style={{ borderColor: RR.border }}>
      <table className="w-full text-left text-[11px]" style={{ minWidth }}>
        <thead>
          <tr style={{ background: RR.purpleMuted, borderBottom: `1px solid ${RR.border}` }}>
            {headers.map((h) => (
              <th
                key={h}
                className="px-2.5 py-2 text-[9px] font-bold uppercase tracking-wider"
                style={{ color: RR.textDim }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((cells, i) => (
            <tr
              key={i}
              className="border-b last:border-0"
              style={{
                borderColor: RR.border,
                background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.015)",
              }}
            >
              {cells.map((cell, j) => (
                <td key={j} className="px-2.5 py-2 align-top" style={{ color: RR.textMuted }}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ReportDetails({
  summary,
  children,
  defaultOpen,
}: {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details
      className="group rounded-lg border overflow-hidden"
      style={{ borderColor: RR.border, background: RR.bgElevated }}
      open={defaultOpen}
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3.5 py-2.5 [&::-webkit-details-marker]:hidden hover:bg-white/[0.02]">
        {summary}
        <ChevronDown className="h-4 w-4 shrink-0 opacity-40 transition-transform group-open:rotate-180" />
      </summary>
      <div className="border-t px-3.5 pb-3.5 pt-3" style={{ borderColor: RR.border }}>
        {children}
      </div>
    </details>
  );
}
