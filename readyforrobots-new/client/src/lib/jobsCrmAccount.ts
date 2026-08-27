/**
 * Jobs CRM account storage — keep, next-steps, apply, inbox.
 * Handoff localStorage is the unsigned bridge; this is the signed-in desk.
 */
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import {
  JOBS_ACTIVATE_SRC,
  jobsActivateHref,
  jobsCrmOpenHref,
  jobsSignupHref,
} from "@/lib/jobsWorkflow";
import type { MatchJob } from "@/lib/robotJobMatch";

export const JOBS_KEEP_JOBS_CTA = "Keep jobs";
export const JOBS_KEEP_YES_CTA = "Yes";
export const JOBS_NEXT_STEPS_CTA = "Next steps →";
export const JOBS_APPLY_NEXT_CTA = "Apply →";
export const JOBS_NEXT_STEPS_ANCHOR = "jobs-next-steps";
export const JOBS_NEXT_STEPS_HINT =
  "Next steps: name the robot, pick catalogued models, add PoC if you have it, then quote the monthly price you will charge.";
export const JOBS_DOCS_HEADING = "Brochures and product specs";
export const JOBS_DOCS_HINT =
  "Upload a PDF or image spec for this robot. We attach what you select to the application — not a public dump.";
export const JOBS_EMPLOYER_ACCEPT_CTA = "Accept";
export const JOBS_EMPLOYER_INTERVIEW_CTA = "Set up interview";
export const JOBS_PROPOSED_PRICE_LABEL = "Proposed monthly price you will charge";
export const JOBS_PROPOSED_PRICE_HINT =
  "Your proposed offer — not a rate this site invented. Employers see this as your quote.";
export const JOBS_MODEL_SELECT_LABEL = "Model they will use";
export const JOBS_MODEL_SELECT_HINT =
  "Catalogued SKUs for this OEM. We do not invent a model name.";
export const JOBS_APPLY_OFFER_CTA = "Apply to the job →";
export const JOBS_INBOX_HEADING = "Employer inbox";
export const JOBS_INBOX_PASTE_HINT =
  "Inbound MX is not required to store a reply. Paste an employer email here, or send a reply if we have their address.";

export type CatalogSku = {
  name: string;
  slug?: string;
  source?: string;
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
  poc_skipped: boolean;
  monthly_price: string;
  employer_email?: string | null;
  send_status: string;
  send_error?: string | null;
  thread_state: string;
  can_send: boolean;
  no_email_reason?: string | null;
  status?: string | null;
  interview_at?: string | null;
  interview_note?: string | null;
  interview_mode?: string | null;
  oem_email?: string | null;
  employer_decision_url?: string | null;
  documents?: RobotDocument[];
  messages?: JobsCrmMessage[];
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
  application?: JobsCrmApplication | null;
  created_at?: string | null;
};

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
  submissionId?: number | null,
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

export function isJobsCrmOfferQuery(search: string | null | undefined): boolean {
  try {
    return new URLSearchParams((search || "").replace(/^\?/, "")).get("next") === "offer";
  } catch {
    return false;
  }
}

async function jobsCrmFetch<T>(
  path: string,
  token: string,
  init: RequestInit = {},
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
    liveFetchInit({ ...init, headers }),
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
  },
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
  const data = await jobsCrmFetch<{ jobs: KeptJobRow[] }>("/api/jobs-crm/jobs", token);
  return data.jobs || [];
}

export async function fetchCatalogSkus(
  token: string,
  opts: { url?: string; company?: string },
): Promise<CatalogSku[]> {
  const q = new URLSearchParams();
  if (opts.url) q.set("url", opts.url);
  if (opts.company) q.set("company", opts.company);
  const data = await jobsCrmFetch<{ skus: CatalogSku[] }>(
    `/api/jobs-crm/skus?${q.toString()}`,
    token,
  );
  return data.skus || [];
}

export async function applyJobOnAccount(
  token: string,
  body: {
    jobKey: string;
    robotName: string;
    selectedModels: string[];
    monthlyPrice: string;
    pocEvidence?: string;
    pocSkipped?: boolean;
    job?: MatchJob;
    documentIds?: string[];
  },
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>("/api/jobs-crm/apply", token, {
    method: "POST",
    body: JSON.stringify({
      job_key: body.jobKey,
      robot_name: body.robotName,
      selected_models: body.selectedModels,
      monthly_price: body.monthlyPrice,
      poc_evidence: body.pocEvidence || "",
      poc_skipped: Boolean(body.pocSkipped),
      job: body.job || null,
      document_ids: body.documentIds || [],
    }),
  });
}

export async function fetchRobotDocuments(token: string): Promise<RobotDocument[]> {
  const data = await jobsCrmFetch<{ documents: RobotDocument[] }>(
    "/api/jobs-crm/documents",
    token,
  );
  return data.documents || [];
}

export async function uploadRobotDocument(
  token: string,
  file: File,
  kind = "spec",
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
    }),
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
  applicationId: string,
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/confirm-interview`,
    token,
    { method: "POST" },
  );
}

export async function markApplicationOutcome(
  token: string,
  applicationId: string,
  outcome: "success" | "failed",
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/outcome`,
    token,
    { method: "POST", body: JSON.stringify({ outcome }) },
  );
}

export async function fetchApplicationThread(
  token: string,
  applicationId: string,
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}`,
    token,
  );
}

export async function replyOnApplication(
  token: string,
  applicationId: string,
  body: string,
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/reply`,
    token,
    { method: "POST", body: JSON.stringify({ body }) },
  );
}

export async function pasteInboundReply(
  token: string,
  applicationId: string,
  body: string,
  fromEmail?: string,
): Promise<JobsCrmApplication> {
  return jobsCrmFetch<JobsCrmApplication>(
    `/api/jobs-crm/applications/${applicationId}/paste-inbound`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ body, from_email: fromEmail || null }),
    },
  );
}

export async function postJobsCrmActivity(
  token: string,
  event: { kind: string; label: string; jobKey?: string; company?: string },
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

export function threadStateLabel(state: string | null | undefined): string {
  if (state === "replied") return "Replied";
  if (state === "awaiting_reply" || state === "sent") return "Awaiting reply";
  if (state === "draft") return "Stored";
  return state || "Stored";
}

export function applicationStatusLabel(status: string | null | undefined): string {
  const key = (status || "").trim();
  if (key === "accepted") return "Accepted";
  if (key === "interview_requested") return "Interview requested";
  if (key === "interview_scheduled") return "Interview scheduled";
  if (key === "interview_confirmed") return "Interview confirmed";
  if (key === "success") return "Succeeded";
  if (key === "failed") return "Unsuccessful";
  if (key === "declined") return "Declined";
  if (key === "applied") return "Applied";
  return key ? key.replace(/_/g, " ") : "Stored";
}
