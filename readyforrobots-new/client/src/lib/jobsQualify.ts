/**
 * QUALIFY is a judgment on evidence FIND already produced.
 * No new matcher pass. No LLM brief. No hop to /pipeline.
 *
 *   pursue         — confirmed why, no blocker
 *   needs_evidence — no confirmed why (or insufficient verdict)
 *   not_now        — blocker or not a match
 */
import type { MatchJob } from "@/lib/robotJobMatch";

export type QualifyStance = "pursue" | "needs_evidence" | "not_now";

export type QualifyBrief = {
  stance: QualifyStance;
  headline: string;
  reason: string;
  why: string[];
  stillUnknown: string[];
  blockers: string[];
};

type QualifyInput = Pick<
  MatchJob,
  "verdict" | "why" | "still_unknown" | "unknowns" | "blockers"
>;

export function qualifyJob(job: QualifyInput): QualifyBrief {
  const why = (job.why || []).map(s => s.trim()).filter(Boolean);
  const stillUnknown = (
    job.still_unknown?.length ? job.still_unknown : job.unknowns || []
  )
    .map(s => s.trim())
    .filter(Boolean);
  const blockers = (job.blockers || []).map(s => s.trim()).filter(Boolean);
  const notAMatch = job.verdict === "NOT_A_MATCH";
  const insufficient = job.verdict === "INSUFFICIENT";

  if (notAMatch || blockers.length > 0) {
    return {
      stance: "not_now",
      headline: "Do not pursue this yet",
      reason: notAMatch
        ? "This is not a match for this robot. Qualifying it would invent a pursuit."
        : `A confirmed blocker stands in the way: ${blockers[0]}`,
      why,
      stillUnknown,
      blockers,
    };
  }

  if (insufficient || why.length === 0) {
    return {
      stance: "needs_evidence",
      headline: "Not enough to decide",
      reason:
        "There is no confirmed why this robot can do this job. Unknowns stay unknown — we will not promote this into a pursuit.",
      why,
      stillUnknown,
      blockers,
    };
  }

  return {
    stance: "pursue",
    headline: "Worth pursuing",
    reason: stillUnknown.length
      ? "Confirmed fit on this robot. Remaining unknowns are diligence, not a no."
      : "Confirmed fit on this robot. No confirmed blocker.",
    why,
    stillUnknown,
    blockers,
  };
}
