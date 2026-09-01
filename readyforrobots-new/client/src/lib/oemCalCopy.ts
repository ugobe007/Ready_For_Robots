/**
 * OemCal — short commercial proof voice for robot OEMs/integrators on conversion surfaces.
 * BuyerCal (app/services/cal_persona.py) stays for outbound buyer notes.
 * OemCal never lectures; it names the win and the next step.
 */

export const OEM_CAL_NAME = "Cal";

/** Results sticky / header — anonymous */
export function oemCalResultsAnonLine(matchCount: number): string {
  const n = Math.max(matchCount, 0);
  if (n <= 0)
    return "Cal is matching buyers to your robot — sign up to keep the list.";
  return `Cal matched ${n} buyer${n === 1 ? "" : "s"} to your robot — sign up to keep them in your workspace.`;
}

/** Results sticky — signed in */
export function oemCalResultsSignedLine(matchCount: number): string {
  const n = Math.max(matchCount, 0);
  return n > 0
    ? `${n} matched buyer${n === 1 ? "" : "s"} ready — add your company details to unlock 15 sales leads.`
    : "Add your company details to unlock 15 matched sales leads.";
}

export const OEM_CAL_RESULTS_CTA_ANON = "Sign up — keep these buyers";
export const OEM_CAL_RESULTS_CTA_SIGNED = "Unlock 15 matched sales leads";

export const OEM_CAL_RESULTS_HEAD_ANON =
  "These buyers fit your robot — claim them";
export const OEM_CAL_RESULTS_HEAD_SIGNED =
  "Review your matches — then unlock 15 sales leads";

export const OEM_CAL_RESULTS_STRIP_TITLE =
  "Cal's OEM proof — buyers for your robot, not a generic list";

export function oemCalResultsStripBody(
  unlocked: number,
  leadCount: number,
  locked: number
): string {
  if (locked > 0) {
    return `You're seeing ${unlocked} of ${leadCount} with full why-now + pitch. Free signup unlocks ${locked} more and saves them to your pipeline.`;
  }
  return `${leadCount} matched buyer${leadCount === 1 ? "" : "s"} with pitch actions — sign up free to copy Cal's note and track every lead.`;
}

/** Signup — from Results intent */
export const OEM_CAL_SIGNUP_H1_RESULTS =
  "Keep the buyers Cal matched to your robot.";
export const OEM_CAL_SIGNUP_SUB_RESULTS =
  "Free account locks in your URL matches, saves leads to CRM, and lets you copy Cal's outreach notes — built for robot OEMs and integrators.";

export const OEM_CAL_SIGNUP_H1_DEFAULT = "Automate your robot sales funnel.";
export const OEM_CAL_SIGNUP_SUB_DEFAULT =
  "Live buyer intent, pitch actions, and Cal's short notes so your team starts informed conversations — not another cold list.";

export const OEM_CAL_SIGNUP_BULLETS_RESULTS = [
  "Your URL scan matches stay in one workspace after signup",
  "Copy Cal's outreach note in one click — then save to CRM or HubSpot",
  "Next: customer info → 15 matched sales leads for your robot category",
] as const;
