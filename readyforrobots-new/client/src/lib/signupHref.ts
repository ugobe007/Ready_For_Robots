/**
 * Context-preserving signup hrefs (value-first conversion continuity).
 *
 * When an anonymous user acts on a specific HOT lead (save / copy draft / advance),
 * carry the buyer's company name through the signup wall so the signup page can
 * restate exactly what they unlock — "Save Accor Hotels. Copy the draft." — instead
 * of generic copy. The `next` redirect path stays clean; `co` is a sibling param the
 * signup page reads for personalization only.
 *
 * The `next` path also carries `resume=save` so that after auth the pipeline can
 * auto-complete the save the user already asked for — turning expressed intent into
 * a real activation (first_save) instead of a re-click most new users skip.
 */

/** Build a signup href that returns to a lead and names the buyer on the signup page. */
export function signupHrefForLead(
  leadId: number | string,
  company?: string | null,
  opts?: { src?: string },
): string {
  const next = `/pipeline?lead=${leadId}&resume=save`;
  let href = `/signup?next=${encodeURIComponent(next)}`;
  const co = (company || "").trim();
  if (co) href += `&co=${encodeURIComponent(co)}`;
  const src = (opts?.src || "").trim();
  if (src) href += `&src=${encodeURIComponent(src)}`;
  return href;
}
