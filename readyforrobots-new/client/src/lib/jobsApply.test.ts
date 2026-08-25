import { describe, expect, it } from "vitest";
import {
  applyStatusFromGaps,
  canApplyToJob,
  emptyApplyRecord,
  followUpNextStep,
  jobCredentialGaps,
  placementOutreachDraft,
  placementWorkflowStrategy,
  placementAgentBrief,
  placementMoneyLane,
} from "./jobsApply";
import type { MatchJob } from "./robotJobMatch";

const job: MatchJob = {
  job_key: "cnc-1",
  title: "Load parts into CNC",
  industry: "machining",
  path: "tend",
  company_name: "Fulcrum Technologies",
  locality: "Tualatin, OR",
  verdict: "POSSIBLE_MATCH",
  required_task_models: [
    {
      id: "machine_tending_load_unload",
      label: "Machine-tending load/unload policy",
      physical_task: "load",
      vertical: "manufacturing",
      presence: "unknown",
      hardware_not_enough: "Hardware is not enough",
      where_to_look: [],
      card_contract: {
        headline: "To place this job",
        layer: "Layer: Site-adapted policy",
        who_trains: "Who trains: integrator",
        time: "Typical time: 4–12 weeks after a map and demo traces exist",
        you_provide: "You provide: site map",
        field_feedback: "Field traces do not automatically reduce the model price unless the OEM contract says so.",
        list_line: "Site-adapted · 4–12 weeks · integrator",
      },
    },
  ],
};

describe("jobsApply", () => {
  it("blocks apply until pack, PoC, and monthly rental are present", () => {
    const empty = emptyApplyRecord("cnc-1");
    const gaps = jobCredentialGaps(job, empty);
    expect(gaps.map(g => g.id)).toEqual([
      "model_pack",
      "poc_evidence",
      "monthly_rental",
    ]);
    expect(gaps.every(g => !g.met)).toBe(true);
    expect(applyStatusFromGaps(gaps, empty)).toBe("blocked");
    expect(canApplyToJob(gaps, empty)).toBe(false);
    expect(gaps.find(g => g.id === "monthly_rental")?.howToFix).toMatch(/Do not invent/i);
  });

  it("is ready when the OEM/distributor can license the pack and quoted rental", () => {
    const record = {
      ...emptyApplyRecord("cnc-1"),
      packAcknowledged: true,
      pocEvidence: "Cell demo video from integrator SOW",
      monthlyRental: "4800 / month RaaS",
    };
    const gaps = jobCredentialGaps(job, record);
    expect(gaps.every(g => g.met)).toBe(true);
    expect(applyStatusFromGaps(gaps, record)).toBe("ready");
    expect(canApplyToJob(gaps, record)).toBe(true);
    const draft = placementOutreachDraft(job, record, "Dexmate Vega");
    expect(draft).toMatch(/Applying Dexmate Vega to Load parts into CNC/);
    expect(draft).toMatch(/Fulcrum/);
    expect(draft).toMatch(/4800 \/ month RaaS/);
    expect(draft).not.toMatch(/certificate/i);
  });

  it("tracks follow-up after apply", () => {
    const record = {
      ...emptyApplyRecord("cnc-1"),
      status: "applied" as const,
      appliedAt: "2026-08-25",
    };
    expect(followUpNextStep(record)).toMatch(/site assessment/i);
    expect(
      followUpNextStep({ ...record, status: "follow_up", followUpAt: "2026-08-26" }),
    ).toMatch(/Follow up on the application/i);
  });

  it("names a workflow strategy from remaining gaps", () => {
    const empty = emptyApplyRecord("cnc-1");
    const gaps = jobCredentialGaps(job, empty);
    expect(placementWorkflowStrategy(gaps, empty)).toMatch(/Do not apply yet/);
    expect(placementWorkflowStrategy(gaps, empty)).toMatch(/Task-library pack/);
    const ready = {
      ...empty,
      packAcknowledged: true,
      pocEvidence: "Cell demo video from integrator SOW",
      monthlyRental: "4800 / month RaaS",
    };
    expect(placementWorkflowStrategy(jobCredentialGaps(job, ready), ready)).toMatch(
      /Credentials are complete/,
    );
  });

  it("makes Place a money moment: context, then pack → quote → apply", () => {
    const empty = emptyApplyRecord("cnc-1");
    const emptyGaps = jobCredentialGaps(job, empty);
    expect(placementMoneyLane(emptyGaps, empty)).toBe("pack");
    expect(placementAgentBrief(job, empty, "Dexmate Vega")).toMatch(
      /Fulcrum Technologies has work: Load parts into CNC/,
    );
    expect(placementAgentBrief(job, empty, "Dexmate Vega")).toMatch(/Your move: confirm the task-library pack/);
    const quoted = {
      ...empty,
      packAcknowledged: true,
      pocEvidence: "Cell demo video from integrator SOW",
    };
    expect(placementMoneyLane(jobCredentialGaps(job, quoted), quoted)).toBe("quote");
    expect(placementAgentBrief(job, quoted, "Dexmate Vega")).toMatch(/quote the monthly rental/);
    expect(placementAgentBrief(job, quoted, "Dexmate Vega")).toMatch(/do not invent/i);
    const ready = {
      ...quoted,
      monthlyRental: "4800 / month RaaS",
    };
    expect(placementMoneyLane(jobCredentialGaps(job, ready), ready)).toBe("apply");
    expect(placementAgentBrief(job, ready, "Dexmate Vega")).toMatch(/money moment/i);
  });
});
