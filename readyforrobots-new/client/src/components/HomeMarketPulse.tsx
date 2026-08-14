/**
 * Hero market pulse — Supabase-style inline metrics (tight mono, no card padding).
 */
import { useEffect, useState } from "react";
import { getPublicReadApiBase } from "@/lib/apiBase";

export type MarketPulse = {
  buyer_opportunities: number;
  hot_windows: number;
  robot_vendors: number;
  active_deployments: number;
  buying_signals: number;
  live?: boolean;
};

const FALLBACK: MarketPulse = {
  buyer_opportunities: 1979,
  hot_windows: 279,
  robot_vendors: 120,
  active_deployments: 40,
  buying_signals: 3800,
  live: false,
};

function fmt(n: number): string {
  if (!Number.isFinite(n) || n < 0) return "—";
  return Math.round(n).toLocaleString("en-US");
}

type Cell = {
  value: number;
  label: string;
  accent?: "emerald" | "amber" | "white";
};

export default function HomeMarketPulse() {
  const [pulse, setPulse] = useState<MarketPulse>(FALLBACK);

  useEffect(() => {
    let active = true;
    const base = getPublicReadApiBase();
    void fetch(`${base}/api/leads/market-pulse`, { credentials: "omit" })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!active || !data) return;
        setPulse({
          buyer_opportunities: Number(data.buyer_opportunities) || FALLBACK.buyer_opportunities,
          hot_windows: Number(data.hot_windows) || FALLBACK.hot_windows,
          robot_vendors: Number(data.robot_vendors) || FALLBACK.robot_vendors,
          active_deployments: Number(data.active_deployments) || FALLBACK.active_deployments,
          buying_signals: Number(data.buying_signals) || FALLBACK.buying_signals,
          live: true,
        });
      })
      .catch(() => {
        /* keep fallback */
      });
    return () => {
      active = false;
    };
  }, []);

  const cells: Cell[] = [
    { value: pulse.buyer_opportunities, label: "Buyer opportunities", accent: "emerald" },
    { value: pulse.hot_windows, label: "Hot windows", accent: "white" },
    { value: pulse.robot_vendors, label: "Robot vendors", accent: "amber" },
    { value: pulse.active_deployments, label: "Active deployments", accent: "amber" },
  ];

  const valueClass = (accent?: Cell["accent"]) =>
    accent === "emerald"
      ? "text-[#3ecf8e]"
      : accent === "amber"
        ? "text-[#fbbf24]"
        : "text-foreground text-slate-100";

  return (
    <div className="w-full min-w-0">
      <div className="mb-2 flex items-center justify-center gap-1.5 lg:justify-start">
        <span className="relative flex h-1.5 w-1.5 shrink-0">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#3ecf8e] opacity-50" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#3ecf8e]" />
        </span>
        <span
          className="text-[12px] font-normal uppercase tracking-[0.12em] text-[#3ecf8e]"
          style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
        >
          Robot labor market — {pulse.live ? "live" : "cached"}
        </span>
      </div>

      <div className="flex w-full min-w-0 flex-wrap items-baseline justify-between gap-x-2 gap-y-2 border-y border-white/10 py-2 lg:justify-start lg:gap-x-0">
        {cells.map((cell, i) => (
          <div
            key={cell.label}
            className={[
              "flex min-w-0 flex-1 basis-[calc(50%-0.25rem)] flex-col items-center gap-0 overflow-hidden sm:basis-0 lg:items-start",
              i > 0 ? "lg:border-l lg:border-white/10 lg:pl-3" : "",
              i < cells.length - 1 ? "lg:pr-3" : "",
            ].join(" ")}
          >
            <span
              className={`text-[17px] font-medium leading-none tracking-tight tabular-nums sm:text-[18px] ${valueClass(cell.accent)}`}
              style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
            >
              {fmt(cell.value)}
            </span>
            <span
              className="mt-0.5 max-w-full truncate text-[11px] font-normal leading-none tracking-tight text-slate-500"
              style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
            >
              {cell.label}
            </span>
          </div>
        ))}
      </div>

      {pulse.buying_signals > 0 ? (
        <p
          className="mt-1.5 text-center text-[11px] font-normal leading-none tracking-tight text-slate-600 lg:text-left"
          style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
        >
          {fmt(pulse.buying_signals)} buying signals scored
        </p>
      ) : null}
    </div>
  );
}
