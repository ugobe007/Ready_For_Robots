/**
 * Pricing — early access (website copy v1 §6).
 * One founding-customer card until live buyer signals ship (spec Phase 5).
 */
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  HelpCircle,
} from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { JOBS_HEADER_OFFSET_CLASS } from "@/lib/jobsWorkflow";

const EARLY_ACCESS_HREF = "/signup?next=/&src=pricing_early_access";

const FOUNDING_FEATURES = [
  "Free during early access",
  "Buyer matches for every robot you sell",
  "Save buyers and get notified when new ones appear",
] as const;

const FOUNDING_PRICE_PLACEHOLDER = "[founding price, e.g. $X/month]";

const PRICING_FAQS = [
  {
    q: "Where do buyer signals come from?",
    a: "Public procurement notices, company filings and announcements, news, and automation hiring at buyer companies. Every signal links to its source.",
  },
  {
    q: "Do you sell contact lists?",
    a: "No. We show which companies are moving to automate and why. Contact data comes later, opt-in.",
  },
  {
    q: "What does early access cost?",
    a: "Nothing. Founding customers lock in their price before launch.",
  },
] as const;

export default function Pricing() {
  return (
    <div
      className={`pricing-page min-h-screen flex flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />

      <PageHeroDark
        maxWidthClass="max-w-3xl"
        eyebrow="Pricing"
        title="Early access"
        description="Ready For Robots is in early access. Use it free while we roll out live buyer signals by industry."
        innerClassName="pb-8 text-center [&_.page-hero-title]:mx-auto [&_.page-hero-description]:mx-auto"
      />
      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 px-6 pb-20">
        <div className="mx-auto max-w-3xl space-y-12">
          <section
            id="founding-customer"
            className="mx-auto max-w-md rounded-2xl border border-emerald-300 bg-white p-7 text-gray-900 shadow-lg ring-1 ring-emerald-200"
          >
            <h2 className="font-display text-xl font-extrabold">
              Founding customer
            </h2>
            <ul className="mt-5 space-y-2.5">
              {FOUNDING_FEATURES.map(feature => (
                <li key={feature} className="flex items-start gap-2.5">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  <span className="text-sm text-gray-700">{feature}</span>
                </li>
              ))}
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <span className="text-sm text-gray-700">
                  Founding customers lock in{" "}
                  <strong>{FOUNDING_PRICE_PLACEHOLDER}</strong> when live
                  signals launch
                </span>
              </li>
            </ul>
            <a
              href={EARLY_ACCESS_HREF}
              className="mt-7 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700"
            >
              Get early access <ArrowRight className="h-3.5 w-3.5" />
            </a>
          </section>

          <section className="rounded-2xl border border-amber-200 bg-amber-50/50 p-6">
            <div className="flex items-start gap-4">
              <HelpCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
              <div>
                <p className="mb-1 text-sm font-semibold text-amber-800">
                  Optional services
                </p>
                <p className="text-sm leading-relaxed text-gray-600">
                  Help with setup, integration planning, and installation
                  through vetted local partners. Scoped separately.
                </p>
              </div>
            </div>
          </section>

          <section id="faq">
            <h2 className="mb-6 font-display text-[clamp(1.4rem,2.5vw,1.8rem)] font-extrabold text-white">
              Questions
            </h2>
            <div className="space-y-2">
              {PRICING_FAQS.map(faq => (
                <details
                  key={faq.q}
                  className="group overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"
                >
                  <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-left">
                    <span className="text-sm font-semibold text-gray-800">
                      {faq.q}
                    </span>
                    <ChevronDown className="ml-4 h-4 w-4 shrink-0 text-gray-400 transition-transform group-open:rotate-180" />
                  </summary>
                  <p className="border-t border-gray-100 px-5 pb-4 pt-3 text-sm leading-relaxed text-gray-600">
                    {faq.a}
                  </p>
                </details>
              ))}
            </div>
          </section>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
