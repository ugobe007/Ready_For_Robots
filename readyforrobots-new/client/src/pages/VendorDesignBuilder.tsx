/**
 * /vendor/design — deployment design studio (workflow-first layout).
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import { AlertTriangle, ArrowRight, CheckCircle2, Copy, Loader2, Share2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import WorkflowFlowEditor from "@/components/vendor/WorkflowFlowEditor";
import type { WorkflowLayout } from "@/lib/workflowLayoutTypes";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

type RoiIssue = {
  code: string;
  severity: string;
  message: string;
  suggestion: string;
};

type RoiResult = {
  annual_labor_baseline: number;
  annual_labor_replaced: number;
  annual_maintenance: number;
  annual_net_savings: number;
  total_capex: number;
  payback_months: number;
  roi_year_1_pct: number;
  roi_year_3_pct: number;
  net_savings_3yr: number;
  corrected_from_buyer: boolean;
  issues: RoiIssue[];
};

const INDUSTRIES = [
  "Hospitality",
  "Healthcare",
  "Logistics / Warehouse",
  "Food Service",
  "Manufacturing",
  "Retail",
];

export default function VendorDesignBuilder() {
  const [title, setTitle] = useState("Deployment design");
  const [vendorCompany, setVendorCompany] = useState("");
  const [buyerCompany, setBuyerCompany] = useState("");
  const [industry, setIndustry] = useState("Logistics / Warehouse");
  const [robotProduct, setRobotProduct] = useState("");
  const [robotCost, setRobotCost] = useState("45000");
  const [robotCount, setRobotCount] = useState("2");
  const [fteCount, setFteCount] = useState("1.5");
  const [fteLoaded, setFteLoaded] = useState("58000");
  const [buyerPayback, setBuyerPayback] = useState("");
  const [buyerSavings, setBuyerSavings] = useState("");
  const [layout, setLayout] = useState<WorkflowLayout | null>(null);
  const [roi, setRoi] = useState<RoiResult | null>(null);
  const [shareUrl, setShareUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadTemplate = useCallback(async () => {
    try {
      const res = await fetch(
        `${getApiBase()}/api/vendor-design/layout-template?industry=${encodeURIComponent(industry)}`,
        liveFetchInit(),
      );
      if (res.ok) setLayout((await res.json()) as WorkflowLayout);
    } catch {
      /* ignore */
    }
  }, [industry]);

  const computeRoi = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${getApiBase()}/api/vendor-design/compute-roi`, {
        ...liveFetchInit(),
        method: "POST",
        headers: { "Content-Type": "application/json", ...liveFetchInit().headers },
        body: JSON.stringify({
          robot_unit_cost: parseFloat(robotCost) || 0,
          robot_count: parseInt(robotCount, 10) || 1,
          industry,
          fte_count_replaced: parseFloat(fteCount) || 0,
          fte_fully_loaded_cost: parseFloat(fteLoaded) || 0,
          labor_mode: "fte",
          buyer_stated_payback_months: buyerPayback ? parseFloat(buyerPayback) : null,
          buyer_stated_annual_savings: buyerSavings ? parseFloat(buyerSavings) : null,
        }),
      });
      if (!res.ok) throw new Error("ROI compute failed");
      setRoi((await res.json()) as RoiResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compute failed");
    } finally {
      setLoading(false);
    }
  }, [robotCost, robotCount, industry, fteCount, fteLoaded, buyerPayback, buyerSavings]);

  useEffect(() => {
    void loadTemplate();
  }, [loadTemplate]);

  useEffect(() => {
    void computeRoi();
  }, [computeRoi]);

  async function saveAndShare() {
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${getApiBase()}/api/vendor-design/models`, {
        ...liveFetchInit(),
        method: "POST",
        headers: { "Content-Type": "application/json", ...liveFetchInit().headers },
        body: JSON.stringify({
          title,
          vendor_company: vendorCompany,
          buyer_company: buyerCompany,
          industry,
          robot_product: robotProduct,
          layout,
          roi: {
            robot_unit_cost: parseFloat(robotCost) || 0,
            robot_count: parseInt(robotCount, 10) || 1,
            industry,
            fte_count_replaced: parseFloat(fteCount) || 0,
            fte_fully_loaded_cost: parseFloat(fteLoaded) || 0,
            labor_mode: "fte",
            buyer_stated_payback_months: buyerPayback ? parseFloat(buyerPayback) : null,
            buyer_stated_annual_savings: buyerSavings ? parseFloat(buyerSavings) : null,
          },
        }),
      });
      if (!res.ok) throw new Error("Save failed");
      const data = (await res.json()) as { share_url: string };
      const full = `${window.location.origin}${data.share_url}`;
      setShareUrl(full);
      void navigator.clipboard?.writeText(full);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <PageHeroDark
        eyebrow="Vendor tools"
        title="Deployment design studio"
        subtitle="Map the physical workflow first, then validate ROI for the buyer."
      />

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 pb-16 -mt-4 relative z-10 space-y-5">
        {/* Workflow — primary, top of page */}
        <section className="rounded-2xl border border-gray-200 bg-white p-4 sm:p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">Workflow layout</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Drag zones, connect flows, place robots — this is the buyer-facing floor plan.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
              >
                {INDUSTRIES.map((ind) => (
                  <option key={ind} value={ind}>
                    {ind}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="text-xs font-semibold text-emerald-700 hover:underline"
                onClick={() => void loadTemplate()}
              >
                Reset template
              </button>
            </div>
          </div>
          {layout && <WorkflowFlowEditor layout={layout} onChange={setLayout} />}
        </section>

        {/* Deal + ROI — secondary row */}
        <div className="grid lg:grid-cols-2 gap-5">
          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm space-y-3">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">Deal context</h2>
            <input
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
              placeholder="Design title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <div className="grid sm:grid-cols-2 gap-3">
              <input
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
                placeholder="Your company (vendor)"
                value={vendorCompany}
                onChange={(e) => setVendorCompany(e.target.value)}
              />
              <input
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
                placeholder="Buyer company"
                value={buyerCompany}
                onChange={(e) => setBuyerCompany(e.target.value)}
              />
            </div>
            <input
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
              placeholder="Robot product / SKU"
              value={robotProduct}
              onChange={(e) => setRobotProduct(e.target.value)}
            />
          </section>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm space-y-3">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">ROI inputs</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <label className="space-y-1">
                <span className="text-xs text-gray-500">Robot unit cost ($)</span>
                <input className="w-full rounded-lg border border-gray-200 px-3 py-2" value={robotCost} onChange={(e) => setRobotCost(e.target.value)} />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-gray-500">Robot count</span>
                <input className="w-full rounded-lg border border-gray-200 px-3 py-2" value={robotCount} onChange={(e) => setRobotCount(e.target.value)} />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-gray-500">FTE replaced</span>
                <input className="w-full rounded-lg border border-gray-200 px-3 py-2" value={fteCount} onChange={(e) => setFteCount(e.target.value)} />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-gray-500">Fully loaded FTE ($/yr)</span>
                <input className="w-full rounded-lg border border-gray-200 px-3 py-2" value={fteLoaded} onChange={(e) => setFteLoaded(e.target.value)} />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm pt-1">
              <input
                className="rounded-lg border border-amber-200 bg-amber-50/50 px-3 py-2 text-sm"
                placeholder="Buyer payback (mo)"
                value={buyerPayback}
                onChange={(e) => setBuyerPayback(e.target.value)}
              />
              <input
                className="rounded-lg border border-amber-200 bg-amber-50/50 px-3 py-2 text-sm"
                placeholder="Buyer savings ($/yr)"
                value={buyerSavings}
                onChange={(e) => setBuyerSavings(e.target.value)}
              />
            </div>
            {loading && (
              <p className="text-xs text-gray-500 flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" /> Recalculating…
              </p>
            )}
            {roi && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="text-[10px] uppercase text-emerald-800 font-bold">Payback</p>
                  <p className="text-lg font-bold text-emerald-900">{roi.payback_months} mo</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-emerald-800 font-bold">Annual savings</p>
                  <p className="text-lg font-bold text-emerald-900">${Math.round(roi.annual_net_savings).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-gray-500">3-yr ROI</p>
                  <p className="font-semibold">{roi.roi_year_3_pct}%</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-gray-500">Net 3-yr</p>
                  <p className="font-semibold">${Math.round(roi.net_savings_3yr).toLocaleString()}</p>
                </div>
              </div>
            )}
            {roi?.issues && roi.issues.length > 0 && (
              <ul className="space-y-1.5 max-h-32 overflow-y-auto">
                {roi.issues.map((issue) => (
                  <li key={issue.code} className="rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-[11px] text-amber-950">
                    {issue.message}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <div className="flex flex-wrap gap-3 items-center sticky bottom-4 rounded-xl border border-gray-200 bg-white/95 backdrop-blur px-4 py-3 shadow-lg">
          <button
            type="button"
            onClick={() => void saveAndShare()}
            disabled={saving || !roi}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Share2 className="h-4 w-4" />}
            Save & copy buyer link
          </button>
          {shareUrl && (
            <span className="text-xs text-gray-600 flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              Copied: {shareUrl}
            </span>
          )}
          {error && <span className="text-sm text-red-600">{error}</span>}
          <Link href="/supply-pipeline" className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-gray-600 hover:text-gray-900">
            Supply pipeline <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
