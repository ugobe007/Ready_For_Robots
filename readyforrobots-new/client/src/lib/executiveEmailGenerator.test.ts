import { describe, expect, it } from "vitest";
import { buildPhelanExecutiveEmail } from "./executiveEmailGenerator";

describe("executiveEmailGenerator", () => {
  it("generates the executive sales email template for any lead", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe(
      "Robot job matches & feasibility review for FedEx Ground"
    );
    expect(email.body).toContain("Hi David,");
    expect(email.body).toContain(
      "I’m Phelan, a Robot Job Analyst at ReadyForRobots."
    );
    expect(email.body).toContain(
      "matching payload capacity, cell reach, operating environment, and pre-trained task models."
    );
    expect(email.body).toContain(
      "https://readyforrobots.com/pipeline?company=FedEx%20Ground"
    );
    expect(email.body).toContain(
      "3D cell-feasibility simulation to verify physical fit"
    );
    expect(email.body).toContain("phelan@readyforrobots.com");
    expect(email.body).not.toContain("Bob Christopher");
    expect(email.body).not.toContain("Cal");
  });

  it("handles company names cleanly in the email template", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
      taskType: "Meal Assembly",
    });

    expect(email.body).toContain("For CloudKitchens's **Meal Assembly** job");
    expect(email.body).toContain(
      "https://readyforrobots.com/pipeline?company=CloudKitchens"
    );
  });
});
