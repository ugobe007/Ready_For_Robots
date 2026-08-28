import { describe, expect, it } from "vitest";
import { hostFromOemUrl, lookupKnownOem } from "./knownOemLineups";

describe("knownOemLineups", () => {
  it("maps Reflex homepages to named robots without a network call", () => {
    expect(hostFromOemUrl("https://www.reflexrobotics.com/")).toBe(
      "reflexrobotics.com",
    );
    expect(hostFromOemUrl("reflexrobotics.com")).toBe("reflexrobotics.com");
    const hit = lookupKnownOem("https://www.reflexrobotics.com/");
    expect(hit?.vendor_name).toMatch(/Reflex/i);
    const names = hit?.robots.map(r => r.name) || [];
    expect(names.some(n => /Gen2|Gen 2/i.test(n))).toBe(true);
    expect(names.some(n => /Humanoid/i.test(n))).toBe(true);
    expect(names.length).toBeGreaterThan(0);
  });

  it("returns null for unknown hosts", () => {
    expect(lookupKnownOem("https://unknown-oem.example/")).toBeNull();
    expect(lookupKnownOem("https://www.greenfieldincorporated.com/")).toBeNull();
  });

  it("falls back from a product subdomain to the indexed registrable host", () => {
    const hit = lookupKnownOem("https://shop.reflexrobotics.com/products");
    expect(hit?.vendor_name).toMatch(/Reflex/i);
    expect((hit?.robots.length || 0)).toBeGreaterThan(0);
  });

  it("maps Carbon Robotics LaserWeeder as agriculture without a network call", () => {
    const hit = lookupKnownOem("https://carbonrobotics.com/");
    expect(hit?.vendor_name).toMatch(/Carbon Robotics/i);
    expect(hit?.robots.map(r => r.name)).toEqual(["LaserWeeder"]);
    expect(hit?.robots[0]?.display_class).toBe("agricultural_robot");
  });

  it("maps Skydio X10 as a drone, not a quadruped", () => {
    const hit = lookupKnownOem("https://skydio.com/x10");
    expect(hit?.vendor_name).toMatch(/Skydio/i);
    expect(hit?.robots.some(r => /x10/i.test(r.name))).toBe(true);
    const x10 = hit?.robots.find(r => /x10/i.test(r.name));
    expect(x10?.display_class).toBe("drone");
    expect(x10?.display_class).not.toBe("quadruped");
  });

  it("lists Deere combine, tractor, and See & Spray as separate products", () => {
    const hit = lookupKnownOem("https://deere.com/en/harvesting/x-series-combines");
    const names = (hit?.robots || []).map(r => r.name);
    expect(names.some(n => /combine/i.test(n))).toBe(true);
    expect(names.some(n => /tractor/i.test(n))).toBe(true);
    expect(names.some(n => /see\s*&\s*spray|see and spray/i.test(n))).toBe(true);
    expect(names.length).toBeGreaterThanOrEqual(3);
    expect(
      hit?.robots.every(r => r.display_class === "agricultural_robot"),
    ).toBe(true);
  });

  it("maps Sunday Robotics Memo without a network call", () => {
    const hit = lookupKnownOem("https://www.sunday.ai/");
    expect(hit?.vendor_name).toMatch(/Sunday/i);
    expect(hit?.robots.map(r => r.name)).toEqual(["Memo"]);
    expect(hit?.robots[0]?.display_class).toBe("service_robot");
  });
});
