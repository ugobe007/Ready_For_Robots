/**
 * Anonymous pipeline — summarize proof visible before signup.
 *
 * Value-first continuity: when the anonymous user is actively reading a specific
 * buyer's outreach draft, the CTA becomes lead-specific ("Save {company} free")
 * and routes through `signupHrefForLead`, which carries the company through the
 * signup wall and appends `resume=save` so the expressed intent auto-completes
 * as a first save (activation) after auth — instead of a generic "Start free"
 * that drops the user back at the top of the pipeline with no context.
 */
import { Link } from "wouter";
import { ArrowRight, Sparkles } from "lucide-react";
import { signupHrefForLead } from "@/lib/signupHref";

type Props = {
  leadCount: number;
  limit: number;
  /** Company name of the lead the user is currently reading, if any. */
  selectedCompany?: string | null;
  /** Lead id of the currently-selected lead, for resume-save continuity. */
  selectedLeadId?: number | string | null;
};

export default function AnonymousValueStrip({ leadCount, limit, selectedCompany, selectedLeadId }: Props) {
  const company = (selectedCompany || "").trim();
  const hasLead = Boolean(company) && selectedLeadId != null;
  const ctaHref = hasLead ? signupHrefForLead(selectedLeadId!, company) : "/signup?next=/pipeline";
  const ctaLabel = hasLead ? `Save ${company} free` : "Start free";

  return (
    <div className="pipeline-value-strip flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="flex items-start gap-2 flex-1 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-emerald-700 mt-0.5" />
        <div>
          <p className="pipeline-value-strip-title">
            {hasLead ? `Save ${company} and copy its outreach draft` : "See value before you sign up"}
          </p>
          <p className="pipeline-value-strip-body">
            {hasLead
              ? `Free workspace: sign up and land right back on ${company} — its outreach draft saved and ready to copy, plus HubSpot sync.`
              : `Browse ${Math.min(leadCount, limit)} live leads with pitch actions, robot types, and outreach drafts — no account required. Free workspace adds save, copy, and HubSpot sync.`}
          </p>
        </div>
      </div>
      <Link
        href={ctaHref}
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-emerald-600 bg-white px-3 py-2 text-xs font-bold text-emerald-800 hover:bg-emerald-100"
      >
        {ctaLabel}
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}
