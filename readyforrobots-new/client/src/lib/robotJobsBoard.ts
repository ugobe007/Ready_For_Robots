/**
 * /jobs board — scored opportunities (company × workflow), per
 * docs/opportunity_scoring_model.md v0.4. Every row here is an EXAMPLE
 * until scoring build steps 1-5 ship and Bob reviews the top 20.
 */

export const JOB_FACTORS = [
  "FIT",
  "SCALE",
  "LABOR",
  "PEERS",
  "TIMING",
  "ACCESS",
  "PATH",
] as const;

export const FREE_JOB_COUNT = 5;

export type JobIndustryGroup = "hospital" | "logistics" | "factory" | "guest";
export type JobTiming = "budget" | "team" | "watch";

/** A factor is 0-1. `estimated` means the industry baseline filled it. */
export type JobFactor = { value: number; estimated?: boolean };

export type BoardJob = {
  id: string;
  company: string;
  workflow: string;
  industry: string;
  group: JobIndustryGroup;
  place: string;
  timing: JobTiming;
  why: string;
  factors: JobFactor[];
  robots: string;
  evidence: { k: string; v: string }[];
};

export const INDUSTRY_FILTERS: { value: JobIndustryGroup | "all"; label: string }[] = [
  { value: "all", label: "ALL" },
  { value: "hospital", label: "HEALTHCARE" },
  { value: "logistics", label: "WAREHOUSE & 3PL" },
  { value: "factory", label: "FACTORY & PLANT" },
  { value: "guest", label: "HOSPITALITY & RETAIL" },
];

export const TIMING_FILTERS: { value: JobTiming | "all"; label: string }[] = [
  { value: "all", label: "ALL" },
  { value: "budget", label: "BUDGET CONFIRMED" },
  { value: "team", label: "BUILDING A ROBOT TEAM" },
  { value: "watch", label: "NO TIMING SIGNAL YET" },
];

export const TIMING_TAGS: Record<JobTiming, string> = {
  budget: "BUDGET CONFIRMED",
  team: "BUILDING A ROBOT TEAM",
  watch: "NO TIMING SIGNAL YET",
};

const f = (value: number): JobFactor => ({ value });
const est = (value: number): JobFactor => ({ value, estimated: true });

export const EXAMPLE_JOBS: BoardJob[] = [
  {
    id: "j1",
    company: "Regional health system",
    workflow: "Pharmacy-to-floor delivery",
    industry: "Hospital",
    group: "hospital",
    place: "Ohio · 6 hospitals",
    timing: "budget",
    why: "RFP for autonomous delivery robots, responses due in 21 days.",
    factors: [f(0.95), f(0.8), f(0.7), f(0.85), f(1), f(0.4), est(0.6)],
    robots: "4 robots in the index fit this work",
    evidence: [
      { k: "TIMING", v: "RFP posted on the state procurement board; scope names pharmacy and lab delivery." },
      { k: "PEERS", v: "3 health systems in the region run delivery robots in pharmacy." },
      { k: "LABOR", v: "11 open courier and pharmacy-tech postings across its sites." },
      { k: "PATH (est)", v: "No known robots at these hospitals yet; industry baseline used." },
    ],
  },
  {
    id: "j2",
    company: "Third-party logistics provider",
    workflow: "Tote moving to pack stations",
    industry: "Warehouse / 3PL",
    group: "logistics",
    place: "Texas · 3 sites, 24/7",
    timing: "team",
    why: "Hired an automation engineer for its Dallas site.",
    factors: [f(0.9), f(0.9), f(0.75), f(0.9), f(0.6), f(0.5), f(0.8)],
    robots: "7 robots in the index fit this work",
    evidence: [
      { k: "PATH", v: "AMRs already move pallets at two sites; tote handling is the next step." },
      { k: "SCALE", v: "Three shifts a day; volume of a mid-size e-commerce fulfillment site." },
      { k: "TIMING", v: "Automation engineer posting names tote handling." },
    ],
  },
  {
    id: "j3",
    company: "Airport operator",
    workflow: "Terminal floor cleaning",
    industry: "Airport",
    group: "guest",
    place: "Nevada · 2 terminals",
    timing: "budget",
    why: "Funded pilot of autonomous scrubbers in one terminal.",
    factors: [f(0.9), f(0.7), f(0.65), f(0.8), f(0.85), f(0.3), f(0.7)],
    robots: "5 robots in the index fit this work",
    evidence: [
      { k: "TIMING", v: "Board minutes approve a cleaning-robot pilot budget." },
      { k: "PEERS", v: "Several large US airports run floor-cleaning robots." },
    ],
  },
  {
    id: "j4",
    company: "Auto parts plant",
    workflow: "CNC machine tending",
    industry: "Manufacturing",
    group: "factory",
    place: "Michigan · 1 plant",
    timing: "watch",
    why: "New production line announced for next year.",
    factors: [f(0.85), f(0.6), f(0.8), f(0.6), f(0.45), est(0.3), f(0.75)],
    robots: "3 robots in the index fit this work",
    evidence: [
      { k: "PATH", v: "Inspection robots and AMRs in use; machine tending is the next stage." },
      { k: "LABOR", v: "Machine-operator postings open for 60+ days." },
      { k: "ACCESS (est)", v: "No named contact yet; industry baseline used." },
    ],
  },
  {
    id: "j5",
    company: "Hotel group",
    workflow: "Room-service delivery",
    industry: "Hotel",
    group: "guest",
    place: "Las Vegas · 4 resorts",
    timing: "team",
    why: "Hired a robotics operations lead.",
    factors: [f(0.8), f(0.75), f(0.7), f(0.75), f(0.6), f(0.6), est(0.5)],
    robots: "6 robots in the index fit this work",
    evidence: [
      { k: "TIMING", v: "Robotics operations lead hired; role names guest delivery." },
      { k: "COMMITTED", v: "Already runs cleaning robots: that workflow is closed, delivery is open." },
    ],
  },
  {
    id: "j6",
    company: "Grocery chain",
    workflow: "Shelf scanning",
    industry: "Grocery",
    group: "guest",
    place: "California · 120 stores",
    timing: "watch",
    why: "Labor costs cited in quarterly results.",
    factors: [f(0.85), f(0.95), f(0.6), f(0.7), f(0.35), est(0.3), est(0.5)],
    robots: "2 robots in the index fit this work",
    evidence: [
      { k: "LABOR", v: "Earnings call names in-store labor cost as a pressure." },
      { k: "SCALE", v: "120 stores of similar size." },
    ],
  },
  {
    id: "j7",
    company: "Chemical plant operator",
    workflow: "Gauge and valve inspection rounds",
    industry: "Energy & utilities",
    group: "factory",
    place: "Louisiana · 1 site",
    timing: "watch",
    why: "Safety incident report recommends remote inspection.",
    factors: [f(0.9), f(0.5), f(0.6), f(0.65), f(0.4), est(0.3), f(0.6)],
    robots: "2 robots in the index fit this work",
    evidence: [
      { k: "TIMING", v: "Public safety report recommends remote inspection in hazardous areas." },
    ],
  },
  {
    id: "j8",
    company: "Senior living operator",
    workflow: "Meal tray delivery",
    industry: "Senior living",
    group: "hospital",
    place: "Arizona · 14 communities",
    timing: "watch",
    why: "Dining staff shortages reported.",
    factors: [f(0.8), f(0.7), f(0.8), f(0.5), f(0.3), est(0.3), est(0.4)],
    robots: "4 robots in the index fit this work",
    evidence: [{ k: "LABOR", v: "Dining and aide postings across most communities." }],
  },
];

/** Opportunity score: equal-weight average of the seven factors, ×100. */
export function jobScore(job: Pick<BoardJob, "factors">): number {
  if (!job.factors.length) return 0;
  const sum = job.factors.reduce((total, factor) => total + factor.value, 0);
  return Math.round((sum / job.factors.length) * 100);
}

export type ScoredJob = BoardJob & { score: number; locked: boolean };

export function rankJobs(
  jobs: BoardJob[],
  filters: { group: JobIndustryGroup | "all"; timing: JobTiming | "all" },
  freeCount = FREE_JOB_COUNT
): ScoredJob[] {
  return jobs
    .filter(
      (job) =>
        (filters.group === "all" || job.group === filters.group) &&
        (filters.timing === "all" || job.timing === filters.timing)
    )
    .map((job) => ({ ...job, score: jobScore(job), locked: false }))
    .sort((a, b) => b.score - a.score)
    .map((job, index) => ({ ...job, locked: index >= freeCount }));
}
