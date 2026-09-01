/**
 * Live job-tape corpus — named-employer jobs from the match corpus.
 * Short titles / paths for the terminal board (not marketing cards).
 */
import tapeJson from "@/lib/market_tape_jobs.json";
import {
  KARE_CART,
  KARE_GRIPPER,
  KARE_INSPECT,
  KARE_PALLET,
  KARE_SCRUB,
  KARE_TRANSPORT,
  type PixelMap,
} from "@/lib/kareIcons";

export type TapeFamily =
  | "transport"
  | "cart"
  | "pallet"
  | "scrub"
  | "inspect"
  | "gripper";

export type TapeJob = {
  key: string;
  title: string;
  industry: string;
  path: string;
  family: TapeFamily;
};

export const TAPE_ICONS: Record<TapeFamily, PixelMap> = {
  transport: KARE_TRANSPORT,
  cart: KARE_CART,
  pallet: KARE_PALLET,
  scrub: KARE_SCRUB,
  inspect: KARE_INSPECT,
  gripper: KARE_GRIPPER,
};

/** Idle → one-frame “active” variants (few pixels change). */
export const TAPE_ICONS_ACTIVE: Record<TapeFamily, PixelMap> = {
  transport: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  cart: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  pallet: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  scrub: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  inspect: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  gripper: KARE_GRIPPER,
};

const TAPE_FAMILIES = new Set<TapeFamily>([
  "transport",
  "cart",
  "pallet",
  "scrub",
  "inspect",
  "gripper",
]);

/** Named-employer market tape. Drops anonymous source=tape shorts that repeated the same work. */
export const MARKET_TAPE_JOBS: TapeJob[] = (tapeJson.jobs || []).flatMap(
  raw => {
    const family = raw.family as TapeFamily;
    const key = String(raw.key || "").trim();
    const title = String(raw.title || "").trim();
    if (!key || !title || !TAPE_FAMILIES.has(family)) return [];
    return [
      {
        key,
        title,
        industry: String(raw.industry || "").trim(),
        path: String(raw.path || "WORKSITE → WORKSITE").trim(),
        family,
      },
    ];
  }
);

export function uniqueTapeJobCount(jobs: TapeJob[] = MARKET_TAPE_JOBS): number {
  return new Set(jobs.map(j => j.key)).size;
}

export function shuffleTapeJobs<T>(
  items: T[],
  rng: () => number = Math.random
): T[] {
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** Next job that is not currently on the 12-row board. Reshuffle by wrapping. */
export function nextUnseenTapeJob(
  order: TapeJob[],
  cursor: number,
  visibleKeys: Set<string>
): { job: TapeJob; nextCursor: number; wrapped: boolean } | null {
  const n = order.length;
  if (!n) return null;
  for (let i = 0; i < n; i++) {
    const idx = (cursor + i) % n;
    const job = order[idx];
    if (!visibleKeys.has(job.key) || n <= visibleKeys.size) {
      const nextCursor = (idx + 1) % n;
      return { job, nextCursor, wrapped: nextCursor === 0 };
    }
  }
  const job = order[cursor % n];
  const nextCursor = (cursor + 1) % n;
  return { job, nextCursor, wrapped: nextCursor === 0 };
}

export function demoJobsToTape(
  jobs: Array<{
    job_key: string;
    company_name: string;
    locality?: string | null;
    robot_compatible_task: string;
    action?: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    requirements?: Record<string, any>;
  }>,
  family: string
): TapeJob[] {
  return jobs.map(j => {
    const iface = j.requirements?.load_interface as string | undefined;
    let tapeFamily: TapeFamily = "transport";
    if (family === "floor_scrub") tapeFamily = "scrub";
    else if (iface === "cart") tapeFamily = "cart";
    else if (iface === "kit") tapeFamily = "transport";
    else if (
      j.action === "palletize" ||
      /pallet|stack|case/i.test(j.robot_compatible_task)
    ) {
      tapeFamily = "pallet";
    }

    const title = shortenTask(j.robot_compatible_task);
    const industry =
      (j.locality || j.company_name || "").split(",")[0] || j.company_name;
    const path = pathFromJob(j);

    return {
      key: j.job_key,
      title,
      industry,
      path,
      family: tapeFamily,
    };
  });
}

function shortenTask(task: string): string {
  const t = task.trim();
  if (t.length <= 36) return t;
  return `${t.slice(0, 33).trim()}…`;
}

function pathFromJob(j: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  requirements?: Record<string, any>;
}): string {
  const p = j.requirements?.path as string | undefined;
  if (p) return p.replace(/→/g, " → ").toUpperCase();
  return "WORKSITE → WORKSITE";
}
