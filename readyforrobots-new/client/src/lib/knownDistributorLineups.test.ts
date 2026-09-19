import { describe, expect, it } from "vitest";
import {
  lookupKnownDistributor,
  searchDistributorsForBrand,
  listKnownDistributors,
} from "./knownDistributorLineups";

describe("knownDistributorLineups dataset & lookup engine", () => {
  it("resolves Cross Company Robotics from exact domain", () => {
    const dist = lookupKnownDistributor("https://www.crossco.com");
    expect(dist).not.toBeNull();
    expect(dist?.distributor_name).toBe("Cross Company Robotics");
    expect(dist?.supported_brands).toContain("Universal Robots");
    expect(dist?.supported_brands).toContain("Mobile Industrial Robots (MiR)");
    expect(dist?.robot_categories).toContain("cobot");
    expect(dist?.robot_categories).toContain("amr");
  });

  it("resolves Motion Automation Intelligence from eTLD+1 subdomain URL", () => {
    const dist = lookupKnownDistributor("https://robotics.motion.com/products");
    expect(dist).not.toBeNull();
    expect(dist?.distributor_name).toBe("Motion Automation Intelligence");
    expect(dist?.supported_brands).toContain("FANUC");
    expect(dist?.supported_brands).toContain("Universal Robots");
  });

  it("resolves Gibson Engineering from root domain", () => {
    const dist = lookupKnownDistributor("gibsonengineering.com");
    expect(dist).not.toBeNull();
    expect(dist?.distributor_name).toBe("Gibson Engineering");
    expect(dist?.product_mix.length).toBeGreaterThan(0);
  });

  it("returns null for unknown domain", () => {
    const dist = lookupKnownDistributor("https://unknown-random-distributor-12345.com");
    expect(dist).toBeNull();
  });

  it("searches distributors representing Universal Robots", () => {
    const list = searchDistributorsForBrand("Universal Robots");
    expect(list.length).toBeGreaterThanOrEqual(4);
    const names = list.map(d => d.distributor_name);
    expect(names).toContain("Cross Company Robotics");
    expect(names).toContain("Motion Automation Intelligence");
    expect(names).toContain("Gibson Engineering");
  });

  it("resolves AlphaRobotics from exact domain alpharoboticsai.com and subpages", () => {
    const dist = lookupKnownDistributor("https://alpharoboticsai.com/marketplace/agibot-a2");
    expect(dist).not.toBeNull();
    expect(dist?.distributor_name).toBe("AlphaRobotics");
    expect(dist?.supported_brands).toContain("AgiBot");
    expect(dist?.supported_brands).toContain("PUDU Robotics");
    expect(dist?.supported_brands).toContain("Gausium");
    expect(dist?.robot_categories).toContain("humanoid");
    expect(dist?.robot_categories).toContain("delivery");
    expect(dist?.robot_categories).toContain("cleaning");
    expect(dist?.product_mix.length).toBeGreaterThan(5);
  });

  it("lists all indexed distributors in dataset", () => {
    const all = listKnownDistributors();
    expect(all.length).toBeGreaterThanOrEqual(8);
  });
});
