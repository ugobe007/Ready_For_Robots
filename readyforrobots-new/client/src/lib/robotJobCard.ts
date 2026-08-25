/**
 * Robot Job Card — employment-model view of a unit of work.
 * Canonical model: docs/robot_employment_model.md
 */
import robcoPack from "./robcoJobCards.json";

export const ROBOT_JOB_CARD_NEXT_STEP =
  "Site assessment — can the robot actually work here?";

/** Job Card inspect step: three model links, three questions. Price later. */
export const JOB_CARD_MODEL_LINK_CAP = 3;
export const JOB_CARD_OPEN_QUESTION_CAP = 3;

const CARD_LINK_SKIP_KINDS = new Set([
  "curated_survey",
  "benchmarks",
  "github",
  "training_data",
  "talent",
  "token_price_index",
  "physical_compute",
  "managed_api",
  "oem_quote",
  "integrator_sow",
]);

const CARD_LINK_PREFER_KINDS = new Set([
  "open_weights",
  "sim_to_real",
  "foundation_robotics",
]);

/** Canonical VLA project pages — these three are the Job Card model links. */
const CARD_LINK_PRIORITY = [
  "openvla.github.io",
  "pi.website/blog/pi05",
  "gr00t-n1_5",
];

const TASK_MODEL_WHY_HOLE =
  /hardware can enter the workplace|task model for this work is still unknown/i;

function shortModelLinkName(dest: TaskModelLookup): string {
  const url = (dest.url || "").toLowerCase();
  if (url.includes("openvla.github.io") || url.includes("openvla")) return "OpenVLA";
  if (url.includes("pi.website") || url.includes("physicalintelligence")) {
    return "π0.5";
  }
  if (url.includes("gr00t")) return "GR00T N1.5";
  if (url.includes("huggingface.co/lerobot")) return "LeRobot";
  if (url.includes("huggingface.co")) return "Hugging Face robotics";
  if (url.includes("nvidia.com/isaac") || url.includes("/isaac")) return "NVIDIA Isaac";
  return dest.name.replace(/\s+[—–-]\s+.*$/, "").trim() || dest.name;
}

function canonicalModelUrl(url: string): string {
  try {
    const parsed = new URL(url);
    parsed.searchParams.delete("utm_source");
    parsed.searchParams.delete("utm_medium");
    parsed.searchParams.delete("utm_campaign");
    parsed.searchParams.delete("curius");
    const query = parsed.searchParams.toString();
    parsed.search = query;
    return parsed.toString();
  } catch {
    return url;
  }
}

function cardLinkRank(url: string): number {
  const u = url.toLowerCase();
  const idx = CARD_LINK_PRIORITY.findIndex(token => u.includes(token));
  return idx === -1 ? CARD_LINK_PRIORITY.length : idx;
}

export type RobotJobQualification =
  | "qualified"
  | "conditional"
  | "not_qualified"
  | "pending_robot";

export type TaskModelPresence = "unknown" | "present" | "absent";

export type TaskModelLookup = {
  kind: string;
  name: string;
  url: string | null;
  note: string;
};

export type TaskModelQualifyFilter = {
  id: string;
  label: string;
  note: string;
};

export type TaskModelPlacementStep = {
  n: number;
  label: string;
  body: string;
};

export type TaskModelCardContract = {
  headline: string;
  layer: string;
  whoTrains: string;
  time: string;
  youProvide: string;
  fieldFeedback: string;
  listLine: string;
  steps: TaskModelPlacementStep[];
};

export type RequiredTaskModel = {
  id: string;
  label: string;
  physicalTask: string;
  vertical: string;
  presence: TaskModelPresence;
  hardwareNotEnough: string;
  candidateFamilies: string[];
  whereToLook: TaskModelLookup[];
  qualifyFilters: TaskModelQualifyFilter[];
  pricingLookups: TaskModelLookup[];
  cardContract: TaskModelCardContract | null;
};

export type RobotJobCardView = {
  employer: string | null;
  workplace: string | null;
  jobTitle: string;
  work: string;
  requirements: string[];
  workVolume: string | null;
  currentLabor: string | null;
  evidence: string | null;
  qualification: RobotJobQualification;
  qualificationLabel: string;
  qualificationHint: string;
  openQuestions: string[];
  nextStep: string;
  taskModels: RequiredTaskModel[];
  modelLinks: TaskModelLookup[];
  modelContract: TaskModelCardContract | null;
};

export const QUALIFICATION_LABEL: Record<RobotJobQualification, string> = {
  qualified: "Qualified",
  conditional: "Conditional",
  not_qualified: "Not qualified",
  pending_robot: "Pending robot résumé",
};

export const QUALIFICATION_HINT: Record<RobotJobQualification, string> = {
  qualified: "Confirmed by you or the employer.",
  conditional: "Pending your review, a site assessment, and a task model for this work.",
  not_qualified: "A required capability or task model is unmet.",
  pending_robot: "Submit this robot’s URL to evaluate it against the job.",
};

export function qualificationFromVerdict(
  verdict?: string | null,
  blockers?: string[] | null,
  taskModels?: { presence?: string | null }[] | null,
): RobotJobQualification {
  if (verdict === "NOT_A_MATCH" || (blockers && blockers.length > 0)) {
    return "not_qualified";
  }
  if (taskModels?.some(m => m.presence === "absent")) {
    return "not_qualified";
  }
  if (verdict === "POSSIBLE_MATCH" || verdict === "INSUFFICIENT") {
    return "conditional";
  }
  return "pending_robot";
}

type MatchLookupIn = {
  kind?: string | null;
  name?: string | null;
  url?: string | null;
  note?: string | null;
};

type MatchTaskModelIn = {
  id?: string | null;
  label?: string | null;
  physical_task?: string | null;
  vertical?: string | null;
  presence?: string | null;
  hardware_not_enough?: string | null;
  candidate_families?: string[] | null;
  where_to_look?: MatchLookupIn[] | null;
  qualify_filters?: {
    id?: string | null;
    label?: string | null;
    name?: string | null;
    note?: string | null;
  }[] | null;
  pricing_lookups?: MatchLookupIn[] | null;
    card_contract?: {
      headline?: string | null;
      layer?: string | null;
      who_trains?: string | null;
      time?: string | null;
      you_provide?: string | null;
      field_feedback?: string | null;
      list_line?: string | null;
      steps?: {
        n?: number | null;
        label?: string | null;
        body?: string | null;
      }[] | null;
    } | null;
};

function mapLookups(raw?: MatchLookupIn[] | null): TaskModelLookup[] {
  return (raw || []).map(d => ({
    kind: (d.kind || "").trim(),
    name: (d.name || "").trim(),
    url: d.url ? d.url.trim() : null,
    note: (d.note || "").trim(),
  }));
}

/** Clickable model destinations for the Job Card — no catalogs, surveys, or price maps. */
export function cardModelLinks(lookups: TaskModelLookup[]): TaskModelLookup[] {
  const withUrl = lookups.filter(d => d.url && d.name);
  const preferred = withUrl
    .filter(
      d => CARD_LINK_PREFER_KINDS.has(d.kind) && !CARD_LINK_SKIP_KINDS.has(d.kind),
    )
    .sort((a, b) => cardLinkRank(a.url || "") - cardLinkRank(b.url || ""));
  const ranked = [
    ...preferred,
    ...withUrl.filter(
      d => !CARD_LINK_PREFER_KINDS.has(d.kind) && !CARD_LINK_SKIP_KINDS.has(d.kind),
    ),
  ];
  const out: TaskModelLookup[] = [];
  const seen = new Set<string>();
  for (const dest of ranked) {
    const key = (dest.url || dest.name).toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      ...dest,
      url: canonicalModelUrl(dest.url || ""),
      name: shortModelLinkName(dest),
      note: "",
    });
    if (out.length >= JOB_CARD_MODEL_LINK_CAP) break;
  }
  return out;
}

function stripPrefix(value: string, prefix: RegExp): string {
  return value.replace(prefix, "").trim();
}

function shortLayer(layer: string): string {
  const t = stripPrefix(layer, /^Layer:\s*/i);
  if (/site-adapted/i.test(t)) return "Site-adapted";
  if (/task library/i.test(t)) return "Task library";
  if (/foundation/i.test(t)) return "Foundation VLA";
  return t.split("/")[0].trim() || t;
}

function shortTime(time: string): string {
  const t = stripPrefix(time, /^Typical time:\s*/i);
  const m = t.match(
    /(\d+\s*[–-]\s*\d+\s*weeks|Days to ~2 weeks|Months to years)/i,
  );
  if (m) return m[1].replace(/-/g, "–");
  return t.split(" after")[0].trim();
}

function shortWho(who: string): string {
  return stripPrefix(who, /^Who trains:\s*/i);
}

function defaultPlacementSteps(opts: {
  slotLabel: string;
  who: string;
  time: string;
  youProvide: string;
  fieldFeedback: string;
}): TaskModelPlacementStep[] {
  const provide = stripPrefix(opts.youProvide, /^You provide:\s*/i);
  const rebate =
    opts.fieldFeedback ||
    "Field traces do not automatically reduce the model price unless the OEM contract says so.";
  return [
    { n: 1, label: "Name the slot", body: opts.slotLabel || "this work" },
    {
      n: 2,
      label: "License a task-library pack",
      body: "Ask the OEM which pack covers this SKU class. Do not train a foundation VLA.",
    },
    {
      n: 3,
      label: "Budget site adapt",
      body: `${opts.who || "OEM / integrator"} · typical ${opts.time || "2–8 weeks"}`,
    },
    {
      n: 4,
      label: "Bring workplace data",
      body: provide || "site map, object geometry, demo traces, SOP",
    },
    {
      n: 5,
      label: "Qualify on this workplace",
      body: "A checkpoint is not qualified until this site says so.",
    },
    { n: 6, label: "Write the field-data clause", body: rebate },
  ];
}

function mapPlacementSteps(
  raw: MatchTaskModelIn["card_contract"],
  fallback: TaskModelPlacementStep[],
): TaskModelPlacementStep[] {
  const steps = (raw?.steps || [])
    .map(row => ({
      n: Number(row.n) || 0,
      label: (row.label || "").trim(),
      body: (row.body || "").trim(),
    }))
    .filter(row => row.label && row.body);
  return steps.length ? steps : fallback;
}

function mapCardContract(
  raw?: MatchTaskModelIn["card_contract"],
  slotLabel = "",
): TaskModelCardContract | null {
  if (!raw) return null;
  const headline = (raw.headline || "").trim();
  const layer = (raw.layer || "").trim();
  if (!headline && !layer) return null;
  const whoTrains = (raw.who_trains || "").trim();
  const time = (raw.time || "").trim();
  const youProvide = (raw.you_provide || "").trim();
  const fieldFeedback = (raw.field_feedback || "").trim();
  const who = shortWho(whoTrains);
  const timeShort = shortTime(time);
  const listLine =
    (raw.list_line || "").trim() ||
    [shortLayer(layer), timeShort, who].filter(Boolean).join(" · ");
  const steps = mapPlacementSteps(
    raw,
    defaultPlacementSteps({
      slotLabel,
      who,
      time: timeShort,
      youProvide,
      fieldFeedback,
    }),
  );
  return {
    headline: headline || "To place this job",
    layer,
    whoTrains,
    time,
    youProvide,
    fieldFeedback,
    listLine,
    steps,
  };
}

function normalizeTaskModels(raw?: MatchTaskModelIn[] | null): RequiredTaskModel[] {
  const out: RequiredTaskModel[] = [];
  for (const row of raw || []) {
    const id = (row.id || "").trim();
    const label = (row.label || "").trim();
    if (!id && !label) continue;
    const presence: TaskModelPresence =
      row.presence === "present" || row.presence === "absent"
        ? row.presence
        : "unknown";
    out.push({
      id: id || label,
      label: label || id,
      physicalTask: (row.physical_task || "").trim(),
      vertical: (row.vertical || "").trim(),
      presence,
      hardwareNotEnough: (row.hardware_not_enough || "").trim(),
      candidateFamilies: [],
      whereToLook: [],
      qualifyFilters: [],
      pricingLookups: [],
      cardContract: mapCardContract(row.card_contract, label || id),
    });
  }
  return out;
}

export function robotJobCardFromMatch(job: {
  title?: string | null;
  company_name?: string | null;
  locality?: string | null;
  why?: string[] | null;
  still_unknown?: string[] | null;
  unknowns?: string[] | null;
  blockers?: string[] | null;
  verdict?: string | null;
  industry?: string | null;
  text?: string | null;
  required_task_models?: MatchTaskModelIn[] | null;
}): RobotJobCardView {
  const taskModels = normalizeTaskModels(job.required_task_models);
  const modelLinks = cardModelLinks(
    (job.required_task_models || []).flatMap(row => mapLookups(row.where_to_look)),
  );
  const open = unique([
    ...(job.still_unknown || []),
    ...(job.unknowns || []),
  ]).slice(0, JOB_CARD_OPEN_QUESTION_CAP);
  const qualification = qualificationFromVerdict(
    job.verdict,
    job.blockers,
    taskModels,
  );
  const title = (job.title || "").trim() || "Untitled job";
  return {
    employer: emptyToNull(job.company_name),
    workplace: emptyToNull(job.locality),
    jobTitle: title,
    work: title,
    requirements: (job.why || []).filter(w => !TASK_MODEL_WHY_HOLE.test(w)),
    workVolume: null,
    currentLabor: null,
    evidence: emptyToNull(job.text) || (job.why?.[0] ?? null),
    qualification,
    qualificationLabel: QUALIFICATION_LABEL[qualification],
    qualificationHint: QUALIFICATION_HINT[qualification],
    openQuestions: open,
    nextStep: ROBOT_JOB_CARD_NEXT_STEP,
    taskModels,
    modelLinks,
    modelContract: taskModels.find(m => m.cardContract)?.cardContract || null,
  };
}

/** Collapsed list / CRM taste — training burden without inventing a price. */
export function jobModelListLine(
  job: Parameters<typeof robotJobCardFromMatch>[0],
): string {
  return robotJobCardFromMatch(job).modelContract?.listLine || "";
}

export type RobcoJobCard = (typeof robcoPack)["jobs"][number];

export function robcoJobCards(): RobcoJobCard[] {
  return robcoPack.jobs;
}

export function robcoPackHonesty(pack = robcoPack): string[] {
  const errors: string[] = [];
  if (pack.invented_economics) errors.push("pack must not invent economics");
  if (pack.jobs.length < 1) errors.push("pack is empty");
  for (const job of pack.jobs) {
    if (!job.employer?.trim()) errors.push(`${job.id} missing employer`);
    if (!job.workplace?.trim()) errors.push(`${job.id} missing workplace`);
    if (!job.job_key?.startsWith("manip_")) {
      errors.push(`${job.id} must point at a corpus/ledger job_key`);
    }
    if (job.workVolume != null) errors.push(`${job.id} invented workVolume`);
    if (job.currentLabor != null) errors.push(`${job.id} invented currentLabor`);
    if (job.qualification !== "pending_robot") {
      errors.push(`${job.id} must stay pending_robot until a RobCo URL exists`);
    }
  }
  return errors;
}

const PLACEHOLDER_JOB_NAMES = new Set([
  "unknown",
  "[unknown]",
  "n/a",
  "na",
  "none",
  "tbd",
  "—",
  "-",
]);

/** A Robot Job is named employer + workplace. Incomplete rows are not jobs. */
export function isNamedRobotJob(job: {
  company_name?: string | null;
  locality?: string | null;
}): boolean {
  const company = (job.company_name || "").trim();
  const place = (job.locality || "").trim();
  if (!company || !place) return false;
  if (PLACEHOLDER_JOB_NAMES.has(company.toLowerCase())) return false;
  if (PLACEHOLDER_JOB_NAMES.has(place.toLowerCase())) return false;
  return true;
}

function emptyToNull(value?: string | null): string | null {
  const t = (value || "").trim();
  return t ? t : null;
}

function unique(rows: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const row of rows) {
    const t = row.trim();
    if (!t || seen.has(t)) continue;
    seen.add(t);
    out.push(t);
  }
  return out;
}
