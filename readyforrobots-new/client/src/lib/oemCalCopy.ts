/**
 * Cal — Jobs recruiter copy. He lives on `/pipeline?src=jobs_activate` after
 * Open CRM. He asks missing apply facts and prepares the draft. You send.
 *
 * SIGNAL `/results` strings below do not name Cal as a buyer matcher.
 * BuyerCal leftover notes stay in app/services/cal_persona.py and stay frozen.
 */

export const OEM_CAL_NAME = "Cal";
export const OEM_CAL_TITLE = "Jobs Recruiter";
export const OEM_CAL_JOB =
  "Help me apply these kept jobs without sounding like a list broker.";
export const OEM_CAL_DESK_EYEBROW = "Cal · Jobs recruiter";
export const OEM_CAL_DESK_LEAD =
  "I'm Cal. I work these kept jobs with you. I ask what's missing, prepare the apply draft, and you send.";
export const OEM_CAL_PREPARE_CTA = "Prepare application →";
export const OEM_CAL_OPERATOR_SENDS =
  "This is a draft. Review it. You send. I do not email the employer until you do.";

/** SIGNAL /results — leftover buyer scan. Cal is not this matcher. */
export function oemCalResultsAnonLine(matchCount: number): string {
  const n = Math.max(matchCount, 0);
  if (n <= 0) return "URL scan matches stay here. Sign up to keep the list.";
  return `${n} match${n === 1 ? "" : "es"} from your URL scan. Sign up to keep them in your workspace.`;
}

export function oemCalResultsSignedLine(matchCount: number): string {
  const n = Math.max(matchCount, 0);
  return n > 0
    ? `${n} match${n === 1 ? "" : "es"} ready — add your company details to unlock 15 sales leads.`
    : "Add your company details to unlock 15 matched sales leads.";
}

export const OEM_CAL_RESULTS_CTA_ANON = "Sign up — keep these matches";
export const OEM_CAL_RESULTS_CTA_SIGNED = "Unlock 15 matched sales leads";

export const OEM_CAL_RESULTS_HEAD_ANON = "These companies match your scan — claim them";
export const OEM_CAL_RESULTS_HEAD_SIGNED = "Review your matches — then unlock 15 sales leads";

export const OEM_CAL_RESULTS_STRIP_TITLE =
  "URL scan matches for this robot, not a generic list";

export function oemCalResultsStripBody(
  unlocked: number,
  leadCount: number,
  locked: number
): string {
  if (locked > 0) {
    return `You're seeing ${unlocked} of ${leadCount} with full why-now + pitch. Free signup unlocks ${locked} more and saves them to your pipeline.`;
  }
  return `${leadCount} match${leadCount === 1 ? "" : "es"} with pitch actions — sign up free to copy the note and track every lead.`;
}

export const OEM_CAL_SIGNUP_H1_RESULTS = "Keep the matches from your URL scan.";
export const OEM_CAL_SIGNUP_SUB_RESULTS =
  "Free account locks in your URL matches, saves leads to CRM, and lets you copy outreach notes — built for robot OEMs and integrators.";

export const OEM_CAL_SIGNUP_H1_DEFAULT = "Automate your robot sales funnel.";
export const OEM_CAL_SIGNUP_SUB_DEFAULT =
  "Live buyer intent, pitch actions, and short notes so your team starts informed conversations — not another cold list.";

export const OEM_CAL_SIGNUP_BULLETS_RESULTS = [
  "Your URL scan matches stay in one workspace after signup",
  "Copy the outreach note in one click — then save to CRM or HubSpot",
  "Next: customer info → 15 matched sales leads for your robot category",
] as const;
