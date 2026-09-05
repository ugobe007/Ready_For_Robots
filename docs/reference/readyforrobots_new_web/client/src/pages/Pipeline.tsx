import ExpandableLeadsTable from "@/components/leads/ExpandableLeadsTable";
import SiteShell from "@/components/SiteShell";
import { LEADS_PUBLIC_FETCH_LIMIT } from "@/lib/leadsApiConstants";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import type { LeadRow } from "@/lib/leadTypes";
import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";

type PipelineSummary = {
  total?: number;
  hot?: number;
  warm?: number;
  cold?: number;
  companies_in_database?: number;
  signals_in_database?: number;
  total_signals?: number;
};

const EM = "oklch(0.527 0.154 162.5)";

export default function Pipeline() {
  const [leads, setLeads] = useState<LeadRow[]>([]);
  const [summary, setSummary] = useState<PipelineSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const load = useCallback(async () => {
    const API = getApiBase();
    setLoading(true);
    setError(null);
    setExpandedId(null);
    const p = new URLSearchParams({
      limit: LEADS_PUBLIC_FETCH_LIMIT,
      exclude_junk: "true",
      sort: "score",
      tier: "HOT",
    });
    try {
      const [rSum, rLeads] = await Promise.all([
        fetch(`${API}/api/leads/summary?exclude_junk=true`, liveFetchInit()),
        fetch(`${API}/api/leads?${p}`, liveFetchInit()),
      ]);
      if (rSum.ok) {
        const t = await rSum.text();
        if (!t.trimStart().startsWith("<")) {
          try {
            setSummary(JSON.parse(t) as PipelineSummary);
          } catch {
            setSummary(null);
          }
        } else setSummary(null);
      } else setSummary(null);

      if (!rLeads.ok) {
        setError(`Could not load pipeline (${rLeads.status}).`);
        setLeads([]);
        return;
      }
      const raw = await rLeads.text();
      if (raw.trimStart().startsWith("<")) {
        setError("We couldn’t load the pipeline. Please try again shortly.");
        setLeads([]);
        return;
      }
      setLeads(JSON.parse(raw) as LeadRow[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setLeads([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const fmt = (n: number | undefined) =>
    n != null && Number.isFinite(n) ? n.toLocaleString() : "—";

  return (
    <SiteShell>
      <div className="pb-16">
        <section className="border-b border-gray-200 bg-white">
          <div className="container py-10 md:py-12 max-w-4xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Pipeline</p>
            <h1
              className="text-3xl md:text-4xl font-extrabold text-gray-900 tracking-tight"
              style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
            >
              HOT deals — live feed
            </h1>
            <p className="text-gray-600 mt-3 text-sm md:text-base leading-relaxed max-w-2xl">
              Same scoring and junk gates as the dashboard. Expand rows for signals and GTM context; sign in to unlock
              the full list and CRM export.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void load()}
                disabled={loading}
                className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-transparent px-4 py-2 text-sm font-medium text-gray-800 hover:border-gray-400 hover:text-gray-950 disabled:opacity-50"
              >
                {loading ? "Refreshing…" : "Refresh"}
              </button>
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-transparent px-4 py-2 text-sm font-medium text-gray-800 hover:border-gray-400"
              >
                Dashboard
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-md border px-4 py-2 text-sm font-medium bg-transparent hover:opacity-90"
                style={{ borderColor: EM, color: EM }}
              >
                Sign in to unlock
              </Link>
            </div>
          </div>
        </section>

        {summary ? (
          <div className="container py-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-4xl">
              {[
                ["HOT (scored window)", summary.hot],
                ["Companies in DB", summary.companies_in_database],
                ["Signal rows in DB", summary.signals_in_database ?? summary.total_signals],
                ["Loaded preview", leads.length],
              ].map(([label, val]) => (
                <div key={String(label)} className="rounded-lg border border-gray-200 px-4 py-3 bg-white">
                  <p className="text-2xl font-semibold tabular-nums text-gray-900">{fmt(val as number)}</p>
                  <p className="text-xs font-medium text-gray-500 mt-1">{label}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div className="container py-2 md:py-4 space-y-6">
          <ExpandableLeadsTable
            leads={leads}
            loading={loading}
            error={error}
            expandedId={expandedId}
            onToggle={setExpandedId}
            urlBar="readyforrobots.com/pipeline"
            showSignupBlur={false}
            showAnalyzeCta={false}
          />
        </div>
      </div>
    </SiteShell>
  );
}
