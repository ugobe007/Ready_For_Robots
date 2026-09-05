/**
 * Jobs chrome for the pstack protocol. Honest, not a chatbot.
 */
import { Link } from "wouter";
import {
  PSTACK_ABOUT_HREF,
  PSTACK_CHROME_EYEBROW,
  PSTACK_CHROME_FOOT,
  PSTACK_CHROME_LEAD,
  PSTACK_CHROME_TITLE,
  PSTACK_ROLES,
  jobsMatcherPath,
} from "@/lib/pstackSite";

export default function JobsPstackProtocol({
  compact = false,
  aboutLink = true,
}: {
  compact?: boolean;
  aboutLink?: boolean;
}) {
  if (compact) {
    return (
      <aside
        aria-label="Jobs agent protocol"
        className="border border-slate-600 bg-[#081126] px-3 py-3 text-sm leading-relaxed text-slate-300"
      >
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-400">
          {PSTACK_CHROME_EYEBROW}
        </p>
        <p className="mt-1.5">
          These jobs came from {jobsMatcherPath()}. How, Act, and Critic govern
          site agents. They do not rewrite the matcher.
        </p>
      </aside>
    );
  }

  return (
    <section
      id="jobs-protocol"
      aria-label="Jobs agent protocol"
      className="border border-slate-600 bg-[#081126]"
    >
      <div className="grid grid-cols-1 gap-px bg-slate-600 lg:grid-cols-[1.2fr_1fr]">
        <div className="bg-[#0b162f] px-4 py-4 sm:px-5">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-400">
            {PSTACK_CHROME_EYEBROW}
          </p>
          <h2 className="mt-2 font-display text-lg font-bold text-white sm:text-xl">
            {PSTACK_CHROME_TITLE}
          </h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-300">
            {PSTACK_CHROME_LEAD}
          </p>
          <p className="mt-2 font-mono text-[12px] text-emerald-300">
            {jobsMatcherPath()}
          </p>
          {aboutLink ? (
            <Link
              href={PSTACK_ABOUT_HREF}
              className="mt-3 inline-flex text-sm font-semibold text-emerald-400 hover:text-emerald-300"
            >
              Protocol on About
            </Link>
          ) : null}
        </div>
        <div className="bg-[#0b162f] px-4 py-4 sm:px-5">
          <ul className="space-y-2.5">
            {PSTACK_ROLES.map(role => (
              <li
                key={role.id}
                className="border-l-2 border-emerald-400/50 pl-3"
              >
                <p className="text-sm font-semibold text-slate-100">
                  {role.label}
                </p>
                <p className="mt-0.5 text-xs leading-relaxed text-slate-400">
                  {role.job}
                </p>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs leading-relaxed text-slate-500">
            {PSTACK_CHROME_FOOT}
          </p>
        </div>
      </div>
    </section>
  );
}
