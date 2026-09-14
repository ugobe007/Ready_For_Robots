import { useState } from "react";
import { Link, useRoute } from "wouter";
import {
  Award,
  CheckCircle2,
  ChevronRight,
  Clock,
  Copy,
  Check,
  Download,
  ExternalLink,
  Layers,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
  Building2,
  Zap,
} from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import {
  INDUSTRY_BENCHMARKS,
  getBenchmarkForIndustry,
  type IndustryBenchmarkDataset,
} from "@/lib/industryBenchmarkingData";

export default function IndustryBenchmarkingReport() {
  const [, params] = useRoute("/reports/benchmarking/:industry");
  const initialIndustry = params?.industry || "hospitality";
  const [selectedIndustry, setSelectedIndustry] = useState<string>(initialIndustry);
  const [copiedLink, setCopiedLink] = useState(false);

  const report: IndustryBenchmarkDataset =
    getBenchmarkForIndustry(selectedIndustry);

  const copyShareableLink = () => {
    const url = `${window.location.origin}/reports/benchmarking/${report.id}`;
    void navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleDownloadPdf = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  return (
    <div className="min-h-screen bg-[#060d1f] text-slate-100 font-sans selection:bg-emerald-500 selection:text-white">
      <style>{`
        @media print {
          .no-print, header, footer, nav { display: none !important; }
          body { background: #ffffff !important; color: #000000 !important; }
          main { padding-top: 0 !important; max-width: 100% !important; }
          .print-header { display: block !important; margin-bottom: 20px; border-bottom: 2px solid #10b981; pb-3; }
          .print-border { border: 1px solid #cccccc !important; background: #f8fafc !important; color: #000000 !important; }
          table { width: 100% !important; border-collapse: collapse !important; color: #000000 !important; }
          th, td { border: 1px solid #dddddd !important; padding: 8px !important; color: #000000 !important; }
          th { background: #f1f5f9 !important; color: #000000 !important; font-weight: bold !important; }
        }
      `}</style>
      <div className="no-print">
        <ExperimentHeader />
      </div>

      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        {/* Printable Header Banner */}
        <div className="hidden print-header">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-black text-black">ReadyForRobots</h2>
            <span className="text-xs font-semibold text-gray-600">Executive Industry Benchmarking Report · 2026</span>
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="no-print mb-6 flex items-center gap-2 text-xs text-slate-400">
          <Link href="/pipeline" className="hover:text-emerald-400 transition">
            Workspace
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-600" />
          <span>Industry Benchmarking Reports</span>
          <ChevronRight className="h-3 w-3 text-slate-600" />
          <span className="font-semibold text-emerald-300">{report.title}</span>
        </div>

        {/* Hero Title & Actions */}
        <div className="mb-8 flex flex-wrap items-start justify-between gap-6 border-b border-slate-800 pb-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-950/60 px-3.5 py-1 text-xs font-bold text-emerald-300 backdrop-blur-md no-print">
              <Award className="h-3.5 w-3.5 text-amber-400" />
              Comparative Industry Benchmarks · 2026 Edition
            </div>
            <h1 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">
              {report.title}
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-300">
              {report.subtitle}
            </p>
          </div>

          <div className="no-print flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={copyShareableLink}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-xs font-semibold text-slate-200 transition hover:border-emerald-500/50 hover:bg-slate-700 hover:text-white"
            >
              {copiedLink ? (
                <>
                  <Check className="h-4 w-4 text-emerald-400" />
                  Link Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 text-slate-400" />
                  Copy Shareable Report Link
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleDownloadPdf}
              className="inline-flex items-center gap-2 rounded-xl border border-emerald-500 bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-emerald-500 shadow-lg shadow-emerald-950/50"
            >
              <Download className="h-4 w-4" />
              Download Full Report (PDF)
            </button>
          </div>
        </div>

        {/* Industry Selector Tabs */}
        <div className="no-print mb-8 flex flex-wrap gap-2 rounded-2xl border border-slate-800 bg-[#0b162c] p-2 shadow-xl">
          {Object.values(INDUSTRY_BENCHMARKS).map(item => {
            const active = report.id === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedIndustry(item.id)}
                className={`rounded-xl px-4 py-2 text-xs font-bold transition ${
                  active
                    ? "border border-emerald-500/50 bg-emerald-600 text-white shadow-md shadow-emerald-950/50"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                {item.id.charAt(0).toUpperCase() + item.id.slice(1)}
              </button>
            );
          })}
        </div>

        {/* Key Metrics Cards */}
        <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-800 bg-[#0c1836] p-5 shadow-lg">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-rose-400">
              <Users className="h-4 w-4" />
              Industry Vacancy Rate
            </div>
            <div className="mt-2 text-3xl font-black text-white">
              {report.labor_vacancy_rate}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Chronic front-line labor deficit across target accounts.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0c1836] p-5 shadow-lg">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
              <TrendingUp className="h-4 w-4" />
              Physical Strain Reduction
            </div>
            <div className="mt-2 text-3xl font-black text-emerald-300">
              {report.avg_strain_reduction}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Average manual transport offloaded to autonomous workcells.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0c1836] p-5 shadow-lg">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
              <Clock className="h-4 w-4" />
              Avg Payback Period
            </div>
            <div className="mt-2 text-3xl font-black text-amber-300">
              {report.avg_payback_months} Months
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Average time to full capital payback and positive cash flow.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0c1836] p-5 shadow-lg">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-sky-400">
              <Building2 className="h-4 w-4" />
              Target Enterprise Accounts
            </div>
            <div className="mt-2 text-xl font-bold text-slate-100 truncate">
              {report.target_accounts.length} Key Accounts
            </div>
            <p className="mt-1 text-[11px] text-slate-400 truncate">
              {report.target_accounts.slice(0, 2).join(", ")}...
            </p>
          </div>
        </div>

        {/* Overview Section */}
        <div className="mb-10 rounded-2xl border border-slate-800 bg-[#0b162c] p-6 shadow-xl">
          <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-emerald-400" />
            Executive Industry Summary
          </h2>
          <p className="text-sm leading-relaxed text-slate-300">
            {report.overview}
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-400">Target Accounts Evaluated:</span>
            {report.target_accounts.map(acc => (
              <span
                key={acc}
                className="rounded-lg bg-slate-800/80 px-2.5 py-1 text-xs font-semibold text-slate-200 border border-slate-700/60"
              >
                {acc}
              </span>
            ))}
          </div>
        </div>

        {/* Comparative Platform Specs Matrix */}
        <div className="mb-12">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-emerald-400" />
              Comparative Robot Platform Spec Matrix
            </h2>
            <span className="text-xs text-slate-400">
              Showing {report.platforms.length} evaluated OEM platforms
            </span>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-[#0b162c] shadow-2xl">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3.5">Vendor & Model</th>
                  <th className="px-4 py-3.5">Category</th>
                  <th className="px-4 py-3.5">Payload & Speed</th>
                  <th className="px-4 py-3.5">Battery & Navigation</th>
                  <th className="px-4 py-3.5">Price Range / RaaS</th>
                  <th className="px-4 py-3.5">Payback</th>
                  <th className="px-4 py-3.5">Best For Application</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {report.platforms.map((p, idx) => (
                  <tr
                    key={idx}
                    className="transition hover:bg-slate-800/40"
                  >
                    <td className="px-4 py-4 font-bold text-white">
                      <div>{p.vendor}</div>
                      <div className="text-[11px] font-normal text-emerald-400">
                        {p.model}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex rounded-md bg-emerald-950/80 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-300 border border-emerald-500/30">
                        {p.category}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div>Payload: <span className="font-semibold text-white">{p.payload}</span></div>
                      <div className="text-slate-400">Speed: {p.speed}</div>
                    </td>
                    <td className="px-4 py-4">
                      <div>Runtime: <span className="font-semibold text-white">{p.battery_runtime}</span></div>
                      <div className="text-slate-400 truncate max-w-[160px]">{p.navigation}</div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="font-semibold text-white">{p.price_range}</div>
                      <div className="text-sky-300 font-mono text-[11px]">{p.est_monthly_raas}</div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-950/80 px-2 py-0.5 text-[11px] font-bold text-amber-300 border border-amber-500/30">
                        {p.payback_months} mos
                      </span>
                    </td>
                    <td className="px-4 py-4 text-slate-300 max-w-[220px]">
                      {p.best_for}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Site Implementation Checklist */}
        <div className="rounded-2xl border border-slate-800 bg-[#0b162c] p-6 shadow-xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            Site Assessment & Facility Readiness Checklist
          </h2>

          <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2">
            {report.site_checklist.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-200"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
