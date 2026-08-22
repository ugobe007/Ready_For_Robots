/**
 * Robot Job Card — employment-model view of a unit of work.
 * Canonical model: docs/robot_employment_model.md
 */
import robcoPack from "./robcoJobCards.json";
import { jobExplanation } from "./jobsWorkflow";

export const ROBOT_JOB_CARD_NEXT_STEP =
  "Site assessment — can the robot actually work here?";

export type RobotJobQualification =
  | "qualified"
  | "conditional"
  | "not_qualified"
  | "pending_robot";

export type RobotJobCardView = {
  employer: string | null;
  workplace: string | null;
  jobTitle: string;
  work: string;
  requirements: string[];
  workVolume: string | null;
  currentLabor: string | null;
  evidence: string | null;
  qualification: RobotJobQualification;
  qualificationLabel: string;
  openQuestions: string[];
  nextStep: string;
};

export const QUALIFICATION_LABEL: Record<RobotJobQualification, string> = {
  qualified: "Qualified",
  conditional: "Conditional",
  not_qualified: "Not qualified",
  pending_robot: "Pending robot résumé",
};

export function qualificationFromVerdict(
  verdict?: string | null,
): RobotJobQualification {
  if (verdict === "NOT_A_MATCH") return "not_qualified";
  if (verdict === "INSUFFICIENT") return "conditional";
  if (verdict === "POSSIBLE_MATCH") return "qualified";
  return "pending_robot";
}

export function robotJobCardFromMatch(job: {
  title?: string | null;
  company_name?: string | null;
  locality?: string | null;
  why?: string[] | null;
  still_unknown?: string[] | null;
  unknowns?: string[] | null;
  blockers?: string[] | null;
  verdict?: string | null;
  industry?: string | null;
  text?: string | null;
}): RobotJobCardView {
  const open = unique([
    ...(job.still_unknown || []),
    ...(job.unknowns || []),
  ]);
  const qualification = qualificationFromVerdict(job.verdict);
  const work = jobExplanation({
    title: job.title,
    why: job.why,
    company: job.company_name,
    industry: job.industry,
  });
  return {
    employer: emptyToNull(job.company_name),
    workplace: emptyToNull(job.locality),
    jobTitle: (job.title || "").trim() || "Untitled job",
    work: work || (job.title || "").trim(),
    requirements: [...(job.why || [])],
    workVolume: null,
    currentLabor: null,
    evidence: emptyToNull(job.text) || (job.why?.[0] ?? null),
    qualification,
    qualificationLabel: QUALIFICATION_LABEL[qualification],
    openQuestions: open,
    nextStep: ROBOT_JOB_CARD_NEXT_STEP,
  };
}

export type RobcoJobCard = (typeof robcoPack)["jobs"][number];

export function robcoJobCards(): RobcoJobCard[] {
  return robcoPack.jobs;
}

export function robcoPackHonesty(pack = robcoPack): string[] {
  const errors: string[] = [];
  if (pack.invented_economics) errors.push("pack must not invent economics");
  if (pack.jobs.length < 1) errors.push("pack is empty");
  for (const job of pack.jobs) {
    if (!job.employer?.trim()) errors.push(`${job.id} missing employer`);
    if (!job.workplace?.trim()) errors.push(`${job.id} missing workplace`);
    if (!job.job_key?.startsWith("manip_")) {
      errors.push(`${job.id} must point at a corpus/ledger job_key`);
    }
    if (job.workVolume != null) errors.push(`${job.id} invented workVolume`);
    if (job.currentLabor != null) errors.push(`${job.id} invented currentLabor`);
    if (job.qualification !== "pending_robot") {
      errors.push(`${job.id} must stay pending_robot until a RobCo URL exists`);
    }
  }
  return errors;
}

function emptyToNull(value?: string | null): string | null {
  const t = (value || "").trim();
  return t ? t : null;
}

function unique(rows: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const row of rows) {
    const t = row.trim();
    if (!t || seen.has(t)) continue;
    seen.add(t);
    out.push(t);
  }
  return out;
}
