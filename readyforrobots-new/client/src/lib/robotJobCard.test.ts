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
    expect(card.qualification).toBe("qualified");
    expect(card.qualificationLabel).toBe("Qualified");
    expect(card.workVolume).toBeNull();
    expect(card.currentLabor).toBeNull();
    expect(card.openQuestions).toEqual(["How much of role is tend vs program"]);
    expect(card.nextStep).toMatch(/Site assessment/i);
  });

  it("does not score a robot with no verdict as already qualified", () => {
    expect(qualificationFromVerdict(null)).toBe("pending_robot");
    expect(qualificationFromVerdict("INSUFFICIENT")).toBe("conditional");
    expect(qualificationFromVerdict("NOT_A_MATCH")).toBe("not_qualified");
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
    expect(cardSrc).toMatch(/Open questions/);
    expect(cardSrc).toMatch(/Next step:/);
    expect(cardSrc).toMatch(/card\.nextStep/);
    expect(cardSrc).not.toMatch(/Possible match/);
    expect(cardSrc).not.toMatch(/\bLead\b/);
  });
});
