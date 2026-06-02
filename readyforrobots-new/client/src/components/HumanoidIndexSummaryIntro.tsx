import { ChevronDown, Download, RefreshCw } from "lucide-react";
import { humanoidReportPdfUrl } from "@/lib/humanoidIntelligenceReport";

const TEAL = "#03DAC5";

/** Editorial framing for the humanoid index — updated copy from product. */
const REPORT_INTRO: readonly string[] = [
  "In the world of robotics, humanoids show great technical progress. With large funding rounds and new capabilities, humanoids are ready for deployment.",
  "The following report reviews humanoids using the HEIR methodology for benchmarking and a number of market signals tracked by Ready For Robots. We report on the most capable humanoids and examples of their deployments and customer trials.",
  "This market is fluid and quickly changing — we update this report monthly.",
];

type Finding = { title: string; body: string };

type Props = {
  robotCount: number;
  keyFindings: Finding[] | null;
  loading: boolean;
  leaderName?: string;
  leaderScore?: number;
};

function fallbackBullets(robotCount: number, leaderName?: string, leaderScore?: number): string[] {
  const lines: string[] = [];
  if (robotCount > 0) {
    lines.push(
      `Tracking ${robotCount} humanoids in the live index — ranked by HEIF engineering maturity (0–4) and a composite 0–100 score from published specs.`
    );
    if (leaderName != null && leaderScore != null) {
      lines.push(
        `${leaderName} currently leads the index at ${Math.round(leaderScore)}. Scores update as vendor pages and HEIR research benchmarks change.`
      );
    }
  }
  lines.push(
    "Expand any row for dimension breakdowns. Deployment headlines, PoC signals, and customer names are in the analysis section below the rankings."
  );
  return lines;
}

export default function HumanoidIndexSummaryIntro({
  robotCount,
  keyFindings,
  loading,
  leaderName,
  leaderScore,
}: Props) {
  const findings =
    keyFindings?.filter((f) => f?.title && f?.body) ??
    fallbackBullets(robotCount, leaderName, leaderScore).map((body, i) => ({
      title: i === 0 ? "Index snapshot" : "Note",
      body,
    }));

  return (
    <section
      aria-labelledby="index-summary-heading"
      className="mx-auto max-w-5xl px-4 pb-6"
    >
      <div
        className="rounded-xl border px-5 py-5 sm:px-6"
        style={{
          borderColor: "rgba(3,218,197,0.15)",
          background: "linear-gradient(135deg, rgba(3,218,197,0.06) 0%, rgba(124,58,237,0.04) 100%)",
        }}
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
              Summary · updated monthly
            </p>
            <h2
              id="index-summary-heading"
              className="mt-1 text-xl font-bold text-white sm:text-2xl"
              style={{ fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Humanoid readiness & deployment report
            </h2>
          </div>
          <a
            href={humanoidReportPdfUrl(12)}
            download
            className="inline-flex shrink-0 items-center gap-2 rounded-lg border px-4 py-2.5 text-[13px] font-bold transition-colors hover:bg-white/[0.06]"
            style={{ borderColor: "rgba(3,218,197,0.35)", color: TEAL, background: "rgba(3,218,197,0.08)" }}
          >
            <Download className="h-4 w-4" />
            Download PDF
          </a>
        </div>

        <div className="mt-5 w-full space-y-4 text-[15px] sm:text-base leading-[1.7] text-white/58">
          {REPORT_INTRO.map((paragraph) => (
            <p key={paragraph} className="max-w-none">
              {paragraph}
            </p>
          ))}
        </div>

        <details className="group mt-6 rounded-lg border border-white/10 overflow-hidden" style={{ background: "rgba(0,0,0,0.15)" }}>
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3.5 [&::-webkit-details-marker]:hidden hover:bg-white/[0.03]">
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-white/50">
              This month&apos;s snapshot
            </p>
            <ChevronDown className="h-4 w-4 shrink-0 text-white/35 transition-transform group-open:rotate-180" />
          </summary>

          <div className="border-t border-white/8 px-4 pb-4 pt-3">
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-white/35">
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Loading live signals…
              </div>
            ) : (
              <ul className="w-full space-y-4">
                {findings.slice(0, 5).map((f) => (
                  <li key={f.title + f.body.slice(0, 40)} className="text-[15px] sm:text-base leading-[1.65]">
                    <p className="font-semibold text-white/80">{f.title}</p>
                    <p className="mt-1 text-white/58 max-w-none">{f.body}</p>
                  </li>
                ))}
              </ul>
            )}

            <p className="mt-4 text-[13px] text-white/35">
              <a
                href="/find-robots"
                className="text-violet-300/80 hover:text-violet-200 underline underline-offset-4 decoration-white/15"
              >
                Find robots for your operation
              </a>
              {" · "}
              <a
                href="#intelligence-report"
                className="text-violet-300/80 hover:text-violet-200 underline underline-offset-4 decoration-white/15"
              >
                Deployment & score analysis
              </a>
            </p>
          </div>
        </details>
      </div>
    </section>
  );
}
