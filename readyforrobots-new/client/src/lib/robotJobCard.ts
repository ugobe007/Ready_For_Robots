/**
 * Robot Job Card — employment-model view of a unit of work.
 * Canonical model: docs/robot_employment_model.md
 */
import robcoPack from "./robcoJobCards.json";

export const ROBOT_JOB_CARD_NEXT_STEP =
  "Site assessment — can the robot actually work here?";

export type RobotJobQualification =
  | "qualified"
  | "conditional"
  | "not_qualified"
  | "pending_robot";

export type TaskModelPresence = "unknown" | "present" | "absent";

export type TaskModelLookup = {
  kind: string;
  name: string;
  url: string | null;
  note: string;
};

export type RequiredTaskModel = {
  id: string;
  label: string;
  physicalTask: string;
  vertical: string;
  presence: TaskModelPresence;
  hardwareNotEnough: string;
  whereToLook: TaskModelLookup[];
};

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
  qualificationHint: string;
  openQuestions: string[];
  nextStep: string;
  taskModels: RequiredTaskModel[];
};

export const QUALIFICATION_LABEL: Record<RobotJobQualification, string> = {
  qualified: "Qualified",
  conditional: "Conditional",
  not_qualified: "Not qualified",
  pending_robot: "Pending robot résumé",
};

export const QUALIFICATION_HINT: Record<RobotJobQualification, string> = {
  qualified: "Confirmed by you or the employer.",
  conditional: "Pending your review, a site assessment, and a task model for this work.",
  not_qualified: "A required capability or task model is unmet.",
  pending_robot: "Submit this robot’s URL to evaluate it against the job.",
};

export function qualificationFromVerdict(
  verdict?: string | null,
  blockers?: string[] | null,
  taskModels?: { presence?: string | null }[] | null,
): RobotJobQualification {
  if (verdict === "NOT_A_MATCH" || (blockers && blockers.length > 0)) {
    return "not_qualified";
  }
  if (taskModels?.some(m => m.presence === "absent")) {
    return "not_qualified";
  }
  if (verdict === "POSSIBLE_MATCH" || verdict === "INSUFFICIENT") {
    return "conditional";
  }
  return "pending_robot";
}

type MatchTaskModelIn = {
  id?: string | null;
  label?: string | null;
  physical_task?: string | null;
  vertical?: string | null;
  presence?: string | null;
  hardware_not_enough?: string | null;
  where_to_look?: {
    kind?: string | null;
    name?: string | null;
    url?: string | null;
    note?: string | null;
  }[] | null;
};

function normalizeTaskModels(raw?: MatchTaskModelIn[] | null): RequiredTaskModel[] {
  const out: RequiredTaskModel[] = [];
  for (const row of raw || []) {
    const id = (row.id || "").trim();
    const label = (row.label || "").trim();
    if (!id && !label) continue;
    const presence: TaskModelPresence =
      row.presence === "present" || row.presence === "absent"
        ? row.presence
        : "unknown";
    out.push({
      id: id || label,
      label: label || id,
      physicalTask: (row.physical_task || "").trim(),
      vertical: (row.vertical || "").trim(),
      presence,
      hardwareNotEnough: (row.hardware_not_enough || "").trim(),
      whereToLook: (row.where_to_look || []).map(d => ({
        kind: (d.kind || "").trim(),
        name: (d.name || "").trim(),
        url: d.url ? d.url.trim() : null,
        note: (d.note || "").trim(),
      })),
    });
  }
  return out;
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
  required_task_models?: MatchTaskModelIn[] | null;
}): RobotJobCardView {
  const taskModels = normalizeTaskModels(job.required_task_models);
  const open = unique([
    ...(job.still_unknown || []),
    ...(job.unknowns || []),
  ]);
  const qualification = qualificationFromVerdict(
    job.verdict,
    job.blockers,
    taskModels,
  );
  const title = (job.title || "").trim() || "Untitled job";
  return {
    employer: emptyToNull(job.company_name),
    workplace: emptyToNull(job.locality),
    jobTitle: title,
    work: title,
    requirements: [...(job.why || [])],
    workVolume: null,
    currentLabor: null,
    evidence: emptyToNull(job.text) || (job.why?.[0] ?? null),
    qualification,
    qualificationLabel: QUALIFICATION_LABEL[qualification],
    qualificationHint: QUALIFICATION_HINT[qualification],
    openQuestions: open,
    nextStep: ROBOT_JOB_CARD_NEXT_STEP,
    taskModels,
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
