/**
 * How It Works — ReadyForRobots
 * Hero: SIGNAL in motion + synced 5-step rail. Process: Supabase-style inline prose.
 */

import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import ScoutHeroShowcase from "@/components/ScoutHeroShowcase";
import { Link } from "wouter";
import {
  Zap, Shield, Clock, ArrowRight,
  Briefcase, BarChart3, AlertTriangle, Building2,
  Newspaper, Activity, Globe, MapPin,
} from "lucide-react";

const processSteps: {
  title: string;
  body: string;
  pills?: string[];
}[] = [
  {
    title: "Signal detection",
    body: "Signal monitors OSHA filings, job postings, SEC disclosures, LinkedIn activity, press, permits, and dozens of other public sources — continuously, so your team does not have to.",
    pills: ["150+ sources", "24/7"],
  },
  {
    title: "AI scoring",
    body: "Every signal is scored on Confidence, Urgency, and Fit. Only opportunities at or above the threshold enter your pipeline — noise stays out.",
    pills: ["score ≥ 70"],
  },
  {
    title: "Outreach campaigns",
    body: "For each qualified signal, Signal writes a subject line, opening hook, and call to action tied to the exact trigger event — expansion, filing, hire, CapEx, or pilot news.",
    pills: ["<2 min to draft"],
  },
  {
    title: "You review",
    body: "Choose how much automation you want: Manual (you send everything), Assisted (Signal drafts, you approve), or Auto (high-confidence signals send after a short review window).",
    pills: ["Manual", "Assisted", "Auto"],
  },
  {
    title: "Pipeline advances",
    body: "Replies, opens, and engagement feed back into the pipeline. Signal schedules follow-ups and syncs context to HubSpot—or the CRM your team already uses.",
  },
];

const sources = [
  { icon: Briefcase, label: "Job Postings", sub: "LinkedIn · Indeed · ZipRecruiter" },
  { icon: BarChart3, label: "Earnings Calls", sub: "SEC filings · CapEx announcements" },
  { icon: AlertTriangle, label: "OSHA Filings", sub: "Safety incidents · Workers' comp" },
  { icon: Building2, label: "Real Estate", sub: "Permits · Lease filings · Expansions" },
  { icon: Newspaper, label: "Press Releases", sub: "News · PR Newswire · Business Wire" },
  { icon: Activity, label: "Intent Signals", sub: "RFP databases · Automation searches" },
  { icon: Globe, label: "Web Signals", sub: "Careers pages · Tech stack changes" },
  { icon: MapPin, label: "Local Data", sub: "Permits · Zoning · Construction starts" },
  { icon: BarChart3, label: "Trade Publications", sub: "Industry journals · Analyst reports" },
  { icon: Building2, label: "Facility Expansions", sub: "New sites · Capacity increases" },
  { icon: AlertTriangle, label: "Safety Incidents", sub: "OSHA 300 logs · Inspection reports" },
  { icon: Briefcase, label: "CapEx Announcements", sub: "Capital expenditure filings · Budgets" },
];

const scoreDimensions = [
  { label: "Confidence", sublabel: "Source reliability & corroboration", value: 88, color: "bg-emerald-500" },
  { label: "Urgency", sublabel: "Decision window & buying intent", value: 72, color: "bg-amber-500" },
  { label: "Fit", sublabel: "ICP match & company profile", value: 95, color: "bg-emerald-600" },
];

const autonomyModes = [
  {
    mode: "Manual",
    icon: Shield,
    accent: "text-slate-600",
    tagline: "You control every step",
    steps: ["Signal detected and scored", "You receive a notification", "You review the signal detail", "You write or edit the outreach", "You send when ready"],
  },
  {
    mode: "Assisted",
    icon: Zap,
    accent: "text-emerald-600",
    tagline: "Signal drafts, you approve",
    steps: ["Signal detected and scored", "Signal drafts personalized email", "You review the draft in your queue", "You approve with one click", "Signal sends and tracks response"],
  },
  {
    mode: "Auto",
    icon: Clock,
    accent: "text-amber-600",
    tagline: "Score 85+ triggers automatically",
    steps: ["Signal detected and scored", "Signal drafts personalized email", "Auto-sends after 30-min review window", "Signal tracks replies", "Follow-up scheduled automatically"],
  },
];

const DIV = () => (
  <div className="max-w-6xl mx-auto px-6 lg:px-8">
    <div className="h-px bg-gray-200" />
  </div>
);

function InlinePill({ children }: { children: string }) {
  return (
    <span className="mx-0.5 inline-block rounded px-1.5 py-px text-[13px] font-medium align-baseline font-mono-data text-emerald-700 bg-emerald-50 border border-emerald-200">
      {children}
    </span>
  );
}

export default function HowItWorks() {
  return (
    <div className="min-h-screen flex flex-col bg-white text-gray-900">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-6xl"
        eyebrow="How it works"
        title={
          <>
            From signal to signed deal —{" "}
            <span className="text-emerald-400">automated.</span>
          </>
        }
        description={
          <>
            <span className="font-bold uppercase tracking-widest text-emerald-400">Signal</span>
            {" — robotics prospecting, qualifying, and outreach synced to "}
            <span className="font-bold text-amber-400">HubSpot</span>
            {" or your CRM."}
          </>
        }
        innerClassName="pb-0"
      >
        <div className="grid lg:grid-cols-2 gap-10 lg:gap-12 items-center pb-12 lg:pb-16 pt-4">
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/results?url="
              className="inline-flex items-center gap-2 rounded-xl border border-emerald-500 bg-emerald-600 px-5 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-500 hover:-translate-y-0.5"
            >
              <Zap size={16} />
              Activate SIGNAL
              <ArrowRight size={16} />
            </Link>
            <Link
              href="/pipeline"
              className="btn-secondary-hero"
            >
              Browse live pipeline
              <ArrowRight size={16} className="btn-arrow" />
            </Link>
          </div>
          <ScoutHeroShowcase />
        </div>
      </PageHeroDark>
      <div className="page-hero-fade" aria-hidden />

      <section className="py-6 lg:py-8">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 px-6 py-5">
            <p className="font-display text-sm font-bold text-gray-900 mb-2">Intelligence layer, not a stack replacement</p>
            <p className="text-sm leading-relaxed text-gray-600">
              All-in-one revenue platforms consolidate CRM, sequences, and AI into one workspace—you migrate your stack.
              Signal does the opposite: robotics prospecting, qualifying, and outreach synced to HubSpot, Salesforce, Pipedrive, or your native workspace. Your CRM stays system of record; Signal is system of opportunity.
            </p>
          </div>
        </div>
      </section>

      <DIV />

      <section className="py-12 lg:py-14">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 w-full">
          <p className="section-eyebrow mb-2">The Process</p>
          <h2 className="font-display text-3xl md:text-4xl font-semibold tracking-tight leading-tight w-full">
            <span className="text-emerald-600">Five stages.</span>{" "}
            <span className="text-gray-900">One continuous pipeline.</span>
          </h2>
          <p className="mt-3 text-base md:text-lg leading-relaxed w-full text-gray-600">
            Signal runs prospecting, qualifying, and outreach as one continuous service for robotics sales teams.
            Each stage below maps to what you saw in the hero animation.
          </p>

          <div className="mt-3 w-full">
            {processSteps.map((step, i) => (
              <div key={step.title} className="w-full pb-4 last:pb-0">
                <h3 className="font-display text-lg md:text-xl font-semibold tracking-tight text-emerald-700">
                  {step.title}
                </h3>
                <p className="mt-1.5 text-base md:text-[17px] leading-[1.72] w-full text-gray-600">
                  {step.body}
                  {step.pills?.map((pill) => (
                    <span key={pill}>
                      {" "}
                      <InlinePill>{pill}</InlinePill>
                    </span>
                  ))}
                </p>
                {i < processSteps.length - 1 && (
                  <div className="mt-4 h-px w-full bg-gradient-to-r from-transparent via-emerald-200 to-transparent" aria-hidden />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <DIV />

      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-[260px_1fr] gap-16 items-start">
            <div>
              <p className="section-eyebrow mb-4">Signal Sources</p>
              <h2 className="font-display font-bold text-2xl mb-4 text-gray-900">
                150+ sources,
                <br />
                one pipeline.
              </h2>
              <p className="text-sm leading-relaxed text-gray-600">
                Public and semi-public data across regulatory filings, employment signals,
                financial disclosures, and industry news — normalized into one scored feed.
              </p>
            </div>
            <div className="flex flex-wrap gap-x-8 gap-y-4 pt-2">
              {sources.map((s) => {
                const Icon = s.icon;
                return (
                  <div key={s.label} className="flex items-start gap-2.5 w-[calc(50%-1rem)] lg:w-auto">
                    <Icon size={14} className="text-emerald-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{s.label}</p>
                      <p className="text-xs text-gray-500">{s.sub}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <DIV />

      <section className="py-20 bg-slate-50">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-[260px_1fr] gap-16 items-start">
            <div>
              <p className="section-eyebrow mb-4">Scoring Model</p>
              <h2 className="font-display font-bold text-2xl mb-4 text-gray-900">
                Three dimensions.
                <br />
                One score.
              </h2>
              <p className="text-sm leading-relaxed text-gray-600">
                Signals below 70 are filtered out automatically. Above 70, they enter your pipeline
                with a full breakdown.
              </p>
              <div className="mt-6 flex flex-col gap-2">
                {[["80–100", "text-emerald-600", "Act now"], ["60–79", "text-amber-600", "Watch"], ["<60", "text-gray-400", "Monitor only"]].map(([range, color, label]) => (
                  <div key={range} className="flex items-center gap-3">
                    <span className={`font-mono-data text-xs font-bold w-14 ${color}`}>{range}</span>
                    <span className="text-xs text-gray-500">{label}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-8 pt-2">
              {scoreDimensions.map((dim) => (
                <div key={dim.label}>
                  <div className="flex items-baseline justify-between mb-2">
                    <div className="flex items-baseline gap-3">
                      <span className="font-display font-semibold text-sm text-gray-900">{dim.label}</span>
                      <span className="text-xs text-gray-500">{dim.sublabel}</span>
                    </div>
                    <span className="font-mono-data font-bold text-lg text-emerald-700">{dim.value}</span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden bg-gray-200">
                    <div className={`h-full rounded-full ${dim.color}`} style={{ width: `${dim.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <DIV />

      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <p className="section-eyebrow mb-4">Autonomy Modes</p>
          <h2 className="font-display font-bold text-2xl mb-12 text-gray-900">You choose how much Signal automates.</h2>
          <div className="grid lg:grid-cols-3 gap-8 lg:gap-0">
            {autonomyModes.map((m, mi) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.mode}
                  className={`${mi < 2 ? "lg:pr-12 lg:border-r lg:border-gray-200" : ""} ${mi > 0 ? "lg:pl-12" : ""}`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon size={15} className={m.accent} />
                    <span className="font-display font-semibold text-sm text-gray-900">{m.mode}</span>
                  </div>
                  <p className="text-xs mb-5 text-gray-500">{m.tagline}</p>
                  <ol className="space-y-2.5">
                    {m.steps.map((s, si) => (
                      <li key={si} className="flex items-start gap-2.5">
                        <span className={`font-mono-data text-xs mt-0.5 shrink-0 ${m.accent}`}>{si + 1}.</span>
                        <span className="text-sm leading-relaxed text-gray-600">{s}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <DIV />

      <section className="py-20 bg-emerald-50/50">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h2 className="font-display font-bold text-2xl mb-2 text-gray-900">Ready to automate your pipeline?</h2>
              <p className="text-sm text-gray-600">Enter your company URL and see your first signals in seconds.</p>
            </div>
            <Link
              href="/results?url="
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700 hover:-translate-y-0.5"
            >
              Find buyers <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
