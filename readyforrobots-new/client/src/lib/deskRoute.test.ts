import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("editorial desk routes", () => {
  it("sends pipeline, crm, and integrations to the desk", () => {
    const app = readFileSync(join(here, "../App.tsx"), "utf8");
    expect(app).toMatch(/path="\/desk"/);
    expect(app).toMatch(/path="\/pipeline" component=\{DeskRedirect\}/);
    expect(app).toMatch(/path="\/crm" component=\{DeskRedirect\}/);
    expect(app).toMatch(
      /path="\/integrations" component=\{HubSpotSettingsRedirect\}/
    );
    const desk = readFileSync(join(here, "../pages/Desk.tsx"), "utf8");
    expect(desk).toMatch(/Sample data/);
    expect(desk).toMatch(/fetchKeptJobs/);
    expect(desk).toMatch(/desk_stage/);
    for (const stage of [
      "Saved",
      "Contacted",
      "Meeting",
      "Site assessment",
      "Pilot",
      "Won",
    ]) {
      expect(desk).toContain(stage);
    }
    expect(desk).toMatch(/Lost/);
  });
});
