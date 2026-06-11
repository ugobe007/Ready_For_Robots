/**
 * Compact daily humanoid recap — 2–3 sentence summary with expandable full debrief.
 * Keeps the scrolling robot list from burying intelligence content.
 */
import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, ArrowRight } from "lucide-react";
import { Link } from "wouter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  isValidHumanoidReport,
  type HumanoidIntelligenceReportData,
} from "@/lib/humanoidIntelligenceReport";

function recapSummary(report: HumanoidIntelligenceReportData): string {
  const lines = report.executive_summary?.filter(Boolean) || [];
  if (lines.length >= 2) {
    return `${lines[0]} ${lines[1]}`.trim();
  }
  if (lines.length === 1) return lines[0];
  const leader = report.top_ranked?.[0];
  if (leader) {
    return `${leader.name} leads the HEIR index at ${leader.score_total}/100. ${leader.why_top_rank || "Fleet rankings updated from live deployment evidence and spec scoring."}`;
  }
  return "Daily humanoid index refresh — HEIF scores, deployment signals, and vendor momentum.";
}

function debriefParagraphs(report: HumanoidIntelligenceReportData): string[] {
  const out: string[] = [];
  const narrative = report.narrative;
  if (narrative?.market_overview?.length) out.push(...narrative.market_overview.slice(0, 2));
  if (narrative?.deployment_reality?.length) out.push(narrative.deployment_reality[0]);
  if (narrative?.ranking_commentary?.length) out.push(narrative.ranking_commentary[0]);
  if (report.month_over_month?.narrative_bullets?.length) {
    out.push(...report.month_over_month.narrative_bullets.slice(0, 2));
  }
  if (!out.length && report.executive_summary?.length) {
    out.push(...report.executive_summary.slice(0, 4));
  }
  return out.filter(Boolean).slice(0, 6);
}

export default function HumanoidDailyRecap({ className = "" }: { className?: string }) {
  const [report, setReport] = useState<HumanoidIntelligenceReportData | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/humanoid/intelligence-report?top_n=8`, liveFetchInit())
      .then(async (r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (cancelled) return;
        const payload = data?.report;
        if (isValidHumanoidReport(payload)) setReport(payload);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const summary = report ? recapSummary(report) : null;
  const top = report?.top_ranked?.slice(0, 5) || [];
  const findings = report?.narrative?.key_findings?.slice(0, 3) || [];
  const debrief = report ? debriefParagraphs(report) : [];

  return (
    <section className={`px-6 ${className}`.trim()} style={{ background: "#0d0520" }}>
      <div className="max-w-6xl mx-auto">
        <div
          className="rounded-2xl border overflow-hidden"
          style={{
            borderColor: "rgba(124,58,237,0.22)",
            background: "linear-gradient(135deg, rgba(124,58,237,0.08) 0%, rgba(3,218,197,0.04) 100%)",
            boxShadow: "0 0 0 1px rgba(124,58,237,0.08)",
          }}
        >
          <div className="px-5 py-4 sm:px-6 sm:py-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#03DAC5" }}>
                    Daily humanoid recap
                  </p>
                </div>
                <h3
                  className="text-lg font-extrabold text-white sm:text-xl"
                  style={{ fontFamily: "'Sora', system-ui, sans-serif" }}
                >
                  {report?.title || "HEIR Humanoid Intelligence"}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-white/55" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                  {loading
                    ? "Loading today's index movement and deployment signals…"
                    : summary || "Independent HEIF scoring across the humanoid fleet — updated daily."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="inline-flex shrink-0 items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold transition-all hover:bg-white/5"
                style={{ borderColor: "rgba(124,58,237,0.35)", color: "#c4b5fd" }}
                aria-expanded={expanded}
              >
                {expanded ? "Collapse debrief" : "Read full debrief"}
                {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              </button>
            </div>

            {expanded && report && (
              <div
                className="mt-5 pt-5 border-t space-y-5"
                style={{ borderColor: "rgba(124,58,237,0.15)" }}
              >
                {debrief.length > 0 && (
                  <div className="space-y-2">
                    {debrief.map((para) => (
                      <p key={para.slice(0, 40)} className="text-sm leading-relaxed text-white/50">
                        {para}
                      </p>
                    ))}
                  </div>
                )}

                {top.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-3 text-white/30">
                      Top rankings today
                    </p>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      {top.map((robot) => (
                        <div
                          key={robot.name}
                          className="rounded-lg border px-3 py-2.5"
                          style={{
                            borderColor: "rgba(255,255,255,0.08)",
                            background: "rgba(0,0,0,0.2)",
                          }}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono text-[10px] text-white/30">#{robot.rank}</span>
                            <span className="font-mono text-sm font-bold" style={{ color: "#03DAC5" }}>
                              {robot.score_total}
                            </span>
                          </div>
                          <p className="text-sm font-semibold text-white truncate mt-1">{robot.name}</p>
                          <p className="text-[10px] text-white/35 truncate">{robot.vendor}</p>
                          <p className="text-[10px] mt-1 truncate" style={{ color: "#a78bfa" }}>
                            {robot.deployment_tier_label}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {findings.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-2 text-white/30">
                      Key findings
                    </p>
                    <ul className="space-y-2">
                      {findings.map((f) => (
                        <li key={f.title} className="text-xs text-white/45">
                          <span className="font-semibold text-white/65">{f.title}: </span>
                          {f.body}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Link
                  href="/robots"
                  className="inline-flex items-center gap-2 text-xs font-bold transition-colors hover:text-white"
                  style={{ color: "#FFB000" }}
                >
                  Open full humanoid index
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
