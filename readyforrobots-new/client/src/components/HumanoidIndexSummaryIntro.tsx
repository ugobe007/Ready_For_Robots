import { RefreshCw } from "lucide-react";
import { humanoidReportPdfUrl } from "@/lib/humanoidIntelligenceReport";
import { RR } from "@/lib/humanoidReportTheme";
import {
  ReportBodyText,
  ReportBtnDownload,
  ReportFindingCard,
  ReportKicker,
  ReportLink,
  ReportPanel,
  ReportTitle,
  ReportDetails,
} from "@/components/humanoid-report/HumanoidReportUI";

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

function fallbackFindings(robotCount: number, leaderName?: string, leaderScore?: number): Finding[] {
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
  const findings =
    keyFindings?.filter((f) => f?.title && f?.body) ??
    fallbackFindings(robotCount, leaderName, leaderScore);

  return (
    <section aria-labelledby="index-summary-heading" className="mx-auto max-w-5xl px-4 pb-4">
      <ReportPanel accent="purple" className="!px-4 !py-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 flex-1">
            <ReportKicker>Monthly report</ReportKicker>
            <ReportTitle id="index-summary-heading">Humanoid readiness & deployment</ReportTitle>
          </div>
          <ReportBtnDownload href={humanoidReportPdfUrl(12)} />
        </div>

        <div className="mt-3 space-y-2.5 border-t pt-3" style={{ borderColor: RR.border }}>
          {REPORT_INTRO.map((paragraph) => (
            <ReportBodyText key={paragraph}>{paragraph}</ReportBodyText>
          ))}
        </div>

        <div className="mt-4">
          <ReportDetails
            summary={
              <span className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: RR.textDim }}>
                Key findings
              </span>
            }
          >
            {loading ? (
              <div className="flex items-center gap-2 text-[13px]" style={{ color: RR.textDim }}>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Loading…
              </div>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {findings.slice(0, 6).map((f) => (
                  <ReportFindingCard key={f.title + f.body.slice(0, 32)} title={f.title} body={f.body} />
                ))}
              </div>
            )}
            <p className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[12px]" style={{ color: RR.textDim }}>
              <ReportLink href="/find-robots">Find robots</ReportLink>
              <span>·</span>
              <ReportLink href="#intelligence-report">Full analysis</ReportLink>
            </p>
          </ReportDetails>
        </div>
      </ReportPanel>
    </section>
  );
}
