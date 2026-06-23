/**
 * Compact daily humanoid recap — light emerald theme (matches Precision Intelligence home).
 */
import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, ArrowRight } from "lucide-react";
import { Link } from "wouter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  isValidHumanoidReport,
  type HumanoidIntelligenceReportData,
} from "@/lib/humanoidIntelligenceReport";
import { LiveDot } from "@/components/marketing/primitives";

function recapSummary(report: HumanoidIntelligenceReportData): string {
  const lines = report.executive_summary?.filter(Boolean) || [];
  if (lines.length >= 2) return `${lines[0]} ${lines[1]}`.trim();
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
    <section className={`px-6 bg-slate-50 ${className}`.trim()}>
      <div className="container">
        <div className="rounded-2xl border border-emerald-100 bg-white shadow-sm overflow-hidden">
          <div className="px-5 py-4 sm:px-6 sm:py-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex items-center gap-2">
                  <LiveDot />
                  <p className="section-eyebrow mb-0">Daily humanoid recap</p>
                </div>
                <h3 className="font-display text-lg font-bold text-gray-900 sm:text-xl">
                  {report?.title || "HEIR Humanoid Intelligence"}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  {loading
                    ? "Loading today's index movement and deployment signals…"
                    : summary || "Independent HEIF scoring across the humanoid fleet — updated daily."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs font-bold text-emerald-700 transition-colors hover:bg-emerald-100"
                aria-expanded={expanded}
              >
                {expanded ? "Collapse debrief" : "Read full debrief"}
                {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              </button>
            </div>

            {expanded && report && (
              <div className="mt-5 pt-5 border-t border-gray-100 space-y-5">
                {debrief.length > 0 && (
                  <div className="space-y-2">
                    {debrief.map((para) => (
                      <p key={para.slice(0, 40)} className="text-sm leading-relaxed text-gray-600">
                        {para}
                      </p>
                    ))}
                  </div>
                )}

                {top.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-3 text-gray-400">
                      Top rankings today
                    </p>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      {top.map((robot) => (
                        <div key={robot.name} className="rounded-lg border border-gray-100 bg-slate-50 px-3 py-2.5">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono-data text-[10px] text-gray-400">#{robot.rank}</span>
                            <span className="score-number text-sm">{robot.score_total}</span>
                          </div>
                          <p className="text-sm font-semibold text-gray-900 truncate mt-1">{robot.name}</p>
                          <p className="text-[10px] text-gray-500 truncate">{robot.vendor}</p>
                          <p className="text-[10px] mt-1 truncate text-emerald-600">{robot.deployment_tier_label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {findings.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-2 text-gray-400">Key findings</p>
                    <ul className="space-y-2">
                      {findings.map((f) => (
                        <li key={f.title} className="text-xs text-gray-600">
                          <span className="font-semibold text-gray-800">{f.title}: </span>
                          {f.body}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Link
                  href="/robots"
                  className="inline-flex items-center gap-2 text-xs font-bold text-emerald-600 hover:text-emerald-700"
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
