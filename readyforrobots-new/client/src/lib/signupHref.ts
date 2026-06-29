/**
 * Context-preserving signup hrefs (value-first conversion continuity).
 *
 * When an anonymous user acts on a specific HOT lead (save / copy draft / advance),
 * carry the buyer's company name through the signup wall so the signup page can
 * restate exactly what they unlock — "Save Accor Hotels. Copy the draft." — instead
 * of generic copy. The `next` redirect path stays clean; `co` is a sibling param the
 * signup page reads for personalization only.
 */

/** Build a signup href that returns to a lead and names the buyer on the signup page. */
export function signupHrefForLead(leadId: number | string, company?: string | null): string {
  const next = `/pipeline?lead=${leadId}`;
  let href = `/signup?next=${encodeURIComponent(next)}`;
  const co = (company || "").trim();
  if (co) href += `&co=${encodeURIComponent(co)}`;
  return href;
}
