/**
 * Shared content model for all three 1970s concepts.
 * Copy is lifted from the live readyforrobots.com so the options can be
 * compared like-for-like against the current site.
 */

export interface JobCard {
  id: string;
  employer: string;
  sector: string;
  workplace: string;
  work: string;
  drivers: string[];
  window: string;
  fit: string[];
  status: "CONDITIONAL" | "OPEN";
}

export const JOB_CARDS: JobCard[] = [
  {
    id: "JOB-001",
    employer: "Amazon",
    sector: "Logistics & Fulfillment",
    workplace: "European fulfillment network",
    work: "Warehouse automation across a €10bn Europe expansion — new fulfillment capacity, pick-and-place lines.",
    drivers: ["New locations / capacity growth", "Public automation news", "Capital budgets opening up"],
    window: "120–365 days (build-out & evaluation)",
    fit: ["Pick-and-place robots", "Industrial robotic arms", "Collaborative robots (cobots)"],
    status: "OPEN",
  },
  {
    id: "JOB-002",
    employer: "Benchmark Senior Living",
    sector: "Senior Living & Assisted Living",
    workplace: "Large multi-site care operator",
    work: "Front-line labor shortage pushing evaluation of service and material-handling robots across residences.",
    drivers: ["Staffing pressure", "Capacity growth", "Leadership driving new initiatives"],
    window: "90–210 days (capital program phase)",
    fit: ["Pick-and-place robots", "Industrial robotic arms", "Collaborative robots (cobots)"],
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

export const STEPS = [
  { n: "01", title: "Show us your robot", body: "Paste a product URL, or pick a named catalog robot. We read the SKU — not a category guess." },
  { n: "02", title: "Available jobs", body: "Inspect employment cards: employer, workplace, work. Cards stay Conditional until there is evidence." },
  { n: "03", title: "CRM", body: "Keep 5 opportunities on free. Run the next robot the same way." },
] as const;

export const DEFINITIONS = [
  { term: "Employer", def: "The organization with physical work — not a prospect or lead." },
  { term: "Workplace", def: "The facility where the work happens." },
  { term: "Work", def: "Observable activity, robot-neutral. We do not invent a use-case to fit a SKU." },
  { term: "Robot Job", def: "Work defined well enough to recruit against. Cards stay Conditional until evidence." },
] as const;

export const TAGLINE = "Robots need jobs. We find the work your machine is qualified to do — employer, workplace, work — then keep it in CRM.";

export const ASSETS = {
  groovyRobot: "/manus-storage/robot-70s-groovy_d4d5a95d.png",
  spaceRobot: "/manus-storage/robot-spaceage_1f7795d6.png",
  missionPatch: "/manus-storage/mission-patch_ca6da6f4.png",
  terminal: "/manus-storage/robot-terminal_267dd9e8.png",
  paper: "/manus-storage/paper-texture_10c76429.png",
} as const;
