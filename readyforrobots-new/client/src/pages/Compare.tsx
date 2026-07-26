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

const rfrEngine = [
  {
    title: "Discover",
    copy: "Scan for automation signals across labor, expansion, capex, deployment, and operations events.",
  },
  {
    title: "Curate",
    copy: "Filter noisy opportunities into relevant robotics demand with context that sales teams can trust.",
  },
  {
    title: "Qualify",
    copy: "Score readiness and urgency so reps spend time on buyers likely to move this quarter.",
  },
  {
    title: "Categorize",
    copy: "Classify by industry and workflow to match each account to the right deployment motion.",
  },
  {
    title: "Configure",
    copy: "Recommend robot types, timing, and next action so outreach can start immediately.",
  },
];

const crmGenerations = [
  { generation: "CRM 1.0", purpose: "Store customer information", example: "Salesforce" },
  { generation: "CRM 2.0", purpose: "Automate sales workflow", example: "HubSpot" },
  { generation: "CRM 3.0", purpose: "AI-assisted selling", example: "Reevo, Attio AI, HubSpot AI" },
  { generation: "CRM 4.0", purpose: "Autonomous revenue generation", example: "ReadyForRobots" },
];

const capabilityRows = [
  { capability: "CRM", salesforce: "Yes", hubspot: "Yes", reevo: "Yes", rfr: "Yes (lightweight)" },
  { capability: "Contact management", salesforce: "Yes", hubspot: "Yes", reevo: "Yes", rfr: "Yes" },
  { capability: "Pipeline management", salesforce: "Yes", hubspot: "Yes", reevo: "Yes", rfr: "Yes" },
  { capability: "Email automation", salesforce: "Yes", hubspot: "Yes", reevo: "Yes", rfr: "Yes" },
  { capability: "AI email writing", salesforce: "Partial", hubspot: "Yes", reevo: "Yes", rfr: "Yes" },
  { capability: "Workflow automation", salesforce: "Yes", hubspot: "Yes", reevo: "Yes", rfr: "Yes" },
  { capability: "Meeting scheduling", salesforce: "Yes", hubspot: "Yes", reevo: "Yes", rfr: "Yes" },
  { capability: "Lead database", salesforce: "Partial", hubspot: "Partial", reevo: "Yes", rfr: "Robot-specific" },
  { capability: "Intent signals", salesforce: "Limited", hubspot: "Limited", reevo: "Coming soon", rfr: "Robot deployment signals" },
  { capability: "Company research", salesforce: "Partial", hubspot: "Partial", reevo: "Yes", rfr: "Continuous AI research" },
  { capability: "Industry intelligence", salesforce: "Limited", hubspot: "Limited", reevo: "Limited", rfr: "Robotics only" },
  { capability: "Robot readiness score", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Detect companies ready for robots", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Detect labor shortages", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Estimate automation ROI", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Recommend robot vendors", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Match customer to OEM", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Build outreach campaign", salesforce: "Partial", hubspot: "Partial", reevo: "Yes", rfr: "Yes" },
  { capability: "AI runs outreach automatically", salesforce: "No", hubspot: "Partial", reevo: "Partial", rfr: "Yes" },
  { capability: "Finds new buyers daily", salesforce: "No", hubspot: "No", reevo: "Partial", rfr: "Yes" },
  { capability: "Tracks competitor activity", salesforce: "Partial", hubspot: "Partial", reevo: "Partial", rfr: "Yes" },
  { capability: "Understands robot capabilities", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Understands facility requirements", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Deployment planning", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Pilot program management", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
  { capability: "Robot ROI dashboard", salesforce: "No", hubspot: "No", reevo: "No", rfr: "Yes" },
];

export default function Compare() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-5xl"
        eyebrow="Compare"
        title={
          <>
            Data tools surface opportunities.
            <br />
            <span className="text-sky-300">ReadyForRobots delivers qualified leads ready for engagement.</span>
          </>
        }
        description="Tools like Explee help teams discover broad opportunities. ReadyForRobots is built for robot companies that need sales leads already qualified by live buyer intent and ready for immediate outreach in CRM."
        innerClassName="pb-8 text-center [&_.page-hero-title]:mx-auto [&_.page-hero-title]:text-4xl md:[&_.page-hero-title]:text-6xl [&_.page-hero-title]:leading-[1.02] [&_.page-hero-title]:tracking-tight [&_.page-hero-description]:mx-auto [&_.page-hero-description]:text-base md:[&_.page-hero-description]:text-lg [&_.page-hero-description]:leading-relaxed"
      />
      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 pb-20 px-6 antialiased bg-[radial-gradient(circle_at_top,rgba(15,23,42,0.045),transparent_52%)]">
        <div className="max-w-5xl mx-auto">

          <section className="mb-10 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-md shadow-slate-200/50">
            <div className="grid grid-cols-1 gap-px bg-slate-200 md:grid-cols-2">
              <div className="border-l-2 border-slate-400 bg-white p-6 md:p-7 text-slate-900">
                <p className="mb-2 text-[11px] font-black uppercase tracking-[0.14em] text-slate-700">GTM data tools</p>
                <p className="text-2xl md:text-3xl font-black tracking-tight leading-tight text-slate-900">Search-heavy workflow</p>
                <p className="mt-2 text-[15px] leading-relaxed text-slate-700">Great for broad prospect discovery, but your team still has to decide timing, message, and next action manually.</p>
                <div className="mt-4 inline-flex rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.08em] text-slate-700">
                  Output: records to sort
                </div>
              </div>
              <div className="border-l-2 border-sky-500 bg-sky-50 p-6 md:p-7 text-slate-900">
                <p className="mb-2 text-[11px] font-black uppercase tracking-[0.14em] text-sky-700">ReadyForRobots</p>
                <p className="text-2xl md:text-3xl font-black tracking-tight leading-tight text-slate-900">Execution-ready workflow</p>
                <p className="mt-2 text-[15px] leading-relaxed text-slate-700">Built for robot teams that need verified buyer intent, SKU guidance, and clear pipeline next steps in CRM.</p>
                <div className="mt-4 inline-flex rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.08em] text-sky-700">
                  Output: actions to run
                </div>
              </div>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="mb-4 text-center font-display text-3xl md:text-4xl font-black tracking-tight leading-tight text-slate-900">Same query, different outcome</h2>
            <div className="grid md:grid-cols-2 gap-4">
            {examples.map((ex) => (
              <div
                key={ex.tool}
                className={`rounded-2xl border p-5 ${
                  ex.tool.includes("Ready")
                    ? "border-sky-200 bg-sky-50 text-slate-900 shadow-sm"
                    : "border-slate-200 bg-white text-slate-900"
                }`}
              >
                <p className={`text-[11px] font-black uppercase tracking-[0.12em] mb-2 ${ex.tool.includes("Ready") ? "text-sky-700" : "text-slate-700"}`}>{ex.tool}</p>
                <p className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.09em] mb-3 ${ex.tool.includes("Ready") ? "border-sky-200 bg-sky-50 text-sky-700" : "border-slate-300 bg-slate-100 text-slate-700"}`}>
                  {ex.tool.includes("Ready") ? "Action output" : "List output"}
                </p>
                <p className="text-xs font-mono text-slate-700 mb-3">{ex.query}</p>
                <p className={`text-base leading-relaxed font-semibold ${ex.tool.includes("Ready") ? "text-sky-900" : "text-slate-900"}`}>
                  → {ex.result}
                </p>
              </div>
            ))}
            </div>
          </section>

          <section className="mb-12">
            <h2 className="mb-4 text-center font-display text-3xl md:text-4xl font-black tracking-tight leading-tight text-slate-900">Panel-by-panel difference</h2>
            <div className="space-y-3">
              {rows.map((row) => (
                <article key={row.dimension} className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5 shadow-sm">
                  <p className="mb-3 text-sm font-black uppercase tracking-[0.1em] text-slate-600">{row.dimension}</p>
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <div className="rounded-xl border border-slate-300 bg-white p-3.5">
                      <p className="mb-1.5 text-[10px] font-black uppercase tracking-[0.1em] text-slate-700">GTM data tools</p>
                      <p className="flex gap-2 text-[13px] leading-relaxed text-slate-900">
                        <X className="h-4 w-4 shrink-0 text-slate-600 mt-0.5" />
                        <span>{row.dataTools}</span>
                      </p>
                    </div>
                    <div className="rounded-xl border border-sky-200 bg-sky-50 p-3.5">
                      <p className="mb-1.5 text-[10px] font-black uppercase tracking-[0.1em] text-sky-700">ReadyForRobots</p>
                      <p className="flex gap-2 text-[13px] leading-relaxed text-sky-950 font-semibold">
                        {row.rfrWins && <Check className="h-4 w-4 shrink-0 text-sky-600 mt-0.5" />}
                        <span>{row.rfr}</span>
                      </p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="mb-12 rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="font-display text-2xl md:text-3xl font-black tracking-tight text-slate-900 mb-2">Why ReadyForRobots wins in robotics sales</h2>
            <p className="text-sm text-slate-600 leading-relaxed mb-5">
              ReadyForRobots does the heavy lift before a rep sends the first message: discover, curate, and qualify leads, then map each account to industry, robot type, and timing.
            </p>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
              {rfrEngine.map((step) => (
                <div key={step.title} className="rounded-xl border border-sky-200 bg-sky-50 p-3.5">
                  <p className="text-[10px] font-black uppercase tracking-[0.1em] text-sky-700 mb-1.5">{step.title}</p>
                  <p className="text-[13px] leading-relaxed text-slate-800">{step.copy}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mb-12 rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="font-display text-2xl md:text-3xl font-black tracking-tight text-slate-900 mb-4">CRM evolution: from records to autonomous revenue</h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              {crmGenerations.map((row) => (
                <article key={row.generation} className={`rounded-xl border p-4 ${row.generation === "CRM 4.0" ? "border-sky-300 bg-sky-50" : "border-slate-200 bg-slate-50"}`}>
                  <p className={`text-[10px] font-black uppercase tracking-[0.1em] mb-1.5 ${row.generation === "CRM 4.0" ? "text-sky-700" : "text-slate-700"}`}>{row.generation}</p>
                  <p className="text-sm font-semibold text-slate-900 mb-1.5">{row.purpose}</p>
                  <p className="text-xs text-slate-600">{row.example}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="mb-12 rounded-2xl border border-slate-200 bg-white p-6 overflow-hidden">
            <h2 className="font-display text-2xl md:text-3xl font-black tracking-tight text-slate-900 mb-4">Capability comparison</h2>
            <div className="overflow-x-auto">
              <table className="min-w-[900px] w-full border-collapse">
                <thead>
                  <tr className="text-left">
                    <th className="border-b border-slate-200 bg-slate-50 px-3 py-2 text-[10px] font-black uppercase tracking-[0.1em] text-slate-700">Capability</th>
                    <th className="border-b border-slate-200 bg-slate-50 px-3 py-2 text-[10px] font-black uppercase tracking-[0.1em] text-slate-700">Salesforce</th>
                    <th className="border-b border-slate-200 bg-slate-50 px-3 py-2 text-[10px] font-black uppercase tracking-[0.1em] text-slate-700">HubSpot</th>
                    <th className="border-b border-slate-200 bg-slate-50 px-3 py-2 text-[10px] font-black uppercase tracking-[0.1em] text-slate-700">Reevo</th>
                    <th className="border-b border-sky-200 bg-sky-50 px-3 py-2 text-[10px] font-black uppercase tracking-[0.1em] text-sky-800">ReadyForRobots</th>
                  </tr>
                </thead>
                <tbody>
                  {capabilityRows.map((row) => (
                    <tr key={row.capability}>
                      <td className="border-b border-slate-100 px-3 py-2 text-[13px] font-semibold text-slate-900">{row.capability}</td>
                      <td className="border-b border-slate-100 px-3 py-2 text-[13px] text-slate-700">{row.salesforce}</td>
                      <td className="border-b border-slate-100 px-3 py-2 text-[13px] text-slate-700">{row.hubspot}</td>
                      <td className="border-b border-slate-100 px-3 py-2 text-[13px] text-slate-700">{row.reevo}</td>
                      <td className="border-b border-sky-100 bg-sky-50/70 px-3 py-2 text-[13px] font-semibold text-sky-900">{row.rfr}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 mb-12">
            <h2 className="font-display text-2xl md:text-3xl font-black tracking-tight text-gray-900 mb-2">vs Revenue OS (Reevo, etc.)</h2>
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">
              Reevo and similar platforms are building horizontal AI-native revenue operating systems for broad B2B teams.
              ReadyForRobots is vertical: autonomous robotics revenue generation grounded in deployment signals, facility context, and robot-commercialization workflows.
            </p>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.1em] text-gray-500 mb-2">Revenue OS pitch</p>
                <p className="text-[13px] text-gray-700 leading-relaxed italic">
                  “Replace fragmented sales tools… surface opportunities… recommend next steps… one platform for marketing, sales, and CS.”
                </p>
                <p className="mt-2 text-[13px] text-gray-500">Horizontal. No robot category. No SKU-level pitch.</p>
              </div>
              <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.1em] text-sky-800 mb-2">ReadyForRobots</p>
                <p className="text-[13px] text-sky-950 leading-relaxed font-semibold">
                  Live robot-buyer signals → HOT/WARM timing → pipeline_action + robot_types_needed → Cal outreach draft → save &amp; sync to HubSpot.
                </p>
                <p className="mt-2 text-[13px] text-sky-800">Vertical pipeline. Proof before signup on /pipeline.</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 mb-12">
            <h2 className="font-display text-2xl md:text-3xl font-black tracking-tight text-gray-900 mb-4">When to use which</h2>
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <p className="font-black text-gray-800 mb-2 flex items-center gap-2">
                  <X className="h-4 w-4 text-red-500" />
                  Stick with a data tool if…
                </p>
                <ul className="space-y-2 text-gray-600 text-[13px] leading-relaxed">
                  <li>You are replacing Salesforce + Outreach with one horizontal revenue platform</li>
                  <li>You sell generic B2B SaaS and need maximum company count</li>
                  <li>Your team already built list → enrich → sequence workflows</li>
                  <li>Robot category and timing do not matter for your pitch</li>
                </ul>
              </div>
              <div>
                <p className="font-black text-sky-900 mb-2 flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-600" />
                  Use ReadyForRobots if…
                </p>
                <ul className="space-y-2 text-gray-600 text-[13px] leading-relaxed">
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
