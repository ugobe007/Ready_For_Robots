/**
 * Jobs CRM account storage — keep, next-steps, apply, inbox.
 * Handoff localStorage is the unsigned bridge; this is the signed-in desk.
 */
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import {
  JOBS_ACTIVATE_SRC,
  JOBS_APPLY_HERO_CTA,
  jobsActivateHref,
  jobsCrmOpenHref,
  jobsSignupHref,
} from "@/lib/jobsWorkflow";
export {
  JOBS_APPLY_CTA_BUTTON_CLASS,
  JOBS_APPLY_CTA_CLASS,
  JOBS_APPLY_HERO_CTA,
} from "@/lib/jobsWorkflow";
import {
  sameRobotHandoffUrl,
  type JobsHandoffSnapshot,
} from "@/lib/jobsHandoffSnapshot";
import { canonicalRobotUrl } from "@/lib/robotUrlIdentity";
import type { MatchJob } from "@/lib/robotJobMatch";

export const JOBS_KEEP_JOBS_CTA = "Keep jobs";
export const JOBS_KEEP_YES_CTA = "Yes, keep them";
export const JOBS_NEXT_STEPS_CTA = "Next steps →";
export const JOBS_APPLY_NEXT_CTA = JOBS_APPLY_HERO_CTA;
export const JOBS_APPLY_SELECTED_CTA = JOBS_APPLY_HERO_CTA;
export const JOBS_NEXT_STEPS_ANCHOR = "jobs-next-steps";
export const JOBS_APPLY_SEQUENCE =
  "Apply to the job. We prepare a draft. You review and send. Then we help set up the interview.";
export const JOBS_PREPARE_CTA = "Prepare application →";
export const JOBS_SEND_DRAFT_CTA = "Send to employer →";
export const JOBS_SEND_DRAFT_HINT =
  "This is a draft. Review it. You send. We do not email the employer until you do.";
export const JOBS_VIDEO_EMPTY_NOTE =
  "No public YouTube clip of this robot turned up. We left the video empty rather than guess.";
export const JOBS_CONTACTS_EMPTY_NOTE =
  "No employer email on this Job Card or stored public page. We will not invent one.";
export const JOBS_NEXT_STEPS_HINT =
  "Pick the model and say what you'll charge. Then we prepare a draft for you to send.";
export const JOBS_DOCS_HEADING = "Brochures and product specs";
export const JOBS_DOCS_HINT =
  "Upload a PDF or image spec for this robot. We attach what you select to the application — not a public dump.";
export const JOBS_EMPLOYER_ACCEPT_CTA = "Accept";
export const JOBS_EMPLOYER_DECLINE_CTA = "Decline";
export const JOBS_EMPLOYER_INTERVIEW_CTA = "Set up interview";
export const JOBS_EMPLOYER_PROPOSE_CTA = "Propose this time";
export const JOBS_EMPLOYER_HOLD_CTA = "Hold this slot";
export const JOBS_EMPLOYER_CONNECT_CTA = "Connect us";
export const JOBS_OEM_CONFIRM_HOLD_CTA = "Confirm hold";
export const JOBS_OEM_RELEASE_HOLD_CTA = "Release hold";
export const JOBS_PROPOSED_PRICE_LABEL =
  "Proposed monthly price you will charge";
export const JOBS_PROPOSED_PRICE_HINT =
  "Your proposed offer — not a rate this site invented. Employers see this as your quote.";
export const JOBS_MODEL_SELECT_LABEL = "Model they will use";
export const JOBS_MODEL_SELECT_HINT =
  "Catalogued SKUs for this OEM. We do not invent a model name.";
export const JOBS_APPLY_OFFER_CTA = JOBS_PREPARE_CTA;
export const JOBS_INBOX_HEADING = "Employer inbox";
export const JOBS_INBOX_PASTE_HINT =
  "Inbound MX is not required to store a reply. Paste an employer email here, or send a reply if we have their address.";

export type CatalogSku = {
  name: string;
  slug?: string;
  source?: string;
};

export type JobsApplyContact = {
  email: string;
  source: string;
};

export type JobsApplyDraft = {
  subject: string;
  body: string;
  video_url: string | null;
  video_search_url: string;
  video_note: string;
  clip_description: string | null;
  why: string;
  contacts: JobsApplyContact[];
  operator_sends: boolean;
};

export type JobsCrmApplication = {
  id: string;
  job_key: string;
  employer_name: string;
  work_title: string;
  workplace?: string | null;
  robot_name: string;
  selected_models: string[];
  poc_evidence?: string | null;
  poc_video_url?: string | null;
  poc_skipped: boolean;
  monthly_price: string;
  employer_email?: string | null;
  send_status: string;
  send_error?: string | null;
  thread_state: string;
  can_send: boolean;
  can_operator_send?: boolean;
  no_email_reason?: string | null;
  status?: string | null;
  interview_at?: string | null;
  interview_note?: string | null;
  interview_mode?: string | null;
  held_at?: string | null;
  hold_expires_at?: string | null;
  slot_start?: string | null;
  slot_end?: string | null;
  slot_label?: string | null;
  can_confirm_hold?: boolean;
  can_release_hold?: boolean;
  hold_url?: string | null;
  oem_email?: string | null;
  employer_decision_url?: string | null;
  decline_reason_code?: string | null;
  decline_reason_label?: string | null;
  decline_note?: string | null;
  can_decline?: boolean;
  documents?: RobotDocument[];
  messages?: JobsCrmMessage[];
  meeting_url?: string | null;
  scheduling_state?: string | null;
  scheduling_label?: string | null;
  draft?: JobsApplyDraft | null;
  why?: string | null;
  contacts?: JobsApplyContact[];
  clip_description?: string | null;
};

export type HoldSlotOption = {
  start: string;
  end: string;
  label: string;
};

export type RobotDocument = {
  id: string;
  filename: string;
  mime_type?: string;
  size_bytes?: number;
  kind?: string;
  created_at?: string | null;
};

export type JobsCrmMessage = {
  id: string;
  direction: "inbound" | "outbound" | string;
  body: string;
  subject?: string | null;
  from_email?: string | null;
  to_email?: string | null;
  provider_id?: string | null;
  created_at?: string | null;
};

export type KeptJobRow = {
  id: string;
  job_key: string;
  employer_name: string;
  work_title: string;
  workplace?: string | null;
  job: MatchJob;
  robot_name?: string | null;
  robot_url?: string | null;
  employer_email?: string | null;
  work_task_model_kind?: string | null;
  work_task_model_source?: string | null;
  application?: JobsCrmApplication | null;
  created_at?: string | null;
};

export const WORK_TASK_MODEL_KINDS = [
  "unknown",
  "source",
  "self_train",
] as const;
export type WorkTaskModelKind = (typeof WORK_TASK_MODEL_KINDS)[number];

export type WorkTaskModelAnswer =
  | { kind: "unknown" }
  | { kind: "source"; source: string }
  | { kind: "self_train" };

export const WORK_TASK_MODEL_QUESTION = "Do you have a model for this work?";
export const WORK_TASK_MODEL_SOURCE_OPTION = "Yes. Name the model source.";
export const WORK_TASK_MODEL_SOURCE_HINT =
  "Product, vendor, or known policy. Your words. We will not guess a name.";
export const WORK_TASK_MODEL_SOURCE_PLACEHOLDER = "Model name or vendor";
export const WORK_TASK_MODEL_SELF_OPTION = "We'll train this for the job.";
export const WORK_TASK_MODEL_UNKNOWN_HINT = "Unknown until you answer.";
export const WORK_TASK_MODEL_SOURCE_REQUIRED =
  "Name the model source. We will not guess.";

export const CAL_JOBS_DESK_TOOLS = [
  "read_desk",
  "save_task_model",
  "prepare_apply",
] as const;
export type CalJobsDeskTool = (typeof CAL_JOBS_DESK_TOOLS)[number];

export type CalDeskFact =
  | "task_model"
  | "selected_models"
  | "monthly_price"
  | "poc"
  | "prepare_apply";

export type CalDeskJob = {
  job_key: string;
  employer_name: string;
  work_title: string;
  workplace?: string | null;
  robot_name?: string | null;
  robot_url?: string | null;
  work_task_model_kind?: string | null;
  work_task_model_source?: string | null;
  contacts: JobsApplyContact[];
  contacts_note?: string | null;
  selected_models: string[];
  catalog_skus: CatalogSku[];
  monthly_price?: string | null;
  poc?: { evidence?: string; video?: string; skipped?: boolean };
  application_status?: string | null;
  application?: JobsCrmApplication | null;
  missing: string[];
  next_fact?: CalDeskFact | string | null;
  prompt: string;
};

export type CalDeskQuestion = {
  job_key: string;
  fact: CalDeskFact | string;
  prompt: string;
};

export type CalDeskBrief = {
  ok: boolean;
  name: string;
  title: string;
  job: string;
  greeting: string;
  next_question: CalDeskQuestion | null;
  jobs: CalDeskJob[];
  operator_sends: boolean;
  autonomy_enabled: boolean;
  tools: string[];
  forbidden_tools: string[];
};

export type CalDeskTurn = {
  ok: boolean;
  refused?: boolean;
  tool?: string;
  detail?: string;
  result?: KeptJobRow | JobsCrmApplication | null;
  desk: CalDeskBrief;
  next_question?: CalDeskQuestion | null;
};

export async function fetchCalDesk(token: string): Promise<CalDeskBrief> {
  return jobsCrmFetch<CalDeskBrief>("/api/jobs-crm/cal/desk", token);
}

export async function runCalDeskTool(
  token: string,
  body: {
    tool: string;
    jobKey?: string;
    kind?: WorkTaskModelKind | string;
    source?: string;
    robotName?: string;
    selectedModels?: string[];
    monthlyPrice?: string;
    pocEvidence?: string;
    pocVideoUrl?: string;
    pocSkipped?: boolean;
    why?: string;
    companyName?: string;
  }
): Promise<CalDeskTurn> {
  return jobsCrmFetch<CalDeskTurn>("/api/jobs-crm/cal/desk", token, {
    method: "POST",
    body: JSON.stringify({
      tool: body.tool,
      job_key: body.jobKey || null,
      kind: body.kind || null,
      source: body.source || null,
      robot_name: body.robotName || null,
      selected_models: body.selectedModels || [],
      monthly_price: body.monthlyPrice || null,
      poc_evidence: body.pocEvidence || null,
      poc_video_url: body.pocVideoUrl || null,
      poc_skipped: Boolean(body.pocSkipped),
      why: body.why || null,
      company_name: body.companyName || null,
    }),
  });
}

export function parseWorkTaskModel(
  row:
    | {
        work_task_model_kind?: string | null;
        work_task_model_source?: string | null;
      }
    | null
    | undefined
): WorkTaskModelAnswer {
  return normalizeWorkTaskModel({
    kind: row?.work_task_model_kind,
    source: row?.work_task_model_source,
    requireSource: false,
  });
}

export function normalizeWorkTaskModel(input: {
  kind?: string | null;
  source?: string | null;
  requireSource?: boolean;
}): WorkTaskModelAnswer {
  const kind = String(input.kind || "")
    .trim()
    .toLowerCase();
  const source = String(input.source || "")
    .replace(/\s+/g, " ")
    .trim();
  if (kind === "self_train") return { kind: "self_train" };
  if (kind === "source") {
    if (source) return { kind: "source", source };
    if (input.requireSource) {
      throw new Error(WORK_TASK_MODEL_SOURCE_REQUIRED);
    }
    return { kind: "unknown" };
  }
  return { kind: "unknown" };
}

export function workTaskModelListLine(answer: WorkTaskModelAnswer): string {
  if (answer.kind === "source") return answer.source;
  if (answer.kind === "self_train") return "We'll train this";
  return "Model not named yet";
}

export type KeepJobsResult = {
  saved_count: number;
  created_count: number;
  skipped_monthly: number;
  jobs: KeptJobRow[];
};

export type KeepJobsStatusBar = {
  text: string;
  href?: string;
  hrefLabel?: string;
};

export function keepJobsSavedLabel(count: number): string {
  const n = Math.max(0, count);
  return n === 1 ? "1 job saved" : `${n} jobs saved`;
}

/** Status bar after Keep jobs. CRM link only when the user is not already on the desk. */
export function keepJobsStatusBar(opts: {
  savedCount: number;
  onCrmDesk: boolean;
  signedIn: boolean;
  submissionId?: number | null;
}): KeepJobsStatusBar {
  const text = keepJobsSavedLabel(opts.savedCount);
  if (opts.onCrmDesk) {
    return {
      text,
      href: jobsCrmOfferHref(true, opts.submissionId),
      hrefLabel: JOBS_APPLY_NEXT_CTA,
    };
  }
  return {
    text,
    href: jobsCrmOpenHref(opts.signedIn, opts.submissionId),
    hrefLabel: "Open CRM",
  };
}

export function canSubmitNextStepsOffer(opts: {
  monthlyPrice: string;
  selectedModels: string[];
}): boolean {
  const price = (opts.monthlyPrice || "").trim();
  if (!price || /^(n\/?a|none|tbd|unknown|-)$/i.test(price)) return false;
  return (opts.selectedModels || []).some(name => Boolean((name || "").trim()));
}

export function jobsCrmOfferHref(
  signedIn: boolean,
  submissionId?: number | null
): string {
  const dest = jobsActivateHref(submissionId);
  const offer = dest.includes("next=offer")
    ? dest
    : `${dest}${dest.includes("?") ? "&" : "?"}next=offer`;
  if (!signedIn) return jobsSignupHref(offer, JOBS_ACTIVATE_SRC);
  return offer.includes("#") ? offer : `${offer}#${JOBS_NEXT_STEPS_ANCHOR}`;
}

export function openJobsCrmNextStepsForm(): void {
  if (typeof document === "undefined") return;
  const node = document.getElementById(JOBS_NEXT_STEPS_ANCHOR);
  if (node) {
    node.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  if (typeof window !== "undefined") {
    window.location.hash = JOBS_NEXT_STEPS_ANCHOR;
  }
}

export function isJobsCrmOfferQuery(
  search: string | null | undefined
): boolean {
  try {
    return (
      new URLSearchParams((search || "").replace(/^\?/, "")).get("next") ===
      "offer"
    );
  } catch {
    return false;
  }
}

async function jobsCrmFetch<T>(
  path: string,
  token: string,
  init: RequestInit = {}
): Promise<T> {
  const base = getApiBase();
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(authHeader(token) as Record<string, string>),
    ...((init.headers as Record<string, string>) || {}),
  };
  const res = await fetch(
    `${base}${path}`,
    liveFetchInit({ ...init, headers })
  );
  if (!res.ok) {
    let detail = `jobs-crm ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export async function keepJobsOnAccount(
  token: string,
  body: {
    jobs: MatchJob[];
    robotName?: string;
    robotUrl?: string;
    submissionId?: number | null;
  }
): Promise<KeepJobsResult> {
  return jobsCrmFetch<KeepJobsResult>("/api/jobs-crm/keep", token, {
    method: "POST",
    body: JSON.stringify({
      jobs: body.jobs,
      robot_name: body.robotName || null,
      robot_url: body.robotUrl || null,
      robot_submission_id: body.submissionId || null,
    }),
  });
}

export async function fetchKeptJobs(token: string): Promise<KeptJobRow[]> {
  const data = await jobsCrmFetch<{ jobs: KeptJobRow[] }>(
    "/api/jobs-crm/jobs",
    token
  );
  return data.jobs || [];
}

export async function saveWorkTaskModelOnAccount(
  token: string,
  body: { jobKey: string; kind: WorkTaskModelKind; source?: string }
): Promise<KeptJobRow> {
  const answer = normalizeWorkTaskModel({
    kind: body.kind,
    source: body.source,
    requireSource: body.kind === "source",
  });
  return jobsCrmFetch<KeptJobRow>("/api/jobs-crm/jobs/task-model", token, {
    method: "POST",
    body: JSON.stringify({
      job_key: body.jobKey,
      kind: answer.kind,
      source: answer.kind === "source" ? answer.source : null,
    }),
  });
}

export async function fetchCatalogSkus(
  token: string,
  opts: { url?: string; company?: string }
): Promise<CatalogSku[]> {
  const q = new URLSearchParams();
  if (opts.url) q.set("url", opts.url);
  if (opts.company) q.set("company", opts.company);
  const data = await jobsCrmFetch<{ skus: CatalogSku[] }>(
    `/api/jobs-crm/skus?${q.toString()}`,
    token
  );
  return data.skus || [];
}

/** OEM name for YouTube search. Host of the robot URL, not the employer. */
export function companyHintFromRobotUrl(url?: string | null): string {
  const raw = (url || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw.includes("://") ? raw : `https://${raw}`);
    const host = parsed.hostname.replace(/^www\./i, "");
    const root = (host.split(".")[0] || "").trim();
    if (root.length < 2) return "";
    return root;
  } catch {
    return "";
  }
}

export async function applyJobOnAccount(
  token: string,
  body: {
    jobKey: string;
    robotName: string;
    selectedModels: string[];
    monthlyPrice: string;
    pocEvidence?: string;
    pocVideoUrl?: string;
    pocSkipped?: boolean;
    why?: string;
    companyName?: string;
    job?: MatchJob;
    documentIds?: string[];
  }
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>("/api/jobs-crm/apply", token, {
    method: "POST",
    body: JSON.stringify({
      job_key: body.jobKey,
      robot_name: body.robotName,
      selected_models: body.selectedModels,
      monthly_price: body.monthlyPrice,
      poc_evidence: body.pocEvidence || "",
      poc_video_url: body.pocVideoUrl || "",
      poc_skipped: Boolean(body.pocSkipped),
      why: body.why || "",
      company_name: body.companyName || "",
      job: body.job || null,
      document_ids: body.documentIds || [],
    }),
  });
}

export async function applySelectedJobsOnAccount(
  token: string,
  body: {
    jobs: MatchJob[];
    robotName: string;
    selectedModels: string[];
    monthlyPrice: string;
    pocEvidence?: string;
    pocVideoUrl?: string;
    pocSkipped?: boolean;
    why?: string;
    companyName?: string;
    documentIds?: string[];
  }
): Promise<{
  applied: JobsCrmApplication[];
  errors: { job_key: string; error: string }[];
  applied_count: number;
}> {
  return jobsCrmFetch("/api/jobs-crm/apply-selected", token, {
    method: "POST",
    body: JSON.stringify({
      jobs: body.jobs,
      robot_name: body.robotName,
      selected_models: body.selectedModels,
      monthly_price: body.monthlyPrice,
      poc_evidence: body.pocEvidence || "",
      poc_video_url: body.pocVideoUrl || "",
      poc_skipped: Boolean(body.pocSkipped),
      why: body.why || "",
      company_name: body.companyName || "",
      document_ids: body.documentIds || [],
    }),
  });
}

export async function sendPreparedApplication(
  token: string,
  applicationId: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch(
    `/api/jobs-crm/applications/${applicationId}/send`,
    token,
    { method: "POST", body: JSON.stringify({}) }
  );
}

export async function fetchApplyPrep(
  token: string,
  opts: { robot?: string; company?: string; sku?: string }
): Promise<{
  video_url: string | null;
  video_search_url: string;
  video_note: string;
  clip_description: string | null;
}> {
  const q = new URLSearchParams();
  if (opts.robot) q.set("robot", opts.robot);
  if (opts.company) q.set("company", opts.company);
  if (opts.sku) q.set("sku", opts.sku);
  return jobsCrmFetch(`/api/jobs-crm/apply-prep?${q.toString()}`, token);
}

export async function saveApplicationMeetingUrl(
  token: string,
  applicationId: string,
  meetingUrl: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch(
    `/api/jobs-crm/applications/${applicationId}/meeting-url`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ meeting_url: meetingUrl }),
    }
  );
}

export async function fetchRobotDocuments(
  token: string
): Promise<RobotDocument[]> {
  const data = await jobsCrmFetch<{ documents: RobotDocument[] }>(
    "/api/jobs-crm/documents",
    token
  );
  return data.documents || [];
}

export async function uploadRobotDocument(
  token: string,
  file: File,
  kind = "spec"
): Promise<RobotDocument> {
  const base = getApiBase();
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file);
  const res = await fetch(
    `${base}/api/jobs-crm/documents`,
    liveFetchInit({
      method: "POST",
      headers: {
        Accept: "application/json",
        ...(authHeader(token) as Record<string, string>),
      },
      body: form,
    })
  );
  if (!res.ok) {
    let detail = `jobs-crm ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as RobotDocument;
}

export async function confirmInterviewOnAccount(
  token: string,
  applicationId: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/confirm-interview`,
    token,
    { method: "POST" }
  );
}

export async function confirmHoldOnAccount(
  token: string,
  applicationId: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/confirm-hold`,
    token,
    { method: "POST" }
  );
}

export async function releaseHoldOnAccount(
  token: string,
  applicationId: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/release-hold`,
    token,
    { method: "POST" }
  );
}

export async function markApplicationOutcome(
  token: string,
  applicationId: string,
  outcome: "success" | "failed"
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/outcome`,
    token,
    { method: "POST", body: JSON.stringify({ outcome }) }
  );
}

export async function fetchApplicationThread(
  token: string,
  applicationId: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}`,
    token
  );
}

export async function replyOnApplication(
  token: string,
  applicationId: string,
  body: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/reply`,
    token,
    { method: "POST", body: JSON.stringify({ body }) }
  );
}

export async function pasteInboundReply(
  token: string,
  applicationId: string,
  body: string,
  fromEmail?: string
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/paste-inbound`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ body, from_email: fromEmail || null }),
    }
  );
}

export async function postJobsCrmActivity(
  token: string,
  event: { kind: string; label: string; jobKey?: string; company?: string }
): Promise<void> {
  await jobsCrmFetch("/api/jobs-crm/activity", token, {
    method: "POST",
    body: JSON.stringify({
      kind: event.kind,
      label: event.label,
      job_key: event.jobKey || null,
      company: event.company || null,
    }),
  });
}

export function keptRowsToMatchJobs(rows: KeptJobRow[]): MatchJob[] {
  return rows
    .map(row => {
      const job = row.job && typeof row.job === "object" ? row.job : null;
      if (job && job.job_key) return job;
      return {
        job_key: row.job_key,
        title: row.work_title,
        industry: "",
        path: "",
        company_name: row.employer_name,
        locality: row.workplace,
      } satisfies MatchJob;
    })
    .filter(job => Boolean(job.job_key));
}

function normalizeRobotName(name?: string | null): string {
  return String(name || "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

/** Kept row belongs to the FIND robot currently on the desk — never a prior SKU. */
export function keptRowMatchesRobot(
  row: Pick<KeptJobRow, "robot_url" | "robot_name">,
  current: { url?: string | null; name?: string | null }
): boolean {
  const currentUrl = (current.url || "").trim();
  const rowUrl = (row.robot_url || "").trim();
  if (currentUrl) {
    if (rowUrl) return sameRobotHandoffUrl(rowUrl, currentUrl);
    // Old saves without a URL must not leak onto a new FIND robot.
    return false;
  }
  const currentName = normalizeRobotName(current.name);
  const rowName = normalizeRobotName(row.robot_name);
  return Boolean(currentName && rowName && currentName === rowName);
}

export type CrmDeskForRobot = {
  product: string;
  robotUrl: string;
  rows: KeptJobRow[];
  jobs: MatchJob[];
  savedCount: number;
};

const EMPTY_CRM_DESK: CrmDeskForRobot = {
  product: "your robot",
  robotUrl: "",
  rows: [],
  jobs: [],
  savedCount: 0,
};

/**
 * Desk identity + jobs for the robot FIND just ran.
 * The submitted URL is the only key. No snap URL → honest empty, never
 * accountRows[0] / first saved robot / leftover class jobs.
 */
export function crmDeskForCurrentRobot(opts: {
  snap: JobsHandoffSnapshot | null;
  accountRows: KeptJobRow[];
}): CrmDeskForRobot {
  const snapUrl = canonicalRobotUrl(opts.snap?.url || "");
  if (!snapUrl) return EMPTY_CRM_DESK;
  const snap = opts.snap as JobsHandoffSnapshot;
  const current = { url: snapUrl, name: snap.productName };
  const handoffJobs = snap.jobs || [];
  const handoffKeys = new Set(
    handoffJobs.map(job => job.job_key).filter(Boolean)
  );
  const rows = opts.accountRows.filter(row => {
    if (!keptRowMatchesRobot(row, current)) return false;
    if (!handoffJobs.length) return false;
    return handoffKeys.has(row.job_key);
  });
  const accountJobs = keptRowsToMatchJobs(rows);
  const jobs = handoffJobs.length
    ? accountJobs.length
      ? accountJobs
      : handoffJobs
    : [];
  return {
    product: snap.productName || "your robot",
    robotUrl: snapUrl,
    rows: handoffJobs.length ? rows : [],
    jobs,
    savedCount: handoffJobs.length ? rows.length : 0,
  };
}

export function threadStateLabel(state: string | null | undefined): string {
  if (state === "replied") return "Replied";
  if (state === "awaiting_reply" || state === "sent") return "Awaiting reply";
  if (state === "draft") return "Draft. You send.";
  return state || "Stored";
}

export function applicationStatusLabel(
  status: string | null | undefined
): string {
  const key = (status || "").trim();
  if (key === "accepted") return "Accepted";
  if (key === "interview_requested") return "Interview requested";
  if (key === "interview_scheduled") return "Interview scheduled";
  if (key === "interview_held") return "Interview slot held";
  if (key === "interview_confirmed") return "Interview confirmed";
  if (key === "hold_released") return "Hold released";
  if (key === "success") return "Succeeded";
  if (key === "failed") return "Unsuccessful";
  if (key === "declined") return "Declined";
  if (key === "applied") return "Applied";
  if (key === "prepared") return "Prepared. You send.";
  return key ? key.replace(/_/g, " ") : "Stored";
}

/** Task-model loop: why this robot/policy did not fit the job. Short list, not a novel. */
export const JOBS_DECLINE_REASONS = [
  {
    code: "work_mismatch",
    label: "This robot cannot do this physical work",
  },
  {
    code: "model_unproven",
    label: "Hardware maybe, task model / demo not convincing",
  },
  {
    code: "site_constraints",
    label: "Aisle, payload, SOP, safety, environment",
  },
  {
    code: "timing_budget",
    label: "Not now / budget / contract",
  },
  {
    code: "other",
    label: "Other (add a note)",
  },
] as const;

export type JobsDeclineReasonCode =
  (typeof JOBS_DECLINE_REASONS)[number]["code"];

export function declineReasonLabel(code: string | null | undefined): string {
  const key = (code || "").trim();
  const hit = JOBS_DECLINE_REASONS.find(row => row.code === key);
  if (hit) return hit.label;
  return key ? key.replace(/_/g, " ") : "";
}

export function toDatetimeLocalValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function suggestedHoldSlots(now: Date = new Date()): HoldSlotOption[] {
  const atHour = (base: Date, hours: number, minutes = 0) => {
    const stamp = new Date(base);
    stamp.setHours(hours, minutes, 0, 0);
    return stamp;
  };
  const addDays = (base: Date, days: number) => {
    const stamp = new Date(base);
    stamp.setDate(stamp.getDate() + days);
    return stamp;
  };
  const windowFor = (start: Date, label: string): HoldSlotOption => {
    const end = new Date(start);
    end.setHours(end.getHours() + 1);
    return {
      start: toDatetimeLocalValue(start),
      end: toDatetimeLocalValue(end),
      label,
    };
  };
  const tomorrow = addDays(now, 1);
  const twoOut = addDays(now, 2);
  return [
    windowFor(atHour(tomorrow, 10), "Tomorrow 10:00–11:00"),
    windowFor(atHour(tomorrow, 14), "Tomorrow 14:00–15:00"),
    windowFor(atHour(twoOut, 10), "In two days 10:00–11:00"),
  ];
}
