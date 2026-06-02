import { useState } from "react";
import { ChevronDown, ExternalLink, RefreshCw } from "lucide-react";
import type { HumanoidIntelligenceReportData } from "@/lib/humanoidIntelligenceReport";

const TEAL = "#03DAC5";

function fmtNum(value: unknown): string {
  if (value == null || typeof value === "object") return "—";
  const n = Number(value);
  return Number.isFinite(n) ? String(n) : "—";
}

type Props = {
  report: HumanoidIntelligenceReportData | null;
  loading: boolean;
  error: string | null;
};

export default function HumanoidIntelligenceReport({ report, loading, error }: Props) {
  const [openRobot, setOpenRobot] = useState<string | null>(null);

  return (
    <details className="group rounded-xl border border-white/10 overflow-hidden" style={{ background: "rgba(255,255,255,0.02)" }}>
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 [&::-webkit-details-marker]:hidden">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-white/35">Optional analysis</p>
          <h2 className="mt-1 text-lg font-bold text-white/90">Deployment & score intelligence</h2>
          <p className="mt-1 text-sm text-white/40">
            Per-robot HEIF drivers, PoC/pilot signals, press headlines, and customers (collapsed by default).
          </p>
        </div>
        <ChevronDown className="h-5 w-5 shrink-0 text-white/30 transition-transform group-open:rotate-180" />
      </summary>

      <div className="border-t border-white/8 px-5 pb-6 pt-5">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-white/30">
            <RefreshCw className="h-4 w-4 animate-spin" /> Loading report…
          </div>
        )}

        {!loading && error && (
          <p className="py-8 text-center text-sm text-white/45">{error}</p>
        )}

        {!loading && !error && report && (
          <div className="space-y-8">
            <p className="text-sm text-white/45">
              {report.title || "Humanoid intelligence report"} — metrics and robot-level detail. The summary above
              mirrors the executive snapshot; expand each robot for score drivers and news evidence.
            </p>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Trial/PoC headlines", report.adoption_metrics?.news_trial_headlines_top_slice],
                ["Deployment headlines", report.adoption_metrics?.news_deployment_headlines_top_slice],
                ["Robots with named customers", report.adoption_metrics?.robots_with_named_customers_top_slice],
                ["Catalog deployments (top 12)", report.adoption_metrics?.catalog_commercial_deployments_sum],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-lg border border-white/8 px-3 py-2.5"
                  style={{ background: "rgba(255,255,255,0.02)" }}
                >
                  <p className="text-[10px] uppercase tracking-wider text-white/30">{label}</p>
                  <p className="mt-1 text-xl font-black text-white">{fmtNum(value)}</p>
                </div>
              ))}
            </div>

            {(report.customer_landscape?.length ?? 0) > 0 && (
              <div>
                <h4 className="text-sm font-bold text-white/80 mb-2">Customers in press coverage</h4>
                <div className="flex flex-wrap gap-2">
                  {report.customer_landscape
                    .filter((c) => c?.customer)
                    .slice(0, 14)
                    .map((c) => (
                      <span
                        key={c.customer}
                        className="rounded-full border border-white/10 px-3 py-1 text-[11px] text-white/70"
                        style={{ background: "rgba(124,58,237,0.08)" }}
                      >
                        {c.customer}
                        <span className="ml-1.5 text-white/30">({(c.robots ?? []).length})</span>
                      </span>
                    ))}
                </div>
              </div>
            )}

            <div>
              <h4 className="text-sm font-bold text-white/80 mb-2">Why top robots rank high</h4>
              <div className="space-y-2">
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
                      className="rounded-lg border overflow-hidden"
                      style={{
                        borderColor: open ? "rgba(3,218,197,0.2)" : "rgba(255,255,255,0.08)",
                        background: open ? "rgba(3,218,197,0.04)" : "rgba(255,255,255,0.02)",
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => setOpenRobot(open ? null : robot.name)}
                        className="w-full flex items-center gap-4 px-4 py-3 text-left"
                      >
                        <span className="text-base font-black text-white/20 w-7">#{robot.rank}</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-white text-sm">{robot.name}</p>
                          <p className="text-[11px] text-white/35">{robot.vendor}</p>
                          {robot.why_top_rank ? (
                            <p className="mt-1 text-[11px] text-white/45 line-clamp-2">{robot.why_top_rank}</p>
                          ) : null}
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-lg font-black" style={{ color: TEAL }}>
                            {fmtNum(robot.score_total)}
                          </p>
                          <p className="text-[10px] text-white/30">
                            HEIF {Number(robot.heif_total ?? 0).toFixed(1)}
                          </p>
                        </div>
                      </button>

                      {open && (
                        <div className="px-4 pb-4 border-t border-white/7 pt-3 grid gap-4 lg:grid-cols-2">
                          <div className="text-[12px] text-white/50 space-y-1">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-1">
                              Trials · PoCs · integrations
                            </p>
                            <p>
                              News: {fmtNum(trials.news_trial_headlines)} trial/PoC,{" "}
                              {fmtNum(trials.news_deployment_headlines)} deployment headlines
                            </p>
                            <p>Catalog deployments: {fmtNum(customers.catalog_deployment_count)}</p>
                            <p>
                              {customers.named_customers?.length
                                ? `Customers: ${customers.named_customers.join(", ")}`
                                : "No customer names in headlines yet — run deployment-news scan on API"}
                            </p>
                            {(robot.top_headlines ?? [])
                              .filter((h) => h?.title)
                              .slice(0, 4)
                              .map((h) => (
                                <p key={h.url || h.title} className="pt-1">
                                  {h.url ? (
                                    <a
                                      href={h.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-violet-300/90 hover:text-violet-200 inline-flex items-center gap-1"
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
                            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">
                              Score drivers (HEIF)
                            </p>
                            <div className="space-y-2">
                              {Object.entries(rationale).map(([key, dim]) => {
                                if (!dim?.label) return null;
                                return (
                                  <div
                                    key={key}
                                    className="rounded-lg px-3 py-2 bg-white/[0.03] border border-white/6"
                                  >
                                    <div className="flex justify-between text-[11px]">
                                      <span className="font-semibold text-white/70">{dim.label}</span>
                                      <span className="font-mono text-white/40">
                                        {Number(dim.heif ?? 0).toFixed(1)} · idx{" "}
                                        {Math.round(Number(dim.index_score ?? 0))}
                                      </span>
                                    </div>
                                    <ul className="mt-1 text-[10px] text-white/40 list-disc pl-4">
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
      </div>
    </details>
  );
}
