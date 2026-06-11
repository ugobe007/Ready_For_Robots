/**
 * Hero right panel — live SCOUT-ranked sales leads with typewriter reveal and 10s rotation.
 * Palette aligned with ScoutWorkflowAnimation (#130d2a shell, purple/teal accents).
 */
import { useEffect, useMemo, useState } from "react";
import { ChevronRight } from "lucide-react";
import { Link } from "wouter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanAndClampText, leadPreviewSentences } from "@/lib/text";
import { useSequentialTypewriter } from "@/hooks/useTypewriter";
import type { HomepageLeadRow } from "@/components/HeroLivePipeline";

const ROTATE_MS = 10_000;

const FALLBACK: HomepageLeadRow[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    industry: "Logistics",
    priority_tier: "HOT",
    score: { overall_score: 84 },
    share_summary:
      "Lineage is expanding cold-chain capacity while labor stays tight across DC operations — a strong window for AMRs and pallet automation before the next RFP cycle.",
    signals: [{ signal_label: "Expansion", display_text: "New distribution centers and automation CapEx signals." }],
    robot_types_needed: ["AMR", "Palletizing"],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels Corp.",
    industry: "Hospitality",
    priority_tier: "HOT",
    score: { overall_score: 79 },
    share_summary:
      "Housekeeping labor pressure and multi-property expansion are pushing Hyatt toward service robots and back-of-house automation with near-term pilot budgets.",
    signals: [{ signal_label: "Labor", display_text: "Staffing crisis and property expansion in key markets." }],
    robot_types_needed: ["Service robot", "Delivery AMR"],
  },
  {
    id: -3,
    company_name: "Pepsi Beverage Co.",
    industry: "Food Processing",
    priority_tier: "WARM",
    score: { overall_score: 71 },
    share_summary:
      "OSHA pressure on packaging lines plus CapEx mentions point to collaborative arms and line-side automation — buyer intent is building, not yet at fleet scale.",
    signals: [{ signal_label: "Compliance", display_text: "OSHA citation and packaging line automation interest." }],
    robot_types_needed: ["Collaborative arm"],
  },
];

function leadWriteup(lead: HomepageLeadRow): string {
  const summary = leadPreviewSentences(lead.share_summary, 3, 420);
  if (summary) return summary;
  const signal = cleanAndClampText(lead.signals?.[0]?.display_text, 200);
  if (signal) return signal;
  return cleanAndClampText(lead.core_need, 200) || "SCOUT scored high automation intent from live market signals.";
}

function signalLine(lead: HomepageLeadRow): string {
  const label = lead.signals?.[0]?.signal_label;
  const text = cleanAndClampText(lead.signals?.[0]?.display_text, 120);
  if (label && text) return `${label} · ${text}`;
  if (text) return text;
  return cleanAndClampText(lead.industry, 80) || "Buying signal detected";
}

function scoreOf(lead: HomepageLeadRow): number | string {
  const v = lead.score?.overall_score;
  return v != null ? Math.round(Number(v)) : "—";
}

const tierColors: Record<string, string> = {
  HOT: "#03DAC5",
  WARM: "#FFB000",
  COLD: "#a78bfa",
};

export default function HeroSpotlightLeads() {
  const [leads, setLeads] = useState<HomepageLeadRow[]>(FALLBACK);
  const [idx, setIdx] = useState(0);
  const [live, setLive] = useState(false);
  const [fade, setFade] = useState(false);

  const lead = leads[idx % leads.length];

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const base = getApiBase();
        const r = await fetch(`${base}/api/leads/homepage`, liveFetchInit());
        if (!r.ok || cancelled) return;
        const raw = await r.text();
        if (raw.trimStart().startsWith("<")) return;
        const data = JSON.parse(raw) as { hotLeads?: HomepageLeadRow[] };
        const rows = Array.isArray(data.hotLeads) ? data.hotLeads.filter((l) => l.company_name) : [];
        if (rows.length >= 2 && !cancelled) {
          setLeads(rows.slice(0, 10));
          setLive(true);
        }
      } catch {
        /* fallback */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (leads.length < 2) return undefined;
    const timer = window.setInterval(() => {
      setFade(true);
      window.setTimeout(() => {
        setIdx((i) => (i + 1) % leads.length);
        setFade(false);
      }, 320);
    }, ROTATE_MS);
    return () => window.clearInterval(timer);
  }, [leads.length]);

  const segments = useMemo(() => {
    if (!lead) return [];
    const robots = (lead.robot_types_needed || []).slice(0, 3).join(" · ");
    const parts = [
      signalLine(lead),
      leadWriteup(lead),
    ];
    if (robots) parts.push(`Robot fit: ${robots}`);
    return parts.filter(Boolean);
  }, [lead]);

  const typed = useSequentialTypewriter(segments, 22, 240);
  const tier = (lead?.priority_tier || "HOT").toUpperCase();
  const tierColor = tierColors[tier] || tierColors.HOT;

  return (
    <div
      className="flex flex-col overflow-hidden w-full min-h-[420px]"
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
        <span className="rfr-scout-wordmark text-[10px] text-white/40">scout · live leads</span>
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
              {lead?.company_name}
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

      {/* Typed content — top to bottom */}
      <div className="flex-1 flex flex-col gap-3 px-4 py-4 min-h-[200px]">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: "rgba(255,255,255,0.28)" }}>
            Signal
          </p>
          <p className="text-[12px] leading-relaxed text-white/70 min-h-[2.5rem]">
            {typed.segments[0] || ""}
            {typed.segmentIdx === 0 && !typed.allDone && (
              <span className="inline-block w-[6px] h-[1em] ml-0.5 align-middle animate-pulse" style={{ background: "#03DAC5" }} />
            )}
          </p>
        </div>

        <div
          className="rounded-md px-3 py-3 flex-1"
          style={{
            background: "rgba(124,58,237,0.06)",
            border: "1px solid rgba(124,58,237,0.15)",
          }}
        >
          <p className="text-[10px] font-bold uppercase tracking-widest mb-2 rfr-scout-wordmark" style={{ color: "#a78bfa" }}>
            Why SCOUT ranked this lead
          </p>
          <p className="text-[12px] leading-relaxed text-white/75 min-h-[4.5rem]" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            {typed.segments[1] || (typed.segmentIdx >= 1 ? "" : "")}
            {typed.segmentIdx === 1 && !typed.allDone && (
              <span className="inline-block w-[6px] h-[1em] ml-0.5 align-middle animate-pulse" style={{ background: "#03DAC5" }} />
            )}
          </p>
        </div>

        {segments.length > 2 && (
          <div>
            <p className="text-[11px] text-white/45 min-h-[1.25rem]">
              {typed.segments[2] || ""}
              {typed.segmentIdx === 2 && !typed.allDone && (
                <span className="inline-block w-[6px] h-[1em] ml-0.5 align-middle animate-pulse" style={{ background: "#FFB000" }} />
              )}
            </p>
          </div>
        )}
      </div>

      {/* Rotation indicator */}
      <div
        className="px-4 py-2 flex items-center justify-between shrink-0"
        style={{ borderTop: "1px solid rgba(124,58,237,0.1)", background: "rgba(0,0,0,0.15)" }}
      >
        <div className="flex gap-1">
          {leads.map((_, i) => (
            <span
              key={i}
              className="h-1 rounded-full transition-all duration-300"
              style={{
                width: i === idx % leads.length ? 16 : 6,
                background: i === idx % leads.length ? "#03DAC5" : "rgba(255,255,255,0.15)",
              }}
            />
          ))}
        </div>
        <span className="text-[10px] text-white/25">
          {live ? "API" : "Demo"} · {(idx % leads.length) + 1}/{leads.length}
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
