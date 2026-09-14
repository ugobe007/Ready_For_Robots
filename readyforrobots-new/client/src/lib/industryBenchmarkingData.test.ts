import { describe, expect, it } from "vitest";
import {
  INDUSTRY_BENCHMARKS,
  getBenchmarkForIndustry,
} from "./industryBenchmarkingData";

describe("industryBenchmarkingData datasets & getters", () => {
  it("contains benchmarking datasets for all 7 target industry verticals", () => {
    const keys = Object.keys(INDUSTRY_BENCHMARKS);
    expect(keys).toContain("hospitality");
    expect(keys).toContain("logistics");
    expect(keys).toContain("facilities");
    expect(keys).toContain("healthcare");
    expect(keys).toContain("gaming");
    expect(keys).toContain("aviation");
    expect(keys).toContain("agriculture");
  });

  it("resolves hospitality benchmark from keyword alias", () => {
    const bm = getBenchmarkForIndustry("hotel");
    expect(bm.id).toBe("hospitality");
    expect(bm.target_accounts).toContain("Thompson Hospitality");
    expect(bm.platforms.length).toBeGreaterThan(0);
  });

  it("resolves surface logistics benchmark from keyword alias", () => {
    const bm = getBenchmarkForIndustry("warehouse");
    expect(bm.id).toBe("logistics");
    expect(bm.target_accounts).toContain("FedEx Ground");
    expect(bm.target_accounts).toContain("Ryder System");
  });

  it("resolves healthcare benchmark from keyword alias", () => {
    const bm = getBenchmarkForIndustry("clinical");
    expect(bm.id).toBe("healthcare");
    expect(bm.target_accounts).toContain("HCA Healthcare");
  });

  it("resolves agriculture benchmark from keyword alias", () => {
    const bm = getBenchmarkForIndustry("berry");
    expect(bm.id).toBe("agriculture");
    expect(bm.target_accounts).toContain("Wish Farms (Tampa Bay AG)");
  });
});
