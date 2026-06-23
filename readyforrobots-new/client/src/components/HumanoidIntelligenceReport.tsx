import { useState } from "react";
import { ExternalLink, RefreshCw } from "lucide-react";
import type { HumanoidIntelligenceReportData } from "@/lib/humanoidIntelligenceReport";
import { humanoidReportPdfUrl } from "@/lib/humanoidIntelligenceReport";
import { RR } from "@/lib/humanoidReportTheme";
import {
  ReportBodyText,
  ReportBtnDownload,
  ReportDetails,
  ReportFindingCard,
  ReportKicker,
  ReportMetric,
  ReportPanel,
  ReportSectionLabel,
  ReportTable,
  ReportTitle,
} from "@/components/humanoid-report/HumanoidReportUI";

function fmtNum(value: unknown): string {
  if (value == null || typeof value === "object") return "—";
  const n = Number(value);
  return Number.isFinite(n) ? String(n) : "—";
}

function tealNum(v: unknown) {
  return <span className="font-mono font-semibold tabular-nums" style={{ color: RR.teal }}>{fmtNum(v)}</span>;
}

type Props = {
  report: HumanoidIntelligenceReportData | null;
  loading: boolean;
  error: string | null;
};

export default function HumanoidIntelligenceReport({ report, loading, error }: Props) {
  const [openRobot, setOpenRobot] = useState<string | null>(null);

  return (
    <section id="intelligence-report" className="mx-auto max-w-5xl px-4 pb-8">
      <ReportDetails
        summary={
          <div className="min-w-0">
            <ReportKicker>Optional analysis</ReportKicker>
            <ReportTitle>Deployment & score intelligence</ReportTitle>
            <p className="mt-0.5 text-[12px]" style={{ color: RR.textDim }}>
              HEIF drivers, PoC signals, headlines, customers
            </p>
          </div>
        }
      >
        {loading && (
          <div className="flex items-center justify-center gap-2 py-8" style={{ color: RR.textDim }}>
            <RefreshCw className="h-4 w-4 animate-spin" /> Loading…
          </div>
        )}

        {!loading && error && <p className="py-6 text-center text-[13px]" style={{ color: RR.textMuted }}>{error}</p>}

        {!loading && !error && report && (
          <div className="space-y-5">
            {report.narrative?.market_overview && report.narrative.market_overview.length > 0 && (
              <ReportPanel accent="purple">
                <ReportSectionLabel>Market overview</ReportSectionLabel>
                {report.narrative.market_overview.map((p) => (
                  <ReportBodyText key={p.slice(0, 48)} className="mb-2 last:mb-0">
                    {p}
                  </ReportBodyText>
                ))}
              </ReportPanel>
            )}

            {report.month_over_month?.has_prior && (report.month_over_month.narrative_bullets?.length ?? 0) > 0 && (
              <ReportPanel accent="teal">
                <ReportSectionLabel>Vs last month ({report.month_over_month.previous_period})</ReportSectionLabel>
                <ul className="space-y-1.5">
                  {(report.month_over_month.narrative_bullets ?? []).map((line) => (
                    <li key={line} className="text-[13px] leading-snug" style={{ color: RR.textMuted }}>
                      {line}
                    </li>
                  ))}
                </ul>
                {(report.month_over_month.new_to_top10?.length ?? 0) > 0 && (
                  <p className="mt-2 text-[11px]" style={{ color: RR.textDim }}>
                    Entered top 10: {(report.month_over_month.new_to_top10 ?? []).join(", ")}
                  </p>
                )}
              </ReportPanel>
            )}

            {report.narrative?.key_findings && report.narrative.key_findings.length > 0 && (
              <div>
                <ReportSectionLabel>Key findings</ReportSectionLabel>
                <div className="grid gap-2 sm:grid-cols-2">
                  {report.narrative.key_findings.map((f) => (
                    <ReportFindingCard key={f.title} title={f.title} body={f.body} />
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[12px]" style={{ color: RR.textDim }}>
                {report.subtitle || report.title}
              </p>
              <ReportBtnDownload href={humanoidReportPdfUrl(12)} label="Download PDF" compact />
            </div>

            {report.comparisons?.dimension_leaders && report.comparisons.dimension_leaders.length > 0 && (
              <div>
                <ReportSectionLabel>HEIF dimension leaders</ReportSectionLabel>
                <ReportTable
                  headers={["Dimension", "Robot", "HEIF", "Index"]}
                  rows={report.comparisons.dimension_leaders.map((row) => [
                    row.dimension,
                    <>
                      <span className="font-semibold" style={{ color: RR.text }}>{row.name}</span>
                      <span className="block text-[10px]" style={{ color: RR.textDim }}>{row.vendor}</span>
                    </>,
                    row.heif.toFixed(1),
                    Math.round(row.index_score),
                  ])}
                />
              </div>
            )}

            {report.comparisons?.index_vs_deployment && report.comparisons.index_vs_deployment.length > 0 && (
              <div>
                <ReportSectionLabel>Capability vs deployment</ReportSectionLabel>
                <ReportTable
                  minWidth="520px"
                  headers={["#", "Robot", "Index", "HEIF", "Tier", "Depl."]}
                  rows={report.comparisons.index_vs_deployment.map((row) => [
                    row.rank,
                    <span className="font-semibold" style={{ color: RR.text }}>{row.name}</span>,
                    tealNum(Math.round(row.score_total)),
                    row.heif_total.toFixed(1),
                    row.deployment_tier_label,
                    <>
                      {row.commercial_deployments}
                      {row.capability_ahead_of_deployment ? (
                        <span className="ml-1" style={{ color: RR.amber }}>· gap</span>
                      ) : null}
                    </>,
                  ])}
                />
              </div>
            )}

            {report.narrative?.ranking_commentary && report.narrative.ranking_commentary.length > 0 && (
              <div>
                <ReportSectionLabel>Ranking commentary</ReportSectionLabel>
                <ul className="space-y-1.5">
                  {report.narrative.ranking_commentary.map((line) => (
                    <li key={line} className="text-[13px] leading-snug" style={{ color: RR.textMuted }}>
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.comparisons?.ranking_divergence && report.comparisons.ranking_divergence.length > 0 && (
              <div>
                <ReportSectionLabel>Index vs deployment rank</ReportSectionLabel>
                <ReportTable
                  headers={["Robot", "Index #", "Depl. #", "Note"]}
                  rows={report.comparisons.ranking_divergence.map((row) => [
                    row.name,
                    row.index_rank,
                    row.deployment_weighted_rank,
                    row.commentary,
                  ])}
                />
              </div>
            )}

            {report.comparisons?.vendor_leaderboard && report.comparisons.vendor_leaderboard.length > 0 && (
              <div>
                <ReportSectionLabel>Vendor deployment</ReportSectionLabel>
                <div className="flex flex-wrap gap-1.5">
                  {report.comparisons.vendor_leaderboard.slice(0, 10).map((v) => (
                    <span
                      key={v.vendor}
                      className="rounded-md border px-2.5 py-1.5 text-[10px]"
                      style={{ borderColor: RR.border, background: RR.purpleMuted, color: RR.textMuted }}
                    >
                      <span className="font-semibold" style={{ color: RR.text }}>{v.vendor}</span>
                      <span className="ml-1.5" style={{ color: RR.textDim }}>
                        {v.deployment_signal} commercial · {v.total_deployments} depl.
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
              {[
                ["Trial/PoC news", report.adoption_metrics?.news_trial_headlines_top_slice],
                ["Deployment news", report.adoption_metrics?.news_deployment_headlines_top_slice],
                ["Named customers", report.adoption_metrics?.robots_with_named_customers_top_slice],
                ["Catalog depl.", report.adoption_metrics?.catalog_commercial_deployments_sum],
              ].map(([label, value]) => (
                <ReportMetric key={String(label)} label={String(label)} value={fmtNum(value)} />
              ))}
            </div>

            {(report.customer_landscape?.length ?? 0) > 0 && (
              <div>
                <ReportSectionLabel>Customers in press</ReportSectionLabel>
                <div className="flex flex-wrap gap-1.5">
                  {report.customer_landscape
                    .filter((c) => c?.customer)
                    .slice(0, 14)
                    .map((c) => (
                      <span
                        key={c.customer}
                        className="rounded-full border px-2.5 py-0.5 text-[10px]"
                        style={{ borderColor: RR.purpleBorder, background: RR.purpleMuted, color: RR.textMuted }}
                      >
                        {c.customer}
                        <span className="ml-1" style={{ color: RR.textDim }}>
                          ({(c.robots ?? []).length})
                        </span>
                      </span>
                    ))}
                </div>
              </div>
            )}

            <div>
              <ReportSectionLabel>Why top robots rank high</ReportSectionLabel>
              <div className="space-y-1.5">
                {report.top_ranked.map((robot) => {
                  if (!robot?.name) return null;
                  const open = openRobot === robot.name;
                  const rationale = robot.score_rationale ?? {};
                  const trials = robot.trials_and_pocs ?? {
                    news_trial_headlines: 0,
                    news_deployment_headlines: 0,
                  };
                  const customers = robot.customer_integrations ?? {
                    catalog_deployment_count: 0,
                    named_customers: [],
                  };

                  return (
                    <div
                      key={robot.name}
                      className="rounded-md border overflow-hidden"
                      style={{
                        borderColor: open ? RR.tealBorder : RR.border,
                        background: open ? RR.tealMuted : RR.bg,
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => setOpenRobot(open ? null : robot.name)}
                        className="flex w-full items-center gap-3 px-3 py-2.5 text-left"
                      >
                        <span className="w-6 text-sm font-black tabular-nums" style={{ color: RR.textDim }}>
                          #{robot.rank}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[13px] font-bold" style={{ color: RR.text }}>
                            {robot.name}
                          </p>
                          <p className="text-[10px]" style={{ color: RR.textDim }}>
                            {robot.vendor}
                          </p>
                          {robot.why_top_rank ? (
                            <p className="mt-0.5 line-clamp-1 text-[11px]" style={{ color: RR.textMuted }}>
                              {robot.why_top_rank}
                            </p>
                          ) : null}
                        </div>
                        <div className="shrink-0 text-right">
                          <p className="text-base font-black tabular-nums" style={{ color: RR.teal }}>
                            {fmtNum(robot.score_total)}
                          </p>
                          <p className="text-[9px]" style={{ color: RR.textDim }}>
                            HEIF {Number(robot.heif_total ?? 0).toFixed(1)}
                          </p>
                        </div>
                      </button>

                      {open && (
                        <div
                          className="grid gap-3 border-t px-3 pb-3 pt-2.5 lg:grid-cols-2"
                          style={{ borderColor: RR.border }}
                        >
                          <div className="text-[11px] space-y-1" style={{ color: RR.textMuted }}>
                            <p className="text-[9px] font-bold uppercase tracking-wider" style={{ color: RR.textDim }}>
                              Trials · PoCs · integrations
                            </p>
                            <p>
                              News: {fmtNum(trials.news_trial_headlines)} trial/PoC,{" "}
                              {fmtNum(trials.news_deployment_headlines)} deployment
                            </p>
                            <p>Catalog deployments: {fmtNum(customers.catalog_deployment_count)}</p>
                            <p>
                              {customers.named_customers?.length
                                ? `Customers: ${customers.named_customers.join(", ")}`
                                : "No named customers in headlines yet"}
                            </p>
                            {(robot.top_headlines ?? [])
                              .filter((h) => h?.title)
                              .slice(0, 3)
                              .map((h) => (
                                <p key={h.url || h.title}>
                                  {h.url ? (
                                    <a
                                      href={h.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 hover:underline"
                                      style={{ color: "rgba(167,139,250,0.95)" }}
                                    >
                                      {h.title}
                                      <ExternalLink className="h-3 w-3 opacity-50" />
                                    </a>
                                  ) : (
                                    h.title
                                  )}
                                </p>
                              ))}
                          </div>
                          <div>
                            <p className="text-[9px] font-bold uppercase tracking-wider mb-1.5" style={{ color: RR.textDim }}>
                              Score drivers
                            </p>
                            <div className="space-y-1.5">
                              {Object.entries(rationale).map(([key, dim]) => {
                                if (!dim?.label) return null;
                                return (
                                  <div
                                    key={key}
                                    className="rounded-md border px-2.5 py-1.5"
                                    style={{ borderColor: RR.border, background: RR.bgElevated }}
                                  >
                                    <div className="flex justify-between text-[10px]">
                                      <span className="font-semibold" style={{ color: RR.textMuted }}>
                                        {dim.label}
                                      </span>
                                      <span className="font-mono tabular-nums" style={{ color: RR.textDim }}>
                                        {Number(dim.heif ?? 0).toFixed(1)} · {Math.round(Number(dim.index_score ?? 0))}
                                      </span>
                                    </div>
                                    <ul className="mt-0.5 list-disc pl-3.5 text-[10px]" style={{ color: RR.textDim }}>
                                      {(dim.drivers ?? []).slice(0, 3).map((d) => (
                                        <li key={d}>{d}</li>
                                      ))}
                                    </ul>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </ReportDetails>
    </section>
  );
}
