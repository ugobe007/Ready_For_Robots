/** Client workspace profile for URL-matched pipeline unlock. */

export const ROBOT_WORKSPACE_PROFILE_KEY = "rfr_robot_workspace_profile";

export type RobotWorkspaceProfile = {
  company_name: string;
  category: string;
  icp: string;
  company_url?: string;
  saved_at?: number;
};

export const ROBOT_CATEGORY_OPTIONS = [
  "AMR / warehouse automation",
  "Cobot / manipulation",
  "Humanoid",
  "Service / hospitality",
  "Cleaning / disinfection",
  "Inspection / security",
  "Industrial arm / welding",
  "Other robot systems",
] as const;

export function readRobotWorkspaceProfile(): RobotWorkspaceProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(ROBOT_WORKSPACE_PROFILE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as RobotWorkspaceProfile;
    if (!parsed || typeof parsed !== "object") return null;
    return {
      company_name: String(parsed.company_name || "").trim(),
      category: String(parsed.category || "").trim(),
      icp: String(parsed.icp || "").trim(),
      company_url: parsed.company_url ? String(parsed.company_url).trim() : undefined,
      saved_at: typeof parsed.saved_at === "number" ? parsed.saved_at : undefined,
    };
  } catch {
    return null;
  }
}

export function writeRobotWorkspaceProfile(profile: RobotWorkspaceProfile): RobotWorkspaceProfile {
  const next: RobotWorkspaceProfile = {
    company_name: profile.company_name.trim(),
    category: profile.category.trim(),
    icp: profile.icp.trim(),
    company_url: profile.company_url?.trim() || undefined,
    saved_at: Date.now(),
  };
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(ROBOT_WORKSPACE_PROFILE_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }
  return next;
}

export function isRobotWorkspaceProfileComplete(profile: RobotWorkspaceProfile | null | undefined): boolean {
  if (!profile) return false;
  return Boolean(profile.company_name.trim() && profile.category.trim() && profile.icp.trim());
}

/** Split ICP text into industry tokens for match-url filtering. */
export function icpIndustryTokens(icp: string): string[] {
  return icp
    .split(/[,;/|]+/)
    .map((part) => part.trim())
    .filter((part) => part.length >= 2)
    .slice(0, 8);
}
