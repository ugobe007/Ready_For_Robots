/**
 * Compare — Jobs for robots vs sales lists and human job boards.
 */
import { ArrowRight, Check, X } from "lucide-react";
import { Link } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import {
  FIND_JOBS_CTA,
  JOBS_HEADER_OFFSET_CLASS,
  jobsFreshHomeHref,
} from "@/lib/jobsWorkflow";

const rows: {
  dimension: string;
  other: string;
  rfr: string;
}[] = [
  {
    dimension: "What you get",
    other: "Company lists, contact exports, or human job postings",
    rfr: "Robot Job Cards — employer, workplace, work, and why this robot qualifies",
  },
  {
    dimension: "Input",
    other: "Titles, industries, keywords, or a human resume",
    rfr: "A robot URL. We read the SKU, not a category guess.",
  },
  {
    dimension: "Unit of value",
    other: "A row in a CRM or a person to email",
    rfr: "A job the machine can actually do",
  },
  {
    dimension: "Match",
    other: "Firmographics, lookalikes, or keyword overlap",
    rfr: "Job requirements ↔ robot capabilities and the task models that job needs",
  },
  {
    dimension: "Output",
    other: "Records to sort. You still invent the pitch.",
    rfr: "Named employers and specific work. Keep five jobs in CRM on free.",
  },
  {
    dimension: "Best for",
    other: "SDR teams buying lists, or people looking for human work",
    rfr: "OEMs, integrators, and fleets placing robots into work",
  },
];

const examples = [
  {
    tool: "Explee / Apollo-style search",
    query: "CTOs at warehouse companies in Texas",
    result:
      "Hundreds of contacts — no job, no workplace, no proof a robot belongs there",
    ours: false,
  },
  {
    tool: "ReadyForRobots Jobs",
    query: "Paste your robot URL",
    result:
      "Job cards for that SKU: who employs, where the work is, what the robot would do",
    ours: true,
  },
];

const whenOther = [
  "You need a horizontal company database to export into your own stack",
  "You are hiring humans and want Indeed-style postings",
  "Robot capability and the work itself do not matter for your search",
];

const whenUs = [
  "You have a robot (or a line of robots) and need jobs it is qualified to perform",
  "You want named employers and workplaces, not a list of accounts to pitch",
  "You will keep matched jobs in CRM and place later — sale follows the job",
];

export default function Compare() {
  return (
    <div
      className={`compare-page flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />
      <PageHeroDark
        maxWidthClass="max-w-5xl"
        eyebrow="Compare"
        title={
          <>
            Sales lists find buyers.
            <br />
            <span className="text-emerald-400">
              We find jobs for your robot.
            </span>
          </>
        }
        description="Explee, Apollo, and similar tools sell company and people search. Job boards list work for humans. ReadyForRobots matches a robot URL to specific jobs — employer, workplace, and work the machine can do."
      />

      <main className="flex-1 px-6 pb-20">
        <div className="mx-auto max-w-5xl space-y-12">
          <section className="overflow-hidden border border-slate-600">
            <div className="grid grid-cols-1 gap-px bg-slate-700 md:grid-cols-2">
              <div className="border-l-2 border-slate-500 bg-[#0b162f] p-6 md:p-7">
                <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">
                  GTM data tools &amp; job boards
                </p>
                <p className="text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
                  Lists of companies or people
                </p>
                <p className="mt-2 text-[15px] leading-relaxed text-slate-300">
                  Useful if you are selling to a title. They do not say which
                  job a robot is qualified to perform.
                </p>
                <div className="mt-4 inline-flex border border-slate-600 bg-[#081126] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.08em] text-slate-400">
                  Output: records to sort
                </div>
              </div>
              <div className="border-l-2 border-emerald-400 bg-[#0b162f] p-6 md:p-7">
                <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-400">
                  ReadyForRobots
                </p>
                <p className="text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
                  Jobs for a specific robot
                </p>
                <p className="mt-2 text-[15px] leading-relaxed text-slate-300">
                  Paste a robot URL. We return employment cards: who has the
                  work, where it happens, and why this SKU fits.
                </p>
                <div className="mt-4 inline-flex border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.08em] text-emerald-300">
                  Output: Robot Job Cards
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 className="mb-4 text-center font-display text-3xl font-bold tracking-tight text-slate-100 md:text-4xl">
              Same search reflex, different product
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {examples.map(ex => (
                <div
                  key={ex.tool}
                  className={`border p-5 ${
                    ex.ours
                      ? "border-emerald-500/40 bg-emerald-500/5"
                      : "border-slate-600 bg-[#0b162f]"
                  }`}
                >
                  <p
                    className={`mb-2 text-[11px] font-bold uppercase tracking-[0.12em] ${
                      ex.ours ? "text-emerald-400" : "text-slate-400"
                    }`}
                  >
                    {ex.tool}
                  </p>
                  <p className="mb-3 font-mono text-xs text-slate-400">
                    {ex.query}
                  </p>
                  <p className="text-base font-semibold leading-relaxed text-slate-100">
                    → {ex.result}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="overflow-hidden border border-slate-600 bg-[#0b162f]">
            <h2 className="border-b border-slate-600 px-5 py-4 font-display text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
              Side by side
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-left">
                <thead>
                  <tr>
                    <th className="border-b border-slate-700 bg-[#081126] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">
                      Dimension
                    </th>
                    <th className="border-b border-slate-700 bg-[#081126] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">
                      Lists &amp; boards
                    </th>
                    <th className="border-b border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-[10px] font-bold uppercase tracking-[0.1em] text-emerald-300">
                      ReadyForRobots
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(row => (
                    <tr key={row.dimension}>
                      <td className="border-b border-slate-800 px-4 py-3 text-[13px] font-semibold text-slate-200">
                        {row.dimension}
                      </td>
                      <td className="border-b border-slate-800 px-4 py-3 text-[13px] text-slate-400">
                        {row.other}
                      </td>
                      <td className="border-b border-slate-800 bg-emerald-500/5 px-4 py-3 text-[13px] font-semibold text-slate-100">
                        {row.rfr}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="grid gap-6 md:grid-cols-2">
            <div className="border border-slate-600 bg-[#0b162f] p-6">
              <p className="mb-3 flex items-center gap-2 font-bold text-slate-200">
                <X className="h-4 w-4 text-red-400" />
                Stick with a list tool if…
              </p>
              <ul className="space-y-2 text-[13px] leading-relaxed text-slate-400">
                {whenOther.map(line => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
            <div className="border border-emerald-500/40 bg-emerald-500/5 p-6">
              <p className="mb-3 flex items-center gap-2 font-bold text-emerald-300">
                <Check className="h-4 w-4 text-emerald-400" />
                Use ReadyForRobots if…
              </p>
              <ul className="space-y-2 text-[13px] leading-relaxed text-slate-300">
                {whenUs.map(line => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          </section>

          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href={jobsFreshHomeHref()}
              className="inline-flex items-center gap-2 border border-emerald-400 bg-emerald-500/15 px-6 py-3 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-500/25"
            >
              {FIND_JOBS_CTA}
              <ArrowRight size={14} />
            </Link>
            <Link
              href="/signup?src=jobs_activate&next=/"
              className="inline-flex items-center gap-2 border border-slate-600 bg-[#0b162f] px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-400"
            >
              Keep jobs in CRM
            </Link>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
