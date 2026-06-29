import { useState } from "react";
import { Link } from "wouter";
import { ArrowRight, Check, Copy, RefreshCw, Share2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import {
  ReportBodyText,
  ReportBtnDownload,
  ReportFindingCard,
  ReportKicker,
  ReportMetric,
  ReportPanel,
  ReportSectionLabel,
  ReportTable,
  ReportTitle,
} from "@/components/humanoid-report/HumanoidReportUI";
import {
  humanoidReportPdfUrl,
  useHumanoidIntelligenceReport,
} from "@/lib/humanoidIntelligenceReport";
import { RR } from "@/lib/humanoidReportTheme";

const TOP_N = 12;
const DIM_KEYS = ["mobility", "manipulation", "cognition", "safety", "data_pipeline", "production"] as const;
const DIM_LABELS: Record<(typeof DIM_KEYS)[number], string> = {
  mobility: "Mobility",
  manipulation: "Manipulation",
  cognition: "Cognition",
  safety: "Safety",
  data_pipeline: "Data",
  production: "Production",
};

function fmtNum(value: unknown): string {
  if (value == null || typeof value === "object") return "—";
  const n = Number(value);
  return Number.isFinite(n) ? String(n) : "—";
}

function fmtPct(value: unknown): string {
  const n = Number(value);
  return Number.isFinite(n) ? `${n}%` : "—";
}

function tealNum(v: unknown) {
  return (
    <span className="font-mono font-semibold tabular-nums" style={{ color: RR.teal }}>
      {fmtNum(v)}
    </span>
  );
}

function heifCell(v: number | undefined) {
  if (v == null || !Number.isFinite(v)) return "—";
  const pct = (v / 4) * 100;
  return (
    <div className="min-w-[72px]">
      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: RR.teal }} />
      </div>
      <span className="mt-0.5 block font-mono text-[10px] tabular-nums" style={{ color: RR.textDim }}>
        {v.toFixed(1)}
      </span>
    </div>
  );
}

export default function HumanoidComparisonReport() {
  const { report, loading, error } = useHumanoidIntelligenceReport(TOP_N);
  const [copied, setCopied] = useState(false);
  const metrics = report?.adoption_metrics ?? {};
  const shareUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/robots/report`
      : "https://readyforrobots.com/robots/report";

  async function copyShareLink() {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  const heroStats = report
    ? [
        { label: "Fleet tracked", value: fmtNum(metrics.fleet_total_robots), tone: "emerald" as const },
        { label: "PoC or better", value: fmtPct(metrics.fleet_poc_or_better_pct), tone: "emerald" as const },
        { label: "Top slice", value: fmtNum(metrics.robots_in_top_slice), tone: "white" as const },
        { label: "Deploy signals", value: fmtNum(metrics.fleet_deployment_signal_count), tone: "amber" as const },
      ]
    : undefined;

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <PageHeroDark
        maxWidthClass="max-w-5xl"
        badge={
          <div className="page-hero-badge">
            HEIR 2026 · HEIF benchmarking · Updated monthly
          </div>
        }
        eyebrow="Public intelligence"
        title={
          <>
            Humanoid{" "}
            <span className="text-emerald-400">Comparison Report</span>
          </>
        }
        description="Side-by-side rankings, dimension leaders, vendor deployment signals, and capability vs. field reality — built from our live humanoid index and news evidence."
        stats={heroStats}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <ReportBtnDownload href={humanoidReportPdfUrl(TOP_N)} label="Download PDF" />
            <button
              type="button"
              onClick={() => void copyShareLink()}
              className="inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/5 px-3.5 py-2 text-[12px] font-semibold text-white transition-colors hover:bg-white/10"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Share2 className="h-4 w-4" />}
              {copied ? "Link copied" : "Share report"}
            </button>
            <Link
              href="/robots"
              className="inline-flex items-center gap-1.5 text-[12px] text-slate-400 underline underline-offset-4 decoration-white/20 hover:text-emerald-300"
            >
              Full index <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        }
        innerClassName="pb-8"
      />
      <div className="page-hero-fade" aria-hidden />

      <main className="mx-auto max-w-5xl px-4 py-10">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-16" style={{ color: RR.textDim }}>
            <RefreshCw className="h-5 w-5 animate-spin" />
            Loading comparison data…
          </div>
        )}

        {!loading && error && (
          <ReportPanel accent="none">
            <p className="text-[13px]" style={{ color: RR.textMuted }}>
              {error}
            </p>
            <Link href="/robots" className="mt-3 inline-flex text-[13px] font-semibold text-emerald-700 hover:underline">
              Browse live index instead →
            </Link>
          </ReportPanel>
        )}

        {!loading && !error && report && (
          <div className="space-y-10">
            {/* Social proof strip */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <ReportMetric label="Humanoids indexed" value={fmtNum(metrics.fleet_total_robots)} />
              <ReportMetric label="PoC / pilot / commercial" value={fmtPct(metrics.fleet_poc_or_better_pct)} />
              <ReportMetric label="Named customers (top slice)" value={fmtNum(metrics.robots_with_named_customers_top_slice)} />
              <ReportMetric label="News deployment headlines" value={fmtNum(metrics.news_deployment_headlines_top_slice)} />
            </div>

            {/* Executive summary */}
            {report.executive_summary.length > 0 && (
              <section>
                <ReportKicker>Executive summary</ReportKicker>
                <ReportTitle>What the fleet looks like right now</ReportTitle>
                <ReportPanel accent="purple" className="mt-4">
                  <ul className="space-y-2.5">
                    {report.executive_summary.map((line) => (
                      <li key={line.slice(0, 48)} className="flex gap-2 text-[13px] leading-snug" style={{ color: RR.textMuted }}>
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: RR.teal }} />
                        {line}
                      </li>
                    ))}
                  </ul>
                </ReportPanel>
              </section>
            )}

            {/* Key findings */}
            {report.narrative?.key_findings && report.narrative.key_findings.length > 0 && (
              <section>
                <ReportSectionLabel>Key findings</ReportSectionLabel>
                <div className="grid gap-2 sm:grid-cols-2">
                  {report.narrative.key_findings.map((f) => (
                    <ReportFindingCard key={f.title} title={f.title} body={f.body} />
                  ))}
                </div>
              </section>
            )}

            {/* Head-to-head table */}
            <section>
              <ReportKicker>Head-to-head</ReportKicker>
              <ReportTitle id="comparison-table">Top {TOP_N} humanoids compared</ReportTitle>
              <p className="mt-1 text-[13px]" style={{ color: RR.textDim }}>
                HEIF dimensions (0–4) and composite index (0–100). Index ≈ HEIF × 25.
              </p>
              <div className="mt-4">
                <ReportTable
                  minWidth="920px"
                  headers={["#", "Robot", "Index", "HEIF", "Tier", ...DIM_KEYS.map((k) => DIM_LABELS[k])]}
                  rows={report.top_ranked.map((r) => [
                    r.rank,
                    <>
                      <span className="font-semibold" style={{ color: RR.text }}>
                        {r.name}
                      </span>
                      <span className="block text-[10px]" style={{ color: RR.textDim }}>
                        {r.vendor}
                      </span>
                    </>,
                    tealNum(Math.round(r.score_total)),
                    r.heif_total.toFixed(1),
                    r.deployment_tier_label,
                    ...DIM_KEYS.map((k) => {
                      const dim = r.score_rationale?.[k];
                      return heifCell(dim?.heif);
                    }),
                  ])}
                />
              </div>
            </section>

            {/* Dimension leaders */}
            {report.comparisons?.dimension_leaders && report.comparisons.dimension_leaders.length > 0 && (
              <section>
                <ReportSectionLabel>Dimension leaders</ReportSectionLabel>
                <ReportTable
                  headers={["Dimension", "Leader", "HEIF", "Index"]}
                  rows={report.comparisons.dimension_leaders.map((row) => [
                    row.dimension,
                    <>
                      <span className="font-semibold" style={{ color: RR.text }}>
                        {row.name}
                      </span>
                      <span className="block text-[10px]" style={{ color: RR.textDim }}>
                        {row.vendor}
                      </span>
                    </>,
                    row.heif.toFixed(1),
                    Math.round(row.index_score),
                  ])}
                />
              </section>
            )}

            {/* Peer HEIF matrix */}
            {report.comparisons?.peer_heif_matrix?.robots?.length ? (
              <section>
                <ReportSectionLabel>Peer HEIF matrix</ReportSectionLabel>
                <ReportTable
                  minWidth="640px"
                  headers={[
                    "#",
                    "Robot",
                    "Total",
                    ...(report.comparisons.peer_heif_matrix.dimension_labels ?? DIM_KEYS.map((k) => DIM_LABELS[k])),
                  ]}
                  rows={report.comparisons.peer_heif_matrix.robots.map((row) => [
                    row.rank,
                    <span className="font-semibold" style={{ color: RR.text }}>
                      {row.name}
                    </span>,
                    row.heif_total.toFixed(1),
                    ...DIM_KEYS.map((k) => {
                      const v = row.dimensions?.[k];
                      return v != null ? v.toFixed(1) : "—";
                    }),
                  ])}
                />
              </section>
            ) : null}

            {/* Vendor leaderboard */}
            {report.comparisons?.vendor_leaderboard && report.comparisons.vendor_leaderboard.length > 0 && (
              <section>
                <ReportSectionLabel>Vendor deployment leaderboard</ReportSectionLabel>
                <ReportTable
                  minWidth="560px"
                  headers={["Vendor", "Robots", "PoC+", "PoC %", "Deploy signal", "Deployments"]}
                  rows={report.comparisons.vendor_leaderboard.slice(0, 12).map((row) => [
                    <span className="font-semibold" style={{ color: RR.text }}>
                      {row.vendor}
                    </span>,
                    row.robot_count,
                    row.poc_or_deployment,
                    `${row.poc_or_deployment_pct}%`,
                    row.deployment_signal,
                    row.total_deployments,
                  ])}
                />
              </section>
            )}

            {/* Capability vs deployment */}
            {report.comparisons?.index_vs_deployment && report.comparisons.index_vs_deployment.length > 0 && (
              <section>
                <ReportSectionLabel>Capability vs deployment reality</ReportSectionLabel>
                <ReportTable
                  minWidth="520px"
                  headers={["#", "Robot", "Index", "HEIF", "Tier", "Deployments"]}
                  rows={report.comparisons.index_vs_deployment.map((row) => [
                    row.rank,
                    <span className="font-semibold" style={{ color: RR.text }}>
                      {row.name}
                    </span>,
                    tealNum(Math.round(row.score_total)),
                    row.heif_total.toFixed(1),
                    row.deployment_tier_label,
                    <>
                      {row.commercial_deployments}
                      {row.capability_ahead_of_deployment ? (
                        <span className="ml-1 text-[10px] font-semibold" style={{ color: RR.amber }}>
                          capability gap
                        </span>
                      ) : null}
                    </>,
                  ])}
                />
              </section>
            )}

            {/* Ranking divergence */}
            {report.comparisons?.ranking_divergence && report.comparisons.ranking_divergence.length > 0 && (
              <section>
                <ReportSectionLabel>Index vs deployment-weighted rank</ReportSectionLabel>
                <div className="space-y-2">
                  {report.comparisons.ranking_divergence.slice(0, 6).map((row) => (
                    <ReportPanel key={row.name} accent="teal">
                      <p className="text-[13px] font-bold" style={{ color: RR.text }}>
                        {row.name}
                        <span className="ml-2 font-mono text-[11px] font-normal" style={{ color: RR.textDim }}>
                          index #{row.index_rank} · deploy #{row.deployment_weighted_rank}
                          {row.rank_delta !== 0 ? ` · Δ${row.rank_delta > 0 ? "+" : ""}${row.rank_delta}` : ""}
                        </span>
                      </p>
                      <ReportBodyText className="mt-1">{row.commentary}</ReportBodyText>
                    </ReportPanel>
                  ))}
                </div>
              </section>
            )}

            {/* Methodology + CTA */}
            <section className="rounded-xl border p-6 sm:p-8" style={{ borderColor: RR.border, background: RR.bgElevated }}>
              <ReportKicker>Methodology</ReportKicker>
              <ReportTitle>How we score humanoids</ReportTitle>
              <ReportBodyText className="mt-3">
                HEIF (Humanoid Engineering Intelligence Framework) scores six dimensions from HEIR 2026 research
                benchmarks and published specs. Deployment tiers combine catalog status, commercial deployment counts,
                and English/Chinese news headlines. Customer names are extracted from headlines — verify before citing.
              </ReportBodyText>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-[13px] font-bold text-white transition-colors hover:bg-emerald-700"
                >
                  Get pipeline access <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/pipeline"
                  className="inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-[13px] font-semibold transition-colors hover:bg-white"
                  style={{ borderColor: RR.border, color: RR.text }}
                >
                  Browse live pipeline
                </Link>
                <button
                  type="button"
                  onClick={() => void copyShareLink()}
                  className="inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-[13px] font-semibold transition-colors hover:bg-white"
                  style={{ borderColor: RR.border, color: RR.text }}
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                  {copied ? "Copied!" : "Copy share link"}
                </button>
                <ReportBtnDownload href={humanoidReportPdfUrl(TOP_N)} label="PDF for LinkedIn" compact />
              </div>
            </section>
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
