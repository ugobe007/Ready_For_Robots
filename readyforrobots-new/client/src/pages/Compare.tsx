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
        <div className="max-w-5xl mx-auto">

          <section className="mb-10 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="grid grid-cols-1 gap-px bg-slate-200 md:grid-cols-2">
              <div className="bg-rose-50 p-5">
                <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-rose-700">GTM data tools</p>
                <p className="text-sm font-semibold text-rose-900">Built for search and list building</p>
                <p className="mt-2 text-xs leading-relaxed text-rose-800">Best when your team wants broad account coverage and handles qualification, timing, and outreach externally.</p>
              </div>
              <div className="bg-emerald-50 p-5">
                <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-emerald-700">ReadyForRobots</p>
                <p className="text-sm font-semibold text-emerald-900">Built for robot sales execution</p>
                <p className="mt-2 text-xs leading-relaxed text-emerald-800">Best when you need verified buyer intent, SKU-level pitch guidance, and pipeline movement inside CRM.</p>
              </div>
            </div>
          </section>

          <div className="grid md:grid-cols-2 gap-4 mb-12">
            {examples.map((ex) => (
              <div
                key={ex.tool}
                className={`rounded-2xl border p-5 ${
                  ex.tool.includes("Ready")
                    ? "border-emerald-300 bg-emerald-50/60 shadow-sm"
                    : "border-rose-200 bg-rose-50/50"
                }`}
              >
                <p className={`text-[10px] font-bold uppercase tracking-widest mb-2 ${ex.tool.includes("Ready") ? "text-emerald-700" : "text-rose-700"}`}>{ex.tool}</p>
                <p className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider mb-3 ${ex.tool.includes("Ready") ? "border-emerald-300 bg-emerald-100 text-emerald-800" : "border-rose-300 bg-rose-100 text-rose-800"}`}>
                  {ex.tool.includes("Ready") ? "Action output" : "List output"}
                </p>
                <p className="text-xs font-mono text-gray-700 mb-3">{ex.query}</p>
                <p className={`text-sm leading-relaxed ${ex.tool.includes("Ready") ? "text-emerald-900 font-medium" : "text-rose-900"}`}>
                  → {ex.result}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden shadow-sm mb-12">
            <div className="grid grid-cols-1 gap-px bg-gray-200 text-[10px] font-bold uppercase tracking-widest md:grid-cols-[190px_1fr_1fr]">
              <div className="bg-gray-50 px-4 py-3 text-gray-500">Dimension</div>
              <div className="bg-rose-50 px-4 py-3 text-rose-700">GTM data tools</div>
              <div className="bg-emerald-50 px-4 py-3 text-emerald-800">ReadyForRobots</div>
            </div>
            {rows.map((row) => (
              <div key={row.dimension} className="grid grid-cols-1 gap-px bg-gray-100 border-t border-gray-100 md:grid-cols-[190px_1fr_1fr]">
                <div className="bg-white px-4 py-4 text-sm font-semibold text-gray-900">{row.dimension}</div>
                <div className="bg-rose-50/40 px-4 py-4 text-xs text-rose-900 leading-relaxed flex gap-2">
                  <X className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                  {row.dataTools}
                </div>
                <div className="bg-emerald-50/50 px-4 py-4 text-xs text-emerald-950 leading-relaxed font-medium flex gap-2">
                  {row.rfrWins && <Check className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />}
                  {row.rfr}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 mb-12">
            <h2 className="font-display font-bold text-gray-900 mb-2">vs Revenue OS (Reevo, etc.)</h2>
            <p className="text-xs text-gray-600 mb-4 leading-relaxed">
              Well-funded platforms pitch one system to replace CRM + engagement + intelligence for any B2B team.
              ReadyForRobots does not ask you to migrate your stack—we add a robotics pipeline on top.
            </p>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-2">Revenue OS pitch</p>
                <p className="text-xs text-gray-700 leading-relaxed italic">
                  “Replace fragmented sales tools… surface opportunities… recommend next steps… one platform for marketing, sales, and CS.”
                </p>
                <p className="mt-2 text-xs text-gray-500">Horizontal. No robot category. No SKU-level pitch.</p>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800 mb-2">ReadyForRobots</p>
                <p className="text-xs text-emerald-950 leading-relaxed font-medium">
                  Live robot-buyer signals → HOT/WARM timing → pipeline_action + robot_types_needed → Cal outreach draft → save &amp; sync to HubSpot.
                </p>
                <p className="mt-2 text-xs text-emerald-800">Vertical pipeline. Proof before signup on /pipeline.</p>
              </div>
            </div>
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
                  <li>You are replacing Salesforce + Outreach with one horizontal revenue platform</li>
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
                  <li>You sell robots and need buyers in motion, not cold titles or generic CRM AI</li>
                  <li>Reps need to know what robot SKU to pitch before the call</li>
                  <li>You want pipeline + HubSpot sync without a full GTM stack migration</li>
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
