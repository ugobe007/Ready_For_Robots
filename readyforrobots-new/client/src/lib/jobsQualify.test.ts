import { describe, expect, it } from "vitest";
import { qualifyJob } from "./jobsQualify";
import { jobForNextStep, JOBS_NEXT_CTA } from "./jobsWorkflow";

describe("qualifyJob", () => {
  it("pursues a possible match with confirmed why and no blocker", () => {
    const brief = qualifyJob({
      verdict: "POSSIBLE_MATCH",
      why: ["mobile inspection route", "mobile platform"],
      still_unknown: ["payload at this site"],
      blockers: [],
    });
    expect(brief.stance).toBe("pursue");
    expect(brief.headline).toBe("Worth pursuing");
    expect(brief.reason).toMatch(/diligence/i);
    expect(brief.why).toHaveLength(2);
    expect(brief.stillUnknown).toEqual(["payload at this site"]);
  });

  it("pursues with no unknowns when why is confirmed", () => {
    const brief = qualifyJob({
      verdict: "POSSIBLE_MATCH",
      why: ["hard-floor scrubbing"],
      still_unknown: [],
      blockers: [],
    });
    expect(brief.stance).toBe("pursue");
    expect(brief.reason).toMatch(/no confirmed blocker/i);
  });

  it("does not pursue a not-a-match even if why text exists", () => {
    const brief = qualifyJob({
      verdict: "NOT_A_MATCH",
      why: ["looks similar"],
      still_unknown: [],
      blockers: [],
    });
    expect(brief.stance).toBe("not_now");
    expect(brief.headline).toBe("Do not pursue this yet");
    expect(brief.reason).toMatch(/not a match/i);
  });

  it("does not pursue when a blocker is confirmed", () => {
    const brief = qualifyJob({
      verdict: "POSSIBLE_MATCH",
      why: ["arm reach"],
      still_unknown: [],
      blockers: ["payload over rated limit"],
    });
    expect(brief.stance).toBe("not_now");
    expect(brief.reason).toContain("payload over rated limit");
  });

  it("refuses to invent a pursuit when there is no confirmed why", () => {
    const brief = qualifyJob({
      verdict: "POSSIBLE_MATCH",
      why: [],
      still_unknown: ["end effector"],
      blockers: [],
    });
    expect(brief.stance).toBe("needs_evidence");
    expect(brief.headline).toBe("Not enough to decide");
  });

  it("treats an insufficient verdict as needs evidence", () => {
    const brief = qualifyJob({
      verdict: "INSUFFICIENT",
      why: ["maybe"],
      still_unknown: [],
      blockers: [],
    });
    expect(brief.stance).toBe("needs_evidence");
  });
});

describe("jobForNextStep", () => {
  const jobs = [
    { job_key: "a", title: "First" },
    { job_key: "b", title: "Second" },
  ];

  it("uses the expanded job when it is on the list", () => {
    expect(jobForNextStep(jobs, "b")?.title).toBe("Second");
  });

  it("falls back to the first job when nothing is expanded", () => {
    expect(jobForNextStep(jobs, null)?.job_key).toBe("a");
  });

  it("labels the jobs-list advance Next, not Qualify this job", () => {
    expect(JOBS_NEXT_CTA).toBe("Next →");
    expect(JOBS_NEXT_CTA).not.toMatch(/qualify/i);
  });
});
