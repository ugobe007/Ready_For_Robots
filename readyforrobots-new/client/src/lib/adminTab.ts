export type AdminTab = "cal" | "pipeline" | "system";

export function adminTabFromHash(hash: string): AdminTab {
  const h = (hash || "").replace(/^#/, "").toLowerCase();
  if (h === "pipeline" || h === "pipeline-tab") return "pipeline";
  if (h === "system" || h === "workflow") return "system";
  return "cal";
}

export function adminTabHash(tab: AdminTab): string {
  if (tab === "pipeline") return "#pipeline";
  if (tab === "system") return "#system";
  return "#cal-outreach";
}

export function setAdminTabHash(tab: AdminTab): void {
  if (typeof window === "undefined") return;
  const hash = adminTabHash(tab);
  const path = window.location.pathname || "/admin";
  if (`${path}${window.location.hash}` !== `${path}${hash}`) {
    window.history.replaceState(null, "", `${path}${hash}`);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  }
}
