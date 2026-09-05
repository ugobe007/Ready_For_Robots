/**
 * /design/:shareId — shareable floor plan for a robot job.
 */
import { useEffect, useState } from "react";
import { Link, useRoute } from "wouter";
import { Loader2 } from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import WorkflowFlowViewer from "@/components/vendor/WorkflowFlowViewer";
import type { WorkflowLayout } from "@/lib/workflowLayoutTypes";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  FIND_JOBS_CTA,
  JOBS_HEADER_OFFSET_CLASS,
  jobsFreshHomeHref,
} from "@/lib/jobsWorkflow";

type DesignModel = {
  title?: string;
  vendor_company?: string;
  buyer_company?: string;
  industry?: string;
  robot_product?: string;
  roi?: {
    payback_months?: number;
    annual_net_savings?: number;
    roi_year_3_pct?: number;
    net_savings_3yr?: number;
    issues?: Array<{ severity: string; message: string }>;
  };
  layout?: WorkflowLayout;
  workflow_impact?: {
    labor_hours_saved_per_week?: number;
    peak_throughput_delta_pct?: number;
    automated_handoffs?: number;
  };
};

export default function DesignShare() {
  const [, params] = useRoute("/design/:shareId");
  const shareId = params?.shareId ?? "";
  const [data, setData] = useState<DesignModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!shareId) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${getApiBase()}/api/vendor-design/models/${shareId}`,
          liveFetchInit()
        );
        if (!res.ok) throw new Error("Design not found");
        if (!cancelled) setData((await res.json()) as DesignModel);
      } catch (e) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [shareId]);

  return (
    <div
      className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        {loading ? (
          <div className="flex justify-center gap-2 py-20 text-sm text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading site plan…
          </div>
        ) : error ? (
          <p className="text-center text-red-400">{error}</p>
        ) : data ? (
          <article className="space-y-6">
            <header>
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">
                Job site sketch
              </p>
              <h1 className="mt-1 text-2xl font-bold text-slate-100">
                {data.title}
              </h1>
              <p className="mt-2 text-sm text-slate-400">
                {data.vendor_company && <span>{data.vendor_company}</span>}
                {data.buyer_company && <span> → {data.buyer_company}</span>}
                {data.industry && <span> · {data.industry}</span>}
              </p>
              {data.robot_product && (
                <p className="mt-1 text-sm text-slate-200">
                  Robot: <strong>{data.robot_product}</strong>
                </p>
              )}
            </header>

            {data.roi && (
              <section className="grid gap-4 sm:grid-cols-3">
                <div className="border border-emerald-500/40 bg-emerald-500/10 p-4">
                  <p className="text-[10px] font-bold uppercase text-emerald-300">
                    Payback
                  </p>
                  <p className="text-2xl font-bold text-emerald-200">
                    {data.roi.payback_months} mo
                  </p>
                </div>
                <div className="border border-slate-600 bg-[#0b162f] p-4">
                  <p className="text-[10px] font-bold uppercase text-slate-400">
                    Annual savings
                  </p>
                  <p className="text-2xl font-bold text-slate-100">
                    $
                    {Math.round(
                      data.roi.annual_net_savings || 0
                    ).toLocaleString()}
                  </p>
                </div>
                <div className="border border-slate-600 bg-[#0b162f] p-4">
                  <p className="text-[10px] font-bold uppercase text-slate-400">
                    3-year ROI
                  </p>
                  <p className="text-2xl font-bold text-slate-100">
                    {data.roi.roi_year_3_pct}%
                  </p>
                </div>
              </section>
            )}

            {data.workflow_impact && (
              <p className="text-sm text-slate-300">
                Workflow impact:{" "}
                <strong>
                  {data.workflow_impact.labor_hours_saved_per_week}h/wk
                </strong>{" "}
                labor saved ·{" "}
                <strong>
                  +{data.workflow_impact.peak_throughput_delta_pct}%
                </strong>{" "}
                throughput · {data.workflow_impact.automated_handoffs} automated
                handoffs
              </p>
            )}

            {data.layout && (
              <section className="border border-slate-600 bg-[#0b162f] p-5">
                <h2 className="mb-3 text-sm font-bold uppercase tracking-widest text-slate-400">
                  Physical workflow
                </h2>
                <WorkflowFlowViewer layout={data.layout} />
              </section>
            )}

            <p className="text-center text-xs text-slate-500">
              <Link
                href={jobsFreshHomeHref()}
                className="text-emerald-400 underline"
              >
                {FIND_JOBS_CTA}
              </Link>
            </p>
          </article>
        ) : null}
      </main>
      <SiteFooter />
    </div>
  );
}
