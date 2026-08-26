/**
 * Jobs submit workflow — FIND on `/`.
 *
 * Step 01 FIND → step 02 JOBS → step 03 CRM.
 * Checking a job dumps it into CRM. Next / 03 opens the CRM desk
 * (quote → Place this job). Process chrome lives on the page. The document
 * scrolls. Do not trap the next step inside a clipped 100vh box.
 *
 * Cap: 5 example jobs on `/`. Activate fills the live list to 15.
 */

export type JobsConfirmLanding = "review" | "jobs" | "portfolio";
export type JobLookupGrain = "robot_type" | "product";

export type LineupProduct = { name: string; displayClass?: string | null };

export type LineupJobLookup = {
  grain: JobLookupGrain;
  robotClass: string | null;
  productNames: string[];
};

/** Frontend aliases — keep in sync with `robot_class_qualify.normalize_class_id`. */
const ROBOT_CLASS_ALIASES: Record<string, string> = {
  humanoid: "humanoid",
  biped: "humanoid",
  bipedal: "humanoid",
  amr: "amr",
  agv: "amr",
  mobile_robot: "amr",
  mobile_manipulator: "mobile_manipulator",
  cobot: "cobot",
  arm: "cobot",
  collaborative: "cobot",
  quadruped: "quadruped",
  spot: "quadruped",
  scrubber: "autonomous_scrubber",
  autonomous_scrubber: "autonomous_scrubber",
  forklift: "amr",
};

const ROBOT_CLASS_JOBS_LABEL: Record<string, string> = {
  humanoid: "humanoids",
  amr: "AMRs",
  mobile_manipulator: "mobile manipulators",
  cobot: "collaborative arms",
  quadruped: "quadrupeds",
  autonomous_scrubber: "floor scrubbers",
};

const ROBOT_CLASS_TITLE: Record<string, string> = {
  humanoid: "Humanoid",
  amr: "AMR",
  mobile_manipulator: "Mobile manipulator",
  cobot: "Collaborative arm",
  quadruped: "Quadruped",
  autonomous_scrubber: "Floor scrubber",
};

export function normalizeRobotClass(raw?: string | null): string | null {
  const want = (raw || "").trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (!want) return null;
  return ROBOT_CLASS_ALIASES[want] || null;
}

export function robotClassTitle(classId?: string | null): string {
  const id = normalizeRobotClass(classId);
  if (!id) return "robot";
  return ROBOT_CLASS_TITLE[id] || id.replace(/_/g, " ");
}

export function robotClassJobsLabel(classId?: string | null): string {
  const id = normalizeRobotClass(classId);
  if (!id) return "this robot type";
  return ROBOT_CLASS_JOBS_LABEL[id] || `${id.replace(/_/g, " ")}s`;
}

/**
 * One lookup per robot type (class), not per SKU.
 * Unknown class falls back to a product-level lookup so we never mix types.
 */
export function lineupJobLookups(products: LineupProduct[]): LineupJobLookup[] {
  const groups = new Map<string, string[]>();
  const unknown: string[] = [];
  for (const row of products) {
    const name = (row.name || "").trim();
    if (!name) continue;
    const cls = normalizeRobotClass(row.displayClass);
    if (!cls) {
      unknown.push(name);
      continue;
    }
    const names = groups.get(cls) || [];
    names.push(name);
    groups.set(cls, names);
  }
  const out: LineupJobLookup[] = [];
  for (const [robotClass, productNames] of groups) {
    out.push({ grain: "robot_type", robotClass, productNames });
  }
  for (const name of unknown) {
    out.push({ grain: "product", robotClass: null, productNames: [name] });
  }
  return out;
}

export function productClassesFromLineup(
  products: LineupProduct[],
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const row of products) {
    const cls = normalizeRobotClass(row.displayClass);
    if (row.name && cls) out[row.name] = cls;
  }
  return out;
}

/**
 * SKU family stem: LD-250 → LD, Fourier GR-1 → GR, N1 → N.
 * Marketing names without a model code return null.
 */
export function skuFamilyStem(name: string): string | null {
  const raw = (name || "").trim();
  if (!raw) return null;
  const tokens = raw.split(/\s+/);
  for (let i = tokens.length - 1; i >= 0; i--) {
    const match = tokens[i].match(/^([A-Za-z]{1,8})[-_]?(\d)/);
    if (match) return match[1].toUpperCase();
  }
  return null;
}

export type LineupSegment = {
  id: string;
  title: string;
  subtitle: string;
  robotClass: string | null;
  family: string | null;
  products: LineupProduct[];
};

function classBucketTitle(cls: string | null): string {
  return cls ? robotClassJobsLabel(cls) : "robots";
}

function classBucketSubtitle(cls: string | null): string {
  return cls ? robotClassTitle(cls) : "One robot";
}

function segmentsForClass(cls: string | null, rows: LineupProduct[]): LineupSegment[] {
  const classKey = cls || "unknown";
  if (rows.length === 1) {
    const row = rows[0];
    return [
      {
        id: `sku:${row.name}`,
        title: row.name,
        subtitle: classBucketSubtitle(cls),
        robotClass: cls,
        family: skuFamilyStem(row.name),
        products: rows,
      },
    ];
  }

  const byStem = new Map<string, LineupProduct[]>();
  const noStem: LineupProduct[] = [];
  for (const row of rows) {
    const stem = skuFamilyStem(row.name);
    if (!stem) {
      noStem.push(row);
      continue;
    }
    const list = byStem.get(stem) || [];
    list.push(row);
    byStem.set(stem, list);
  }

  const families: Array<[string, LineupProduct[]]> = [];
  const leftovers: LineupProduct[] = [...noStem];
  for (const [stem, group] of byStem) {
    if (group.length >= 2) families.push([stem, group]);
    else leftovers.push(...group);
  }

  const splitFamilies = families.length >= 2 || (families.length === 1 && leftovers.length > 0);
  if (!splitFamilies) {
    const family = families.length === 1 ? families[0][0] : null;
    return [
      {
        id: `class:${classKey}`,
        title: cls ? robotClassJobsLabel(cls) : `${rows.length} robots`,
        subtitle: `${rows.length} robots`,
        robotClass: cls,
        family,
        products: rows,
      },
    ];
  }

  const out: LineupSegment[] = [];
  for (const [stem, group] of families) {
    out.push({
      id: `family:${classKey}:${stem}`,
      title: `${stem} ${classBucketTitle(cls)}`,
      subtitle: group.map(p => p.name).join(" · "),
      robotClass: cls,
      family: stem,
      products: group,
    });
  }
  for (const row of leftovers) {
    out.push({
      id: `sku:${row.name}`,
      title: row.name,
      subtitle: classBucketSubtitle(cls),
      robotClass: cls,
      family: skuFamilyStem(row.name),
      products: [row],
    });
  }
  return out;
}

/** Class buckets, then SKU families inside a class (LD vs HD AMRs). */
export function lineupSegments(products: LineupProduct[]): LineupSegment[] {
  const byClass = new Map<string, LineupProduct[]>();
  const unknown: LineupProduct[] = [];
  for (const row of products) {
    const name = (row.name || "").trim();
    if (!name) continue;
    const cls = normalizeRobotClass(row.displayClass);
    if (!cls) {
      unknown.push({ ...row, name });
      continue;
    }
    const list = byClass.get(cls) || [];
    list.push({ ...row, name });
    byClass.set(cls, list);
  }
  const out: LineupSegment[] = [];
  for (const [cls, rows] of byClass) {
    out.push(...segmentsForClass(cls, rows));
  }
  if (unknown.length) {
    out.push(...segmentsForClass(null, unknown));
  }
  return out;
}

/** Segmented picker when the lineup is bigger than one search, or spans types. */
export function usesLineupSegments(
  products: LineupProduct[],
  cap = JOBS_PRODUCT_CAP_FREE,
): boolean {
  const named = products.filter(p => (p.name || "").trim());
  if (named.length <= 1) return false;
  const classes = new Set(
    named.map(p => normalizeRobotClass(p.displayClass)).filter(Boolean),
  );
  if (classes.size >= 2) return true;
  if (named.length > cap) return true;
  const segs = lineupSegments(named);
  return segs.length >= 2 && segs.some(s => (s.products || []).length >= 2);
}

export function searchNamesForSegment(
  segment: LineupSegment | undefined,
  cap = JOBS_PRODUCT_CAP_FREE,
): string[] {
  if (!segment) return [];
  return segment.products.map(p => p.name).filter(Boolean).slice(0, cap);
}

export const JOBS_EXAMPLE_CAP = 5;
/** Lineup preview: one sample job per robot. Run each SKU for five jobs. */
export const JOBS_LINEUP_JOBS_PER_ROBOT = 1;
export const BUYER_LEADS_ANON_CAP = 5;
/** See All on `/` — more than the 5-example cap, still the same page. */
export const JOBS_PIPELINE_CAP = 15;
/** Live list after Activate: checked jobs first, then fill to this cap. */
export const JOBS_ACTIVATE_CAP = 15;
/** Free CRM taste — keep in sync with `JOBS_CRM_FREE_BATCH` in plan_entitlements. */
export const CRM_UNLOCKED_JOBS = 5;
/** Free FIND dump size. Paid skips the cap. Spec: docs/jobs_crm.md */
export const CRM_FREE_BATCH = CRM_UNLOCKED_JOBS;
export const CRM_FREE_BATCHES_PER_MONTH = 3;
export const CRM_FREE_MONTHLY_CAP = CRM_FREE_BATCH * CRM_FREE_BATCHES_PER_MONTH;
export const CRM_FREE_TTL_DAYS = 7;
/** Free / anonymous: search this many SKUs per FIND. Paid unlocks five. */
export const JOBS_PRODUCT_CAP_FREE = 3;
export const JOBS_PRODUCT_CAP_PAID = 5;
/** FIND shows this many robots per picker page. Not a company roster cap. */
export const JOBS_LINEUP_DISPLAY_CAP = 3;
export const OEM_LISTING_TIMEOUT_MS = 5_000;
export const ROBOT_PROFILE_TIMEOUT_MS = 22_000;
export const ROBOT_JOB_SEARCH_TIMEOUT_MS = 30_000;

const JOBS_LINEUP_NOISE_NAMES = new Set([
  "about",
  "about us",
  "industries",
  "industry",
  "products overview",
  "product overview",
  "overview",
  "discontinued",
  "discontinued products",
  "deutsch",
  "español",
  "espanol",
  "français",
  "francais",
  "english",
  "italiano",
  "nederlands",
  "activate your amr license",
  "collaborative",
  "collaborative robots",
  "amr",
  "amrs",
  "agv",
  "agvs",
  "mobile robots",
  "mobile robot",
  "contact",
  "contact us",
  "news",
  "company",
  "solutions",
]);

const JOBS_LINEUP_NOISE_RE =
  /\b(discontinued|activate your|amr license|products?\s+overview)\b/i;
const JOBS_LINEUP_LOCALE_RE =
  /^(deutsch|espa[nñ]ol|fran[cç]ais|english|italiano|nederlands|portugu[eê]s|日本語|中文|한국어|de|fr|es|en|zh|ja)$/i;

export function jobsProductLimitForPlan(plan?: string | null): number {
  return plan === "paid" ? JOBS_PRODUCT_CAP_PAID : JOBS_PRODUCT_CAP_FREE;
}

export function isJobsLineupNoiseName(name: string): boolean {
  const raw = (name || "").replace(/\s+/g, " ").trim();
  if (!raw) return true;
  const low = raw.toLowerCase();
  if (JOBS_LINEUP_NOISE_NAMES.has(low)) return true;
  if (JOBS_LINEUP_LOCALE_RE.test(low)) return true;
  if (JOBS_LINEUP_NOISE_RE.test(low)) return true;
  if (low.startsWith("about ")) return true;
  return false;
}

export function filterJobsLineupProducts<T extends { name: string }>(
  products: T[],
  limit?: number,
): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const row of products) {
    const name = (row.name || "").trim();
    if (!name || isJobsLineupNoiseName(name)) continue;
    const key = name.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(row);
    if (limit != null && out.length >= limit) break;
  }
  return out;
}

/** One picker page. Search still uses JOBS_PRODUCT_CAP_FREE / PAID. */
export function pageJobsLineup<T>(
  products: T[],
  page = 0,
  pageSize = JOBS_LINEUP_DISPLAY_CAP,
): T[] {
  const size = Math.max(1, pageSize);
  const start = Math.max(0, page) * size;
  return products.slice(start, start + size);
}

export function landingStageAfterConfirm(robotCount: number): JobsConfirmLanding {
  // Picker already chose the robot(s). Land on jobs — do not ask Find jobs again.
  return robotCount >= 1 ? "jobs" : "review";
}

/** Hide "0 matching jobs" on unresearched shells; hide identical counts across a lineup. */
export function portfolioShowsJobCounts(
  robots: Array<{ matched?: boolean; jobCount?: number }>,
): boolean {
  const matched = robots.filter(a => a.matched);
  if (matched.length === 0) return false;
  if (matched.length === 1) return true;
  return new Set(matched.map(a => a.jobCount ?? 0)).size > 1;
}

export function jobsHeading(opts: {
  productName: string;
  companyName: string;
  robotCount: number;
  lookupGrain?: JobLookupGrain | null;
  robotClass?: string | null;
}): string {
  if (opts.robotCount > 1 && opts.companyName) {
    return `Jobs for ${opts.companyName}`;
  }
  // One selected SKU keeps the product name even when the match was type-first.
  // "Jobs for humanoids" is a lineup heading, not a single-robot heading.
  return `Jobs for ${opts.productName}`;
}

export function jobsCountEyebrow(opts: {
  visibleCount: number;
  productName: string;
  companyName?: string;
  robotCount?: number;
  lookupGrain?: JobLookupGrain | null;
  robotClass?: string | null;
}): string {
  if (opts.visibleCount === 0) return "";
  if ((opts.robotCount || 1) > 1) {
    return `${opts.visibleCount} ROBOTS · 1 JOB EACH`;
  }
  return `${opts.visibleCount} JOBS FOR ${opts.productName.toUpperCase()}`;
}

export function capExampleJobs<T>(jobs: T[], cap = JOBS_EXAMPLE_CAP): T[] {
  return jobs.slice(0, cap);
}

export function exampleJobCap(robotCount: number): number {
  return robotCount > 1 ? JOBS_LINEUP_JOBS_PER_ROBOT : JOBS_EXAMPLE_CAP;
}

export type TaggedExampleJob<T extends { job_key: string }> = T & {
  forRobot: string;
};

/**
 * One robot → five tagged jobs. Several robots → one distinct sample each,
 * tagged with that SKU. Shared type-level matches still get different jobs
 * when the pool allows it so the lineup is not five copies of the same card.
 */
export function exampleJobsForLineup<T extends { job_key: string }>(
  robots: Array<{ productName: string; jobs: T[] }>,
): TaggedExampleJob<T>[] {
  const list = robots.filter(row => (row.productName || "").trim());
  if (list.length <= 1) {
    const row = list[0];
    if (!row) return [];
    return capExampleJobs(row.jobs).map(job => ({
      ...job,
      forRobot: row.productName,
    }));
  }
  const used = new Set<string>();
  const out: TaggedExampleJob<T>[] = [];
  for (const row of list) {
    const pool = row.jobs || [];
    const job =
      pool.find(j => j?.job_key && !used.has(j.job_key)) ||
      pool.find(j => j?.job_key);
    if (!job) continue;
    used.add(job.job_key);
    out.push({ ...job, forRobot: row.productName });
  }
  return out;
}

export function jobIndexLabel(index: number): string {
  return `Job ${String(Math.max(1, index)).padStart(5, "0")}`;
}

export function jobIsForLabel(index: number, robotName: string): string {
  const id = String(Math.max(1, index)).padStart(5, "0");
  const who = (robotName || "this robot").trim() || "this robot";
  return `Job ${id} is for ${who}`;
}

/** Readable 1970s terminal type — identity is never 10px. */
export const JOBS_EYEBROW_CLASS =
  "font-mono text-sm font-semibold uppercase tracking-[0.12em] text-slate-400";
export const JOBS_ROBOT_NAME_CLASS =
  "block font-display text-xl font-bold leading-tight tracking-tight text-white sm:text-2xl";
export const JOBS_JOB_TITLE_CLASS =
  "mt-1 block font-display text-lg font-bold leading-snug text-slate-100 sm:text-xl";
export const JOBS_META_CLASS =
  "mt-1.5 block font-mono text-sm text-emerald-400/90";
export const JOBS_PLACE_CLASS = "mt-1 block text-sm leading-snug text-slate-400";
export const JOBS_PROCESS_NAV_CLASS =
  "font-mono text-sm font-bold uppercase tracking-[0.08em]";
export const JOBS_RAIL_LINK_CLASS =
  "block text-left font-mono text-sm font-semibold uppercase tracking-[0.08em] text-slate-400 transition hover:text-slate-200";

/** Employer names on the CRM desk. Emerald, display font, not body copy. */
export const CRM_EMPLOYER_NAME_CLASS =
  "font-display text-lg font-bold leading-snug tracking-tight text-emerald-400 sm:text-xl";
export const CRM_SELECT_ALL_LABEL = "Keep all 5";
export const CRM_LISTING_EYEBROW = "Collected jobs";
export const CRM_INSPECT_HINT =
  "Inspect a collected egg for the Job Card. Place this job when you are ready. The others stay in the basket.";
export const CRM_PLACE_EGG_HINT =
  "Place this job hatches a collected egg. The rest stay in the basket.";
export const CRM_PAGE_HEADLINE = "CRM";
export const CRM_PAGE_NEXT =
  "Jobs you keep stay jobs. Collect several, inspect one, then quote the monthly rental you will charge and Place this job. We do not invent a number.";
export const CRM_HOW_TO_STEPS = [
  "Sign in to save the jobs you checked. The desk is those jobs — not a SIGNAL buyer list.",
  "Collect several jobs (up to 5). Inspect an egg, then Place this job when you are ready.",
  "Follow up after apply. Export if you must; native CRM is the default.",
] as const;
export const CRM_SUBHEAD_CLASS =
  "mt-2 max-w-2xl text-lg leading-relaxed text-slate-200 sm:text-xl";
export const JOBS_ACTIVATE_JOBS_CTA = "Activate jobs";
export const JOBS_AUTOMATE_JOBS_CTA = "Automate jobs";
export const JOBS_AUTOMATE_SRC = "jobs_automate";
export const PIPELINE_JOBS_AUTOMATE_NEXT =
  "CRM automation applies to the jobs you unlocked and helps land them. Open a row, then Automate jobs — we help you apply and get the robot hired.";
export const PIPELINE_JOBS_AUTOMATE_STEPS = [
  "These rows are the employers for the jobs in your CRM.",
  "Open a job. Automate jobs starts CRM automation for that employer.",
  "We help you apply to the job and land the robot at that workplace.",
] as const;
export const CRM_WATCH_OPT_IN_LABEL =
  "Email me when these jobs change or we find new work for my robot.";
export const CRM_WATCH_FREE_HINT =
  "Free watches 1 robot and sends 2 alerts so you feel the loop. Pro keeps every SKU on the cron.";
export const CRM_WATCH_SIGNED_OUT =
  "Sign in to opt in. We will watch the robot URL you ran on Jobs.";
export const CRM_HEADLINE_CLASS =
  "font-display text-3xl font-bold tracking-tight text-emerald-400 sm:text-4xl";
export const PIPELINE_PAGE_HEADLINE = "Pipeline";
export const PIPELINE_PAGE_NEXT =
  "This is your live list. Open a row, then save it to CRM so we can watch the job and tell you what to do next.";
export const JOBS_OPEN_CRM_CTA = "Open CRM →";
export const JOBS_HEADER_OFFSET_CLASS = "pt-14";

const SALES_PITCH_RE =
  /\b(pitch|lead with|ask who owns|ask about|open with|sequence the|upgrade to|buyer intent|sales motion|outreach draft|hard sell|owns the budget|easy wedge|capex this quarter|focus on|qualify (manufacturing|lab)|avoid front-of-house|discovery call|automation opportunity|confirm specific pain|why now signal not yet)\b/i;

export type JobExplanationInput = {
  title?: string | null;
  why?: string[] | null;
  company?: string | null;
  industry?: string | null;
  friction?: string | null;
  workflow?: string | null;
  summary?: string | null;
  action?: string | null;
};

/** One sentence of work — not a sales pitch. */
export function isSalesPlaceholder(text?: string | null): boolean {
  const value = String(text || "").replace(/\s+/g, " ").trim();
  if (value.length < 8) return true;
  return SALES_PITCH_RE.test(value);
}

export function jobExplanation(input: JobExplanationInput): string {
  const strippedAction = (input.action || "")
    .replace(/^(priority|next)\s*:\s*/i, "")
    .replace(/^pitch\s+/i, "")
    .trim();
  const candidates = [
    ...(input.why || []),
    input.friction,
    input.workflow,
    input.summary,
    input.title,
    strippedAction,
  ];
  for (const raw of candidates) {
    const text = String(raw || "").replace(/\s+/g, " ").trim();
    if (text.length < 8) continue;
    if (SALES_PITCH_RE.test(text)) continue;
    const place = [input.company, input.industry].filter(Boolean).join(" · ");
    if (input.title && text === input.title.trim() && place) {
      return `${text} — ${place}`;
    }
    return text;
  }
  const title = (input.title || "This job").trim();
  const place = [input.company, input.industry].filter(Boolean).join(" · ");
  return place ? `${title} at ${place}` : title;
}

export function jobsListHint(opts: {
  robotCount: number;
  productName: string;
}): string {
  if (opts.robotCount > 1) {
    return "One sample job per robot. Sample rows start checked — checking dumps the row into CRM. Run each robot by itself for five jobs, then Open CRM.";
  }
  return `Five example jobs ${opts.productName} can do. Each row names the policy layer and typical training time — expand for the placement steps. All five start checked (Keep) and land in CRM. Uncheck any you do not want. Open CRM to quote the rental, then Place this job.`;
}

export const JOBS_RUN_ONE_ROBOT_CTA = "Run one robot for 5 jobs →";
export const JOBS_SAVE_TO_CRM_CTA = "Open CRM →";
export const JOBS_SAVE_TO_CRM_HINT =
  "Checking a job dumps it into CRM. Open CRM is step 03 — sign in to save the desk, then quote, Place this job, follow-up. Not a SIGNAL buyer list.";
export const JOBS_KEEP_LABEL = "Keep";
export const JOBS_SKIP_LABEL = "Skip";

/** Jobs / results `src` values that continue the Jobs terminal. */
export function isJobsHandoffSrc(src: string | null | undefined): boolean {
  const value = (src || "").trim();
  return (
    value.startsWith("jobs_") ||
    value.startsWith("robot_jobs") ||
    value === "jobs_all_robots" ||
    value === "robot_jobs_qualify"
  );
}

/** Path without query — `/` and `/jobs…` are the Jobs terminal. */
export function isJobsChromePath(pathname: string | null | undefined): boolean {
  const path = (pathname || "").trim().split("?")[0] || "";
  return path === "/" || path === "/jobs" || path.startsWith("/jobs/");
}

/**
 * SIGNAL Pipeline in the header. Hidden on Jobs chrome and Jobs CRM so
 * FIND → cards → CRM does not hop onto buyer pipeline.
 */
export function showSignalPipelineNav(opts: {
  pathname: string;
  src?: string | null;
}): boolean {
  const path = (opts.pathname || "").trim().split("?")[0] || "";
  if (isJobsChromePath(path) || isJobsHandoffSrc(opts.src)) return false;
  return path.startsWith("/pipeline") || path.startsWith("/crm");
}

/** Jobs chrome CRM is step 3 (`src=jobs_activate`). SIGNAL `/crm` stays `/crm`. */
export function jobsHeaderCrmHref(
  pathname: string,
  src?: string | null,
  signedIn = true,
): string {
  if (showSignalPipelineNav({ pathname, src })) return "/crm";
  return jobsCrmOpenHref(signedIn);
}

function queryParams(search?: string | null): URLSearchParams {
  const raw = (search || "").trim();
  if (!raw) return new URLSearchParams();
  return new URLSearchParams(raw.startsWith("?") ? raw.slice(1) : raw);
}

function srcFromDest(dest: string): string {
  const raw = (dest || "").trim();
  const q = raw.includes("?") ? raw.slice(raw.indexOf("?") + 1) : "";
  if (!q) return "";
  try {
    return new URLSearchParams(q).get("src") || "";
  } catch {
    return "";
  }
}

/**
 * Footer + Signal FAB follow the header: Jobs chrome has no Pipeline / SIGNAL.
 * True on `/` `/jobs…`, About, Jobs CRM, and auth pages that continue Jobs.
 * False on SIGNAL `/pipeline`, `/signals`, bare `/crm`, and `/signup?next=/pipeline`.
 */
export function showJobsSiteChrome(opts: {
  pathname: string;
  search?: string | null;
}): boolean {
  const path = (opts.pathname || "").trim().split("?")[0] || "";
  const params = queryParams(opts.search);
  const src = params.get("src") || "";
  if (isJobsChromePath(path)) return true;
  if (path === "/intelligence" || path === "/compare" || path === "/vendor/design") return true;
  if (path.startsWith("/design/")) return true;
  if (isJobsHandoffSrc(src)) return true;
  if (path === "/signup" || path === "/login") {
    const next = params.get("next") || "";
    if (isJobsHomeDest(next)) return true;
    if (isJobsHandoffSrc(srcFromDest(next))) return true;
  }
  return false;
}

export const FIND_JOBS_CTA = "Start jobs →";
export const FIND_JOBS_HOME_HEADLINE = "Find jobs for your robot.";
export const FIND_JOBS_HOME_SUBHEAD =
  "We match your robots to specific jobs and models using your URL";
export const FIND_JOBS_HEADLINE_CLASS =
  "mt-1 font-display text-5xl font-bold leading-[1.05] tracking-tight text-slate-100 sm:text-6xl lg:text-7xl";
export const FIND_JOBS_SUBHEAD_CLASS =
  "mt-4 max-w-3xl text-lg leading-snug text-slate-300 sm:text-xl";
export const JOBS_FOR_YOUR_ROBOT_HEADING = "Jobs for your robot";
/** Page-level advance on the jobs list. Not on the card. */
export const JOBS_NEXT_CTA = JOBS_SAVE_TO_CRM_CTA;
export const JOBS_NEXT_HINT =
  "All five start checked and dump into CRM. Uncheck any you do not want. Open CRM is step 03 — sign in to keep the desk, collect jobs, then Place this job.";
export const JOBS_SEE_JOBS_CTA = "See jobs →";

export type JobsProcessStepId = "find" | "jobs" | "activate";

/** FIND → jobs → activate. Always shown as navigational links. */
export const JOBS_PROCESS_STEPS = [
  {
    id: "find" as const,
    n: "01",
    label: "Show us your robot",
    linkLabel: FIND_JOBS_CTA,
  },
  {
    id: "jobs" as const,
    n: "02",
    label: "Here are its jobs",
    linkLabel: JOBS_SEE_JOBS_CTA,
  },
  {
    id: "activate" as const,
    n: "03",
    label: "CRM",
    linkLabel: JOBS_NEXT_CTA,
  },
];

export function jobsProcessStepFromStage(stage: string): JobsProcessStepId {
  if (stage === "jobs" || stage === "portfolio") return "jobs";
  return "find";
}

/** Page-chrome wizard button: Start jobs on FIND, Next on the job list. */
export function jobsProcessActionLabel(step: JobsProcessStepId): string {
  return step === "find" ? FIND_JOBS_CTA : JOBS_NEXT_CTA;
}

export const JOBS_ACTIVATE_SRC = "jobs_activate";
export const JOBS_PLACE_SRC = "place";
export const JOBS_PLACE_CTA = "Activate job list →";

export const JOBS_FRESH_QUERY = "new";
export const JOBS_WORKSPACE_SESSION_KEY = "rfr_jobs_workspace";
export const JOBS_RESTORE_ONCE_KEY = "rfr_jobs_restore_once";

export function jobsFreshHomeHref(): string {
  return `/?${JOBS_FRESH_QUERY}=1`;
}

export function isJobsFreshQuery(search: string | null | undefined): boolean {
  return new URLSearchParams(search || "").get(JOBS_FRESH_QUERY) === "1";
}

/** In-page reset on Jobs home. Wordmark must not `location.assign("/")` while already on `/`. */
export const JOBS_FRESH_HOME_EVENT = "rfr:jobs-fresh";

export function isJobsHomePath(pathname: string | null | undefined): boolean {
  const path = (pathname || "").trim().split("?")[0] || "";
  return path === "/" || path === "" || path === "/jobs" || path.startsWith("/jobs/");
}

/**
 * Drop `new=1` from the current URL without a document reload or wouter
 * `setLocation`. Wouter patches `history.replaceState`, so callers must not
 * run this during render (useState initializer) — only in an effect.
 * Returns true when the URL actually changed.
 */
export function stripJobsFreshQuery(): boolean {
  if (typeof window === "undefined") return false;
  if (!isJobsFreshQuery(window.location.search)) return false;
  const params = new URLSearchParams(window.location.search);
  params.delete(JOBS_FRESH_QUERY);
  const next = params.toString();
  const path = window.location.pathname || "/";
  const hash = window.location.hash || "";
  const url = `${path}${next ? `?${next}` : ""}${hash}`;
  window.history.replaceState(window.history.state, "", url);
  return true;
}

/**
 * FIND submit never navigates. One Start jobs click stays on this document:
 * research → Job Cards. No `location.assign`, no reload, no `/?new=1` bounce.
 */
export function findSubmitNavigationTarget(_url?: string | null): null {
  return null;
}

export function canStartFindSubmit(opts: {
  url?: string | null;
  inFlight?: boolean;
  stage?: string | null;
}): boolean {
  if (opts.inFlight) return false;
  if (opts.stage === "research") return false;
  return (opts.url || "").trim().length > 0;
}

/** Drop in-progress FIND state. Used by the wordmark before leaving the page. */
export function clearJobsWorkspaceSession(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(JOBS_WORKSPACE_SESSION_KEY);
    window.sessionStorage.removeItem(JOBS_RESTORE_ONCE_KEY);
  } catch {
    /* ignore */
  }
}

/**
 * Wordmark / Jobs home. Wouter Link to `/` is a no-op while already on `/`
 * (jobs, picker) — same pathname — so the chrome looks dead. Reset in place
 * on Jobs home. Hard-load `/` only when leaving another route. Do not bounce
 * through `/?new=1` (that paints FIND, then strips the query and paints again).
 */
export function goJobsFreshHome(): void {
  clearJobsWorkspaceSession();
  if (typeof window === "undefined") return;
  const path = window.location.pathname || "/";
  if (isJobsHomePath(path)) {
    stripJobsFreshQuery();
    window.dispatchEvent(new Event(JOBS_FRESH_HOME_EVENT));
    return;
  }
  window.location.assign("/");
}

export function onJobsFreshHomeClick(event: {
  preventDefault: () => void;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  button?: number;
}): void {
  const newTab = Boolean(
    event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      (event.button != null && event.button !== 0),
  );
  clearJobsWorkspaceSession();
  if (newTab) return;
  event.preventDefault();
  goJobsFreshHome();
}

/** Place leftovers still must not bounce as a Jobs handoff. */
export function isPlaceSrc(src: string | null | undefined): boolean {
  return (src || "").trim() === JOBS_PLACE_SRC;
}

export function isJobsActivateSrc(src: string | null | undefined): boolean {
  return (src || "").trim() === JOBS_ACTIVATE_SRC;
}

export function isJobsAutomateSrc(src: string | null | undefined): boolean {
  return (src || "").trim() === JOBS_AUTOMATE_SRC;
}

/** CRM desk lives on Pipeline with Jobs src — never SIGNAL buyers, never the OEM as `url=`. */
export function jobsActivateHref(submissionId?: number | null): string {
  const params = new URLSearchParams();
  params.set("src", JOBS_ACTIVATE_SRC);
  if (submissionId && submissionId > 0) params.set("submission", String(submissionId));
  return `/pipeline?${params.toString()}`;
}

/** CRM → Pipeline: apply and land the unlocked jobs with CRM automation. */
export function jobsAutomateHref(submissionId?: number | null): string {
  const params = new URLSearchParams();
  params.set("src", JOBS_AUTOMATE_SRC);
  if (submissionId && submissionId > 0) params.set("submission", String(submissionId));
  return `/pipeline?${params.toString()}`;
}

/** @deprecated Use jobsActivateHref. Kept so leftover Place links compile. */
export function jobsPlaceHref(opts?: {
  leadId?: number | null;
  submissionId?: number | null;
}): string {
  return jobsActivateHref(opts?.submissionId);
}

export function jobsForActivatedPipeline<T extends { job_key: string }>(
  selected: T[],
  pool: T[],
  cap = JOBS_ACTIVATE_CAP,
): T[] {
  const picked = selected.filter(job => job?.job_key);
  const seen = new Set(picked.map(job => job.job_key));
  const extra = pool.filter(job => job?.job_key && !seen.has(job.job_key));
  return [...picked, ...extra].slice(0, cap);
}

/** Activate never no-ops: checked jobs first, else the example cap, else the pool. */
export function jobsToActivate<T extends { job_key: string }>(
  selected: T[],
  pool: T[],
  cap = JOBS_ACTIVATE_CAP,
): T[] {
  const picked = selected.filter(job => job?.job_key);
  const seed = picked.length > 0 ? picked : capExampleJobs(pool);
  return jobsForActivatedPipeline(seed, pool, cap);
}

/** Checked rows only — this is what the CRM desk shows as the user checks. */
export function jobsDumpedToCrm<T extends { job_key: string }>(
  pool: T[],
  checkedKeys: string[],
  cap = CRM_UNLOCKED_JOBS,
): T[] {
  const keys = new Set((checkedKeys || []).filter(Boolean));
  return pool.filter(job => job?.job_key && keys.has(job.job_key)).slice(0, cap);
}

/** Open CRM: checked jobs, or the example cap so step 03 is never empty. */
export function jobsForCrmDesk<T extends { job_key: string }>(
  pool: T[],
  checkedKeys: string[],
  cap = CRM_UNLOCKED_JOBS,
): T[] {
  const dumped = jobsDumpedToCrm(pool, checkedKeys, cap);
  return dumped.length > 0 ? dumped : jobsToActivate([], pool, cap);
}

export function crmDeskJobKeys<T extends { job_key: string }>(jobs: T[]): string[] {
  return jobs.map(job => job.job_key).filter(Boolean);
}

/** Keep every collected job. Acting on one job must not clear the rest. */
export function crmSelectAllKeys(poolKeys: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const key of poolKeys) {
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(key);
  }
  return out;
}

export function crmToggleSelectedKey(
  selected: string[],
  jobKey: string,
  on: boolean,
): string[] {
  if (!jobKey) return crmSelectAllKeys(selected);
  const set = new Set(selected.filter(Boolean));
  if (on) set.add(jobKey);
  else set.delete(jobKey);
  return [...set];
}

/**
 * Default: every dumped job is kept. If the pool is new (no overlap), keep all.
 * Unchecking one job leaves the rest. Does not touch which row is expanded.
 */
export function crmSyncSelectedKeys(
  prev: string[],
  poolKeys: string[],
): string[] {
  const pool = crmSelectAllKeys(poolKeys);
  if (pool.length === 0) return [];
  const kept = prev.filter(key => pool.includes(key));
  if (kept.length === 0) return pool;
  return pool.filter(key => kept.includes(key));
}

export function crmActingKeepsSelection(
  selected: string[],
  actedJobKey: string,
): string[] {
  return crmToggleSelectedKey(selected, actedJobKey, true);
}

export function crmSelectAllLabel(
  count: number,
  cap = CRM_UNLOCKED_JOBS,
): string {
  const n = Math.max(0, count);
  return n >= cap ? CRM_SELECT_ALL_LABEL : `Keep all ${n || cap}`;
}

export function crmCollectedCountLabel(
  collected: number,
  cap = CRM_UNLOCKED_JOBS,
): string {
  const n = Math.min(Math.max(0, collected), cap);
  return `${n} of ${cap} eggs in the basket`;
}

export function defaultCheckedJobKeys<T extends { job_key: string }>(
  jobs: T[],
  cap = JOBS_EXAMPLE_CAP,
): string[] {
  return capExampleJobs(jobs, cap).map(job => job.job_key);
}

export function defaultCheckedKeysForLineup<T extends { job_key: string }>(
  robots: Array<{ productName: string; jobs: T[] }>,
): string[] {
  return exampleJobsForLineup(robots).map(job => job.job_key);
}

export const RAIL_STEP_HINT = {
  find: FIND_JOBS_HOME_SUBHEAD,
  profile: "Confirm we understood this robot. Then find jobs against these capabilities.",
  jobs: "Each job is tagged with its robot. One SKU shows five jobs, all starting checked into CRM. Several robots show one each — run each SKU by itself, then Open CRM.",
  pipeline: "CRM is step 03: collect jobs, inspect an egg, quote the rental you will charge, Place this job.",
} as const;

/** The job Next will place: expanded card, else the first visible job. */
export function jobForNextStep<T extends { job_key: string }>(
  jobs: T[],
  expandedKey: string | null | undefined,
): T | null {
  if (expandedKey) {
    const hit = jobs.find(j => j.job_key === expandedKey);
    if (hit) return hit;
  }
  return jobs[0] ?? null;
}

/** Scan status on /results when arriving from Jobs — unused; Jobs stays on `/`. */
export const JOBS_SCAN_STEPS = [
  "Waiting for your robot URL…",
  "Reading what this robot can do…",
  "Finding jobs for your robot…",
  "Matching work to confirmed capabilities…",
  "Preparing five jobs to review…",
] as const;

/**
 * After a robot-URL lookup, never leave the jobs list empty when a live
 * feed exists. Scoped matches win; otherwise show the live pipeline.
 */
export function buyerLeadsToShow<T>(opts: {
  scopedRows: T[];
  liveRows: T[];
  lookupPending: boolean;
  scopeToUrl: boolean;
}): T[] {
  if (!opts.scopeToUrl) return opts.liveRows;
  if (opts.lookupPending) return opts.scopedRows;
  return opts.scopedRows.length > 0 ? opts.scopedRows : opts.liveRows;
}

/**
 * Place prefers buyers in the job's industry. If the filter is too thin,
 * keep the live feed so step 3 is never empty.
 */
export function placeBuyersToShow<T extends { industry?: string | null }>(
  rows: T[],
  industry?: string | null,
  cap = BUYER_LEADS_ANON_CAP,
): T[] {
  const needle = (industry || "").trim().toLowerCase();
  const scoped = needle
    ? rows.filter(row => {
        const ind = (row.industry || "").trim().toLowerCase();
        if (!ind) return false;
        return ind.includes(needle) || needle.includes(ind);
      })
    : [];
  const pool = scoped.length >= 2 ? scoped : rows;
  return pool.slice(0, cap);
}

/** Keep a Jobs src on later hops. Never rewrite Jobs → results_scan. */
export function persistJobsHandoffSrc(src: string | null | undefined): string {
  const value = (src || "").trim();
  return isJobsHandoffSrc(value) ? value : "jobs_all_robots";
}

export function jobsSignupHref(nextHref: string, src: string): string {
  return `/signup?next=${encodeURIComponent(nextHref)}&src=${encodeURIComponent(src)}`;
}

/**
 * Only entry to the CRM desk. Signed-out users hit the signup wall
 * (`next` = desk). Job Cards on step 02 stay anonymous. Spec: docs/jobs_crm.md.
 */
export function jobsCrmOpenHref(
  signedIn: boolean,
  submissionId?: number | null,
): string {
  const dest = jobsActivateHref(submissionId);
  return signedIn ? dest : jobsSignupHref(dest, JOBS_ACTIVATE_SRC);
}

export type PipelineActivityKind =
  | "dump"
  | "open_crm"
  | "place"
  | "apply"
  | "follow_up";

export type PipelineActivityEvent = {
  at: string;
  kind: PipelineActivityKind;
  label: string;
  jobKey?: string;
  company?: string;
};

export const PIPELINE_ACTIVITY_KEY = "rfr_pipeline_activity_v1";
const PIPELINE_ACTIVITY_CAP = 40;

/** Pipeline / FIND actions land on the CRM job record for later review. */
export function recordPipelineActivity(
  event: Omit<PipelineActivityEvent, "at">,
): void {
  if (typeof window === "undefined") return;
  try {
    const next: PipelineActivityEvent = {
      ...event,
      at: new Date().toISOString(),
    };
    const list = [next, ...readPipelineActivity()].slice(0, PIPELINE_ACTIVITY_CAP);
    window.localStorage.setItem(PIPELINE_ACTIVITY_KEY, JSON.stringify(list));
  } catch {
    /* ignore */
  }
}

export function readPipelineActivity(): PipelineActivityEvent[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(PIPELINE_ACTIVITY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? (parsed as PipelineActivityEvent[]) : [];
  } catch {
    return [];
  }
}

/** Desk-level events (no jobKey) plus events for this job. */
export function pipelineActivityForJob(
  jobKey?: string | null,
): PipelineActivityEvent[] {
  const all = readPipelineActivity();
  if (!jobKey) return all;
  return all.filter(event => !event.jobKey || event.jobKey === jobKey);
}

/** Auth / leftover-link return to the Jobs workspace on `/`. */
export function jobsWorkspaceRestoreHref(): string {
  return "/?restore=1";
}

/**
 * Revisit of `/` must show FIND (hero), not replay the last robot URL.
 * Restore only on browser back/forward, auth return (one-shot), or ?restore=1.
 * Reload / tab-discard / typed URL / bookmark stay on FIND — same-tab session
 * cache must not auto-run the previous submit.
 */
export function shouldRestoreJobsWorkspace(opts: {
  navigationType?: string | number | null;
  restoreOnce?: boolean;
  restoreQuery?: boolean;
}): boolean {
  if (opts.restoreQuery || opts.restoreOnce) return true;
  const t = opts.navigationType;
  return t === "back_forward" || t === 2;
}

/** True when post-auth `next` is the Jobs front door (not pipeline). */
export function isJobsHomeDest(dest: string | null | undefined): boolean {
  const path = (dest || "").trim().split("?")[0] || "";
  return path === "/" || path === "/jobs" || path.startsWith("/jobs/");
}

/** Auth return to `/` or `/jobs…` may restore in-progress work once. */
export function markJobsWorkspaceRestoreIfHome(dest: string | null | undefined): void {
  if (isJobsHomeDest(dest)) markJobsWorkspaceRestoreOnce();
}

export function markJobsWorkspaceRestoreOnce(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(JOBS_RESTORE_ONCE_KEY, "1");
  } catch {
    /* ignore */
  }
}

export function consumeJobsWorkspaceRestoreOnce(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const on = window.sessionStorage.getItem(JOBS_RESTORE_ONCE_KEY) === "1";
    if (on) window.sessionStorage.removeItem(JOBS_RESTORE_ONCE_KEY);
    return on;
  } catch {
    return false;
  }
}

export function readNavigationType(): string | number | null {
  if (typeof performance === "undefined") return null;
  const entry = performance.getEntriesByType("navigation")[0] as
    | PerformanceNavigationTiming
    | undefined;
  if (entry?.type) return entry.type;
  const legacy = (performance as Performance & { navigation?: { type?: number } }).navigation?.type;
  return typeof legacy === "number" ? legacy : null;
}

/**
 * Stamp restore and return `/`. Use when a leftover Jobs link still points
 * at /pipeline or /results — bounce, do not render a second job list.
 */
export function armJobsWorkspaceRestore(): string {
  markJobsWorkspaceRestoreOnce();
  return jobsWorkspaceRestoreHref();
}

/**
 * Legacy name. Jobs CTAs used to dump signed-in users on /pipeline as a
 * second job list. Activate uses jobsActivateHref (`src=jobs_activate`) instead.
 * This helper still returns the Jobs workspace for leftover links.
 */
export function buyerLeadsHref(_opts: {
  robotUrl: string;
  signedIn: boolean;
  submissionId?: number | null;
  src?: string;
  industry?: string;
  leadId?: number | null;
}): string {
  return jobsWorkspaceRestoreHref();
}
