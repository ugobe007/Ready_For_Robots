/**
 * /design/:shareId — buyer-facing deployment design + ROI (shareable).
 */
import { useEffect, useState } from "react";
import { Link, useRoute } from "wouter";
import { Loader2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import WorkflowFlowViewer from "@/components/vendor/WorkflowFlowViewer";
import type { WorkflowLayout } from "@/lib/workflowLayoutTypes";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

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
        const res = await fetch(`${getApiBase()}/api/vendor-design/models/${shareId}`, liveFetchInit());
        if (!res.ok) throw new Error("Design not found");
        if (!cancelled) setData((await res.json()) as DesignModel);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [shareId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
        {loading ? (
          <div className="flex justify-center py-20 text-gray-500 text-sm gap-2">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading design…
          </div>
        ) : error ? (
          <p className="text-center text-red-600">{error}</p>
        ) : data ? (
          <article className="space-y-6">
            <header>
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-700">
                Deployment proposal
              </p>
              <h1 className="text-2xl font-bold text-gray-900 mt-1">{data.title}</h1>
              <p className="text-sm text-gray-600 mt-2">
                {data.vendor_company && <span>{data.vendor_company}</span>}
                {data.buyer_company && <span> → {data.buyer_company}</span>}
                {data.industry && <span> · {data.industry}</span>}
              </p>
              {data.robot_product && (
                <p className="text-sm text-gray-800 mt-1">
                  Robot: <strong>{data.robot_product}</strong>
                </p>
              )}
            </header>

            {data.roi && (
              <section className="grid sm:grid-cols-3 gap-4">
                <div className="rounded-xl border border-emerald-200 bg-white p-4">
                  <p className="text-[10px] uppercase text-gray-500 font-bold">Payback</p>
                  <p className="text-2xl font-bold text-emerald-800">{data.roi.payback_months} mo</p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-white p-4">
                  <p className="text-[10px] uppercase text-gray-500 font-bold">Annual savings</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${Math.round(data.roi.annual_net_savings || 0).toLocaleString()}
                  </p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-white p-4">
                  <p className="text-[10px] uppercase text-gray-500 font-bold">3-year ROI</p>
                  <p className="text-2xl font-bold text-gray-900">{data.roi.roi_year_3_pct}%</p>
                </div>
              </section>
            )}

            {data.workflow_impact && (
              <p className="text-sm text-gray-700">
                Workflow impact:{" "}
                <strong>{data.workflow_impact.labor_hours_saved_per_week}h/wk</strong> labor saved ·{" "}
                <strong>+{data.workflow_impact.peak_throughput_delta_pct}%</strong> throughput ·{" "}
                {data.workflow_impact.automated_handoffs} automated handoffs
              </p>
            )}

            {data.layout && (
              <section className="rounded-2xl border border-gray-200 bg-white p-5">
                <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500 mb-3">
                  Physical workflow
                </h2>
                <WorkflowFlowViewer layout={data.layout} />
              </section>
            )}

            <p className="text-center text-xs text-gray-400">
              <Link href="/pipeline" className="text-emerald-700 underline">
                Explore live buyer signals
              </Link>
            </p>
          </article>
        ) : null}
      </main>
      <SiteFooter />
    </div>
  );
}
