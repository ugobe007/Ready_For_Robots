/**
 * Jobs submit workflow — one explicit state machine.
 * Research privately. Reveal deliberately. Never stream partial jobs.
 */
export type SubmitPhase =
  | "idle"
  | "researching"
  | "product_selection"
  | "composing"
  | "results"
  | "recover"
  | "gate";

export const SUBMIT_PHASES: SubmitPhase[] = [
  "idle",
  "researching",
  "product_selection",
  "composing",
  "results",
  "recover",
  "gate",
];

export type SearchTimings = {
  resolve_ms: number;
  profile_ms: number;
  match_ms: number;
  total_ms: number;
  cached: boolean;
};

export type ComposedSearch = {
  robotName: string;
  companyName: string | null;
  robotClass: string | null;
  profileTier: "A" | "B" | "C" | null;
  jobCount: number;
  jobs: unknown[];
  topJobs: unknown[];
  capabilities: unknown[];
  profile: unknown | null;
  timings: SearchTimings | null;
  thin: boolean;
};

export function isResearchingPhase(phase: SubmitPhase): boolean {
  return phase === "researching" || phase === "composing";
}

export function isStableLandingPhase(phase: SubmitPhase): boolean {
  return (
    phase === "idle" ||
    isResearchingPhase(phase) ||
    phase === "product_selection" ||
    phase === "results"
  );
}

/** Right-hand public tape must keep scrolling until RESULTS. */
export function tapeStaysMarket(phase: SubmitPhase): boolean {
  return phase !== "results" && phase !== "gate";
}

export function canRevealResults(composed: ComposedSearch | null): boolean {
  return Boolean(composed && (composed.jobs.length > 0 || composed.profile));
}

const RESEARCH_STAGES = [
  { id: "identify", label: "Identifying robot" },
  { id: "capabilities", label: "Reviewing capabilities" },
  { id: "matching", label: "Matching work" },
] as const;

export function researchStageIndex(
  elapsedMs: number,
  composing: boolean
): number {
  if (composing) return 3;
  if (elapsedMs < 300) return 0;
  if (elapsedMs < 900) return 1;
  return 2;
}

export function researchStages(elapsedMs: number, composing: boolean) {
  const idx = researchStageIndex(elapsedMs, composing);
  return RESEARCH_STAGES.map((s, i) => ({
    n: String(i + 1).padStart(2, "0"),
    label: s.label,
    done: i < idx || composing,
    active: i === idx && !composing,
  }));
}

export function researchStatusLine(opts: {
  robotName?: string | null;
  companyName?: string | null;
  composing?: boolean;
  jobCount?: number | null;
}): string {
  if (opts.composing) {
    const n = opts.jobCount ?? 0;
    return n > 0
      ? `Profile ready. ${n} jobs found.`
      : "Profile ready. Displaying best matches…";
  }
  const who = opts.robotName || opts.companyName || "this robot";
  return `Researching ${who} and comparing it against our robot job corpus.`;
}

export function dotsBar(doneCount: number, total = 3): string {
  const filled = Math.max(0, Math.min(total, doneCount));
  return `${"█".repeat(filled * 5)}${"░".repeat((total - filled) * 5)}`;
}
