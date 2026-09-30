/**
 * Live sales-lead ticker — newest lead enters at top every 5s; oldest exits at bottom.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Link } from "wouter";
import { ChevronRight } from "lucide-react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { dedupeHomepageLeads } from "@/lib/homepageLeads";

export type TickerLead = {
  id: number;
  company_name: string;
  industry?: string | null;
  priority_tier?: string | null;
  robot_types_needed?: string[];
};

type TickerRow = TickerLead & { tickKey: number };

const DEFAULT_MAX_VISIBLE = 12;
const DEFAULT_TICK_MS = 5000;
const POOL_REFRESH_MS = 90_000;
const ROW_HEIGHT_PX = 50;

export type ExperimentLeadTickerProps = {
  maxVisible?: number;
  tickMs?: number;
  minHeightClass?: string;
  title?: string;
  subtitle?: string;
  showPipelineLink?: boolean;
};

const FALLBACK_POOL: TickerLead[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    industry: "Logistics",
    priority_tier: "HOT",
    robot_types_needed: ["mobile robots (AMRs)", "warehouse automation"],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels Corp.",
    industry: "Hospitality",
    priority_tier: "HOT",
    robot_types_needed: ["service robots", "cleaning robots"],
  },
  {
    id: -3,
    company_name: "Sysco Corporation",
    industry: "Food Service",
    priority_tier: "WARM",
    robot_types_needed: ["mobile robots (AMRs)", "palletizing robots"],
  },
  {
    id: -4,
    company_name: "Marriott International",
    industry: "Hospitality",
    priority_tier: "HOT",
    robot_types_needed: ["service robots", "delivery robots"],
  },
  {
    id: -5,
    company_name: "FedEx Supply Chain",
    industry: "Logistics",
    priority_tier: "HOT",
    robot_types_needed: ["sortation robots", "mobile robots (AMRs)"],
  },
  {
    id: -6,
    company_name: "Pepsi Beverage Co.",
    industry: "Food Processing",
    priority_tier: "WARM",
    robot_types_needed: ["pick-and-place robots", "packaging automation"],
  },
  {
    id: -7,
    company_name: "HCA Healthcare",
    industry: "Healthcare",
    priority_tier: "WARM",
    robot_types_needed: ["mobile robots (AMRs)", "service robots"],
  },
  {
    id: -8,
    company_name: "Target Corporation",
    industry: "Retail",
    priority_tier: "HOT",
    robot_types_needed: ["mobile robots (AMRs)", "inventory robots"],
  },
  {
    id: -9,
    company_name: "DHL Supply Chain",
    industry: "Logistics",
    priority_tier: "HOT",
    robot_types_needed: ["mobile robots (AMRs)", "conveyor automation"],
  },
  {
    id: -10,
    company_name: "Chipotle Mexican Grill",
    industry: "Food Service",
    priority_tier: "WARM",
    robot_types_needed: ["kitchen automation", "service robots"],
  },
  {
    id: -11,
    company_name: "Amazon Fulfillment",
    industry: "Logistics",
    priority_tier: "HOT",
    robot_types_needed: ["mobile robots (AMRs)", "sortation robots"],
  },
  {
    id: -12,
    company_name: "Walmart",
    industry: "Retail",
    priority_tier: "HOT",
    robot_types_needed: ["inventory robots", "mobile robots (AMRs)"],
  },
  {
    id: -13,
    company_name: "UPS",
    industry: "Logistics",
    priority_tier: "WARM",
    robot_types_needed: ["sortation robots", "mobile robots (AMRs)"],
  },
  {
    id: -14,
    company_name: "Hilton Worldwide",
    industry: "Hospitality",
    priority_tier: "WARM",
    robot_types_needed: ["service robots", "cleaning robots"],
  },
  {
    id: -15,
    company_name: "Costco Wholesale",
    industry: "Retail",
    priority_tier: "HOT",
    robot_types_needed: ["mobile robots (AMRs)", "palletizing robots"],
  },
];

const tierStyle: Record<string, { color: string; bg: string; border: string }> =
  {
    HOT: {
      color: "#f87171",
      bg: "rgba(248,113,113,0.12)",
      border: "rgba(248,113,113,0.25)",
    },
    WARM: {
      color: "#a78bfa",
      bg: "rgba(96,165,250,0.10)",
      border: "rgba(96,165,250,0.22)",
    },
    COLD: {
      color: "#94a3b8",
      bg: "rgba(148,163,184,0.08)",
      border: "rgba(148,163,184,0.2)",
    },
  };

function robotLine(lead: TickerLead): string {
  const types = lead.robot_types_needed?.filter(Boolean) ?? [];
  if (types.length) return types.slice(0, 2).join(" · ");
  if (lead.industry) return `${lead.industry} automation fit`;
  return "Robot category mapping in progress";
}

function normalizePool(raw: unknown[], minVisible: number): TickerLead[] {
  const mapped: TickerLead[] = [];
  for (const row of raw) {
    const r = row as Record<string, unknown>;
    const name = String(r.company_name || "").trim();
    const id = Number(r.id);
    if (!name || !id) continue;
    mapped.push({
      id,
      company_name: name,
      industry: typeof r.industry === "string" ? r.industry : null,
      priority_tier:
        typeof r.priority_tier === "string" ? r.priority_tier : null,
      robot_types_needed: Array.isArray(r.robot_types_needed)
        ? (r.robot_types_needed as string[]).filter(Boolean)
        : [],
    });
  }

  const deduped = dedupeHomepageLeads(mapped) as TickerLead[];
  const withRobots = deduped.filter(
    l => (l.robot_types_needed?.length ?? 0) > 0
  );
  const pool = withRobots.length >= minVisible ? withRobots : deduped;
  return pool.length ? pool : FALLBACK_POOL;
}

async function fetchLeadPool(minVisible: number): Promise<TickerLead[]> {
  const base = getApiBase();
  const res = await fetch(
    `${base}/api/leads?limit=50&sort=score&exclude_junk=true`,
    liveFetchInit()
  );
  if (!res.ok) throw new Error("leads fetch failed");
  const raw = await res.text();
  if (raw.trimStart().startsWith("<")) throw new Error("non-json response");
  const data = JSON.parse(raw) as { leads?: unknown[] };
  const rows = Array.isArray(data.leads) ? data.leads : [];
  return normalizePool(rows, minVisible);
}

export default function ExperimentLeadTicker({
  maxVisible = DEFAULT_MAX_VISIBLE,
  tickMs = DEFAULT_TICK_MS,
  minHeightClass = "min-h-0",
  title = "Live sales leads",
  subtitle = "Robot demand ticker",
  showPipelineLink = false,
}: ExperimentLeadTickerProps) {
  const [pool, setPool] = useState<TickerLead[]>(FALLBACK_POOL);
  const [visible, setVisible] = useState<TickerRow[]>([]);
  const [live, setLive] = useState(false);
  const poolIndex = useRef(0);
  const tickKey = useRef(0);

  const seedVisible = useCallback(
    (nextPool: TickerLead[]) => {
      const initial = nextPool.slice(0, maxVisible).map((lead, i) => ({
        ...lead,
        tickKey: tickKey.current++ + lead.id + i,
      }));
      poolIndex.current = initial.length % Math.max(nextPool.length, 1);
      setVisible(initial);
    },
    [maxVisible]
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const nextPool = await fetchLeadPool(maxVisible);
        if (cancelled) return;
        setPool(nextPool);
        setLive(true);
        seedVisible(nextPool);
      } catch {
        if (!cancelled) {
          setLive(false);
          seedVisible(FALLBACK_POOL);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [maxVisible, seedVisible]);

  useEffect(() => {
    const refresh = window.setInterval(() => {
      fetchLeadPool(maxVisible)
        .then(nextPool => {
          setPool(nextPool);
          setLive(true);
        })
        .catch(() => undefined);
    }, POOL_REFRESH_MS);
    return () => window.clearInterval(refresh);
  }, [maxVisible]);

  useEffect(() => {
    if (pool.length === 0) return;
    const timer = window.setInterval(() => {
      const idx = poolIndex.current % pool.length;
      const next = pool[idx];
      poolIndex.current = (idx + 1) % pool.length;
      setVisible(prev => {
        const row: TickerRow = { ...next, tickKey: tickKey.current++ };
        return [row, ...prev].slice(0, maxVisible);
      });
    }, tickMs);
    return () => window.clearInterval(timer);
  }, [pool, maxVisible, tickMs]);

  return (
    <div
      className={`relative flex w-full max-w-[400px] flex-col overflow-hidden rounded-2xl border ${minHeightClass}`}
      style={{
        background: "rgba(255,255,255,0.025)",
        borderColor: "rgba(124,58,237,0.22)",
        boxShadow:
          "0 0 0 1px rgba(3,218,197,0.08), 0 0 24px rgba(124,58,237,0.14), 0 0 48px rgba(3,218,197,0.06), 0 16px 40px -16px rgba(0,0,0,0.55)",
      }}
    >
      <div
        className="flex shrink-0 items-center justify-between border-b border-white/6 px-4 py-3"
        style={{ background: "rgba(124,58,237,0.06)" }}
      >
        <div className="min-w-0">
          <p
            className="text-[10px] font-bold uppercase tracking-[0.18em]"
            style={{
              color: "#a78bfa",
              fontFamily: "'Inter', system-ui, sans-serif",
            }}
          >
            {title}
          </p>
          <p className="mt-0.5 truncate text-[11px] text-white/35">
            {subtitle}
          </p>
        </div>
        <span
          className="flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider"
          style={{
            color: "#03DAC5",
            background: "rgba(3,218,197,0.08)",
            borderColor: "rgba(3,218,197,0.28)",
          }}
        >
          <span
            className="h-1 w-1 animate-pulse rounded-full"
            style={{ background: "#03DAC5" }}
          />
          {live ? "Live" : "Demo"}
        </span>
      </div>

      <div
        className="relative shrink-0 overflow-hidden"
        style={{ minHeight: `${maxVisible * ROW_HEIGHT_PX + 4}px` }}
      >
        <ul
          className="relative overflow-hidden px-2 py-1.5"
          aria-live="polite"
          aria-label="Latest sales leads and robot types"
        >
          <AnimatePresence initial={false} mode="popLayout">
            {visible.map(lead => {
              const tier = (lead.priority_tier || "WARM").toUpperCase();
              const st = tierStyle[tier] || tierStyle.WARM;
              return (
                <motion.li
                  key={lead.tickKey}
                  layout
                  initial={{ opacity: 0, y: -12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  className="mb-1.5 flex items-center gap-2 rounded-lg border border-white/5 px-2.5 py-2.5"
                  style={{ background: "rgba(255,255,255,0.02)" }}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <p className="truncate text-[12px] font-semibold leading-tight text-white/90">
                        {lead.company_name}
                      </p>
                      <span
                        className="shrink-0 rounded-full border px-1.5 py-px text-[8px] font-bold uppercase"
                        style={{
                          color: st.color,
                          background: st.bg,
                          borderColor: st.border,
                        }}
                      >
                        {tier}
                      </span>
                    </div>
                    <p className="mt-0.5 truncate text-[10px] text-white/38">
                      {robotLine(lead)}
                    </p>
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
      </div>

      <div
        className="shrink-0 border-t border-white/6 px-3 py-2.5"
        style={{ background: "rgba(255,255,255,0.015)" }}
      >
        {showPipelineLink ? (
          <Link
            href="/pipeline"
            className="inline-flex items-center gap-1 text-[11px] font-semibold text-white/45 transition-colors hover:text-white/75"
          >
            View full pipeline
            <ChevronRight className="h-3 w-3" />
          </Link>
        ) : (
          <p className="text-[10px] text-white/25">
            Rotates every {Math.round(tickMs / 1000)}s · {maxVisible} shown
          </p>
        )}
      </div>
    </div>
  );
}
