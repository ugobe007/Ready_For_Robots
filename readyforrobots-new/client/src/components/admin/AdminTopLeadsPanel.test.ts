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

    expect(email.subject).toBe("Robotics feasibility at CloudKitchens?");
    expect(email.body).toContain("Dear Justin,");
    expect(email.body).toContain("Nice to meet you.");
    expect(email.body).toContain("I am with ReadyForRobots, we provide independent, vendor-neutral feasibility benchmarks comparing leading commercial platforms across duty cycles, floor navigation, and real-world payback targets.");
    expect(email.body).toContain("I’m reaching out because we’ve been following CloudKitchens’ growth and operational scale.");
    expect(email.body).toContain("Having spent my career in robotics—leading teams at Panasonic, RichTech Robotics and Anybots");
    expect(email.body).toContain("Either way, I’d be curious to hear how your team is thinking about robotics feasibility across your facilities right now.");
  });
});
