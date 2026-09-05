/**
 * /jobs/{slug} — capability-owner personalization.
 * Durable entity = robot, portfolio, or integrator — not job type.
 * Attribution stays on ?src=
 */
import demo from "@/data/rdd_demo_jobs.json";

export type JobsPersona = "oem" | "distributor" | "integrator";

export type JobsSlugConfig = {
  slug: string;
  persona: JobsPersona;
  displayName: string;
  /** Fixture profile that supplies preview jobs (null = no library yet). */
  profileKey: string | null;
  /** Customer-facing job count (may be portfolio-level, not fixture length). */
  jobCount: number;
  headline: string;
  subhead: string;
};

export const JOBS_SLUGS: Record<string, JobsSlugConfig> = {
  "locus-origin": {
    slug: "locus-origin",
    persona: "oem",
    displayName: "Locus Origin",
    profileKey: "locus_origin",
    jobCount: 67,
    headline: "We found 67 jobs for Locus Origin.",
    subhead:
      "Based on what Origin can do, here are places where we found compatible physical work.",
  },
  "avidbots-neo": {
    slug: "avidbots-neo",
    persona: "oem",
    displayName: "Avidbots Neo",
    profileKey: "avidbots_neo",
    jobCount: 16,
    headline: "We found 16 jobs for Avidbots Neo.",
    subhead:
      "Based on what Neo can do, here are places where we found compatible physical work.",
  },
  "boston-dynamics-spot": {
    slug: "boston-dynamics-spot",
    persona: "oem",
    displayName: "Boston Dynamics Spot",
    profileKey: null,
    jobCount: 0,
    headline: "We don't have jobs for Spot yet.",
    subhead:
      "We couldn't confidently match Spot to our current job corpus yet. Try another robot URL, or tell us what it does.",
  },
  "rg-group": {
    slug: "rg-group",
    persona: "distributor",
    displayName: "RG Group",
    profileKey: "locus_origin",
    jobCount: 37,
    headline: "We found 37 jobs for robots RG Group sells.",
    subhead:
      "Compatible physical work matched to the robots in your portfolio.",
  },
  "cross-company": {
    slug: "cross-company",
    persona: "integrator",
    displayName: "Cross Company",
    profileKey: "locus_origin",
    jobCount: 19,
    headline: "We found 19 automation jobs Cross can solve.",
    subhead:
      "Localized work matched to automation capabilities your team can deliver.",
  },
};

/** OEM demo profiles → shareable slug (for proof cards / redirects). */
export const PROFILE_KEY_TO_SLUG: Record<string, string> = {
  locus_origin: "locus-origin",
  avidbots_neo: "avidbots-neo",
};

export function resolveJobsSlug(
  raw: string | undefined | null
): JobsSlugConfig | null {
  if (!raw) return null;
  const slug = raw.trim().toLowerCase();
  return JOBS_SLUGS[slug] ?? null;
}

export function jobsPathForSlug(slug: string, src?: string | null): string {
  const base = `/jobs/${slug}`;
  if (!src) return base;
  return `${base}?src=${encodeURIComponent(src)}`;
}

export function jobsPathForProfile(
  profileKey: string,
  src?: string | null
): string {
  const slug = PROFILE_KEY_TO_SLUG[profileKey];
  if (!slug) return src ? `/?src=${encodeURIComponent(src)}` : "/";
  return jobsPathForSlug(slug, src);
}

/** Map legacy /experiment?robot=locus_origin → /jobs/locus-origin (or / with ?src=). */
export function experimentQueryToJobsPath(search: string): string {
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search
  );
  const robot = (params.get("robot") || "").trim();
  const src = (params.get("src") || "").trim() || null;
  const slug = PROFILE_KEY_TO_SLUG[robot] || null;
  if (slug) return jobsPathForSlug(slug, src);
  return src ? `/?src=${encodeURIComponent(src)}` : "/";
}

export function demoProfilesForProof() {
  return demo.profiles.map(p => ({
    profileKey: p.profile_key,
    slug:
      PROFILE_KEY_TO_SLUG[p.profile_key] || p.profile_key.replace(/_/g, "-"),
    displayName: p.display_name,
    jobCount: p.job_count_total,
  }));
}
