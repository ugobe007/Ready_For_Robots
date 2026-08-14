/**
 * Hero market pulse — one-line ticker under SIGNAL (buyers · hot · live).
 */
import { useEffect, useState } from "react";
import { fetchWithTimeoutRetry, getPublicReadApiBase } from "@/lib/apiBase";

type PulseNums = {
  buyers: number;
  hot: number;
  live: boolean;
};

const FALLBACK: PulseNums = {
  buyers: 1979,
  hot: 279,
  live: false,
};

function fmt(n: number): string {
  if (!Number.isFinite(n) || n < 0) return "—";
  return Math.round(n).toLocaleString("en-US");
}

function parsePulseJson(data: unknown): PulseNums | null {
  if (!data || typeof data !== "object") return null;
  const d = data as Record<string, unknown>;
  const buyers = Number(d.buyer_opportunities);
  const hot = Number(d.hot_windows);
  if (!Number.isFinite(buyers) || buyers <= 0) return null;
  return {
    buyers,
    hot: Number.isFinite(hot) && hot >= 0 ? hot : 0,
    live: true,
  };
}

function parseHomepageSummary(data: unknown): PulseNums | null {
  if (!data || typeof data !== "object") return null;
  const summary = (data as { summary?: Record<string, unknown> }).summary;
  if (!summary || typeof summary !== "object") return null;
  const hot = Number(summary.hot) || 0;
  const warm = Number(summary.warm) || 0;
  const buyers = hot + warm;
  if (buyers <= 0) return null;
  return { buyers, hot, live: true };
}

export default function HomeMarketPulse() {
  const [pulse, setPulse] = useState<PulseNums>(FALLBACK);

  useEffect(() => {
    let active = true;
    const base = getPublicReadApiBase();

    void (async () => {
      try {
        const res = await fetchWithTimeoutRetry(
          `${base}/api/leads/market-pulse`,
          {},
          6_000,
          { retries: 1, retryDelayMs: 400 },
        );
        if (res.ok) {
          const ct = res.headers.get("content-type") || "";
          if (ct.includes("application/json")) {
            const parsed = parsePulseJson(await res.json());
            if (active && parsed) {
              setPulse(parsed);
              return;
            }
          }
        }
      } catch {
        /* try homepage summary */
      }

      try {
        const res = await fetchWithTimeoutRetry(
          `${base}/api/leads/homepage`,
          {},
          8_000,
          { retries: 1, retryDelayMs: 400 },
        );
        if (!res.ok) return;
        const parsed = parseHomepageSummary(await res.json());
        if (active && parsed) setPulse(parsed);
      } catch {
        /* keep fallback */
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  const mono = {
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  } as const;

  return (
    <p
      className="flex w-full min-w-0 flex-wrap items-baseline justify-center gap-x-1.5 gap-y-1 text-[13px] leading-none tracking-tight sm:text-[14px] lg:justify-start"
      style={mono}
      aria-label="Robot labor market pulse"
    >
      <span className="relative mr-0.5 inline-flex h-1.5 w-1.5 shrink-0 self-center">
        <span
          className={`absolute inline-flex h-full w-full rounded-full bg-[#3ecf8e] ${pulse.live ? "animate-ping opacity-50" : "opacity-0"}`}
        />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#3ecf8e]" />
      </span>
      <span className="font-medium tabular-nums text-[#3ecf8e]">{fmt(pulse.buyers)}</span>
      <span className="text-slate-500">buyers</span>
      <span className="text-slate-600" aria-hidden>
        ·
      </span>
      <span className="font-medium tabular-nums text-slate-100">{fmt(pulse.hot)}</span>
      <span className="text-slate-500">hot</span>
      <span className="text-slate-600" aria-hidden>
        ·
      </span>
      <span className={pulse.live ? "text-[#3ecf8e]" : "text-slate-600"}>
        {pulse.live ? "live" : "cached"}
      </span>
    </p>
  );
}
