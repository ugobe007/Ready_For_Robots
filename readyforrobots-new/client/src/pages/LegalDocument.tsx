import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { Link } from "wouter";
import {
  JOBS_HEADER_OFFSET_CLASS,
  jobsFreshHomeHref,
} from "@/lib/jobsWorkflow";
import { jobsFindHref } from "@/lib/jobsLanding";

export type LegalSection = { title: string; body: string[] };

export default function LegalDocument({
  eyebrow,
  title,
  description,
  effectiveDate,
  sections,
}: {
  eyebrow: string;
  title: string;
  description: string;
  effectiveDate: string;
  sections: LegalSection[];
}) {
  return (
    <div className={`min-h-screen bg-gray-50 ${JOBS_HEADER_OFFSET_CLASS}`}>
      <ExperimentHeader />
      <PageHeroDark eyebrow={eyebrow} title={title} description={description} />

      <main className="max-w-2xl mx-auto px-4 sm:px-6 pb-16 -mt-4 relative z-10">
        <article className="rounded-2xl border border-gray-200 bg-white p-6 sm:p-10 shadow-sm">
          <p className="text-sm text-gray-500 mb-8">Effective date: {effectiveDate}</p>

          {sections.map(section => (
            <section key={section.title} className="mb-8 last:mb-0">
              <h2 className="text-lg font-bold text-gray-900 mb-3">{section.title}</h2>
              <div className="space-y-3">
                {section.body.map(para => (
                  <p
                    key={para.slice(0, 48)}
                    className="text-sm leading-relaxed text-gray-700"
                  >
                    {para}
                  </p>
                ))}
              </div>
            </section>
          ))}

          <p className="mt-10 pt-6 border-t border-gray-100 text-sm text-gray-600">
            <Link href="/privacy" className="font-semibold text-emerald-700 hover:underline">
              Privacy
            </Link>
            {" · "}
            <Link href="/terms" className="font-semibold text-emerald-700 hover:underline">
              Terms
            </Link>
            {" · "}
            <Link href="/support" className="font-semibold text-emerald-700 hover:underline">
              Support
            </Link>
            {" · "}
            <Link href={jobsFindHref()} className="font-semibold text-emerald-700 hover:underline">
              Find jobs
            </Link>
            {" · "}
            <Link href={jobsFreshHomeHref()} className="font-semibold text-emerald-700 hover:underline">
              Home
            </Link>
          </p>
        </article>
      </main>
      <SiteFooter />
    </div>
  );
}
