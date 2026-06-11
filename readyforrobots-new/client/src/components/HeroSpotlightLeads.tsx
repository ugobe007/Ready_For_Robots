/**
 * Hero right panel — live SIGNAL-ranked sales leads with typewriter reveal.
 * Palette aligned with ScoutWorkflowAnimation (#130d2a shell, purple/teal accents).
 */
import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import { Link } from "wouter";
import {
  fetchWithTimeout,
  getApiBase,
  publicFetchInit,
  readSurfaceCache,
  writeSurfaceCache,
} from "@/lib/apiBase";
import {
  dedupeHomepageLeads,
  HOMEPAGE_SPOTLIGHT_CACHE_KEY,
  HOMEPAGE_SPOTLIGHT_CACHE_TTL_MS,
} from "@/lib/homepageLeads";
import { cleanAndClampText, leadPreviewSentences } from "@/lib/text";
import { useSequentialTypewriter } from "@/hooks/useTypewriter";
import type { HomepageLeadRow } from "@/components/HeroLivePipeline";

const TYPE_SPEED_MS = 95;
const SEGMENT_GAP_MS = 1_500;
const START_DELAY_MS = 900;
const PAUSE_AFTER_MS = 15_000;
const EMERALD = "#34d399";

const SIGNAL_KEYWORDS = [
  "AMR",
  "AGV",
  "CapEx",
  "OSHA",
  "RFP",
  "automation",
  "labor",
  "expansion",
  "pilot",
  "warehouse",
  "humanoid",
  "cobot",
  "palletizing",
  "compliance",
  "staffing",
  "distribution",
  "fleet scale",
  "service robot",
  "collaborative arm",
  "delivery",
  "buying signal",
  "Robot fit",
  "Outreach",
  "vendor selection",
  "procurement",
];

type ParsedSummary = {
  opener: string;
  drivers: string;
  schedule: string;
  robotFit: string;
};

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightTerms(text: string, extraTerms: string[] = []) {
  if (!text) return null;
  const terms = [...new Set([...SIGNAL_KEYWORDS, ...extraTerms].filter((t) => t && t.length > 1))].sort(
    (a, b) => b.length - a.length,
  );
  if (!terms.length) return text;

  const re = new RegExp(`(${terms.map(escapeRegex).join("|")})`, "gi");
  const parts = text.split(re);

  return parts.map((part, i) => {
    const hit = terms.some((t) => t.toLowerCase() === part.toLowerCase());
    if (!hit) return <Fragment key={i}>{part}</Fragment>;
    return (
      <span key={i} style={{ color: EMERALD, fontWeight: 600 }}>
        {part}
      </span>
    );
  });
}

function isBrokenTimingLabel(label: string): boolean {
  const t = label.trim();
  if (!t) return true;
  if (/^20\d{2}$/.test(t)) return true;
  if (/^\d{1,4}$/.test(t)) return true;
  return false;
}

function humanizeReason(text: string): string {
  const t = text.trim();
  if (!t) return "";
  if (/[a-z]/.test(t) && /[A-Z]/.test(t) && !t.includes(" ")) return t;
  if (t.includes("_")) {
    return t
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return t;
}

function parseShareSummary(summary: string): ParsedSummary {
  const raw = (summary || "").trim();
  if (!raw) return { opener: "", drivers: "", schedule: "", robotFit: "" };

  const sentences = raw.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
  let opener = sentences[0] || "";
  let drivers = "";
  let schedule = "";
  let robotFit = "";

  for (const sentence of sentences.slice(1)) {
    if (/what'?s driving it/i.test(sentence)) {
      drivers = sentence.replace(/^what'?s driving it:\s*/i, "").replace(/\.$/, "").trim();
    } else if (/good fit for/i.test(sentence)) {
      robotFit = sentence.replace(/^good fit for\s*/i, "").replace(/\.$/, "").trim();
    } else if (/worth engaging/i.test(sentence)) {
      /* decision-maker line — skip */
    } else if (
      /vendor selection|partner conversations|build-out|procurement|high-intent|evaluation cycles|timing of the project|roughly \d+/i.test(
        sentence,
      )
    ) {
      schedule = sentence.replace(/\.$/, "").trim();
    }
  }

  return { opener, drivers, schedule, robotFit };
}

function signalLine(lead: HomepageLeadRow): string {
  for (const sig of lead.signals || []) {
    const raw = sig.display_text || sig.raw_text || "";
    const text = leadPreviewSentences(raw, 2, 280) || cleanAndClampText(raw, 280);
    if (!text || text.length < 18) continue;
    const label = sig.signal_label?.trim();
    return label ? `${label}: ${text}` : text;
  }
  return cleanAndClampText(lead.industry, 100) || "Automation buying signal detected";
}

function whySalesLeadLine(lead: HomepageLeadRow, parsed: ParsedSummary): string {
  const why = lead.lead_highlights?.why_lead?.find((item) => item && item.trim());
  if (why) return cleanAndClampText(why, 280) || why;
  if (parsed.opener) return parsed.opener;
  const summary = leadPreviewSentences(lead.share_summary, 2, 320);
  if (summary) return summary;
  const problem = cleanAndClampText(lead.lead_highlights?.specific_problem, 220);
  if (problem) return problem;
  const need = cleanAndClampText(lead.core_need, 200);
  if (need) return need;
  const tier = (lead.priority_tier || "HOT").toUpperCase();
  return `SIGNAL classified this as a ${tier} lead from live automation intent signals.`;
}

function driversLine(lead: HomepageLeadRow, parsed: ParsedSummary): string {
  if (parsed.drivers) return parsed.drivers;
  const labels = (lead.signals || [])
    .map((s) => s.signal_label?.trim())
    .filter((label): label is string => Boolean(label));
  const unique = [...new Set(labels)].slice(0, 4);
  if (unique.length) return unique.join(" · ");
  const reasons = (lead.priority_reasons || [])
    .map((r) => humanizeReason(String(r)))
    .filter((r) => r && !/quarantined|junk|false positive|buyer opportunity gate/i.test(r))
    .slice(0, 3);
  if (reasons.length) return reasons.join(" · ");
  return "Automation intent, operational pressure, and deployment signals in the corpus.";
}

function scheduleLine(lead: HomepageLeadRow, parsed: ParsedSummary): string {
  const pt = lead.project_timing;
  if (pt?.day_min != null && pt?.day_max != null) {
    const label = pt.label && !isBrokenTimingLabel(pt.label) ? ` (${pt.label})` : "";
    return `Outreach window: ${pt.day_min}–${pt.day_max} days${label}.`;
  }
  if (pt?.label && !isBrokenTimingLabel(pt.label)) {
    return `Outreach window: ${pt.label}.`;
  }
  if (parsed.schedule && !isBrokenTimingLabel(parsed.schedule)) return parsed.schedule;
  const tier = (lead.priority_tier || "WARM").toUpperCase();
  if (tier === "HOT") {
    return "High-intent window — partner conversations often start within 60–90 days.";
  }
  return "Evaluation and vendor selection cycles typically run 90–210 days.";
}

function robotFitLine(lead: HomepageLeadRow, parsed: ParsedSummary): string {
  const robots = (lead.robot_types_needed || []).slice(0, 3);
  if (robots.length) return robots.join(" · ");
  if (parsed.robotFit) return parsed.robotFit;
  return "";
}

function scoreOf(lead: HomepageLeadRow | undefined): number | string {
  const v = lead?.score?.overall_score;
  return v != null ? Math.round(Number(v)) : "—";
}

const tierColors: Record<string, string> = {
  HOT: "#03DAC5",
  WARM: "#FFB000",
  COLD: "#a78bfa",
};

const FALLBACK: HomepageLeadRow[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    industry: "Logistics",
    priority_tier: "HOT",
    score: { overall_score: 84 },
    share_summary:
      "Lineage is expanding cold-chain capacity while labor stays tight across DC operations. What's driving it: public automation news, new locations or capacity growth, and fresh investment to deploy. Vendor selection could move in the next 60–90 days. Good fit for mobile robots (AMRs), palletizing robots, and pick-and-place robots.",
    priority_reasons: ["Expansion signal", "Labor shortage", "CapEx intent"],
    project_timing: { label: "vendor selection", day_min: 60, day_max: 90, source: "estimated" },
    signals: [{ signal_label: "Expansion", display_text: "New distribution centers and automation CapEx signals." }],
    robot_types_needed: ["Mobile robots (AMRs)", "Palletizing robots"],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels Corp.",
    industry: "Hospitality",
    priority_tier: "HOT",
    score: { overall_score: 79 },
    share_summary:
      "Hyatt is piloting service robots as housekeeping labor pressure builds across flagship properties. What's driving it: staffing pressure, new locations or capacity growth, and robots already going in. Partner conversations often start within 75–120 days. Good fit for service robots, cleaning robots, and delivery robots.",
    priority_reasons: ["Labor shortage", "Pilot deployment"],
    project_timing: { label: "pilot expansion", day_min: 75, day_max: 120, source: "estimated" },
    signals: [{ signal_label: "Labor", display_text: "Staffing crisis and property expansion in key markets." }],
    robot_types_needed: ["Service robots", "Cleaning robots"],
  },
  {
    id: -3,
    company_name: "White Castle",
    industry: "Food Service",
    priority_tier: "WARM",
    score: { overall_score: 71 },
    share_summary:
      "White Castle to set up 1,000 automated kiosks to sell sliders. What's driving it: public automation news, new locations or capacity growth, and fresh investment to deploy. Build-out and evaluation cycles here typically run 90–210 days. Good fit for humanoid robots, robotic chefs / automated kitchen systems, and kitchen automation robots.",
    priority_reasons: ["Expansion", "Automation intent"],
    project_timing: { label: "rollout build-out", day_min: 90, day_max: 210, source: "estimated" },
    signals: [{ signal_label: "Expansion", display_text: "Automated kiosk rollout and slider automation at scale." }],
    robot_types_needed: ["Humanoid robots", "Robotic chefs / automated kitchen systems"],
  },
];

const PANEL_SECTIONS = [
  { label: "Signal", accent: "rgba(255,255,255,0.28)", boxed: false },
  { label: "Why this is a sales lead", accent: "#a78bfa", boxed: true },
  { label: "Key drivers", accent: "#FFB000", boxed: false },
  { label: "Outreach window", accent: "#03DAC5", boxed: false },
  { label: "Robot fit", accent: "#34d399", boxed: false },
] as const;

function initialSpotlightLeads(): HomepageLeadRow[] {
  const cached = readSurfaceCache<HomepageLeadRow[]>(
    HOMEPAGE_SPOTLIGHT_CACHE_KEY,
    HOMEPAGE_SPOTLIGHT_CACHE_TTL_MS,
  );
  const rows = dedupeHomepageLeads(cached?.data);
  return rows.length >= 2 ? rows.slice(0, 10) : [];
}

export default function HeroSpotlightLeads() {
  const bootLeads = initialSpotlightLeads();
  const [leads, setLeads] = useState<HomepageLeadRow[]>(bootLeads);
  /** loading = waiting for API; live = API/cache rows; demo = static fallback only after fetch miss */
  const [panelMode, setPanelMode] = useState<"loading" | "live" | "demo">(
    bootLeads.length >= 2 ? "live" : "loading",
  );
  const [idx, setIdx] = useState(0);
  const [fade, setFade] = useState(false);
  const pendingLeadsRef = useRef<HomepageLeadRow[] | null>(null);
  const leadCycleKeyRef = useRef("");
  const panelModeRef = useRef(panelMode);
  panelModeRef.current = panelMode;

  const pool =
    leads.length >= 2 ? leads : panelMode === "demo" ? FALLBACK : [];
  const lead =
    pool.length > 0 ? pool[idx % pool.length] : undefined;
  const leadCycleKey = `${idx}:${lead?.id ?? ""}:${lead?.company_name ?? ""}`;
  leadCycleKeyRef.current = leadCycleKey;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const base = getApiBase();
        const r = await fetchWithTimeout(
          `${base}/api/leads/homepage`,
          publicFetchInit(),
          12_000,
          { publicCache: true },
        );
        if (!r.ok || cancelled) return;
        const data = (await r.json()) as { hotLeads?: HomepageLeadRow[] };
        const rows = dedupeHomepageLeads(
          Array.isArray(data.hotLeads) ? data.hotLeads.filter((l) => l.company_name) : [],
        ).slice(0, 10);
        if (rows.length < 2 || cancelled) {
          if (panelModeRef.current === "loading" && !cancelled) {
            setPanelMode("demo");
          }
          return;
        }
        writeSurfaceCache(HOMEPAGE_SPOTLIGHT_CACHE_KEY, rows);
        if (panelModeRef.current === "loading" || leads.length < 2) {
          if (!cancelled) {
            setLeads(rows);
            setPanelMode("live");
            setIdx(0);
          }
          return;
        }
        if (!cancelled) {
          pendingLeadsRef.current = rows;
        }
      } catch {
        if (panelModeRef.current === "loading" && !cancelled) {
          setPanelMode("demo");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [pauseKey, setPauseKey] = useState(0);

  const parsed = useMemo(
    () => parseShareSummary(lead?.share_summary || ""),
    [lead?.share_summary],
  );

  const segments = useMemo(() => {
    if (!lead) return [];
    const parts = [
      signalLine(lead),
      whySalesLeadLine(lead, parsed),
      driversLine(lead, parsed),
      scheduleLine(lead, parsed),
    ];
    const fit = robotFitLine(lead, parsed);
    if (fit) parts.push(fit);
    return parts.filter(Boolean);
  }, [lead, parsed]);

  const typed = useSequentialTypewriter(
    segments,
    TYPE_SPEED_MS,
    SEGMENT_GAP_MS,
    START_DELAY_MS,
    lead ? leadCycleKey : "loading",
  );
  const tier = (lead?.priority_tier || "HOT").toUpperCase();
  const tierColor = tierColors[tier] || tierColors.HOT;

  const highlightExtras = useMemo(() => {
    const signalLabel = lead?.signals?.[0]?.signal_label || "";
    const robots = lead?.robot_types_needed || [];
    const drivers = driversLine(lead || ({} as HomepageLeadRow), parsed).split(/[·,]/).map((s) => s.trim());
    return [signalLabel, tier, ...robots, ...drivers].filter(Boolean) as string[];
  }, [lead, parsed, tier]);

  useEffect(() => {
    if (!typed.allDone || pool.length < 2 || segments.length < 1) return undefined;
    const cycleKey = leadCycleKey;
    const timer = window.setTimeout(() => {
      if (leadCycleKeyRef.current !== cycleKey) return;
      setFade(true);
      window.setTimeout(() => {
        if (leadCycleKeyRef.current !== cycleKey) {
          setFade(false);
          return;
        }
        if (pendingLeadsRef.current) {
          setLeads(pendingLeadsRef.current);
          pendingLeadsRef.current = null;
          setPanelMode("live");
          setIdx(0);
        } else {
          setIdx((i) => (i + 1) % pool.length);
        }
        setFade(false);
        setPauseKey((k) => k + 1);
      }, 320);
    }, PAUSE_AFTER_MS);
    return () => window.clearTimeout(timer);
  }, [typed.allDone, pauseKey, leadCycleKey, pool.length, segments.length]);

  return (
    <div
      className="flex flex-col overflow-hidden w-full min-h-[540px]"
      style={{
        background: "#130d2a",
        border: "1px solid rgba(124,58,237,0.2)",
        borderRadius: "16px",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        boxShadow:
          "0 0 0 1px rgba(124,58,237,0.1), 0 0 40px rgba(124,58,237,0.08), 0 24px 48px rgba(0,0,0,0.5)",
        opacity: fade ? 0.35 : 1,
        transition: "opacity 0.35s ease",
      }}
    >
      {/* Title bar */}
      <div
        className="flex items-center justify-between px-4 py-2.5 shrink-0"
        style={{
          background: "rgba(124,58,237,0.06)",
          borderBottom: "1px solid rgba(124,58,237,0.15)",
        }}
      >
        <div className="flex items-center gap-1.5" aria-hidden>
          <span className="h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
          <span className="h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
          <span className="h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
        </div>
        <span className="rfr-scout-wordmark text-[10px] text-white/40">signal · live leads</span>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
          <span className="text-[11px] font-bold" style={{ color: "#03DAC5" }}>
            LIVE
          </span>
        </div>
      </div>

      {/* Lead header — instant (no typewriter) */}
      <div
        className="px-4 py-3 shrink-0"
        style={{
          borderBottom: "1px solid rgba(124,58,237,0.12)",
          background: "rgba(124,58,237,0.06)",
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-bold text-white truncate" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              {lead?.company_name || (pool.length ? "—" : "Loading live leads…")}
            </p>
            <p className="text-[11px] text-white/35 mt-0.5 truncate">{lead?.industry || "Market signal"}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span
              className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-sm"
              style={{
                color: tierColor,
                background: `${tierColor}1a`,
                border: `1px solid ${tierColor}55`,
              }}
            >
              {tier}
            </span>
            <span className="text-lg font-bold tabular-nums" style={{ color: "#03DAC5" }}>
              {scoreOf(lead)}
            </span>
          </div>
        </div>
      </div>

      {/* Typed content — structured sections */}
      <div className="flex-1 flex flex-col gap-2.5 px-4 py-3.5 min-h-[320px] overflow-y-auto">
        {pool.length === 0 ? (
          <p className="text-[12px] text-white/40 leading-relaxed">Syncing live sales leads from SIGNAL…</p>
        ) : null}
        {PANEL_SECTIONS.map((section, sectionIdx) => {
          if (sectionIdx >= segments.length) return null;
          const text =
            typed.allDone && segments[sectionIdx]
              ? segments[sectionIdx]
              : typed.segments[sectionIdx] || "";
          const isActive = typed.segmentIdx === sectionIdx && !typed.allDone;
          const body = (
            <p
              className="text-[12px] leading-relaxed text-white/75"
              style={{ fontFamily: sectionIdx === 1 ? "'Inter', system-ui, sans-serif" : undefined }}
            >
              {highlightTerms(text, highlightExtras)}
              {isActive && (
                <span
                  className="inline-block w-[6px] h-[1em] ml-0.5 align-middle animate-pulse"
                  style={{ background: EMERALD }}
                />
              )}
            </p>
          );

          if (section.boxed) {
            return (
              <div
                key={section.label}
                className="rounded-md px-3 py-2.5"
                style={{
                  background: "rgba(124,58,237,0.06)",
                  border: "1px solid rgba(124,58,237,0.15)",
                }}
              >
                <p
                  className="text-[10px] font-bold uppercase tracking-widest mb-1.5 rfr-scout-wordmark"
                  style={{ color: section.accent }}
                >
                  {section.label}
                </p>
                {body}
              </div>
            );
          }

          return (
            <div key={section.label}>
              <p
                className="text-[10px] font-bold uppercase tracking-widest mb-1"
                style={{ color: section.accent }}
              >
                {section.label}
              </p>
              {body}
            </div>
          );
        })}
      </div>

      {/* Rotation indicator */}
      <div
        className="px-4 py-2 flex items-center justify-between shrink-0"
        style={{ borderTop: "1px solid rgba(124,58,237,0.1)", background: "rgba(0,0,0,0.15)" }}
      >
        <div className="flex gap-1">
          {pool.map((item, i) => (
            <span
              key={item.id ?? i}
              className="h-1 rounded-full transition-all duration-300"
              style={{
                width: i === idx % pool.length ? 16 : 6,
                background: i === idx % pool.length ? "#03DAC5" : "rgba(255,255,255,0.15)",
              }}
            />
          ))}
        </div>
        <span className="text-[10px] text-white/25">
          {panelMode === "live" ? "API" : panelMode === "demo" ? "Demo" : "…"} ·{" "}
          {pool.length ? `${(idx % pool.length) + 1}/${pool.length}` : "—"}
        </span>
      </div>

      {/* Footer links */}
      <div
        className="px-4 py-3 flex items-center justify-between gap-3 shrink-0"
        style={{
          borderTop: "1px solid rgba(124,58,237,0.12)",
          background: "rgba(124,58,237,0.08)",
        }}
      >
        <Link
          href="/pipeline"
          className="text-[11px] font-bold flex items-center gap-1 transition-colors hover:text-white"
          style={{ color: "#03DAC5" }}
        >
          Pipeline
          <ChevronRight className="h-3 w-3" />
        </Link>
        <Link
          href="/how-it-works"
          className="text-[11px] font-bold flex items-center gap-1 text-white/45 transition-colors hover:text-white/80"
        >
          How it works
          <ChevronRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
