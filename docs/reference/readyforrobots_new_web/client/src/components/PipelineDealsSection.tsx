/**
 * Home — live HOT pipeline preview (same data as the dashboard list).
 */

import ExpandableLeadsTable from "@/components/leads/ExpandableLeadsTable";
import { LEADS_PUBLIC_FETCH_LIMIT } from "@/lib/leadsApiConstants";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import type { LeadRow } from "@/lib/leadTypes";
import { useCallback, useEffect, useState } from "react";

type Summary = { hot?: number; companies_in_database?: number };

function num(v: unknown): number | undefined {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
  return undefined;
}

export default function PipelineDealsSection() {
  const [leads, setLeads] = useState<LeadRow[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
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
      const [rLeads, rSum] = await Promise.all([
        fetch(`${API}/api/leads?${p}`, liveFetchInit()),
        fetch(`${API}/api/leads/summary?exclude_junk=true`, liveFetchInit()),
      ]);
      if (rSum.ok) {
        const t = await rSum.text();
        if (!t.trimStart().startsWith("<")) {
          try {
            setSummary(JSON.parse(t) as Summary);
          } catch {
            setSummary(null);
          }
        } else setSummary(null);
      } else setSummary(null);

      if (!rLeads.ok) {
        setError(`Could not load leads (${rLeads.status}).`);
        setLeads([]);
        return;
      }
      const raw = await rLeads.text();
      if (raw.trimStart().startsWith("<")) {
        setError("We couldn’t load this section. Please try again in a moment.");
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

  const hotWindow = num(summary?.hot);
  const headlineHot =
    hotWindow != null && hotWindow > 0
      ? hotWindow.toLocaleString()
      : loading
        ? "…"
        : (leads.length || 0).toLocaleString();

  return (
    <section
      id="pipeline-deals"
      className="py-20 scroll-mt-20 border-t border-emerald-900/10"
      style={{ backgroundColor: "oklch(0.97 0.014 162.5)" }}
    >
      <div className="container">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8 mb-10 animate-fade-up">
          <div className="max-w-2xl">
            <span className="section-label block mb-3">Live database</span>
            <h2
              className="text-4xl md:text-[2.35rem] font-bold text-gray-950 leading-tight mb-4"
              style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
            >
              {loading ? "Loading HOT leads…" : `${headlineHot} HOT leads. Updated daily.`}
            </h2>
            <p className="text-gray-700 text-sm md:text-base leading-relaxed max-w-xl">
              Real companies, real signals. Sign up to unlock scores, contacts, and engagement workflows. The table
              shows up to {LEADS_PUBLIC_FETCH_LIMIT} HOT leads from the current API window — expand a row for full
              CRM-style detail; the rest stay blurred until you sign up.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <a
              href="/pipeline"
              className="inline-flex items-center justify-center gap-2 rounded-lg border-2 border-gray-300 bg-white px-5 py-3 text-sm font-semibold text-gray-900 shadow-sm hover:border-gray-400 hover:bg-gray-50/80 transition-colors"
            >
              Full pipeline view
            </a>
            <a href="/dashboard" className="btn-marketing-primary">
              Unlock full dashboard
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
          </div>
        </div>

        <ExpandableLeadsTable
          leads={leads}
          loading={loading}
          error={error}
          expandedId={expandedId}
          onToggle={setExpandedId}
          urlBar="readyforrobots.com/dashboard"
          density="compact"
        />
      </div>
    </section>
  );
}
