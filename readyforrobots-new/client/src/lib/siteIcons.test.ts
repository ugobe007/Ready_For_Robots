import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  SITE_ICON_CATALOG,
  SITE_ICON_MAPS,
  iconForWorkClass,
  siteIconMap,
  type SiteIconId,
} from "./siteIcons";

const here = dirname(fileURLToPath(import.meta.url));

describe("site icon catalog", () => {
  it("ships twenty 24×24 maps with unique ids", () => {
    expect(SITE_ICON_CATALOG).toHaveLength(20);
    const ids = SITE_ICON_CATALOG.map(entry => entry.id);
    expect(new Set(ids).size).toBe(20);
    for (const entry of SITE_ICON_CATALOG) {
      const map = siteIconMap(entry.id);
      expect(map).toHaveLength(24);
      expect(map.every(row => row.length === 24)).toBe(true);
      expect(map.some(row => row.some(bit => bit === 1))).toBe(true);
      expect(SITE_ICON_MAPS[entry.id]).toBe(map);
    }
  });

  it("maps work classes used on MATCH to catalog ids", () => {
    expect(iconForWorkClass("agriculture")).toBe("plant");
    expect(iconForWorkClass("factory")).toBe("factory");
    expect(iconForWorkClass("warehouse")).toBe("box");
    expect(iconForWorkClass("logistics")).toBe("truck");
    expect(iconForWorkClass("healthcare")).toBe("heart");
    expect(iconForWorkClass("serving")).toBe("handshake");
    expect(iconForWorkClass("quadruped")).toBe("profile");
    expect(iconForWorkClass("marine")).toBe("globe");
    expect(iconForWorkClass("unknown")).toBeNull();
    expect(iconForWorkClass("")).toBeNull();
  });

  it("Icons page and SiteIcon look up by catalog id", () => {
    const page = readFileSync(join(here, "../pages/Icons.tsx"), "utf8");
    const component = readFileSync(
      join(here, "../components/SiteIcon.tsx"),
      "utf8"
    );
    const app = readFileSync(join(here, "../App.tsx"), "utf8");
    expect(page).toMatch(/SITE_ICON_CATALOG/);
    expect(page).toMatch(/<SiteIcon/);
    expect(page).toMatch(/id=\{entry\.id\}/);
    expect(page).toMatch(/KARE_FACE/);
    expect(page).not.toMatch(/Apollo|Hunter\.io|SIGNAL/);
    expect(component).toMatch(/siteIconMap\(id\)/);
    expect(app).toMatch(/path="\/icons"/);
    expect(app).toMatch(/path="\/icon-review"/);
  });

  it("landing doors and MATCH tiles import SiteIcon", () => {
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    const match = readFileSync(
      join(here, "../components/EmployerMatchWorkspace.tsx"),
      "utf8"
    );
    expect(landing).toMatch(/SiteIcon/);
    expect(landing).toMatch(/id="truck"/);
    expect(landing).toMatch(/id="handshake"/);
    expect(landing).toMatch(/KARE_FACE/);
    expect(match).toMatch(/iconForWorkClass/);
    expect(match).toMatch(/WorkClassIcon/);
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    expect(workspace).toMatch(/WorkClassIcon/);
    const handshake: SiteIconId = "handshake";
    expect(siteIconMap(handshake).length).toBe(24);
  });
});
