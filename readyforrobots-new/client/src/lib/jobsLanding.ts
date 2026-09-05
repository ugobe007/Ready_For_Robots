/**
 * `/` first beat is the product fork. Not FIND yet.
 *
 * Option 1 Jobs for Robots → OEM FIND step 1 (`/?visit=jobs`).
 * Option 2 Robots for Jobs → employer MATCH/POST (`/?visit=candidates`).
 * Wordmark `/?new=1` returns to this fork. FIND after the fork is unchanged.
 *
 * Layout is the sparse fork: kicker, two-line headline, Kare face down
 * and to the right (emerald stroke + eyes + mouth, no filled square),
 * intro, two door cards (large catalog icons, who-label, dest line),
 * then Jobs brief. FIND is the emerald frame; MATCH is the cream
 * outline. Navy / cream. Outfit on headlines and CTAs, same as the
 * header wordmark (`font-display`). True emerald on Robots, the Kare
 * face, and brief employer names. Archivo on the subhead and intro.
 * No dither, no window bars, no SIGNAL report hero. The A–E picker
 * stays out of production.
 */
export const LANDING_VISIT_QUERY = "visit";
export const LANDING_VISIT_JOBS = "jobs";
export const LANDING_VISIT_CANDIDATES = "candidates";

export type LandingVisit = "landing" | "jobs" | "candidates";

export const LOOK_FOR_ROBOT_JOBS_CTA = "Jobs for Robots";
export const LOOK_FOR_ROBOT_CANDIDATES_CTA = "Robots for Jobs";
/** Points at the two doors. Same arrow as Find jobs →. */
export const LANDING_DOORS_CUE = "START HERE →";
/** 24×24 maps at this scale so the truck / handshake read as marks, not crumbs. */
export const LANDING_DOOR_ICON_SCALE = 3;
export const LANDING_DOOR_ICON_FILL = "#7C3AED";
export const LANDING_JOBS_DOOR_LINE = "Paste a robot URL.";
export const LANDING_CANDIDATES_DOOR_LINE = "Name the work.";

export const LANDING_EYEBROW = "Ready For Robots";
export const LANDING_KICKER_JOBS = "Jobs";
export const LANDING_HEADLINE = "Put Robots to Work.";
export const LANDING_HEADLINE_BEFORE = "Put ";
export const LANDING_HEADLINE_ROBOT = "Robots";
export const LANDING_HEADLINE_AFTER = "";
export const LANDING_HEADLINE_LEAD = `${LANDING_HEADLINE_BEFORE}${LANDING_HEADLINE_ROBOT}${LANDING_HEADLINE_AFTER}`;
export const LANDING_HEADLINE_END = "to Work.";
export const LANDING_SUBHEAD = "Find jobs for robots and robots for jobs....";
export const LANDING_INTRO =
  "Submit your robot URL or your robot job. We put robots to work.";
export const LANDING_CTA_ROBOT_WORD = "Robots";

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
    href: "/?visit=jobs",
    cta: LOOK_FOR_ROBOT_JOBS_CTA,
  },
  {
    n: "02",
    title: "Available jobs",
    body: "Inspect employment cards: employer, workplace, work. Cards stay Conditional until there is evidence.",
    href: "/?visit=jobs",
    cta: "See available jobs →",
  },
  {
    n: "03",
    title: "CRM",
    body: "Keep 5 opportunities on free. Run the next robot the same way.",
    href: "/signup?next=%2Fpipeline%3Fsrc%3Djobs_activate&src=jobs_activate",
    cta: "Open CRM →",
  },
] as const;

export const LANDING_BRIEF_EYEBROW = "Jobs brief · This week";
export const LANDING_BRIEF_HEADLINE = "Jobs for robots.";
export const LANDING_BRIEF_JOB_FIELD = "Jobs";
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
export const LANDING_PRICING_HREF = "/pricing";
export const LANDING_FAQ_HREF = "/pricing#faq";
export const LANDING_PRIVACY_HREF = "/privacy";
export const LANDING_SUPPORT_HREF = "mailto:support@readyforrobots.com";
export const LANDING_ABOUT_HREF = "/intelligence";
export const LANDING_BRIEF_JOB_CTA = LOOK_FOR_ROBOT_JOBS_CTA;
export const LANDING_FOOTER_MARK =
  "© 2026 ReadyForRobots · Jobs for your robot";
export const LANDING_FOOTER_LINKS = [
  { label: "Pricing", href: LANDING_PRICING_HREF },
  { label: "FAQ", href: LANDING_FAQ_HREF },
  { label: "Privacy", href: LANDING_PRIVACY_HREF },
  {
    label: "support@readyforrobots.com",
    href: LANDING_SUPPORT_HREF,
  },
] as const;

/** Label → dest. Tests lock Jobs vs candidates vs CRM vs About so they cannot swap. */
export const LANDING_LINK_MAP = [
  { label: LOOK_FOR_ROBOT_JOBS_CTA, href: "/?visit=jobs" },
  { label: LOOK_FOR_ROBOT_CANDIDATES_CTA, href: "/?visit=candidates" },
  { label: LANDING_START_FREE_CTA, href: LANDING_SIGNUP_HREF },
  { label: LANDING_BRIEFING_CTA, href: LANDING_BRIEFING_HREF },
  { label: "Pricing", href: LANDING_PRICING_HREF },
  { label: "FAQ", href: LANDING_FAQ_HREF },
  { label: "Privacy", href: LANDING_PRIVACY_HREF },
  { label: "support@readyforrobots.com", href: LANDING_SUPPORT_HREF },
] as const;

/** Kare Macintosh palette, landing only. FIND / employer keep Jobs chrome. */
export const LANDING_COLORS = {
  page: "#0A0F1E",
  navy2: "#0D1426",
  charcoal: "#141820",
  panel: "#11162B",
  card: "#11162B",
  mint: "#2EE6A8",
  mintDim: "#1E8F6B",
  /** True emerald for robot / Robots / employer — not the mint square. */
  emerald: "#10B981",
  cream: "#F3E8FF",
  lavender: "#F3E8FF",
  paper: "#E9D5FF",
  text: "#F3E8FF",
  purple: "#C4B5FD",
  violet: "#8B5CF6",
  muted: "#C4B5FD",
  line: "rgba(196,181,253,0.22)",
} as const;

export const I_KNOW_THE_ROBOT_LABEL = "What type of robot?";
export const I_KNOW_THE_ROBOT_HINT =
  "Pick a type we already list. Then find jobs.";

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

export function jobsFindHref(url?: string): string {
  const base = `/?${LANDING_VISIT_QUERY}=${LANDING_VISIT_JOBS}`;
  return url ? `${base}&url=${encodeURIComponent(url)}` : base;
}

export function jobsCandidatesHref(): string {
  return `/?${LANDING_VISIT_QUERY}=${LANDING_VISIT_CANDIDATES}`;
}

export function landingVisitFromSearch(
  search: string | null | undefined
): LandingVisit {
  const params = new URLSearchParams((search || "").replace(/^\?/, ""));
  if (params.get("new") === "1") return "landing";
  if (params.get("restore") === "1") return "jobs";
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

/** Headline stays cream. Mint is not an H1 color. */
export function landingHeadlineParts(
  headline: string
): { text: string; accent: boolean }[] {
  const chunks = headline
    .split(".")
    .map(part => part.trim())
    .filter(Boolean);
  return chunks.map(text => ({
    text: `${text}.`,
    accent: false,
  }));
}

export type LandingAccentPart = { text: string; accent: boolean };

/** One exact word (robot / Robots). Rest of the string stays unaccented. */
export function splitAccentWord(
  text: string,
  word: string
): LandingAccentPart[] {
  const idx = text.indexOf(word);
  if (idx < 0) return [{ text, accent: false }];
  const parts: LandingAccentPart[] = [];
  if (idx > 0) parts.push({ text: text.slice(0, idx), accent: false });
  parts.push({ text: word, accent: true });
  const rest = text.slice(idx + word.length);
  if (rest) parts.push({ text: rest, accent: false });
  return parts;
}
