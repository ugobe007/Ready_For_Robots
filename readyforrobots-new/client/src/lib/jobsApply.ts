/**
 * Jobs Apply desk — rectify credentials before applying a robot to a Job Card.
 * Monthly rental is what the OEM/distributor plans to charge the employer.
 * Never invent a dollar figure.
 */
import { jobModelListLine, robotJobCardFromMatch } from "@/lib/robotJobCard";
import type { MatchJob } from "@/lib/robotJobMatch";

export const JOBS_APPLY_STORAGE_KEY = "rfr_job_apply_v1";
export const JOBS_APPLY_CTA = "Place this job →";

export type PlacementLane = "pack" | "quote" | "apply" | "track";

export type JobApplyStatus = "blocked" | "ready" | "applied" | "follow_up";

export type JobApplyRecord = {
  jobKey: string;
  pocEvidence: string;
  monthlyRental: string;
  packAcknowledged: boolean;
  quoteCommitted: boolean;
  status: JobApplyStatus;
  appliedAt?: string;
  followUpAt?: string;
};

export type CredentialGap = {
  id: string;
  label: string;
  howToFix: string;
  met: boolean;
};

const EMPTY: JobApplyRecord = {
  jobKey: "",
  pocEvidence: "",
  monthlyRental: "",
  packAcknowledged: false,
  quoteCommitted: false,
  status: "blocked",
};

export function emptyApplyRecord(jobKey: string): JobApplyRecord {
  return { ...EMPTY, jobKey };
}

function hasMonthlyRental(value: string): boolean {
  const t = (value || "").trim();
  if (!t) return false;
  if (/^(n\/?a|none|tbd|unknown|-)$/i.test(t)) return false;
  return t.length >= 1;
}

function hasPoc(value: string): boolean {
  return (value || "").trim().length >= 8;
}

export function jobCredentialGaps(
  job: MatchJob,
  record: JobApplyRecord,
): CredentialGap[] {
  const card = robotJobCardFromMatch(job);
  const modelUnknown = (card.taskModels || []).some(
    m => !m.presence || m.presence === "unknown",
  );
  const slot = card.taskModels[0]?.label || "required task-library pack";
  return [
    {
      id: "model_pack",
      label: "Task-library pack",
      howToFix: modelUnknown
        ? `Ask the OEM which pack covers “${slot}”. Distributors license it — they do not train a foundation VLA. Check this box when you can license or already carry it.`
        : "Named pack is on the card. Confirm the license allows commercial placement.",
      met: Boolean(record.packAcknowledged),
    },
    {
      id: "poc_evidence",
      label: "PoC evidence",
      howToFix:
        "Attach what you will show the employer: site demo, video, or a written proof-of-concept. A SKU URL is not evidence.",
      met: hasPoc(record.pocEvidence),
    },
    {
      id: "monthly_rental",
      label: "Monthly rental you will charge",
      howToFix:
        "Enter the monthly amount you plan to charge this employer (RaaS / lease). Do not invent a number — quote your own.",
      met: hasMonthlyRental(record.monthlyRental),
    },
  ];
}

export function applyStatusFromGaps(
  gaps: CredentialGap[],
  record: JobApplyRecord,
): JobApplyStatus {
  if (record.status === "follow_up") return "follow_up";
  if (record.status === "applied") return "applied";
  return gaps.every(g => g.met) ? "ready" : "blocked";
}

export function canApplyToJob(gaps: CredentialGap[], record: JobApplyRecord): boolean {
  if (record.status === "applied" || record.status === "follow_up") return false;
  return gaps.every(g => g.met);
}

export function placementOutreachDraft(
  job: MatchJob,
  record: JobApplyRecord,
  robotName: string,
): string {
  const card = robotJobCardFromMatch(job);
  const employer = card.employer || "the employer";
  const work = card.jobTitle;
  const place = card.workplace || "";
  const model = jobModelListLine(job) || slotLine(card);
  const poc = (record.pocEvidence || "").trim() || "(missing — do not apply yet)";
  const rent = (record.monthlyRental || "").trim() || "(missing — you must quote this)";
  const who = (robotName || "this robot").trim() || "this robot";
  return [
    `Subject: Applying ${who} to ${work} at ${employer}`,
    "",
    `We are applying ${who} to ${work}${place ? ` at ${place}` : ""}.`,
    "",
    `Task model: ${model || "still unnamed"}`,
    `PoC evidence: ${poc}`,
    `Monthly rental we would charge: ${rent}`,
    "",
    "We apply only when the pack, proof, and monthly quote are in hand. Hardware in the room is not enough.",
  ].join("\n");
}

function slotLine(card: ReturnType<typeof robotJobCardFromMatch>): string {
  const slot = card.taskModels[0]?.label;
  return slot ? `${slot} · not yet confirmed` : "";
}

export function placementWorkflowStrategy(
  gaps: CredentialGap[],
  record: JobApplyRecord,
): string {
  if (record.status === "follow_up") {
    return "Follow-up is open: confirm the employer received the application, book the site assessment, and check whether the pack license and monthly rental were accepted.";
  }
  if (record.status === "applied") {
    return "Application is recorded. Next: send or confirm the outreach draft, then track follow-up.";
  }
  const missing = gaps.filter(g => !g.met).map(g => g.label);
  if (missing.length) {
    return `Do not apply yet. Missing: ${missing.join(", ")}. Close every gap, then send the outreach draft.`;
  }
  return "Credentials are complete. Send the outreach draft, then Apply so we can track the submission and follow-up.";
}

export function placementMoneyLane(
  gaps: CredentialGap[],
  record: JobApplyRecord,
): PlacementLane {
  if (record.status === "applied" || record.status === "follow_up") return "track";
  const byId = Object.fromEntries(gaps.map(g => [g.id, g.met]));
  if (!byId.model_pack) return "pack";
  if (!byId.poc_evidence || !byId.monthly_rental || !record.quoteCommitted) {
    return "quote";
  }
  return "apply";
}

export function placementLaneLabel(lane: PlacementLane): string {
  if (lane === "pack") return "Pack";
  if (lane === "quote") return "Quote";
  if (lane === "apply") return "Place";
  return "Live";
}

/** One primary action on the selected job — not a nested 1–2–3 form. */
export function placementNextActionLabel(
  job: MatchJob,
  record: JobApplyRecord,
): string {
  const lane = placementMoneyLane(jobCredentialGaps(job, record), record);
  if (lane === "pack") return "Confirm pack";
  if (lane === "quote") return "Lock this quote";
  if (lane === "apply") return JOBS_APPLY_CTA;
  return "Track follow-up";
}

export function canLockQuote(gaps: CredentialGap[], record: JobApplyRecord): boolean {
  if (record.quoteCommitted) return false;
  const byId = Object.fromEntries(gaps.map(g => [g.id, g.met]));
  return Boolean(byId.poc_evidence && byId.monthly_rental);
}

export function placementAgentBrief(
  job: MatchJob,
  record: JobApplyRecord,
  robotName: string,
): string {
  const card = robotJobCardFromMatch(job);
  const who = (robotName || "this robot").trim() || "this robot";
  const employer = card.employer || "This employer";
  const work = card.jobTitle || "this work";
  const place = card.workplace ? ` at ${card.workplace}` : "";
  const known = `${employer} has work: ${work}${place}. ${who} is a possible match.`;
  const gaps = jobCredentialGaps(job, record);
  const lane = placementMoneyLane(gaps, record);
  if (lane === "track") {
    return `${known} Application is in. Your move: follow up — site assessment, pack license, and whether they accepted the monthly rental.`;
  }
  if (lane === "apply") {
    return `${known} Pack, proof, and your monthly quote are in. This is the money moment. Apply.`;
  }
  if (lane === "quote") {
    return `${known} Your move: quote the monthly rental you will charge ${employer}. That quote is how revenue on this job becomes predictable. We do not invent it.`;
  }
  return `${known} Your move: confirm the task-library pack. Hardware in the room is not enough.`;
}

export function placementBoardStats(
  jobs: MatchJob[],
): { applied: number; quoted: number; total: number; quotes: string[] } {
  const quotes: string[] = [];
  let applied = 0;
  let quoted = 0;
  for (const job of jobs) {
    const rec = loadJobApplyRecord(job.job_key);
    const gaps = jobCredentialGaps(job, rec);
    const rent = gaps.find(g => g.id === "monthly_rental");
    if (rent?.met) {
      quoted += 1;
      const t = (rec.monthlyRental || "").trim();
      if (t) quotes.push(t);
    }
    if (rec.status === "applied" || rec.status === "follow_up") applied += 1;
  }
  return { applied, quoted, total: jobs.length, quotes };
}

export function followUpNextStep(record: JobApplyRecord): string {
  if (record.status === "follow_up") {
    return "Follow up on the application: site assessment date, who signs the pack license, and whether the monthly rental was accepted.";
  }
  if (record.status === "applied") {
    return "Application recorded. Schedule follow-up: confirm the employer received it, then book the site assessment.";
  }
  return "Close the gaps, then apply.";
}

type Store = Record<string, JobApplyRecord>;

function readStore(): Store {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.sessionStorage.getItem(JOBS_APPLY_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Store;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeStore(store: Store): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(JOBS_APPLY_STORAGE_KEY, JSON.stringify(store));
  } catch {
    /* quota */
  }
}

export function loadJobApplyRecord(jobKey: string): JobApplyRecord {
  const hit = readStore()[jobKey];
  if (!hit?.jobKey) return emptyApplyRecord(jobKey);
  return { ...emptyApplyRecord(jobKey), ...hit, jobKey };
}

export function saveJobApplyRecord(record: JobApplyRecord): void {
  if (!record.jobKey) return;
  const store = readStore();
  store[record.jobKey] = record;
  writeStore(store);
}
