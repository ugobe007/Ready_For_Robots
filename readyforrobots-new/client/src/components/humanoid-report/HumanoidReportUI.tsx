import { useState, type ReactNode } from "react";
import { ChevronDown, Loader2 } from "lucide-react";
import { liveFetchInit } from "@/lib/apiBase";
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

function filenameFromContentDisposition(header: string | null): string | null {
  if (!header) return null;
  const star = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1].trim());
    } catch {
      /* ignore */
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(header);
  return plain?.[1]?.trim() || null;
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
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const className = compact
    ? "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-bold transition-opacity hover:opacity-90 disabled:opacity-60"
    : "inline-flex shrink-0 items-center gap-2 rounded-md px-3.5 py-2 text-[12px] font-bold transition-opacity hover:opacity-90 disabled:opacity-60";

  async function handleClick(e: React.MouseEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(href, liveFetchInit());
      if (!res.ok) {
        const raw = await res.text().catch(() => "");
        let message = `Download failed (${res.status})`;
        try {
          const parsed = JSON.parse(raw) as { detail?: string };
          if (parsed.detail) message = String(parsed.detail);
        } catch {
          if (raw.trim()) message = raw.slice(0, 200);
        }
        throw new Error(message);
      }
      const blob = await res.blob();
      if (!blob.size || !blob.type.includes("pdf")) {
        throw new Error("Server did not return a PDF");
      }
      const name =
        filenameFromContentDisposition(res.headers.get("Content-Disposition")) ||
        "Humanoid_Intelligence_Report.pdf";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (ex) {
      const msg = ex instanceof Error ? ex.message : "Download failed";
      setErr(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-end gap-0.5">
      <button
        type="button"
        onClick={handleClick}
        disabled={busy}
        className={className}
        style={{
          background: RR.teal,
          color: RR.bg,
        }}
      >
        {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
        {busy ? "Generating…" : label}
      </button>
      {err ? (
        <span className="max-w-[220px] text-right text-[10px] leading-tight" style={{ color: RR.textDim }}>
          Opened in new tab — {err}
        </span>
      ) : null}
    </span>
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
