/**
 * RobotJobCardUnit — Explicit 7-Point Robot Job Card.
 * 
 * Satisfies Product Charter & User Request:
 * [1] Name of Customer (Employer & Workplace)
 * [2] Name of Robot Job & Description
 * [3] Time Frame (Project window / Urgency)
 * [4] Decision Makers (Named owners & contacts)
 * [5] What Type of Robots They Need (Robot family & task models)
 * [6] Job Value — How Much Is The Job Worth? (Monthly & annual contract estimate)
 * [7] Workflow — Next Steps (Placement steps & primary CTA)
 */
import { MapPin, Clock, Users, Cpu, DollarSign, ArrowRight, Zap, CheckCircle2, ShieldCheck, Mail, Copy, CheckCheck } from "lucide-react";
import { Link } from "wouter";
import { jobCardPayEstimate, qualificationFromVerdict, QUALIFICATION_LABEL } from "@/lib/robotJobCard";
import { cleanAndClampText } from "@/lib/text";
import LeadShareBar from "@/components/LeadShareBar";
import LeadEmailDisplay from "@/components/LeadEmailDisplay";

export type RobotJobCardDeal = {
  id: number;
  company: string;
  location: string;
  industry: string;
  score: number;
  signal: string;
  signalType: string;
  signalColor: string;
  stage?: string;
  contact?: string;
  contactTitle?: string;
  pipelineAction?: string;
  robotTypesNeeded?: string[];
  projectTiming?: {
    label?: string;
    day_min?: number | null;
    day_max?: number | null;
    source?: string;
  };
  notes?: string;
  shareSummary?: string;
  shareBlurb?: string;
  leadHighlights?: {
    specific_problem?: string | null;
    why_lead?: string[];
  };
  crmEvidence?: {
    friction_point?: string | null;
    workflow_scope?: { label?: string | null; items?: string[] };
    timing?: { label?: string | null };
    robot_type?: { label?: string | null };
    budget?: { top_amount?: string | null };
    decision_makers?: Array<{ name?: string; title?: string }>;
  };
  outreachSubject?: string;
  outreachBody?: string;
  verdict?: string;
  blockers?: string[];
};

type Props = {
  deal: RobotJobCardDeal;
  savedInCrm?: boolean;
  hasSession?: boolean;
  advancing?: boolean;
  onSaveLead?: () => void;
  onCopyDraft?: () => void;
  copiedDraft?: boolean;
  className?: string;
};

export default function RobotJobCardUnit({
  deal,
  savedInCrm = false,
  hasSession = false,
  advancing = false,
  onSaveLead,
  onCopyDraft,
  copiedDraft = false,
  className = "",
}: Props) {
  const pay = jobCardPayEstimate();

  // [1] Customer
  const customerName = deal.company || "Unnamed Customer";
  const workplace = [deal.location, deal.industry].filter(Boolean).join(" · ") || "Site pending";

  // [2] Name of Robot Job & Description
  const jobTitle = deal.pipelineAction || deal.signalType || "Robot Automation Opportunity";
  const rawDescription =
    deal.leadHighlights?.specific_problem ||
    deal.shareSummary ||
    deal.notes ||
    deal.signal ||
    "Station inspection, material transfer, and robot deployment match.";
  const description = cleanAndClampText(rawDescription, 320);

  // [3] Time Frame
  const timingLabel =
    deal.projectTiming?.day_min != null && deal.projectTiming?.day_max != null
      ? `${deal.projectTiming.day_min}–${deal.projectTiming.day_max} days`
      : deal.projectTiming?.label || deal.crmEvidence?.timing?.label || "30–90 days (Estimated Q3 Window)";

  // [4] Decision Makers
  const primaryContact = deal.contact ? (
    <span className="inline-flex items-center gap-1.5">
      <LeadEmailDisplay email={deal.contact} variant="inline" />
      {deal.contactTitle ? <span className="text-slate-400">· {deal.contactTitle}</span> : null}
    </span>
  ) : null;
  const decisionMakerList = deal.crmEvidence?.decision_makers?.length
    ? deal.crmEvidence.decision_makers.map(d => `${d.name || "Owner"}${d.title ? ` (${d.title})` : ""}`).join(", ")
    : null;

  // [5] What Type of Robots They Need
  const robotsList =
    (deal.robotTypesNeeded && deal.robotTypesNeeded.length > 0)
      ? deal.robotTypesNeeded.join(" · ")
      : deal.crmEvidence?.robot_type?.label || "Industrial Cobot / High-Payload Palletizer";

  // [6] Job Value
  const jobWorthMonthly = pay.monthlyLabel; // e.g. $5,000–$7,500 / month
  const jobWorthAnnual = pay.annualLabel;   // e.g. $60,000–$90,000 / year
  const publicBudget = deal.crmEvidence?.budget?.top_amount;

  // [7] Qualification
  const qualState = qualificationFromVerdict(deal.verdict, deal.blockers);
  const qualLabel = QUALIFICATION_LABEL[qualState];

  return (
    <div className={`rounded-2xl border-2 border-emerald-500/40 bg-[#09152e] p-4 sm:p-5 shadow-2xl space-y-4 text-slate-100 ${className}`}>
      {/* Job Card Header Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/80 pb-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/40 bg-emerald-400/10 px-2.5 py-1 font-mono text-[10px] font-extrabold uppercase tracking-[0.16em] text-emerald-300">
            ✦ ROBOT JOB CARD
          </span>
          <span className="inline-flex items-center gap-1 rounded-full border border-slate-600 bg-slate-800/80 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-300">
            <ShieldCheck className="h-3 w-3 text-emerald-400" />
            {qualLabel}
          </span>
        </div>
        <LeadShareBar
          compact
          lead={{
            id: deal.id,
            company_name: deal.company,
            priority_tier: deal.stage || "HOT",
            share_summary: deal.shareSummary || deal.signal,
            pipeline_action: deal.pipelineAction,
            robot_types_needed: deal.robotTypesNeeded,
          }}
        />
      </div>

      {/* [1] NAME OF CUSTOMER */}
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-400">
          [1] Customer & Workplace
        </p>
        <h2 className="mt-1 font-display text-xl font-extrabold text-white tracking-tight sm:text-2xl">
          {customerName}
        </h2>
        <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-300">
          <MapPin className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          <span>{workplace}</span>
        </div>
      </div>

      {/* [2] NAME OF ROBOT JOB AND DESCRIPTION */}
      <div className="rounded-xl border border-slate-700/80 bg-[#060e20] p-3.5 space-y-1.5">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-400">
          [2] Robot Job & Description
        </p>
        <p className="text-sm font-bold text-emerald-300">
          {jobTitle}
        </p>
        <p className="text-xs leading-relaxed text-slate-200">
          {description}
        </p>
      </div>

      {/* 2-COLUMN GRID FOR [3] TIME FRAME & [4] DECISION MAKERS */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* [3] TIME FRAME */}
        <div className="rounded-xl border border-slate-700/80 bg-[#060e20] p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-400 flex items-center gap-1">
            <Clock className="h-3 w-3 text-emerald-400" />
            [3] Time Frame
          </p>
          <p className="mt-1 text-xs font-semibold text-slate-100">
            {timingLabel}
          </p>
          <p className="mt-0.5 text-[10px] text-slate-400">
            Active buying window extracted from signals.
          </p>
        </div>

        {/* [4] DECISION MAKERS */}
        <div className="rounded-xl border border-slate-700/80 bg-[#060e20] p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-400 flex items-center gap-1">
            <Users className="h-3 w-3 text-emerald-400" />
            [4] Decision Owner
          </p>
          <div className="mt-1 text-xs font-semibold text-slate-100">
            {primaryContact || decisionMakerList || "Plant Operations / Automation Director"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-400">
            Sign-off authority for robot procurement.
          </p>
        </div>
      </div>

      {/* 2-COLUMN GRID FOR [5] ROBOTS NEEDED & [6] JOB VALUE */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* [5] WHAT TYPE OF ROBOTS THEY NEED */}
        <div className="rounded-xl border border-slate-700/80 bg-[#060e20] p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-400 flex items-center gap-1">
            <Cpu className="h-3 w-3 text-cyan-400" />
            [5] Robots Needed
          </p>
          <p className="mt-1 text-xs font-semibold text-cyan-300">
            {robotsList}
          </p>
          <p className="mt-0.5 text-[10px] text-slate-400">
            Hardware spec matched to work requirements.
          </p>
        </div>

        {/* [6] JOB VALUE — HOW MUCH IS THE JOB WORTH? */}
        <div className="rounded-xl border border-emerald-500/30 bg-[#08182b] p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-400 flex items-center gap-1">
            <DollarSign className="h-3 w-3 text-emerald-400" />
            [6] Job Value (Worth)
          </p>
          <div className="mt-1 font-mono text-sm font-extrabold text-emerald-300">
            {jobWorthMonthly}
            <span className="block text-[11px] font-normal text-emerald-200/80">
              {jobWorthAnnual} {publicBudget ? `· Public budget: ${publicBudget}` : ""}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-400">
            {pay.disclaimer}
          </p>
        </div>
      </div>

      {/* [7] WORKFLOW — NEXT STEPS & PRIMARY CTA */}
      <div className="rounded-xl border border-purple-500/40 bg-gradient-to-r from-[#120a2e] to-[#0a142e] p-4 space-y-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-purple-300">
            [7] Placement Workflow & Next Steps
          </p>
          <ol className="mt-2 space-y-1.5 text-xs text-slate-200">
            <li className="flex items-center gap-2">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-[10px] font-bold text-purple-300">1</span>
              <span>Site assessment — verify payload, reach & workplace safety.</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-[10px] font-bold text-purple-300">2</span>
              <span>License task model pack for this SKU class.</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-[10px] font-bold text-purple-300">3</span>
              <span>Send outreach note & lock robot deployment quote.</span>
            </li>
          </ol>
        </div>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center gap-2.5 pt-2 border-t border-purple-500/30">
          {savedInCrm ? (
            <Link
              href="/crm"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-xs font-extrabold uppercase tracking-wide text-[#03140e] shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 transition"
            >
              <CheckCircle2 className="h-4 w-4" />
              In Native CRM — Open Desk
            </Link>
          ) : hasSession && onSaveLead ? (
            <button
              type="button"
              onClick={onSaveLead}
              disabled={advancing}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-xs font-extrabold uppercase tracking-wide text-white shadow-lg shadow-purple-600/30 hover:bg-purple-500 disabled:opacity-60 transition"
            >
              {advancing ? "Saving…" : "Activate CRM — Save This Job"}
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <Link
              href={`/signup?next=${encodeURIComponent(`/pipeline?lead=${deal.id}`)}&co=${encodeURIComponent(deal.company)}`}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-xs font-extrabold uppercase tracking-wide text-white shadow-lg shadow-purple-600/30 hover:bg-purple-500 transition"
            >
              Start Free Workspace — Save Job
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}

          {onCopyDraft && (
            <button
              type="button"
              onClick={onCopyDraft}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-slate-600 bg-slate-800/80 px-3.5 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition"
            >
              {copiedDraft ? <CheckCheck className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              {copiedDraft ? "Draft Copied!" : "Copy Outreach Draft"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
