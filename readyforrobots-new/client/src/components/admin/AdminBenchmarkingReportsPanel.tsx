import { useState } from "react";
import { Link } from "wouter";
import {
  Award,
  BookOpen,
  Check,
  Copy,
  ExternalLink,
  Layers,
  Sparkles,
} from "lucide-react";
import { INDUSTRY_BENCHMARKS } from "@/lib/industryBenchmarkingData";

export default function AdminBenchmarkingReportsPanel() {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyReportLink = (id: string) => {
    const url = `${window.location.origin}/reports/benchmarking/${id}`;
    void navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <section
      id="admin-benchmarking-reports"
      className="mb-8 rounded-2xl border border-sky-500/30 bg-[#081329] p-6 text-slate-100 shadow-2xl backdrop-blur-md"
    >
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-md bg-sky-500/20 px-2.5 py-1 text-xs font-bold text-sky-300 border border-sky-500/40">
              <Award className="h-3.5 w-3.5 text-amber-400" />
              PROSPECT REPORT LIBRARY
            </span>
            <h2 className="text-xl font-bold tracking-tight text-white">
              Comparative Industry Benchmarking Reports
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Shareable 2026 benchmarking reports pre-configured for executive prospects when they reply.
          </p>
        </div>

        <Link
          href="/reports/benchmarking/hospitality"
          className="inline-flex items-center gap-2 rounded-xl border border-sky-500/40 bg-sky-950/40 px-3.5 py-2 text-xs font-semibold text-sky-300 transition hover:bg-sky-900/60 hover:text-white"
        >
          <BookOpen className="h-3.5 w-3.5" />
          View Full Report Library →
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {Object.values(INDUSTRY_BENCHMARKS).map(bm => (
          <div
            key={bm.id}
            className="flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0d1836] p-4 transition hover:border-sky-500/40 hover:bg-[#101e42]"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-sky-400 border border-slate-700">
                  {bm.id}
                </span>
                <span className="text-[11px] font-bold text-amber-300">
                  {bm.avg_payback_months} mos payback
                </span>
              </div>

              <h3 className="mt-2 text-sm font-bold text-white line-clamp-1">
                {bm.title}
              </h3>

              <p className="mt-1 text-[11px] text-slate-400 line-clamp-2">
                {bm.subtitle}
              </p>

              <div className="mt-3 flex flex-wrap gap-1 text-[10px] text-slate-300">
                <span className="font-semibold text-emerald-400">Accounts: </span>
                {bm.target_accounts.slice(0, 2).join(", ")}
                {bm.target_accounts.length > 2 && "..."}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-2.5 text-xs">
              <button
                type="button"
                onClick={() => copyReportLink(bm.id)}
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white"
              >
                {copiedId === bm.id ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    Link Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    Copy Share Link
                  </>
                )}
              </button>

              <Link
                href={`/reports/benchmarking/${bm.id}`}
                className="inline-flex items-center gap-1 font-semibold text-sky-400 hover:text-sky-300"
              >
                View Report
                <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
