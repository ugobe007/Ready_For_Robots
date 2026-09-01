/**
 * `/` first beat is who is this visit — not FIND yet.
 *
 * Option 1 Look for robot jobs → OEM FIND step 1 (`/?visit=jobs`).
 * Option 2 Look for robot candidates → employer MATCH/POST (`/?visit=candidates`).
 * Wordmark `/?new=1` returns to this fork. FIND after the fork is unchanged.
 */
export const LANDING_VISIT_QUERY = "visit";
export const LANDING_VISIT_JOBS = "jobs";
export const LANDING_VISIT_CANDIDATES = "candidates";

export type LandingVisit = "landing" | "jobs" | "candidates";

export const LOOK_FOR_ROBOT_JOBS_CTA = "Look for robot jobs";
export const LOOK_FOR_ROBOT_CANDIDATES_CTA = "Look for robot candidates";

export const LANDING_HEADLINE = "Who is this visit?";
export const LANDING_SUBHEAD =
  "Jobs for a robot you already have, or robots for work you need done.";

export const LANDING_JOBS_HINT =
  "Paste a product URL, or pick a named catalog robot. We match it to real jobs.";
export const LANDING_CANDIDATES_HINT =
  "Tell us the work. We match named catalog robots. Then you can post the job.";

export const I_KNOW_THE_ROBOT_LABEL = "I know the robot";
export const I_KNOW_THE_ROBOT_HINT =
  "Pick a class or a named SKU from the catalog. We will not invent a model.";

export const EMPLOYER_MATCH_CTA = "Match robots →";
export const EMPLOYER_POST_JOB_CTA = "Post this job →";
export const EMPLOYER_EMPTY_MATCH =
  "No catalog robots for this work yet. Post the job so OEMs can find it.";

export const EMPLOYER_PROCESS_STEPS = [
  {
    id: "work" as const,
    n: "01",
    label: "What is the work",
    linkLabel: EMPLOYER_MATCH_CTA,
  },
  {
    id: "robots" as const,
    n: "02",
    label: "Matching robots",
    linkLabel: "Here are the robots →",
  },
  {
    id: "post" as const,
    n: "03",
    label: "Post the job",
    linkLabel: EMPLOYER_POST_JOB_CTA,
  },
];

export type EmployerProcessStepId = (typeof EMPLOYER_PROCESS_STEPS)[number]["id"];

/** Work-language tiles for employer MATCH. Morphology tiles stay on FIND. */
export const EMPLOYER_WORK_TILE_IDS = [
  "serving",
  "cleaning",
  "warehouse",
  "healthcare",
  "food_prep",
  "hospitality",
  "logistics",
  "factory",
  "agriculture",
  "mining",
  "construction",
] as const;

export function jobsFindHref(): string {
  return `/?${LANDING_VISIT_QUERY}=${LANDING_VISIT_JOBS}`;
}

export function jobsCandidatesHref(): string {
  return `/?${LANDING_VISIT_QUERY}=${LANDING_VISIT_CANDIDATES}`;
}

export function landingVisitFromSearch(
  search: string | null | undefined
): LandingVisit {
  const params = new URLSearchParams((search || "").replace(/^\?/, ""));
  if (params.get("new") === "1") return "landing";
  const visit = (params.get(LANDING_VISIT_QUERY) || "").trim();
  if (visit === LANDING_VISIT_JOBS) return "jobs";
  if (visit === LANDING_VISIT_CANDIDATES) return "candidates";
  return "landing";
}

export function isEmployerVisit(search: string | null | undefined): boolean {
  return landingVisitFromSearch(search) === "candidates";
}

export function isJobsFindVisit(search: string | null | undefined): boolean {
  return landingVisitFromSearch(search) === "jobs";
}
