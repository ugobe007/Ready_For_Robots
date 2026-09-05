/**
 * /vendor/design — floor plan for a robot job (not a sales pipeline).
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, CheckCircle2, Loader2, Share2 } from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import WorkflowFlowEditor from "@/components/vendor/WorkflowFlowEditor";
import type { WorkflowLayout } from "@/lib/workflowLayoutTypes";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  FIND_JOBS_CTA,
  JOBS_HEADER_OFFSET_CLASS,
  jobsFreshHomeHref,
} from "@/lib/jobsWorkflow";

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
  const [title, setTitle] = useState("Job site sketch");
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
        liveFetchInit()
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
        headers: {
          "Content-Type": "application/json",
          ...liveFetchInit().headers,
        },
        body: JSON.stringify({
          robot_unit_cost: parseFloat(robotCost) || 0,
          robot_count: parseInt(robotCount, 10) || 1,
          industry,
          fte_count_replaced: parseFloat(fteCount) || 0,
          fte_fully_loaded_cost: parseFloat(fteLoaded) || 0,
          labor_mode: "fte",
          buyer_stated_payback_months: buyerPayback
            ? parseFloat(buyerPayback)
            : null,
          buyer_stated_annual_savings: buyerSavings
            ? parseFloat(buyerSavings)
            : null,
        }),
      });
      if (!res.ok) throw new Error("ROI compute failed");
      setRoi((await res.json()) as RoiResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compute failed");
    } finally {
      setLoading(false);
    }
  }, [
    robotCost,
    robotCount,
    industry,
    fteCount,
    fteLoaded,
    buyerPayback,
    buyerSavings,
  ]);

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
        headers: {
          "Content-Type": "application/json",
          ...liveFetchInit().headers,
        },
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
            buyer_stated_payback_months: buyerPayback
              ? parseFloat(buyerPayback)
              : null,
            buyer_stated_annual_savings: buyerSavings
              ? parseFloat(buyerSavings)
              : null,
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
    <div
      className={`flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />
      <PageHeroDark
        eyebrow="Jobs"
        title="Sketch the job site"
        description="This page is a floor plan for a robot job — not a sales pipeline. Draw where work happens, place the robot, then see whether replacing labor pays back the machine."
      />

      <main className="relative z-10 mx-auto w-full max-w-[1400px] space-y-5 px-4 pb-16 sm:px-6">
        <section className="border border-slate-600 bg-[#0b162f] p-4 sm:p-5">
          <h2 className="text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-400">
            What this page does
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-300">
            ReadyForRobots matches robots to jobs. Use this sketch when you
            already have a workplace in mind: rooms, flows, and where a robot
            would stand. Save a link and keep it with the Job Card. To find jobs
            from a robot URL, go back to Jobs.
          </p>
          <ol className="mt-3 grid gap-2 text-[13px] text-slate-400 sm:grid-cols-5">
            <li>
              <span className="font-mono text-emerald-400">01</span> Pick a site
              type
            </li>
            <li>
              <span className="font-mono text-emerald-400">02</span> Drag rooms
              and robots
            </li>
            <li>
              <span className="font-mono text-emerald-400">03</span> Connect how
              work moves
            </li>
            <li>
              <span className="font-mono text-emerald-400">04</span> Enter cost
              and labor
            </li>
            <li>
              <span className="font-mono text-emerald-400">05</span> Save a
              share link
            </li>
          </ol>
        </section>

        <section className="border border-slate-600 bg-[#0b162f] p-4 sm:p-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-widest text-slate-400">
                Workplace layout
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Drag rooms, connect flows, place robots — this is the floor plan
                for the job.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                className="border border-slate-600 bg-[#081126] px-3 py-1.5 text-xs text-slate-100 outline-none focus:border-emerald-400"
                value={industry}
                onChange={e => setIndustry(e.target.value)}
              >
                {INDUSTRIES.map(ind => (
                  <option key={ind} value={ind}>
                    {ind}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="text-xs font-semibold text-emerald-400 hover:text-emerald-300"
                onClick={() => void loadTemplate()}
              >
                Reset template
              </button>
            </div>
          </div>
          {layout && (
            <WorkflowFlowEditor layout={layout} onChange={setLayout} />
          )}
        </section>

        <div className="grid gap-5 lg:grid-cols-2">
          <section className="space-y-3 border border-slate-600 bg-[#0b162f] p-5">
            <h2 className="text-sm font-bold uppercase tracking-widest text-slate-400">
              Job context
            </h2>
            <input
              className="w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-400"
              placeholder="Sketch title"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <input
                className="border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-400"
                placeholder="Robot company"
                value={vendorCompany}
                onChange={e => setVendorCompany(e.target.value)}
              />
              <input
                className="border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-400"
                placeholder="Employer"
                value={buyerCompany}
                onChange={e => setBuyerCompany(e.target.value)}
              />
            </div>
            <input
              className="w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-400"
              placeholder="Robot / SKU on this job"
              value={robotProduct}
              onChange={e => setRobotProduct(e.target.value)}
            />
          </section>

          <section className="space-y-3 border border-slate-600 bg-[#0b162f] p-5">
            <h2 className="text-sm font-bold uppercase tracking-widest text-slate-400">
              Labor vs robot cost
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <label className="space-y-1">
                <span className="text-xs text-slate-500">
                  Robot unit cost ($)
                </span>
                <input
                  className="w-full border border-slate-600 bg-[#081126] px-3 py-2 text-slate-100 outline-none focus:border-emerald-400"
                  value={robotCost}
                  onChange={e => setRobotCost(e.target.value)}
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-500">Robot count</span>
                <input
                  className="w-full border border-slate-600 bg-[#081126] px-3 py-2 text-slate-100 outline-none focus:border-emerald-400"
                  value={robotCount}
                  onChange={e => setRobotCount(e.target.value)}
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-500">FTE replaced</span>
                <input
                  className="w-full border border-slate-600 bg-[#081126] px-3 py-2 text-slate-100 outline-none focus:border-emerald-400"
                  value={fteCount}
                  onChange={e => setFteCount(e.target.value)}
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-500">
                  Fully loaded FTE ($/yr)
                </span>
                <input
                  className="w-full border border-slate-600 bg-[#081126] px-3 py-2 text-slate-100 outline-none focus:border-emerald-400"
                  value={fteLoaded}
                  onChange={e => setFteLoaded(e.target.value)}
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-1 text-sm">
              <input
                className="border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-amber-400"
                placeholder="Stated payback (mo)"
                value={buyerPayback}
                onChange={e => setBuyerPayback(e.target.value)}
              />
              <input
                className="border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-amber-400"
                placeholder="Stated savings ($/yr)"
                value={buyerSavings}
                onChange={e => setBuyerSavings(e.target.value)}
              />
            </div>
            {loading && (
              <p className="flex items-center gap-2 text-xs text-slate-500">
                <Loader2 className="h-3 w-3 animate-spin" /> Recalculating…
              </p>
            )}
            {roi && (
              <div className="grid grid-cols-2 gap-2 border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm">
                <div>
                  <p className="text-[10px] font-bold uppercase text-emerald-300">
                    Payback
                  </p>
                  <p className="text-lg font-bold text-emerald-200">
                    {roi.payback_months} mo
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase text-emerald-300">
                    Annual savings
                  </p>
                  <p className="text-lg font-bold text-emerald-200">
                    ${Math.round(roi.annual_net_savings).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-slate-500">
                    3-yr ROI
                  </p>
                  <p className="font-semibold text-slate-100">
                    {roi.roi_year_3_pct}%
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-slate-500">
                    Net 3-yr
                  </p>
                  <p className="font-semibold text-slate-100">
                    ${Math.round(roi.net_savings_3yr).toLocaleString()}
                  </p>
                </div>
              </div>
            )}
            {roi?.issues && roi.issues.length > 0 && (
              <ul className="max-h-32 space-y-1.5 overflow-y-auto">
                {roi.issues.map(issue => (
                  <li
                    key={issue.code}
                    className="border border-amber-500/30 bg-amber-500/10 px-2 py-1.5 text-[11px] text-amber-100"
                  >
                    {issue.message}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <div className="sticky bottom-4 flex flex-wrap items-center gap-3 border border-slate-600 bg-[#0b162f]/95 px-4 py-3 backdrop-blur">
          <button
            type="button"
            onClick={() => void saveAndShare()}
            disabled={saving || !roi}
            className="inline-flex items-center gap-2 border border-emerald-400 bg-emerald-500/15 px-4 py-2.5 text-sm font-bold text-emerald-300 hover:bg-emerald-500/25 disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Share2 className="h-4 w-4" />
            )}
            Save &amp; copy site-plan link
          </button>
          {shareUrl && (
            <span className="flex items-center gap-1 text-xs text-slate-300">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Copied: {shareUrl}
            </span>
          )}
          {error && <span className="text-sm text-red-400">{error}</span>}
          <Link
            href={jobsFreshHomeHref()}
            className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300"
          >
            {FIND_JOBS_CTA} <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
