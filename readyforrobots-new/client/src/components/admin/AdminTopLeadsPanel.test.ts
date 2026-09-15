import { describe, expect, it } from "vitest";
import AdminTopLeadsPanel, { buildBobExecutiveEmail } from "./AdminTopLeadsPanel";

describe("AdminTopLeadsPanel component module", () => {
  it("exports AdminTopLeadsPanel as a valid React component function", () => {
    expect(typeof AdminTopLeadsPanel).toBe("function");
  });

  it("builds un-assuming, curious executive email with Bob's Panasonic authority", () => {
    const email = buildBobExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Robotics feasibility at FedEx Ground?");
    expect(email.body).toContain("Dear David,");
    expect(email.body).toContain("I’m reaching out with a simple question regarding FedEx Ground’s operational roadmap");
    expect(email.body).toContain("Having spent years in commercial robotics—leading teams at Panasonic and building 3 robot companies");
    expect(email.body).toContain("Either way, I’d be curious to hear where you see the biggest operational bottlenecks");
  });
});
