import { describe, expect, it } from "vitest";
import AdminTopLeadsPanel, { buildBobExecutiveEmail } from "./AdminTopLeadsPanel";

describe("AdminTopLeadsPanel component module", () => {
  it("exports AdminTopLeadsPanel as a valid React component function", () => {
    expect(typeof AdminTopLeadsPanel).toBe("function");
  });

  it("builds warm greeting & thesis executive email with Bob's Panasonic, RichTech, and Anybots credentials", () => {
    const email = buildBobExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
      robotTypes: ["Meal Assembly Cobots", "Kitchen Prep Manipulators"],
    });

    expect(email.subject).toBe("Engineering task feasibility & robotics evaluation for CloudKitchens");
    expect(email.body).toContain("Dear Justin,");
    expect(email.body).toContain("My name is Bob Christopher, President of ReadyForRobots.");
    expect(email.body).toContain("Would you be open to reviewing a brief feasibility and ROI summary for your facilities?");
  });
});
