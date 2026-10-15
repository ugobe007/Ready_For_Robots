/**
 * Results page copy (docs/website_copy_v1.md §5). Results-only: the CRM desk
 * keeps `jobsHeading` and its own hints.
 */
import { robotClassTitle } from "@/lib/jobsWorkflow";
import type { RobotJobQualification } from "@/lib/robotJobCard";

export const RESULTS_EXAMPLE_NOTE_LEAD = "Early access.";
export const RESULTS_EXAMPLE_NOTE_BODY =
  "Cards marked Example show the kind of work your robot matches. Live buyers with sources are rolling out industry by industry, starting with warehouses and logistics.";

export const RESULTS_EMPTY_HEADLINE = "No buyers yet for this robot.";
export const RESULTS_EMPTY_BODY =
  "We haven't found companies moving to automate this work yet. We'll keep looking.";
/** Bracketed placeholder until the save-robot flow exists. */
export const RESULTS_EMPTY_SAVE_PLACEHOLDER = "[Save this robot]";
export const RESULTS_EMPTY_SAVE_TAIL = "to get notified.";

export const RESULTS_SAVE_CTA = "Save buyers →";
export const RESULTS_RAIL_HINT =
  "Open a card to see the company, the work and why it fits. Keep the ones you want, then save them.";

export function resultsHeading(opts: {
  productName?: string | null;
  companyName?: string | null;
  robotCount?: number;
}): string {
  const product = (opts.productName || "").trim();
  const company = (opts.companyName || "").trim();
  const name =
    (opts.robotCount ?? 1) > 1 ? company || product : product || company;
  return name ? `Buyers for ${name}` : "Buyers for your robot";
}

export function resultsSelectedHint(count: number): string {
  return `${count} selected.`;
}

function sentenceCase(value: string): string {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}

/**
 * Job rows sometimes carry "Employer · City" or a slug in `industry`.
 * Only a plain industry label is shown.
 */
export function cardIndustry(
  industry: string | null | undefined,
  exclude: (string | null | undefined)[] = []
): string | null {
  const raw = String(industry || "")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!raw || raw.includes("·")) return null;
  const lower = raw.toLowerCase();
  if (exclude.some(x => (x || "").trim().toLowerCase() === lower)) return null;
  return sentenceCase(raw);
}

/** "{Form} · {Main work} · {Industries}" — missing parts are omitted. */
export function robotSummaryLine(opts: {
  robotClass?: string | null;
  work?: (string | null | undefined)[];
  industries?: (string | null | undefined)[];
}): string {
  const form = opts.robotClass ? robotClassTitle(opts.robotClass) : "";
  const work = uniqueClean(opts.work).slice(0, 2).join(", ");
  const industries = uniqueClean(opts.industries)
    .slice(0, 3)
    .map((v, i) => (i === 0 ? sentenceCase(v) : v.toLowerCase()))
    .join(", ");
  return [
    form && form !== "robot" ? sentenceCase(form) : "",
    sentenceCase(work),
    industries,
  ]
    .filter(Boolean)
    .join(" · ");
}

function uniqueClean(values?: (string | null | undefined)[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const v of values || []) {
    const s = String(v || "").trim();
    if (!s || seen.has(s.toLowerCase())) continue;
    seen.add(s.toLowerCase());
    out.push(s);
  }
  return out;
}

/** "Pending robot résumé" is internal state, not something a visitor can act on. */
export function showQualificationOnResults(
  qualification: RobotJobQualification
): boolean {
  return qualification !== "pending_robot";
}
