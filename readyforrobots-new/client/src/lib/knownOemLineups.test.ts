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
    expect(names.some(n => /^Humanoid$/i.test(n))).toBe(false);
    expect(names.length).toBeGreaterThan(0);
  });

  it("returns null for unknown hosts", () => {
    expect(lookupKnownOem("https://unknown-oem.example/")).toBeNull();
    expect(lookupKnownOem("https://www.greenfieldincorporated.com/")).toBeNull();
    expect(lookupKnownOem("https://www.xpeng.com/")).toBeNull();
    expect(lookupKnownOem("https://advanced.farm/")).toBeNull();
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
    expect(hit?.robots[0]?.display_class).not.toBe("humanoid");
  });

  it("maps Pudu, Keenon, UBTech, AgiBot, MagicLab, Deep Robotics as mixed product ranges", () => {
    const pudu = lookupKnownOem("https://www.pudurobotics.com/en");
    const puduBy = Object.fromEntries(
      (pudu?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(puduBy.BellaBot).toBe("serving");
    expect(puduBy.CC1).toBe("cleaning");
    expect(puduBy.D9).toBe("humanoid");
    const puduClasses = new Set(
      Object.values(puduBy).filter((c): c is string => Boolean(c)),
    );
    expect(puduClasses.has("serving")).toBe(true);
    expect(puduClasses.has("cleaning")).toBe(true);
    expect(puduClasses.has("humanoid")).toBe(true);

    const keenon = lookupKnownOem("https://www.keenon.com/");
    const keenBy = Object.fromEntries(
      (keenon?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(keenBy["Dinerbot T5"]).toBe("serving");
    expect(keenBy.C55).toBe("cleaning");

    const ub = lookupKnownOem("https://www.ubtrobot.com/");
    const walker = (ub?.robots || []).find(r => /^Walker$|Walker X/i.test(r.name || ""));
    expect(walker?.display_class).toBe("humanoid");
    expect(walker?.display_class).not.toBe("serving");

    const agi = lookupKnownOem("https://www.agibot.com/");
    expect(agi?.robots.some(r => r.display_class === "humanoid")).toBe(true);
    expect(agi?.robots.some(r => r.display_class === "serving")).toBe(false);

    const magic = lookupKnownOem("https://www.magiclab.top/");
    expect(magic?.robots.some(r => r.display_class === "humanoid")).toBe(true);
    expect(magic?.robots.some(r => r.display_class === "quadruped")).toBe(true);

    const deep = lookupKnownOem("https://www.deeprobotics.cn/");
    expect(deep?.robots.some(r => r.display_class === "humanoid")).toBe(true);
    expect(deep?.robots.some(r => r.display_class === "quadruped")).toBe(true);
  });

  it("maps Lucidbots Sherpa as a cleaning drone, not a floor scrubber", () => {
    const hit = lookupKnownOem("https://www.lucidbots.com/");
    const by = Object.fromEntries(
      (hit?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(by["Sherpa Drone"]).toBe("cleaning_drone");
    expect(Object.values(by).some(c => c === "avionics")).toBe(false);
    expect(Object.values(by).some(c => c === "autonomous_scrubber")).toBe(
      false,
    );
  });

  it("maps Bear serving vs clean and Gausium/Avidbots/Ecovacs floors", () => {
    const bear = lookupKnownOem("https://www.bearrobotics.ai/");
    const bearBy = Object.fromEntries(
      (bear?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(bearBy.Servi).toBe("serving");
    expect(bearBy["Servi Clean"]).toBe("cleaning");

    const gau = lookupKnownOem("https://gausium.com/");
    const gauBy = Object.fromEntries(
      (gau?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(["cleaning", "autonomous_scrubber"]).toContain(gauBy.Phantas);

    const avid = lookupKnownOem("https://avidbots.com/");
    const avidBy = Object.fromEntries(
      (avid?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(["cleaning", "autonomous_scrubber"]).toContain(avidBy.Neo);

    const eco = lookupKnownOem("https://www.ecovacscommercial.com/");
    const ecoBy = Object.fromEntries(
      (eco?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(ecoBy["DEEBOT PRO M1"]).toBe("cleaning");
  });

  it("maps Diligent Moxi as healthcare, not humanoid", () => {
    const hit = lookupKnownOem("https://www.diligentrobots.com/");
    expect(hit?.vendor_name).toMatch(/Diligent/i);
    expect(hit?.robots.map(r => r.name)).toEqual(["Moxi"]);
    expect(hit?.robots[0]?.display_class).toBe("healthcare");
    expect(hit?.robots[0]?.display_class).not.toBe("humanoid");
  });

  it("maps VinMotion Motion 1 as a humanoid without inventing SKUs", () => {
    const hit = lookupKnownOem("https://vinmotion.net/");
    expect(hit?.vendor_name).toMatch(/VinMotion/i);
    const by = Object.fromEntries(
      (hit?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(by["Motion 1"]).toBe("humanoid");
    expect(Object.prototype.hasOwnProperty.call(by, "Motion 2")).toBe(true);
    expect(by["Motion 2"] == null).toBe(true);
    expect(by.Product).toBeUndefined();
    expect(Object.keys(by).some(n => /humanoid/i.test(n))).toBe(false);
  });

  it("maps Booster T2 and Galbot S1 from page evidence", () => {
    const booster = lookupKnownOem("https://booster.tech");
    const boosterBy = Object.fromEntries(
      (booster?.robots || []).map(r => [r.name, r.display_class]),
    );
    expect(boosterBy["Booster T2"]).toBe("humanoid");
    expect(boosterBy["Booster K1"]).toBe("humanoid");
    const galbot = lookupKnownOem("https://galbot.com");
    const names = (galbot?.robots || []).map(r => r.name);
    expect(names).toContain("Galbot G1");
    expect(names).toContain("Galbot S1");
    expect(names).not.toContain("Galbot G2");
    const unix = lookupKnownOem("https://unix-group.ai");
    expect((unix?.robots || []).map(r => r.name)).toEqual(
      expect.arrayContaining(["Wanda 2.0", "Panther", "Martian"]),
    );
    expect((unix?.robots || []).map(r => r.name)).not.toContain("Wheeled");
  });
});
