/**
 * Compare — ReadyForRobots vs GTM data tools (Explee, Apollo, etc.)
 */
import { ArrowRight, Check, X } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";

const rows: {
  dimension: string;
  dataTools: string;
  rfr: string;
  rfrWins?: boolean;
}[] = [
  {
    dimension: "What you get",
    dataTools: "Company & people search, CSV export, research API runs",
    rfr: "Automated sales pipeline — detect, qualify, engage, advance",
    rfrWins: true,
  },
  {
    dimension: "Coverage",
    dataTools: "100M+ companies — horizontal B2B",
    rfr: "Curated robot-buyer intent — quality over volume",
    rfrWins: true,
  },
  {
    dimension: "Selection",
    dataTools: "Job titles, lookalikes, firmographics, geo filters",
    rfr: "Live signals: labor, capex, expansion, deployment, hiring",
    rfrWins: true,
  },
  {
    dimension: "Timing",
    dataTools: "Static or periodically enriched records",
    rfr: "HOT / WARM / COLD from recent buyer events",
    rfrWins: true,
  },
  {
    dimension: "Pitch specificity",
    dataTools: '"CTO at a logistics company"',
    rfr: "robot_types_needed + pipeline_action on every lead",
    rfrWins: true,
  },
  {
    dimension: "Workflow",
    dataTools: "Search → export → build your own stack",
    rfr: "Pipeline kanban, outreach drafts, HubSpot sync",
    rfrWins: true,
  },
  {
    dimension: "Best for",
    dataTools: "Any B2B team building top-of-funnel lists",
    rfr: "Robot OEMs, integrators, and distributors automating sales",
    rfrWins: true,
  },
];

const examples = [
  {
    tool: "Explee-style search",
    query: "CTOs at warehouse automation companies in Texas",
    result: "500 contacts — no idea who is buying robots this quarter",
  },
  {
    tool: "ReadyForRobots",
    query: "HOT pipeline · Logistics",
    result: "Priority: Pitch AMR fleet for new DC — mobile robots (AMRs) · sortation robots",
  },
];

export default function Compare() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-4xl"
        eyebrow="Compare"
        title={
          <>
            Data tools find accounts.
            <br />
            <span className="text-emerald-400">We run your robot sales pipeline.</span>
          </>
        }
        description="Tools like Explee excel at horizontal company search. ReadyForRobots is built for robot companies who need verified buyer intent, the right SKU to pitch, and deals moving in CRM — not another stale list."
        innerClassName="pb-8 text-center [&_.page-hero-title]:mx-auto [&_.page-hero-description]:mx-auto"
      />
      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 pb-20 px-6">
        <div className="max-w-4xl mx-auto">

          <div className="grid md:grid-cols-2 gap-4 mb-12">
            {examples.map((ex) => (
              <div
                key={ex.tool}
                className={`rounded-2xl border p-5 ${
                  ex.tool.includes("Ready")
                    ? "border-emerald-300 bg-emerald-50/60 shadow-sm"
                    : "border-gray-200 bg-white"
                }`}
              >
                <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-2">{ex.tool}</p>
                <p className="text-xs font-mono text-gray-700 mb-3">{ex.query}</p>
                <p className={`text-sm leading-relaxed ${ex.tool.includes("Ready") ? "text-emerald-900 font-medium" : "text-gray-600"}`}>
                  → {ex.result}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden shadow-sm mb-12">
            <div className="grid grid-cols-3 gap-px bg-gray-200 text-[10px] font-bold uppercase tracking-widest">
              <div className="bg-gray-50 px-4 py-3 text-gray-500">Dimension</div>
              <div className="bg-gray-50 px-4 py-3 text-gray-500">GTM data tools</div>
              <div className="bg-emerald-50 px-4 py-3 text-emerald-800">ReadyForRobots</div>
            </div>
            {rows.map((row) => (
              <div key={row.dimension} className="grid grid-cols-3 gap-px bg-gray-100 border-t border-gray-100">
                <div className="bg-white px-4 py-4 text-sm font-semibold text-gray-900">{row.dimension}</div>
                <div className="bg-white px-4 py-4 text-xs text-gray-600 leading-relaxed">{row.dataTools}</div>
                <div className="bg-emerald-50/40 px-4 py-4 text-xs text-emerald-950 leading-relaxed font-medium flex gap-2">
                  {row.rfrWins && <Check className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />}
                  {row.rfr}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 mb-12">
            <h2 className="font-display font-bold text-gray-900 mb-4">When to use which</h2>
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <p className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                  <X className="h-4 w-4 text-red-500" />
                  Stick with a data tool if…
                </p>
                <ul className="space-y-2 text-gray-600 text-xs leading-relaxed">
                  <li>You sell generic B2B SaaS and need maximum company count</li>
                  <li>Your team already built list → enrich → sequence workflows</li>
                  <li>Robot category and timing do not matter for your pitch</li>
                </ul>
              </div>
              <div>
                <p className="font-semibold text-emerald-900 mb-2 flex items-center gap-2">
                  <Check className="h-4 w-4 text-emerald-600" />
                  Use ReadyForRobots if…
                </p>
                <ul className="space-y-2 text-gray-600 text-xs leading-relaxed">
                  <li>You sell robots and need buyers in motion, not cold titles</li>
                  <li>Reps need to know what robot SKU to pitch before the call</li>
                  <li>You want pipeline + HubSpot sync without building lead-ops</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/pipeline"
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition-all text-sm"
            >
              See live pipeline demo
              <ArrowRight size={14} />
            </Link>
            <Link
              href="/signup?next=/pipeline"
              className="inline-flex items-center gap-2 px-6 py-3 border border-gray-300 bg-white hover:bg-gray-50 text-gray-800 font-semibold rounded-xl transition-all text-sm"
            >
              Start free workspace
            </Link>
            <Link
              href="/integrations/hubspot"
              className="inline-flex items-center gap-2 px-5 py-3 text-amber-800 font-semibold rounded-xl border border-amber-300 hover:bg-amber-50 transition-all text-sm"
            >
              Connect HubSpot
            </Link>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
