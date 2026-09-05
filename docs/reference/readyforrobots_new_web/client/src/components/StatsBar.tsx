/**
 * StatsBar — live footprint from GET /api/leads/summary (falls back if API unavailable).
 */

import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { useEffect, useRef, useState } from "react";

type Summary = {
  hot?: number;
  warm?: number;
  companies_in_database?: number;
  signals_in_database?: number;
  total_signals?: number;
};

function num(v: unknown): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
  return 0;
}

function useCountUp(target: number, duration = 1200, active: boolean) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!active || target <= 0) {
      setCount(target);
      return;
    }
    let start = 0;
    const step = Math.max(target / (duration / 16), 1);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration, active]);
  return count;
}

function StatItem({
  value,
  suffix,
  label,
  color,
  active,
}: {
  value: number;
  suffix: string;
  label: string;
  color: string;
  active: boolean;
}) {
  const count = useCountUp(value, 1000, active);
  return (
    <div className="flex flex-col items-center text-center px-4 py-6 md:px-6">
      <div
        className="text-3xl md:text-4xl font-extrabold mb-1 font-mono-data tabular-nums"
        style={{ color, fontFamily: "'Bricolage Grotesque', sans-serif" }}
      >
        {count.toLocaleString()}
        {suffix}
      </div>
      <div className="text-xs md:text-sm text-gray-600 font-medium leading-snug max-w-[11rem]">{label}</div>
    </div>
  );
}

const FALLBACK_STATS = [
  { value: 150, suffix: "+", label: "Signal sources (marketing)", color: "oklch(0.527 0.154 162.5)" },
  { value: 14, suffix: "", label: "Signal types tracked", color: "oklch(0.488 0.243 264.376)" },
  { value: 12, suffix: "", label: "Industry verticals", color: "oklch(0.627 0.163 66.5)" },
  { value: 100, suffix: "%", label: "Live pipeline data", color: "oklch(0.527 0.154 162.5)" },
];

export default function StatsBar() {
  const ref = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(false);
  const [live, setLive] = useState<Summary | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setActive(true);
      },
      { threshold: 0.25 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const API = getApiBase();
    (async () => {
      try {
        const r = await fetch(`${API}/api/leads/summary?exclude_junk=true`, liveFetchInit());
        if (!r.ok) return;
        const t = await r.text();
        if (t.trimStart().startsWith("<")) return;
        setLive(JSON.parse(t) as Summary);
      } catch {
        /* keep null → fallback */
      }
    })();
  }, []);

  const stats =
    live != null
      ? [
          {
            value: Math.max(num(live.hot), 0),
            suffix: "",
            label: "HOT leads (scored window)",
            color: "oklch(0.627 0.163 66.5)",
          },
          {
            value: Math.max(num(live.warm), 0),
            suffix: "",
            label: "WARM leads (scored window)",
            color: "oklch(0.488 0.243 264.376)",
          },
          {
            value: Math.max(num(live.companies_in_database), 0),
            suffix: "",
            label: "Companies in database",
            color: "oklch(0.527 0.154 162.5)",
          },
          {
            value: Math.max(num(live.signals_in_database ?? live.total_signals), 0),
            suffix: "",
            label: "Signal rows in database",
            color: "oklch(0.35 0.08 162.5)",
          },
        ]
      : FALLBACK_STATS;

  return (
    <section ref={ref} className="border-y border-gray-200 bg-white">
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-gray-200">
          {stats.map((s) => (
            <StatItem key={s.label} {...s} active={active} />
          ))}
        </div>
      </div>
    </section>
  );
}
