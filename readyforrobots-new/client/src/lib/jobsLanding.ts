/**
 * `/` first beat is the product fork — not FIND yet.
 *
 * Option 1 Look for robot jobs → OEM FIND step 1 (`/?visit=jobs`).
 * Option 2 Look for robot candidates → employer MATCH/POST (`/?visit=candidates`).
 * Wordmark `/?new=1` returns to this fork. FIND after the fork is unchanged.
 *
 * Layout follows the 2026-09-01 Manus mockup
 * (https://rfr70sui-wipjpxme.manus.space). Operator copy wins on
 * headline + subhead. The A–E picker is designer chrome and stays out
 * of production.
 */
export const LANDING_VISIT_QUERY = "visit";
export const LANDING_VISIT_JOBS = "jobs";
export const LANDING_VISIT_CANDIDATES = "candidates";

export type LandingVisit = "landing" | "jobs" | "candidates";

export const LOOK_FOR_ROBOT_JOBS_CTA = "Look for robot jobs";
export const LOOK_FOR_ROBOT_CANDIDATES_CTA = "Look for robot candidates";

export const LANDING_EYEBROW = "ReadyForRobots · Robot Employment";
export const LANDING_HEADLINE = "Put your robot to work.";
export const LANDING_SUBHEAD =
  "Jobs for a robot you already have, or robots for work you need done. Paste a product URL — we match it to real jobs, then keep them in our CRM.";

export const LANDING_JOBS_LABEL = "Robot owner";
export const LANDING_CANDIDATES_LABEL = "Employer";
export const LANDING_JOBS_HINT =
  "Paste a product URL, or pick a named catalog robot. We read the SKU — not a category guess — and match it to real jobs.";
export const LANDING_CANDIDATES_HINT =
  "Tell us the work. We match named catalog robots from the ontology. Then you can post the job.";

export const LANDING_HOW_EYEBROW = "How Jobs works";
export const LANDING_HOW_HEADLINE = "Three steps. No buyer pipeline.";
export const LANDING_HOW_STEPS = [
  {
    n: "01",
    title: "Show us your robot",
    body: "Paste a product URL, or pick a named catalog robot. We read the SKU — not a category guess.",
  },
  {
    n: "02",
    title: "Available jobs",
    body: "Inspect employment cards: employer, workplace, work. Cards stay Conditional until there is evidence.",
  },
  {
    n: "03",
    title: "CRM",
    body: "Keep 5 opportunities on free. Run the next robot the same way.",
  },
] as const;

export const LANDING_BRIEF_EYEBROW = "Jobs brief · This week";
export const LANDING_BRIEF_HEADLINE = "Work robots can take";
export const LANDING_BRIEF_NOTE =
  "5 jobs on free. Cards stay Conditional until evidence.";

export type LandingBriefJob = {
  id: string;
  employer: string;
  sector: string;
  workplace: string;
  work: string;
  drivers: readonly string[];
  window: string;
  fit: readonly string[];
  status: "OPEN" | "CONDITIONAL";
};

/** Named employers from the mockup. Robot classes, not invented SKUs. */
export const LANDING_BRIEF_JOBS: readonly LandingBriefJob[] = [
  {
    id: "JOB-001",
    employer: "Amazon",
    sector: "Logistics & Fulfillment",
    workplace: "European fulfillment network",
    work: "Warehouse automation across a €10bn Europe expansion — new fulfillment capacity, pick-and-place lines.",
    drivers: [
      "New locations / capacity growth",
      "Public automation news",
      "Capital budgets opening up",
    ],
    window: "120–365 days (build-out & evaluation)",
    fit: [
      "Pick-and-place robots",
      "Industrial robotic arms",
      "Collaborative robots (cobots)",
    ],
    status: "OPEN",
  },
  {
    id: "JOB-002",
    employer: "Benchmark Senior Living",
    sector: "Senior Living & Assisted Living",
    workplace: "Large multi-site care operator",
    work: "Front-line labor shortage pushing evaluation of service and material-handling robots across residences.",
    drivers: [
      "Staffing pressure",
      "Capacity growth",
      "Leadership driving new initiatives",
    ],
    window: "90–210 days (capital program phase)",
    fit: [
      "Pick-and-place robots",
      "Industrial robotic arms",
      "Collaborative robots (cobots)",
    ],
    status: "CONDITIONAL",
  },
  {
    id: "JOB-003",
    employer: "Whitsons Culinary Group",
    sector: "Food Service & Catering",
    workplace: "Large food-service production facilities",
    work: "Acute front-line labor shortages pushing evaluation of service and material-handling robots in kitchens.",
    drivers: ["Staffing pressure", "Capacity growth", "Robot job posted"],
    window: "90–210 days (capital program phase)",
    fit: ["Humanoid robots", "Service robots", "Delivery robots"],
    status: "CONDITIONAL",
  },
];

export const LANDING_VOCAB_EYEBROW = "Vocabulary";
export const LANDING_VOCAB_HEADLINE = "Employer. Workplace. Work. Robot Job.";
export const LANDING_VOCAB = [
  {
    term: "Employer",
    def: "The organization with physical work — not a prospect or lead.",
  },
  {
    term: "Workplace",
    def: "The facility where the work happens.",
  },
  {
    term: "Work",
    def: "Observable activity, robot-neutral. We do not invent a use-case to fit a SKU.",
  },
  {
    term: "Robot Job",
    def: "Work defined well enough to recruit against. Cards stay Conditional until evidence.",
  },
] as const;

export const LANDING_CLOSE_HEADLINE = LANDING_HEADLINE;
export const LANDING_CLOSE_SUBHEAD =
  "Start a free workspace — 5 jobs, 5 CRM opportunities, no card required.";
export const LANDING_START_FREE_CTA = "Start free workspace";
export const LANDING_BRIEFING_CTA = "Download the 2026 briefing";
export const LANDING_SIGNUP_HREF =
  "/signup?next=%2Fpipeline%3Fsrc%3Djobs_activate&src=jobs_activate";
export const LANDING_BRIEFING_HREF = "/intelligence#report";
export const LANDING_FOOTER_MARK =
  "© 2026 ReadyForRobots · Jobs for your robot";
export const LANDING_FOOTER_LINKS = [
  { label: "Pricing", href: "/pricing" },
  { label: "FAQ", href: "/pricing#faq" },
  { label: "Privacy", href: "/privacy" },
  {
    label: "support@readyforrobots.com",
    href: "mailto:support@readyforrobots.com",
  },
] as const;

/** Mockup palette, landing only. FIND / employer keep Jobs chrome. */
export const LANDING_COLORS = {
  page: "#0A0F1E",
  panel: "#0E1526",
  card: "#111A30",
  mint: "#2EE6A8",
  mintDim: "#1E8F6B",
  text: "#E8EEF7",
  muted: "#8B98B0",
  line: "rgba(139,152,176,0.18)",
} as const;

export const I_KNOW_THE_ROBOT_LABEL = "I know the robot";
export const I_KNOW_THE_ROBOT_HINT =
  "Pick a class or a named SKU we already have. No invented models.";

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

export type EmployerProcessStepId =
  (typeof EMPLOYER_PROCESS_STEPS)[number]["id"];

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

/** Last sentence is the mint accent, matching the mockup hero. */
export function landingHeadlineParts(
  headline: string
): { text: string; accent: boolean }[] {
  const chunks = headline
    .split(".")
    .map(part => part.trim())
    .filter(Boolean);
  return chunks.map((text, index) => ({
    text: `${text}.`,
    accent: index === chunks.length - 1,
  }));
}
