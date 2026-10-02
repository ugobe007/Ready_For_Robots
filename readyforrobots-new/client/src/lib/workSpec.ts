/**
 * Employer MATCH work spec. Catalog match stays POST /api/employer-robot-match.
 * Payback uses the same labor example as the Copilot, and only from numbers
 * the user typed. No invented employer, SKU, or wage.
 */
import { EMPLOYER_WORK_TILE_IDS } from "./jobsLanding";

export type WorkflowId = (typeof EMPLOYER_WORK_TILE_IDS)[number];

export type WorkflowOption = {
  id: WorkflowId;
  label: string;
  hint: string;
  /** Existing catalog class. Do not send the tile id to the matcher. */
  catalogClass: string;
  tradeoff: string;
};

export const WORKFLOWS: readonly WorkflowOption[] = [
  {
    id: "pallets",
    label: "Pallets",
    hint: "Move pallets across a warehouse floor",
    catalogClass: "warehouse",
    tradeoff:
      "Pallet movement is horizontal transport. An arm that stacks cases is a different machine.",
  },
  {
    id: "pick_pack",
    label: "Pick & pack",
    hint: "Pick items and pack orders",
    catalogClass: "warehouse",
    tradeoff:
      "Pick and pack is piece handling. A pallet tugger does not pack orders.",
  },
  {
    id: "delivery",
    label: "Delivery",
    hint: "Carry goods from one point to another",
    catalogClass: "logistics",
    tradeoff:
      "Delivery is point-to-point transport. It is not assembly or floor cleaning.",
  },
  {
    id: "assembly",
    label: "Assembly",
    hint: "Place, fasten, or fit parts at a station",
    catalogClass: "factory",
    tradeoff:
      "Assembly is placement and fastening at a station. A mobile pallet robot does not do that work.",
  },
  {
    id: "amr",
    label: "Mobile (AMR)",
    hint: "A mobile robot drives a load between points",
    catalogClass: "amr",
    tradeoff:
      "Mobile AMR work is driving a payload between points. A fixed arm stays at one station.",
  },
  {
    id: "serving",
    label: "Serving",
    hint: "Food and drinks in a public room",
    catalogClass: "serving",
    tradeoff:
      "Serving is food and drinks in a public room. Warehouse payload is a different job.",
  },
  {
    id: "cleaning",
    label: "Cleaning",
    hint: "Floor scrubbing and coverage",
    catalogClass: "cleaning",
    tradeoff: "Cleaning is floor coverage. It does not move pallets or pack orders.",
  },
  {
    id: "healthcare",
    label: "Healthcare",
    hint: "Supplies, specimens, linen, pharmacy carts",
    catalogClass: "healthcare",
    tradeoff:
      "Healthcare here is supply and specimen movement. It is not warehouse pallet haul.",
  },
  {
    id: "industrial",
    label: "Industrial",
    hint: "Plant-floor cells and machine work",
    catalogClass: "factory",
    tradeoff:
      "Industrial work is a plant cell. Confirm whether the job is an arm, a mobile robot, or both.",
  },
];

const WORKFLOW_BY_ID = Object.fromEntries(
  WORKFLOWS.map(row => [row.id, row])
) as Record<WorkflowId, WorkflowOption>;

export function workflowById(id: string): WorkflowOption | null {
  return WORKFLOW_BY_ID[id as WorkflowId] ?? null;
}

export type WorkSpecInput = {
  workflowId: string;
  jobType: string;
  loadLb: string;
  hoursPerDay: string;
  alongsideHumans: "" | "yes" | "no";
  robotCost: string;
  laborRate: string;
};

export type WorkSpec = {
  workflowId: WorkflowId;
  jobType: string;
  loadLb: number;
  hoursPerDay: number;
  alongsideHumans: boolean;
  robotCostUsd: number | null;
  laborRateUsd: number | null;
};

export type WorkEconomics = {
  robotCostUsd: number;
  laborRateUsd: number;
  hoursPerDay: number;
  dailySavingsUsd: number;
  annualSavingsUsd: number;
  paybackMonths: number;
  annualRoiPercent: number;
  assumptions: string[];
};

export type QualifiedWork = {
  title: string;
  workflowLabel: string;
  catalogClass: string;
  matchDescription: string;
  requirements: { label: string; value: string }[];
  qualification: "Conditional";
  openQuestions: string[];
  evidence: string;
  tradeoff: string;
  economics: WorkEconomics | null;
  summary: string;
};

export const SITE_SURVEY_LIMIT =
  "We cannot guarantee this robot will work in your facility without a site survey. A catalog match and a payback example are not approval to install.";

function parseAmount(raw: string): number | null {
  const cleaned = raw.replace(/[$,\s]/g, "");
  if (!cleaned) return null;
  const value = Number(cleaned);
  if (!Number.isFinite(value) || value <= 0) return null;
  return value;
}

function money(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value % 1 === 0 ? 0 : 2,
  });
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

/** Same labor-payback example as POST /api/v1/gpt-actions/calculate-payback. */
export function laborPayback(input: {
  robotCostUsd: number;
  laborRateUsd: number;
  hoursPerDay: number;
}): WorkEconomics | null {
  const { robotCostUsd, laborRateUsd, hoursPerDay } = input;
  if (robotCostUsd <= 0 || laborRateUsd <= 0 || hoursPerDay <= 0) return null;
  const dailySavingsUsd = laborRateUsd * hoursPerDay;
  const annualSavingsUsd = dailySavingsUsd * 250;
  return {
    robotCostUsd,
    laborRateUsd,
    hoursPerDay,
    dailySavingsUsd: round1(dailySavingsUsd),
    annualSavingsUsd: round1(annualSavingsUsd),
    paybackMonths: round1(robotCostUsd / dailySavingsUsd / 21.67),
    annualRoiPercent: round1((annualSavingsUsd / robotCostUsd) * 100),
    assumptions: [
      "You entered the robot price, the wage, and the hours.",
      "Annual savings use 250 work days. Payback months divide daily savings by 21.67.",
      "Maintenance, downtime, integration, and charging are left out.",
      "This is an example, not a quote.",
    ],
  };
}

export function parseWorkSpec(
  input: WorkSpecInput
): { ok: true; spec: WorkSpec } | { ok: false; error: string } {
  const workflow = workflowById(input.workflowId);
  if (!workflow) return { ok: false, error: "Pick the workflow." };
  const loadLb = parseAmount(input.loadLb);
  if (loadLb == null) return { ok: false, error: "Enter the load in pounds." };
  const hoursPerDay = parseAmount(input.hoursPerDay);
  if (hoursPerDay == null) {
    return { ok: false, error: "Enter how many hours a day." };
  }
  if (input.alongsideHumans !== "yes" && input.alongsideHumans !== "no") {
    return { ok: false, error: "Say whether people work beside the robot." };
  }
  const jobType = input.jobType.trim();
  return {
    ok: true,
    spec: {
      workflowId: workflow.id,
      jobType: jobType || workflow.label,
      loadLb,
      hoursPerDay,
      alongsideHumans: input.alongsideHumans === "yes",
      robotCostUsd: parseAmount(input.robotCost),
      laborRateUsd: parseAmount(input.laborRate),
    },
  };
}

export function qualifyWork(spec: WorkSpec): QualifiedWork {
  const workflow = WORKFLOW_BY_ID[spec.workflowId];
  const people = spec.alongsideHumans
    ? "Yes. The robot has to avoid hitting them."
    : "No. People are not in the robot path.";
  const economics =
    spec.robotCostUsd != null && spec.laborRateUsd != null
      ? laborPayback({
          robotCostUsd: spec.robotCostUsd,
          laborRateUsd: spec.laborRateUsd,
          hoursPerDay: spec.hoursPerDay,
        })
      : null;
  const openQuestions = [
    "What is the part, pallet, or container, and how is it picked up?",
    "What are the aisle, dock, floor, and charge spot?",
  ];
  if (spec.alongsideHumans) {
    openQuestions.push("Where do people stand relative to the robot path?");
  }
  openQuestions.push("Which site was surveyed?");
  const tradeoff = spec.alongsideHumans
    ? `${workflow.tradeoff} People share this workspace, so the robot has to avoid them. This list is not a safety certification.`
    : `${workflow.tradeoff} Catalog rows do not show a verified ${spec.loadLb} lb payload.`;
  const summary = [
    spec.jobType,
    workflow.label,
    `${spec.loadLb} lb`,
    `${spec.hoursPerDay} hours/day`,
    spec.alongsideHumans ? "alongside humans" : "no people beside the robot",
  ].join(" · ");
  return {
    title: spec.jobType,
    workflowLabel: workflow.label,
    catalogClass: workflow.catalogClass,
    matchDescription: summary,
    requirements: [
      { label: "Job type", value: spec.jobType },
      { label: "Workflow", value: workflow.label },
      { label: "Load", value: `${spec.loadLb} lb` },
      { label: "Hours", value: `${spec.hoursPerDay} hours/day` },
      { label: "People beside the robot", value: people },
    ],
    qualification: "Conditional",
    openQuestions,
    evidence: SITE_SURVEY_LIMIT,
    tradeoff,
    economics,
    summary,
  };
}

export function formatUsd(value: number): string {
  return money(value);
}
