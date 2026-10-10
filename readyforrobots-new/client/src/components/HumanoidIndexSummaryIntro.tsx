import { useState } from "react";
import { Link } from "wouter";
import { ChevronDown, RefreshCw } from "lucide-react";
import { humanoidReportPdfUrl } from "@/lib/humanoidIntelligenceReport";
import { ReportBtnDownload } from "@/components/humanoid-report/HumanoidReportUI";

const REPORT_INTRO: readonly string[] = [
  "In the world of robotics, humanoids show great technical progress. With large funding rounds and new capabilities, humanoids are ready for deployment.",
  "The following report reviews humanoids using the HEIR methodology for benchmarking and market signals tracked by Ready For Robots.",
  "Updated monthly as vendors ship and field evidence accumulates.",
];

type Finding = { title: string; body: string };

type Props = {
  robotCount: number;
  keyFindings: Finding[] | null;
  loading: boolean;
  leaderName?: string;
  leaderScore?: number;
};

function fallbackFindings(
  robotCount: number,
  leaderName?: string,
  leaderScore?: number
): Finding[] {
  const lines: Finding[] = [];
  if (robotCount > 0) {
    lines.push({
      title: "Index snapshot",
      body: `Tracking ${robotCount} humanoids — HEIF maturity (0–4) and composite index (0–100) from published specs.`,
    });
    if (leaderName != null && leaderScore != null) {
      lines.push({
        title: "Current leader",
        body: `${leaderName} leads at ${Math.round(leaderScore)}. Scores refresh as catalogs and HEIR benchmarks update.`,
      });
    }
  }
  lines.push({
    title: "Deep dive",
    body: "Expand ranked rows below for dimensions; optional analysis covers trials, customers, and score drivers.",
  });
  return lines;
}

export default function HumanoidIndexSummaryIntro({
  robotCount,
  keyFindings,
  loading,
  leaderName,
  leaderScore,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const findings =
    keyFindings?.filter(f => f?.title && f?.body) ??
    fallbackFindings(robotCount, leaderName, leaderScore);

  return (
    <section
      aria-labelledby="index-summary-heading"
      className="mx-auto max-w-5xl px-4 pb-2"
    >
      <div className="humanoid-report-dark">
        <div className="flex items-start justify-between gap-3">
          <button
            type="button"
            onClick={() => setExpanded(open => !open)}
            aria-expanded={expanded}
            aria-controls="index-summary-body"
            className="flex min-w-0 flex-1 items-start gap-2 text-left"
          >
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-emerald-400">
                Monthly report
              </p>
              <h2
                id="index-summary-heading"
                className="mt-0.5 text-base font-bold tracking-tight text-white sm:text-lg"
                style={{ fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
              >
                Humanoid readiness & deployment
              </h2>
            </div>
            <ChevronDown
              className={`mt-1 h-4 w-4 shrink-0 text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
              aria-hidden
            />
          </button>
          <ReportBtnDownload href={humanoidReportPdfUrl(12)} compact />
        </div>

        {expanded && (
          <div id="index-summary-body">
            <div className="mt-3 space-y-2.5 border-t border-white/10 pt-3">
              {REPORT_INTRO.map(paragraph => (
                <p
                  key={paragraph}
                  className="text-[13px] leading-relaxed text-slate-300"
                >
                  {paragraph}
                </p>
              ))}
            </div>

            <div className="mt-4 border-t border-white/10 pt-4 pb-1">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
                Key findings
              </p>
              {loading ? (
                <div className="mt-3 flex items-center gap-2 text-[13px] text-slate-500">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Loading…
                </div>
              ) : (
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {findings.slice(0, 6).map(f => (
                    <div
                      key={f.title + f.body.slice(0, 32)}
                      className="rounded-lg border border-white/10 bg-white/[0.04] p-3"
                    >
                      <p className="text-[11px] font-bold uppercase tracking-wide text-emerald-400">
                        {f.title}
                      </p>
                      <p className="mt-1 text-[12px] leading-relaxed text-slate-300">
                        {f.body}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              <p className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-slate-500">
                <Link
                  href="/robots/report"
                  className="font-semibold text-emerald-400 hover:text-emerald-300"
                >
                  Shareable comparison report
                </Link>
                <span>·</span>
                <a
                  href="/find-robots"
                  className="font-semibold text-emerald-400 hover:text-emerald-300"
                >
                  Find robots
                </a>
                <span>·</span>
                <a
                  href="#intelligence-report"
                  className="font-semibold text-emerald-400 hover:text-emerald-300"
                >
                  Full analysis
                </a>
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
