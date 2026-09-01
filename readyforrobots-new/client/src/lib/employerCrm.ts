/**
 * Employer CRM v1 — their postings + shortlisted robots.
 * Session only. Not Cal. Not SIGNAL. No invented emails.
 */
export const EMPLOYER_CRM_SESSION_KEY = "rfr_employer_crm_v1";

export type EmployerShortlist = {
  name: string;
  vendor_name: string;
  robot_class?: string | null;
  vendor_url?: string | null;
};

export type EmployerPosting = {
  id: string;
  employer: string;
  title: string;
  workplace?: string;
  description?: string;
  work_class?: string;
  job_url?: string;
  job_key?: string | null;
  persisted: boolean;
  shortlisted: EmployerShortlist[];
  posted_at: string;
};

function readAll(): EmployerPosting[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(EMPLOYER_CRM_SESSION_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (row): row is EmployerPosting =>
        Boolean(row) &&
        typeof row === "object" &&
        typeof (row as EmployerPosting).employer === "string" &&
        typeof (row as EmployerPosting).title === "string"
    );
  } catch {
    return [];
  }
}

function writeAll(rows: EmployerPosting[]): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(
      EMPLOYER_CRM_SESSION_KEY,
      JSON.stringify(rows)
    );
  } catch {
    /* ignore quota */
  }
}

export function listEmployerPostings(): EmployerPosting[] {
  return readAll();
}

export function saveEmployerPosting(row: EmployerPosting): EmployerPosting[] {
  const next = [row, ...readAll().filter(item => item.id !== row.id)];
  writeAll(next);
  return next;
}

export function clearEmployerCrm(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(EMPLOYER_CRM_SESSION_KEY);
  } catch {
    /* ignore */
  }
}
