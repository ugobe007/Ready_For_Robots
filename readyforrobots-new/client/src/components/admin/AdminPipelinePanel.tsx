import { ArrowRight, BarChart3, Inbox, Workflow } from "lucide-react";
import { Link } from "wouter";

type Props = {
  hot?: number;
  warm?: number;
  totalCompanies?: number;
  totalSignals?: number;
};

export default function AdminPipelinePanel({
  hot = 0,
  warm = 0,
  totalCompanies,
  totalSignals,
}: Props) {
  return (
    <div className="mb-8 space-y-4">
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-xl font-bold text-gray-950">Pipeline review</h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-gray-700">
          Use the live pipeline to browse signals and spot junk before it reaches buyers. Cal&apos;s <strong>send queue</strong> is
          a separate admin list (top 300 HOT/WARM by score on your admin-cal-outreach team) — not the same slice as this page.
        </p>
        <p className="mt-2 text-xs text-gray-600">
          To preview or send emails, switch to the <strong>Cal control</strong> tab. Pipeline is for lead-quality review only.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            href="/pipeline"
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white hover:bg-emerald-500"
          >
            Open live pipeline
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/signals"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-5 py-3 text-sm font-bold text-gray-800"
          >
            <BarChart3 className="h-4 w-4" />
            Signal library
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-amber-800">Hot</p>
          <p className="mt-1 text-2xl font-black text-amber-950">{hot}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800">Warm</p>
          <p className="mt-1 text-2xl font-black text-emerald-950">{warm}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Companies</p>
          <p className="mt-1 text-2xl font-black text-gray-900">{totalCompanies ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Signals</p>
          <p className="mt-1 text-2xl font-black text-gray-900">{totalSignals ?? "—"}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/crm" className="group rounded-2xl border border-gray-200 bg-white p-5 shadow-sm hover:border-emerald-300">
          <Workflow className="h-5 w-5 text-emerald-700" />
          <p className="mt-2 font-display text-base font-bold text-gray-950 group-hover:text-emerald-800">Outreach editor (CRM)</p>
          <p className="mt-1 text-sm text-gray-600">Per-account drafts, approve/send, and contact edits — the detailed workflow.</p>
        </Link>
        <Link href="/sales-workflow" className="group rounded-2xl border border-gray-200 bg-white p-5 shadow-sm hover:border-amber-300">
          <Inbox className="h-5 w-5 text-amber-700" />
          <p className="mt-2 font-display text-base font-bold text-gray-950 group-hover:text-amber-900">Activity & replies</p>
          <p className="mt-1 text-sm text-gray-600">See what happened after sends — opens, clicks, and vendor replies.</p>
        </Link>
      </div>
    </div>
  );
}
