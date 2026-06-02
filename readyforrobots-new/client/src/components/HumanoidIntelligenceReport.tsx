import { useEffect, useState } from "react";
import { ExternalLink, RefreshCw } from "lucide-react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

const TEAL = "#03DAC5";

type DimRationale = {
  label: string;
  heif: number;
  index_score: number;
  drivers: string[];
};

type TopRobot = {
  rank: number;
  name: string;
  vendor: string;
  score_total: number;
  heif_total: number;
  deployment_tier_label: string;
  why_top_rank: string;
  score_rationale: Record<string, DimRationale>;
  trials_and_pocs: {
    news_trial_headlines: number;
    news_deployment_headlines: number;
    catalog_pilot: boolean;
    estimated_poc_signals: number;
  };
  customer_integrations: {
    catalog_deployment_count: number;
    named_customers: string[];
  };
  top_headlines: { title?: string; url?: string; evidence_level?: string }[];
};

type Report = {
  title: string;
  executive_summary: string[];
  adoption_metrics: Record<string, number | Record<string, number>>;
  customer_landscape: {
    customer: string;
    robots: string[];
    vendors: string[];
    deployment_headlines: number;
    trial_headlines: number;
  }[];
  top_ranked: TopRobot[];
  deployment_summary?: { key_findings?: string[] };
};

export default function HumanoidIntelligenceReport() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [openSlug, setOpenSlug] = useState<string | null>(null);
  const api = getApiBase();

  useEffect(() => {
    setLoading(true);
    fetch(`${api}/api/humanoid/intelligence-report?top_n=12`, liveFetchInit())
      .then((r) => (r.ok ? r.json() : Promise.reject(r)))
      .then((d) => setReport(d.report ?? null))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [api]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-white/30">
        <RefreshCw className="h-4 w-4 animate-spin" /> Loading intelligence report…
      </div>
    );
  }

  if (!report) {
    return (
      <p className="py-12 text-center text-sm text-white/35">
        Intelligence report unavailable. Run humanoid discover + deployment-news on the API first.
      </p>
    );
  }

  const metrics = report.adoption_metrics || {};

  return (
    <div className="space-y-8">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
          Intelligence report
        </p>
        <h2 className="mt-1 text-xl font-bold text-white">{report.title}</h2>
        <ul className="mt-4 space-y-2 text-sm text-white/55 list-disc pl-5">
          {report.executive_summary.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Trial/PoC headlines (top 12)", metrics.news_trial_headlines_top_slice],
          ["Deployment headlines", metrics.news_deployment_headlines_top_slice],
          ["Named customers", metrics.robots_with_named_customers_top_slice],
          ["Catalog deployments (sum)", metrics.catalog_commercial_deployments_sum],
        ].map(([label, value]) => (
          <div
            key={String(label)}
            className="rounded-xl border border-white/10 px-4 py-3"
            style={{ background: "rgba(255,255,255,0.02)" }}
          >
            <p className="text-[10px] uppercase tracking-wider text-white/30">{label}</p>
            <p className="mt-1 text-2xl font-black text-white">{value ?? "—"}</p>
          </div>
        ))}
      </div>

      {report.customer_landscape.length > 0 && (
        <div>
          <h3 className="text-sm font-bold text-white/80 mb-3">Customers in press coverage</h3>
          <div className="flex flex-wrap gap-2">
            {report.customer_landscape.slice(0, 14).map((c) => (
              <span
                key={c.customer}
                className="rounded-full border border-white/10 px-3 py-1 text-[11px] text-white/70"
                style={{ background: "rgba(124,58,237,0.08)" }}
                title={`${c.robots.join(", ")} · ${c.deployment_headlines} deployment / ${c.trial_headlines} trial headlines`}
              >
                {c.customer}
                <span className="ml-1.5 text-white/30">({c.robots.length})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <h3 className="text-sm font-bold text-white/80 mb-3">Why top robots rank high</h3>
        <div className="space-y-2">
          {report.top_ranked.map((robot) => {
            const open = openSlug === robot.name;
            return (
              <div
                key={robot.name}
                className="rounded-xl border overflow-hidden"
                style={{
                  borderColor: open ? "rgba(3,218,197,0.2)" : "rgba(255,255,255,0.08)",
                  background: open ? "rgba(3,218,197,0.04)" : "rgba(255,255,255,0.02)",
                }}
              >
                <button
                  type="button"
                  onClick={() => setOpenSlug(open ? null : robot.name)}
                  className="w-full flex items-center gap-4 px-5 py-4 text-left"
                >
                  <span className="text-lg font-black text-white/20 w-8">#{robot.rank}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-white">{robot.name}</p>
                    <p className="text-[11px] text-white/35">{robot.vendor}</p>
                    <p className="mt-1 text-[12px] text-white/45 line-clamp-2">{robot.why_top_rank}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xl font-black" style={{ color: TEAL }}>
                      {Math.round(robot.score_total)}
                    </p>
                    <p className="text-[10px] text-white/30">HEIF {robot.heif_total.toFixed(1)}</p>
                    <p className="text-[9px] text-violet-300/70 mt-0.5 max-w-[8rem] truncate">
                      {robot.deployment_tier_label}
                    </p>
                  </div>
                </button>

                {open && (
                  <div className="px-5 pb-5 border-t border-white/7 pt-4 grid gap-4 lg:grid-cols-2">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">
                        Trials · PoCs · integrations
                      </p>
                      <ul className="text-[12px] text-white/50 space-y-1">
                        <li>
                          News: {robot.trials_and_pocs.news_trial_headlines} trial/PoC,{" "}
                          {robot.trials_and_pocs.news_deployment_headlines} deployment headlines
                        </li>
                        <li>Catalog deployments: {robot.customer_integrations.catalog_deployment_count}</li>
                        {robot.customer_integrations.named_customers.length > 0 ? (
                          <li>Customers: {robot.customer_integrations.named_customers.join(", ")}</li>
                        ) : (
                          <li>No customer names extracted from headlines yet</li>
                        )}
                      </ul>
                      {robot.top_headlines.length > 0 && (
                        <ul className="mt-3 space-y-1.5">
                          {robot.top_headlines.map((h) => (
                            <li key={h.url || h.title} className="text-[11px]">
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
                                <span className="text-white/55">{h.title}</span>
                              )}
                              {h.evidence_level && (
                                <span className="ml-1 text-white/25">· {h.evidence_level}</span>
                              )}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">
                        Score drivers (HEIF)
                      </p>
                      <div className="space-y-2">
                        {Object.entries(robot.score_rationale).map(([key, dim]) => (
                          <div key={key} className="rounded-lg px-3 py-2 bg-white/[0.03] border border-white/6">
                            <div className="flex justify-between text-[11px]">
                              <span className="font-semibold text-white/70">{dim.label}</span>
                              <span className="font-mono text-white/40">
                                {dim.heif.toFixed(1)} · idx {Math.round(dim.index_score)}
                              </span>
                            </div>
                            <ul className="mt-1 text-[10px] text-white/40 list-disc pl-4">
                              {dim.drivers.slice(0, 3).map((d) => (
                                <li key={d}>{d}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
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
  );
}
