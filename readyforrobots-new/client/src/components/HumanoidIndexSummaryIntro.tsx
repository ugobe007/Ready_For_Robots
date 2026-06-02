import { RefreshCw } from "lucide-react";

const TEAL = "#03DAC5";

/** Editorial framing for the humanoid index — updated copy from product. */
const REPORT_INTRO: readonly string[] = [
  "In the world of robotics, humanoids show great technical progress. With large funding rounds and new capabilities, humanoids are ready for deployment.",
  "The following report reviews humanoids using the HEIR methodology for benchmarking and a number of market signals tracked by Ready For Robots. We report on the most capable humanoids and examples of their deployments and customer trials.",
  "This market is fluid and quickly changing — we update this report monthly.",
];

type Props = {
  robotCount: number;
  summaryLines: string[] | null;
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
  summaryLines,
  loading,
  leaderName,
  leaderScore,
}: Props) {
  const snapshotBullets =
    summaryLines?.filter((line): line is string => Boolean(line && String(line).trim())) ??
    fallbackBullets(robotCount, leaderName, leaderScore);

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
        <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
          Summary · updated monthly
        </p>
        <h2
          id="index-summary-heading"
          className="mt-1 text-lg font-bold text-white/95"
          style={{ fontFamily: "'Sora', system-ui, sans-serif" }}
        >
          Humanoid readiness & deployment report
        </h2>

        <div className="mt-4 max-w-3xl space-y-3 text-sm leading-relaxed text-white/55">
          {REPORT_INTRO.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>

        <p className="mt-6 text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">
          This month&apos;s snapshot
        </p>

        {loading ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-white/35">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            Loading live signals…
          </div>
        ) : (
          <ul className="mt-3 space-y-2.5 max-w-3xl">
            {snapshotBullets.slice(0, 5).map((line) => (
              <li key={line} className="flex gap-2.5 text-sm leading-relaxed text-white/62">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full" style={{ background: TEAL }} />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        )}

        <p className="mt-5 text-[12px] text-white/32">
          <a
            href="#intelligence-report"
            className="text-violet-300/80 hover:text-violet-200 underline underline-offset-4 decoration-white/15"
          >
            Deployment & score analysis
          </a>
          {" "}
          — per-robot HEIF drivers, trials, press headlines, and named customers.
        </p>
      </div>
    </section>
  );
}
