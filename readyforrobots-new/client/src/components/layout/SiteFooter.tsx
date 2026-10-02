/**
 * Shared site footer — product, support, and account links.
 * Newsletter signup is optional (Home passes handlers; other pages omit).
 * Jobs chrome (header-matched) has no Pipeline / SIGNAL.
 */
import { useState } from "react";
import { Link, useLocation, useSearch } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  jobsCrmOpenHref,
  jobsFreshHomeHref,
  showJobsSiteChrome,
} from "@/lib/jobsWorkflow";

type Props = {
  newsletterEmail?: string;
  newsletterStatus?: "idle" | "submitting" | "success" | "error";
  onEmailChange?: (v: string) => void;
  onNewsletterSubmit?: (e: React.FormEvent<HTMLFormElement>) => void;
  hideNewsletter?: boolean;
};

const SUPPORT_LINKS = [
  { label: "Pricing", href: "/pricing" },
  { label: "Compare", href: "/compare" },
  { label: "Intelligence", href: "/intelligence" },
  { label: "Integrations", href: "/integrations" },
  { label: "FAQ", href: "/pricing#faq" },
];

const COMPANY_LINKS = [
  { label: "About", href: "/intelligence" },
  { label: "Compare", href: "/compare" },
  { label: "Find Robots", href: "/find-robots" },
  { label: "Job site sketch", href: "/vendor/design" },
  { label: "Privacy Policy", href: "/privacy" },
  { label: "Terms", href: "/terms" },
  { label: "Support", href: "/support" },
];

function jobsProductLinks(signedIn: boolean) {
  return {
    Product: [
      { label: "Jobs", href: jobsFreshHomeHref() },
      { label: "CRM", href: jobsCrmOpenHref(signedIn) },
      { label: "Job site sketch", href: "/vendor/design" },
      { label: "About", href: "/intelligence" },
      { label: "Start free workspace", href: jobsCrmOpenHref(false) },
      { label: "Robots", href: "/robots" },
      { label: "Humanoid Report", href: "/robots/report" },
      { label: "Newsletter", href: "/newsletter" },
    ],
    Support: SUPPORT_LINKS,
    Company: COMPANY_LINKS,
  };
}

const SIGNAL_LINKS = {
  Product: [
    { label: "Pipeline", href: "/pipeline" },
    { label: "Signals", href: "/signals" },
    { label: "Start free workspace", href: "/signup" },
    { label: "Robots", href: "/robots" },
    { label: "Humanoid Report", href: "/robots/report" },
    { label: "Newsletter", href: "/newsletter" },
  ],
  Support: SUPPORT_LINKS,
  Company: COMPANY_LINKS,
};

export default function SiteFooter({
  newsletterEmail,
  newsletterStatus,
  onEmailChange,
  onNewsletterSubmit,
  hideNewsletter = false,
}: Props) {
  const [pathname] = useLocation();
  const search = useSearch();
  const { session } = useAuth();
  const jobsChrome = showJobsSiteChrome({ pathname, search });
  const links = jobsChrome ? jobsProductLinks(Boolean(session)) : SIGNAL_LINKS;
  const homeHref = jobsChrome ? jobsFreshHomeHref() : "/";

  const [internalEmail, setInternalEmail] = useState("");
  const [internalStatus, setInternalStatus] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const emailValue = onEmailChange ? newsletterEmail ?? "" : internalEmail;
  const statusValue = onNewsletterSubmit
    ? newsletterStatus ?? "idle"
    : internalStatus;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (onNewsletterSubmit) {
      onNewsletterSubmit(e);
      return;
    }
    const val = internalEmail.trim();
    if (!val) return;
    setInternalStatus("submitting");
    setErrorMsg("");
    try {
      const res = await fetch(
        `${getApiBase()}/api/newsletter/subscribe`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: val, source: "site_footer" }),
        })
      );
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "Could not subscribe");
      }
      setInternalStatus("success");
      setInternalEmail("");
    } catch (err: unknown) {
      setInternalStatus("error");
      const msg = err instanceof Error ? err.message : "Could not subscribe. Try again.";
      setErrorMsg(msg);
    }
  }

  return (
    <footer className="bg-slate-950 border-t border-white/5">
      <div className="container py-14">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-12">
          <div className="col-span-2">
            <Link href={homeHref} className="flex items-center gap-2.5 mb-4">
              <img src="/logo-r.png" alt="ReadyForRobots" className="h-7 w-7" />
              <div>
                <span className="font-display font-bold text-white text-sm tracking-tight block">
                  ReadyForRobots
                </span>
                <span className="font-mono-data text-emerald-400 text-[10px] font-semibold tracking-widest uppercase">
                  {jobsChrome ? "JOBS" : "SIGNAL"}
                </span>
              </div>
            </Link>
            <p className="text-slate-500 text-sm leading-relaxed mb-5 max-w-xs">
              {jobsChrome
                ? "Find jobs for your robot. Robots need jobs. We find the work."
                : "Robot sales intelligence — discover, develop, and close deals from live market signals."}
            </p>
            {!hideNewsletter && (
              <>
                <form onSubmit={handleSubmit} className="flex gap-2 max-w-sm">
                  <input
                    type="email"
                    required
                    value={emailValue}
                    onChange={e => {
                      if (onEmailChange) onEmailChange(e.target.value);
                      else setInternalEmail(e.target.value);
                    }}
                    placeholder="work email"
                    className="flex-1 px-3 py-2 bg-white/5 border border-white/10 text-white text-sm placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors rounded-lg"
                  />
                  <button
                    type="submit"
                    disabled={statusValue === "submitting"}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors disabled:opacity-50 rounded-lg cursor-pointer"
                  >
                    {statusValue === "submitting" ? "Subscribing…" : "Subscribe"}
                  </button>
                </form>
                {statusValue === "success" && (
                  <p className="text-emerald-400 text-xs mt-2 font-medium">
                    Subscribed! Check your inbox for the daily brief.
                  </p>
                )}
                {statusValue === "error" && (
                  <p className="text-red-400 text-xs mt-2 font-medium">
                    {errorMsg || "Could not subscribe. Try again."}
                  </p>
                )}
                <p className="text-slate-600 text-xs mt-2">
                  Weekly Robot Intelligence Brief. Free.
                </p>
              </>
            )}
          </div>

          {Object.entries(links).map(([group, items]) => (
            <div key={group}>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-4">
                {group}
              </p>
              <ul className="space-y-2.5">
                {items.map(item => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-slate-500 text-sm hover:text-white transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-slate-600 text-xs">
            {jobsChrome
              ? "© 2026 ReadyForRobots · Jobs for your robot."
              : "© 2026 ReadyForRobots · Signal for robotics sales."}
          </p>
          <div className="flex flex-wrap gap-6 justify-center">
            <Link
              href="/privacy"
              className="text-slate-500 text-xs hover:text-white transition-colors"
            >
              Privacy
            </Link>
            <Link
              href="/terms"
              className="text-slate-500 text-xs hover:text-white transition-colors"
            >
              Terms
            </Link>
            <Link
              href="/support"
              className="text-slate-500 text-xs hover:text-white transition-colors"
            >
              Support
            </Link>
            <Link
              href="/login"
              className="text-slate-500 text-xs hover:text-white transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="text-slate-500 text-xs hover:text-white transition-colors"
            >
              Sign up
            </Link>
            <a
              href="mailto:support@readyforrobots.com"
              className="text-slate-500 text-xs hover:text-white transition-colors"
            >
              support@readyforrobots.com
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
