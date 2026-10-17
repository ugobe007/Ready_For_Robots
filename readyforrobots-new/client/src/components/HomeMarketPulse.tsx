/**
 * Hero market pulse — deployments and hot windows.
 * Pipeline buyer counts stay in the API and are not shown here.
 */
import { useEffect, useState } from "react";
import { fetchWithTimeoutRetry, getPublicReadApiBase } from "@/lib/apiBase";

type PulseNums = {
  deployments: number;
  leads: number;
  live: boolean;
};

const FALLBACK: PulseNums = {
  deployments: 10,
  leads: 279,
  live: false,
};

/** Action accent — amber-orange, distinct from SIGNAL emerald evidence. */
const DEPLOY_COLOR = "#f59e0b";

function fmt(n: number): string {
  if (!Number.isFinite(n) || n < 0) return "—";
  return Math.round(n).toLocaleString("en-US");
}

function parsePulseJson(data: unknown): PulseNums | null {
  if (!data || typeof data !== "object") return null;
  const d = data as Record<string, unknown>;
  const leads = Number(d.hot_windows);
  const deployments = Number(d.active_deployments);
  const leadsOk = Number.isFinite(leads) && leads >= 0;
  const deploymentsOk = Number.isFinite(deployments) && deployments >= 0;
  if (!(leadsOk && leads > 0) && !(deploymentsOk && deployments > 0)) return null;
  return {
    leads: leadsOk ? leads : 0,
    deployments: deploymentsOk ? deployments : 0,
    live: true,
  };
}

function parseHomepageSummary(data: unknown): PulseNums | null {
  if (!data || typeof data !== "object") return null;
  const summary = (data as { summary?: Record<string, unknown> }).summary;
  if (!summary || typeof summary !== "object") return null;
  const hot = Number(summary.hot);
  if (!Number.isFinite(hot) || hot <= 0) return null;
  return { deployments: 0, leads: hot, live: true };
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
          { retries: 1, retryDelayMs: 400 }
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
          { retries: 1, retryDelayMs: 400 }
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
    fontFamily:
      "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  } as const;

  return (
    <p
      className="flex w-full min-w-0 flex-wrap items-baseline justify-start gap-x-1.5 gap-y-1 text-[13px] leading-none tracking-tight sm:text-[14px]"
      style={mono}
      aria-label="Robot labor market pulse"
    >
      <span className="relative mr-0.5 inline-flex h-1.5 w-1.5 shrink-0 self-center">
        <span
          className={`absolute inline-flex h-full w-full rounded-full ${pulse.live ? "animate-ping opacity-50" : "opacity-0"}`}
          style={{ backgroundColor: DEPLOY_COLOR }}
        />
        <span
          className="relative inline-flex h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: DEPLOY_COLOR }}
        />
      </span>
      <span
        className="font-medium tabular-nums"
        style={{ color: DEPLOY_COLOR }}
      >
        {fmt(pulse.deployments)}
      </span>
      <span className="text-slate-500">deployments</span>
      <span className="text-slate-600" aria-hidden>
        ·
      </span>
      <span className="font-medium tabular-nums text-slate-100">
        {fmt(pulse.leads)}
      </span>
      <span className="text-slate-500">leads</span>
      <span className="text-slate-600" aria-hidden>
        ·
      </span>
      <span className={pulse.live ? "text-[#3ecf8e]" : "text-slate-600"}>
        {pulse.live ? "live" : "cached"}
      </span>
    </p>
  );
}
