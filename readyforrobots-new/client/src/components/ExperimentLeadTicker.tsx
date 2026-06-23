/**
 * Live sales-lead ticker — newest lead enters at top every 5s; oldest exits at bottom.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Link } from "wouter";
import { ChevronRight, Zap } from "lucide-react";
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
const AMBER = "#FFB000";
const PANEL_BG = "#171717";
const ROW_BG = "#232323";
const SUPABASE_GREEN = "#3ecf8e";

export type ExperimentLeadTickerProps = {
  maxVisible?: number;
  tickMs?: number;
  minHeightClass?: string;
  title?: string;
  subtitle?: string;
  showPipelineLink?: boolean;
  /** Supabase-inspired hero panel — amber headline tied to Activate SIGNAL CTA */
  heroVariant?: boolean;
};

const FALLBACK_POOL: TickerLead[] = [
  { id: -1, company_name: "Lineage Logistics", industry: "Logistics", priority_tier: "HOT", robot_types_needed: ["mobile robots (AMRs)", "warehouse automation"] },
  { id: -2, company_name: "Hyatt Hotels Corp.", industry: "Hospitality", priority_tier: "HOT", robot_types_needed: ["service robots", "cleaning robots"] },
  { id: -3, company_name: "Sysco Corporation", industry: "Food Service", priority_tier: "WARM", robot_types_needed: ["mobile robots (AMRs)", "palletizing robots"] },
  { id: -4, company_name: "Marriott International", industry: "Hospitality", priority_tier: "HOT", robot_types_needed: ["service robots", "delivery robots"] },
  { id: -5, company_name: "FedEx Supply Chain", industry: "Logistics", priority_tier: "HOT", robot_types_needed: ["sortation robots", "mobile robots (AMRs)"] },
  { id: -6, company_name: "Pepsi Beverage Co.", industry: "Food Processing", priority_tier: "WARM", robot_types_needed: ["pick-and-place robots", "packaging automation"] },
  { id: -7, company_name: "HCA Healthcare", industry: "Healthcare", priority_tier: "WARM", robot_types_needed: ["mobile robots (AMRs)", "service robots"] },
  { id: -8, company_name: "Target Corporation", industry: "Retail", priority_tier: "HOT", robot_types_needed: ["mobile robots (AMRs)", "inventory robots"] },
  { id: -9, company_name: "DHL Supply Chain", industry: "Logistics", priority_tier: "HOT", robot_types_needed: ["mobile robots (AMRs)", "conveyor automation"] },
  { id: -10, company_name: "Chipotle Mexican Grill", industry: "Food Service", priority_tier: "WARM", robot_types_needed: ["kitchen automation", "service robots"] },
  { id: -11, company_name: "Amazon Fulfillment", industry: "Logistics", priority_tier: "HOT", robot_types_needed: ["mobile robots (AMRs)", "sortation robots"] },
  { id: -12, company_name: "Walmart", industry: "Retail", priority_tier: "HOT", robot_types_needed: ["inventory robots", "mobile robots (AMRs)"] },
  { id: -13, company_name: "UPS", industry: "Logistics", priority_tier: "WARM", robot_types_needed: ["sortation robots", "mobile robots (AMRs)"] },
  { id: -14, company_name: "Hilton Worldwide", industry: "Hospitality", priority_tier: "WARM", robot_types_needed: ["service robots", "cleaning robots"] },
  { id: -15, company_name: "Costco Wholesale", industry: "Retail", priority_tier: "HOT", robot_types_needed: ["mobile robots (AMRs)", "palletizing robots"] },
];

const tierStyle: Record<string, { color: string; bg: string; border: string }> = {
  HOT: { color: "#fca5a5", bg: "rgba(248,113,113,0.16)", border: "rgba(248,113,113,0.45)" },
  WARM: { color: "#fcd34d", bg: "rgba(251,191,36,0.12)", border: "rgba(251,191,36,0.35)" },
  COLD: { color: "#94a3b8", bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.28)" },
};

function robotLine(lead: TickerLead): string {
  const types = lead.robot_types_needed?.filter(Boolean) ?? [];
  if (types.length) return types.slice(0, 3).join(" · ");
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
      priority_tier: typeof r.priority_tier === "string" ? r.priority_tier : null,
      robot_types_needed: Array.isArray(r.robot_types_needed)
        ? (r.robot_types_needed as string[]).filter(Boolean)
        : [],
    });
  }

  const deduped = dedupeHomepageLeads(mapped) as TickerLead[];
  const withRobots = deduped.filter((l) => (l.robot_types_needed?.length ?? 0) > 0);
  const pool = withRobots.length >= minVisible ? withRobots : deduped;
  return pool.length ? pool : FALLBACK_POOL;
}

async function fetchLeadPool(minVisible: number): Promise<TickerLead[]> {
  const base = getApiBase();
  const res = await fetch(
    `${base}/api/leads?limit=50&sort=score&exclude_junk=true`,
    liveFetchInit(),
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
  minHeightClass = "min-h-[520px]",
  title = "Live sales leads",
  subtitle = "Robot demand ticker",
  showPipelineLink = false,
  heroVariant = false,
}: ExperimentLeadTickerProps) {
  const [pool, setPool] = useState<TickerLead[]>(FALLBACK_POOL);
  const [visible, setVisible] = useState<TickerRow[]>([]);
  const [live, setLive] = useState(false);
  const poolIndex = useRef(0);
  const tickKey = useRef(0);
  const rowHeightPx = heroVariant ? 68 : 52;

  const seedVisible = useCallback(
    (nextPool: TickerLead[]) => {
      const initial = nextPool.slice(0, maxVisible).map((lead, i) => ({
        ...lead,
        tickKey: tickKey.current++ + lead.id + i,
      }));
      poolIndex.current = initial.length % Math.max(nextPool.length, 1);
      setVisible(initial);
    },
    [maxVisible],
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
        .then((nextPool) => {
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
      setVisible((prev) => {
        const row: TickerRow = { ...next, tickKey: tickKey.current++ };
        return [row, ...prev].slice(0, maxVisible);
      });
    }, tickMs);
    return () => window.clearInterval(timer);
  }, [pool, maxVisible, tickMs]);

  const tickSec = Math.round(tickMs / 1000);
  const isHero = heroVariant;

  return (
    <div
      className={`flex w-full flex-col overflow-hidden rounded-xl border shadow-2xl ${minHeightClass}`}
      style={{
        background: isHero ? PANEL_BG : "linear-gradient(165deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)",
        borderColor: isHero ? "rgba(255,255,255,0.14)" : "rgba(255,255,255,0.1)",
        boxShadow: isHero
          ? "0 32px 80px -24px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,176,0,0.08) inset"
          : "0 24px 64px -12px rgba(124,58,237,0.12), 0 0 0 1px rgba(255,255,255,0.06) inset",
      }}
    >
      <div
        className={`flex shrink-0 items-center justify-between border-b px-5 ${isHero ? "py-5" : "py-4"}`}
        style={{
          background: isHero ? "#1f1f1f" : "rgba(124,58,237,0.12)",
          borderColor: isHero ? "rgba(255,176,0,0.22)" : "rgba(255,255,255,0.08)",
        }}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {isHero && <Zap className="h-4 w-4 shrink-0" style={{ color: AMBER }} strokeWidth={2.5} />}
            <p
              className={`truncate font-semibold ${isHero ? "text-lg" : "text-sm text-white"}`}
              style={{
                fontFamily: "'Sora', system-ui, sans-serif",
                color: isHero ? AMBER : undefined,
                letterSpacing: isHero ? "-0.02em" : undefined,
              }}
            >
              {title}
            </p>
          </div>
          <p
            className={`mt-1 uppercase tracking-[0.16em] ${isHero ? "text-[11px] font-medium text-white/55" : "text-[10px] text-violet-200/70"}`}
          >
            {subtitle}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span
            className="flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest"
            style={{
              color: SUPABASE_GREEN,
              background: "rgba(62,207,142,0.1)",
              borderColor: "rgba(62,207,142,0.35)",
            }}
          >
            <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: SUPABASE_GREEN }} />
            Live
          </span>
          <span
            className="hidden rounded-md border border-white/10 bg-black/30 px-2 py-1 font-mono text-[10px] text-white/45 sm:inline"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            {live ? "API" : "Demo"}
          </span>
        </div>
      </div>

      <div className="relative shrink-0 overflow-hidden" style={{ minHeight: `${maxVisible * rowHeightPx + 12}px` }}>
        <div
          className="pointer-events-none absolute inset-x-0 top-0 z-10 h-10 bg-gradient-to-b to-transparent"
          style={{ backgroundImage: `linear-gradient(to bottom, ${PANEL_BG}, transparent)` }}
        />
        <div
          className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-12 bg-gradient-to-t to-transparent"
          style={{ backgroundImage: `linear-gradient(to top, ${PANEL_BG}, transparent)` }}
        />

        <ul className="relative h-full overflow-hidden px-4 py-3" aria-live="polite" aria-label="Latest sales leads and robot types">
          <AnimatePresence initial={false} mode="popLayout">
            {visible.map((lead) => {
              const tier = (lead.priority_tier || "WARM").toUpperCase();
              const st = tierStyle[tier] || tierStyle.WARM;
              return (
                <motion.li
                  key={lead.tickKey}
                  layout
                  initial={{ opacity: 0, y: -18, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 12, height: 0, marginBottom: 0, paddingTop: 0, paddingBottom: 0 }}
                  transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                  className={`mb-2 overflow-hidden rounded-lg border px-3.5 ${isHero ? "py-3" : "py-2.5"}`}
                  style={{
                    background: isHero ? ROW_BG : "rgba(255,255,255,0.025)",
                    borderColor: isHero ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.06)",
                  }}
                >
                  <div className="flex min-w-0 items-start justify-between gap-2">
                    <p className={`truncate font-semibold leading-tight text-white ${isHero ? "text-[14px]" : "text-[13px]"}`}>
                      {lead.company_name}
                    </p>
                    <span
                      className="shrink-0 rounded-md border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide"
                      style={{ color: st.color, background: st.bg, borderColor: st.border }}
                    >
                      {tier}
                    </span>
                  </div>
                  {lead.industry && (
                    <p className="mt-0.5 truncate text-[10px] font-medium uppercase tracking-wide text-white/40">
                      {lead.industry}
                    </p>
                  )}
                  <p
                    className={`mt-1.5 line-clamp-2 leading-snug ${isHero ? "text-[12px]" : "text-[11px]"}`}
                    style={{ color: isHero ? "rgba(62,207,142,0.92)" : "rgba(153,246,228,0.75)" }}
                  >
                    {robotLine(lead)}
                  </p>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
      </div>

      <div
        className="shrink-0 border-t px-4 py-3.5"
        style={{
          background: isHero ? "#1a1a1a" : "rgba(124,58,237,0.06)",
          borderColor: isHero ? "rgba(255,255,255,0.1)" : "rgba(255,255,255,0.08)",
        }}
      >
        {showPipelineLink ? (
          <Link
            href="/pipeline"
            className="inline-flex items-center gap-1.5 text-sm font-semibold transition-colors hover:brightness-110"
            style={{ color: AMBER }}
          >
            View full pipeline
            <ChevronRight className="h-4 w-4" />
          </Link>
        ) : (
          <p className="text-[10px] text-white/35">
            New lead every {tickSec}s · {maxVisible} visible · oldest rolls off the bottom
          </p>
        )}
      </div>
    </div>
  );
}
