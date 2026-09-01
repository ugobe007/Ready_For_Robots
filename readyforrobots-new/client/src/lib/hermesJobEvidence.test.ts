import { describe, expect, it } from "vitest";
import {
  humanizeOverlayRationale,
  isRealVendorName,
  pipelineHermesCard,
} from "./hermesJobEvidence";

describe("hermesJobEvidence", () => {
  it("rejects robot-type slugs and keeps real vendor names", () => {
    expect(isRealVendorName("amr")).toBe(false);
    expect(isRealVendorName("amr_amr_forklift")).toBe(false);
    expect(isRealVendorName("cobot")).toBe(false);
    expect(isRealVendorName("mobile_manipulator")).toBe(false);
    expect(isRealVendorName("Boston Dynamics")).toBe(true);
  });

  it("keeps one human rationale line from an rfr_inference dump", () => {
    const raw =
      "[rfr_inference_v1] Labor shortage / staffing gap; Labor shortage / staffing gap; high-fit industry (Hospitality); 8 hot-type signals (labor_shortage, capex, strategic_hire, expansion, funding_round, ...); 12 signals; work family: unknown";
    expect(humanizeOverlayRationale(raw)).toBe("Labor shortage / staffing gap");
  });

  it("hides the CRM card when overlay is only SIGNAL internals", () => {
    expect(
      pipelineHermesCard({
        hermesQualify: {
          rationale:
            "[rfr_inference_v1] 12 signals; work family: unknown; high-fit industry (Hospitality)",
          vendor_shortlist: [
            { vendor: "amr_amr_forklift" },
            { vendor: "cobot" },
            { vendor: "mobile_manipulator" },
          ],
        },
      })
    ).toBeNull();
  });

  it("keeps named people, roles, videos, and a short human line", () => {
    const card = pipelineHermesCard({
      hermesQualify: {
        rationale:
          "[rfr_inference_v1] Labor shortage / staffing gap; 8 hot-type signals (labor_shortage)",
        vendor_shortlist: [
          { vendor: "amr" },
          { vendor: "Boston Dynamics", model: "Spot" },
        ],
      },
      hermesJobTitles: ["AMR Operator"],
      hermesDecisionMakers: [{ name: "Jane Ops", title: "VP Operations" }],
      hermesVideoEvidence: [
        { source_url: "https://youtu.be/demo", title: "Tote unload" },
      ],
    });
    expect(card?.rationale).toBe("Labor shortage / staffing gap");
    expect(card?.vendors.map(v => v.vendor)).toEqual(["Boston Dynamics"]);
    expect(card?.jobTitles).toEqual(["AMR Operator"]);
    expect(card?.decisionMakers[0]?.name).toBe("Jane Ops");
    expect(card?.videos[0]?.title).toBe("Tote unload");
  });
});
