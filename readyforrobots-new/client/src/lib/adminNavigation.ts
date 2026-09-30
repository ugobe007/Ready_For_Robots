/** Scroll admin sections into view; opens <details> when target lives inside one. */
export function scrollToAdminSection(sectionId: string) {
  if (!sectionId) return;
  const el = document.getElementById(sectionId);
  if (!el) return;

  const details = el instanceof HTMLDetailsElement ? el : el.closest("details");
  if (details) details.open = true;

  el.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function scrollToAdminSectionFromHref(href: string) {
  const hashIndex = href.indexOf("#");
  if (hashIndex === -1) return;
  scrollToAdminSection(href.slice(hashIndex + 1));
}
