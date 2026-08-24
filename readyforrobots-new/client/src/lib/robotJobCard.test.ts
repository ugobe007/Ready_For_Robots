import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  qualificationFromVerdict,
  robcoJobCards,
  robcoPackHonesty,
  robotJobCardFromMatch,
} from "./robotJobCard";

const here = dirname(fileURLToPath(import.meta.url));

describe("robotJobCard", () => {
  it("maps a matched job into employment-model fields without inventing economics", () => {
    const card = robotJobCardFromMatch({
      title: "Tend CNC mills/lathes — workpiece load/unload around cycle",
      company_name: "groninger",
      locality: "Charlotte, NC",
      why: ["Payload in range", "Indoor industrial cell"],
      still_unknown: ["How much of role is tend vs program"],
      verdict: "POSSIBLE_MATCH",
    });
    expect(card.employer).toBe("groninger");
    expect(card.workplace).toBe("Charlotte, NC");
    expect(card.qualification).toBe("conditional");
    expect(card.qualificationLabel).toBe("Conditional");
    expect(card.qualificationHint).toMatch(/Pending your review/i);
    expect(card.work).toBe(
      "Tend CNC mills/lathes — workpiece load/unload around cycle",
    );
    expect(card.requirements).toEqual(["Payload in range", "Indoor industrial cell"]);
    expect(card.workVolume).toBeNull();
    expect(card.currentLabor).toBeNull();
    expect(card.openQuestions).toEqual(["How much of role is tend vs program"]);
    expect(card.nextStep).toMatch(/Site assessment/i);
  });

  it("does not score a matcher hit as Qualified without user or employer feedback", () => {
    expect(qualificationFromVerdict("POSSIBLE_MATCH")).toBe("conditional");
    expect(qualificationFromVerdict(null)).toBe("pending_robot");
    expect(qualificationFromVerdict("INSUFFICIENT")).toBe("conditional");
    expect(qualificationFromVerdict("NOT_A_MATCH")).toBe("not_qualified");
    expect(qualificationFromVerdict("POSSIBLE_MATCH", ["Reach insufficient"])).toBe(
      "not_qualified",
    );
    expect(
      qualificationFromVerdict("POSSIBLE_MATCH", [], [{ presence: "absent" }]),
    ).toBe("not_qualified");
  });

  it("names required task models without claiming the robot already has them", () => {
    const card = robotJobCardFromMatch({
      title: "Pick cases onto pallets",
      company_name: "Novolex",
      locality: "Kinston, NC",
      why: ["Manipulation grounded"],
      verdict: "POSSIBLE_MATCH",
      required_task_models: [
        {
          id: "warehouse_pick_place_policy",
          label: "Warehouse pick-and-place policy",
          physical_task: "Pick and stow cases in a fulfillment cell",
          presence: "unknown",
          hardware_not_enough: "An arm in the DC is not the pick policy.",
          where_to_look: [
            {
              kind: "open_weights",
              name: "Hugging Face robotics models",
              url: "https://huggingface.co/models?pipeline_tag=robotics",
              note: "Public checkpoints. Presence unknown until named.",
            },
          ],
          qualify_filters: [
            {
              id: "commercial_license",
              label: "Does the license allow commercial placement?",
              note: "Research-only licenses cannot put a robot into paid work.",
            },
          ],
          pricing_lookups: [
            {
              kind: "token_price_index",
              name: "BenchLM LLM pricing",
              url: "https://benchlm.ai/llm-pricing",
              note: "Token API list prices. Not a robot-policy price.",
            },
          ],
        },
      ],
    });
    expect(card.qualification).toBe("conditional");
    expect(card.taskModels).toHaveLength(1);
    expect(card.taskModels[0].presence).toBe("unknown");
    expect(card.taskModels[0].label).toMatch(/pick-and-place/i);
    expect(card.taskModels[0].whereToLook[0].name).toMatch(/Hugging Face/i);
    expect(card.taskModels[0].qualifyFilters.map(f => f.id)).toContain(
      "commercial_license",
    );
    expect(card.taskModels[0].pricingLookups.some(d => /BenchLM/i.test(d.name))).toBe(
      true,
    );
    const src = readFileSync(join(here, "./robotJobCard.ts"), "utf8");
    expect(src).not.toMatch(/certificate/i);
  });

  it("keeps the RobCo pack honest: named machine-tending work, no fake labor dollars", () => {
    expect(robcoPackHonesty()).toEqual([]);
    const cards = robcoJobCards();
    expect(cards).toHaveLength(5);
    expect(new Set(cards.map(j => j.employer)).size).toBe(5);
    for (const job of cards) {
      expect(job.work.toLowerCase()).toMatch(/cnc|laser|plasma|workpiece|mill|lathe/);
      expect(job.workVolume).toBeNull();
      expect(job.currentLabor).toBeNull();
      expect(job.qualification).toBe("pending_robot");
    }
    const corpus = readFileSync(
      join(here, "../../../../app/data/robot_job_match_corpus.json"),
      "utf8",
    );
    for (const job of cards) {
      expect(corpus).toContain(`"job_key": "${job.job_key}"`);
    }
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const cardSrc = workspace.slice(workspace.indexOf("function JobCard"));
    expect(cardSrc).toMatch(/robotJobCardFromMatch/);
    expect(cardSrc).toMatch(/Employer/);
    expect(cardSrc).toMatch(/Workplace/);
    expect(cardSrc).toMatch(/Why this is listed/);
    expect(cardSrc).toMatch(/Task models/);
    expect(cardSrc).toMatch(/How we qualify a candidate/);
    expect(cardSrc).toMatch(/Where to find price/);
    expect(cardSrc).not.toMatch(/certificate/i);
    expect(cardSrc).toMatch(/qualificationHint/);
    expect(cardSrc).not.toMatch(/Possible match/);
    expect(cardSrc).not.toMatch(/>Qualified</);
  });
});
