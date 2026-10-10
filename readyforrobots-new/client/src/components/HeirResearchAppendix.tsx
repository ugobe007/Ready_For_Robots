import {
  HEIF_BENCHMARK,
  HEIR_PULL_QUOTES,
  HEIR_REPORTS,
} from "@/content/heir2026";
import { RR } from "@/lib/humanoidReportTheme";
import {
  ReportBodyText,
  ReportDetails,
  ReportKicker,
  ReportLink,
  ReportSectionLabel,
  ReportTable,
  ReportTitle,
} from "@/components/humanoid-report/HumanoidReportUI";

/** Collapsed-by-default HEIR appendix — full detail stays in the PDFs. */
export default function HeirResearchAppendix() {
  return (
    <section className="mx-auto max-w-5xl px-4 pb-5">
      <ReportDetails
        summary={
          <div
            className="min-w-0 flex-1 rounded-lg -m-1 p-1"
            style={{
              background: `linear-gradient(135deg, ${RR.purpleMuted} 0%, ${RR.tealMuted} 55%, transparent 100%)`,
            }}
          >
            <ReportKicker>HEIR 2026 research</ReportKicker>
            <ReportTitle>Engineering maturity framework</ReportTitle>
            <p
              className="mt-1 text-[13px] leading-snug max-w-2xl"
              style={{ color: RR.textMuted }}
            >
              Demo culture vs deployment reality — HEIF scores and vendor
              analysis in the PDF.
            </p>
          </div>
        }
      >
        <ReportBodyText className="mb-3">
          HEIR measures humanoids by engineering maturity, not demo
          choreography. The Humanoid Engineering Intelligence Framework (HEIF)
          scores mobility, manipulation, cognition, safety, data pipeline, and
          production readiness from public evidence.
        </ReportBodyText>

        <ul className="mb-4 space-y-2">
          {HEIR_PULL_QUOTES.map(q => (
            <li
              key={q}
              className="flex gap-2 text-[13px] leading-snug"
              style={{ color: RR.textMuted }}
            >
              <span className="shrink-0" style={{ color: RR.purple }}>
                —
              </span>
              <span>&ldquo;{q}&rdquo;</span>
            </li>
          ))}
        </ul>

        <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 text-[12px]">
          {HEIR_REPORTS.map(r => (
            <ReportLink key={r.href} href={r.href} external>
              Download {r.title} ↗
            </ReportLink>
          ))}
        </div>

        <ReportSectionLabel>HEIF snapshot · out of 4.0</ReportSectionLabel>
        <ReportTable
          minWidth="520px"
          headers={["Company", "Mob", "Manip", "Cog", "Safety", "Data", "Prod"]}
          rows={HEIF_BENCHMARK.map(row => [
            <span className="font-semibold" style={{ color: RR.text }}>
              {row.company}
            </span>,
            row.mobility.toFixed(1),
            row.manipulation.toFixed(1),
            row.cognition.toFixed(1),
            row.safety.toFixed(1),
            row.dataPipeline.toFixed(1),
            row.production.toFixed(1),
          ])}
        />
        <p className="mt-2 text-[10px]" style={{ color: RR.textDim }}>
          HEIF snapshot for seven vendors from HEIR 2026. The live index applies
          the same framework to all ranked robots.
        </p>
      </ReportDetails>
    </section>
  );
}
