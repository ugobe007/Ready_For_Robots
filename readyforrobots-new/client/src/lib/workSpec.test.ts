import { describe, expect, it } from "vitest";
import {
  laborPayback,
  parseWorkSpec,
  qualifyWork,
  workflowById,
} from "./workSpec";

const palletInput = {
  workflowId: "pallets",
  jobType: "Moving pallets in a warehouse",
  loadLb: "500",
  hoursPerDay: "8",
  alongsideHumans: "yes" as const,
  robotCost: "45000",
  laborRate: "28.50",
};

describe("work spec", () => {
  it("maps pallet work onto the warehouse catalog class", () => {
    expect(workflowById("pallets")?.catalogClass).toBe("warehouse");
    expect(workflowById("assembly")?.catalogClass).toBe("factory");
    expect(workflowById("amr")?.catalogClass).toBe("amr");
  });

  it("qualifies a pallet job without inventing an employer", () => {
    const parsed = parseWorkSpec(palletInput);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const card = qualifyWork(parsed.spec);
    expect(card.title).toBe("Moving pallets in a warehouse");
    expect(card.catalogClass).toBe("warehouse");
    expect(card.qualification).toBe("Conditional");
    expect(card.evidence).toMatch(/site survey/);
    expect(card.evidence).toMatch(/cannot guarantee/);
    expect(card.tradeoff).toMatch(/horizontal transport/);
    expect(card.tradeoff).toMatch(/avoid them/);
    expect(card.summary).not.toMatch(/employer/i);
    expect(card.economics?.paybackMonths).toBe(9.1);
    expect(card.economics?.annualRoiPercent).toBe(126.7);
    expect(card.economics?.assumptions.join(" ")).toMatch(/not a quote/);
  });

  it("leaves payback blank when price or wage is missing", () => {
    const parsed = parseWorkSpec({
      ...palletInput,
      robotCost: "",
      laborRate: "",
    });
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(qualifyWork(parsed.spec).economics).toBeNull();
    expect(laborPayback({ robotCostUsd: 0, laborRateUsd: 28.5, hoursPerDay: 8 })).toBeNull();
  });

  it("asks for the missing work facts", () => {
    expect(parseWorkSpec({ ...palletInput, workflowId: "" }).ok).toBe(false);
    expect(parseWorkSpec({ ...palletInput, loadLb: "" }).ok).toBe(false);
    expect(parseWorkSpec({ ...palletInput, hoursPerDay: "0" }).ok).toBe(false);
    expect(
      parseWorkSpec({ ...palletInput, alongsideHumans: "" }).ok
    ).toBe(false);
  });
});
