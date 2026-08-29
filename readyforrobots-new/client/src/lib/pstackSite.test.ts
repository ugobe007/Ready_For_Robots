import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  CRITIC_GATES,
  CRITIC_HELDOUT_FIND_URLS,
  JOBS_MATCHER_SOURCE,
  PSTACK_CHROME_LEAD,
  PSTACK_CHROME_TITLE,
  PSTACK_CRM_WALL_REQUIRED,
  PSTACK_CUSTOMER_CHAT_FORBIDDEN,
  PSTACK_ROLE_IDS,
  PSTACK_ROLES,
  criticGateIds,
  criticHeldoutFindUrls,
  crmWallRequired,
  isMatcherTheJobSource,
  jobsMatcherPath,
  refuseSiteAgent,
  siteAgentAsk,
} from "./pstackSite";
import { jobsCrmOpenHref } from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("pstackSite protocol", () => {
  it("owns How / Act / Critic and keeps the matcher as the job source", () => {
    expect(PSTACK_ROLE_IDS).toEqual(["how", "act", "critic"]);
    expect(PSTACK_ROLES.map(role => role.id)).toEqual(["how", "act", "critic"]);
    expect(isMatcherTheJobSource()).toBe(true);
    expect(JOBS_MATCHER_SOURCE).toEqual({
      kind: "matcher",
      method: "POST",
      path: "/api/robot-job-match",
      owner: "app/services/robot_job_capability_match.py",
    });
    expect(jobsMatcherPath()).toBe("POST /api/robot-job-match");
    expect(PSTACK_CHROME_LEAD).toMatch(/robot ontology/);
    expect(PSTACK_CHROME_LEAD).toMatch(/POST \/api\/robot-job-match/);
    expect(PSTACK_CHROME_LEAD).not.toMatch(/AI powered/i);
    expect(PSTACK_CHROME_TITLE).toBe("How this site finds work");
  });

  it("critic gates cover FIND, Job Cards, the CRM wall, and the matcher", () => {
    expect(criticGateIds()).toEqual([
      "find",
      "find_abort",
      "find_identity",
      "crm_leftover",
      "job_cards",
      "wall",
      "matcher",
      "oem_extract",
      "class_picker",
      "healthcare_class",
    ]);
    expect(CRITIC_GATES.find(gate => gate.id === "class_picker")?.fail).toMatch(/no-op/);
    expect(CRITIC_GATES.find(gate => gate.id === "find")?.prove).toBe("FIND is /");
    expect(CRITIC_GATES.find(gate => gate.id === "find")?.fail).toMatch(/experiment/);
    expect(CRITIC_GATES.find(gate => gate.id === "oem_extract")?.fail).toMatch(/chrome/);
    expect(CRITIC_GATES.find(gate => gate.id === "healthcare_class")?.fail).toMatch(/humanoid/);
    expect(criticHeldoutFindUrls()).toEqual([...CRITIC_HELDOUT_FIND_URLS]);
    expect(CRITIC_HELDOUT_FIND_URLS).toContain("https://www.xpeng.com/");
    expect(CRITIC_HELDOUT_FIND_URLS).toContain("https://www.greenfieldincorporated.com/");
    expect(CRITIC_HELDOUT_FIND_URLS).toContain("https://www.organifarms.de/");
    expect(CRITIC_HELDOUT_FIND_URLS).toContain("https://www.diligentrobots.com/");
    expect(crmWallRequired()).toBe(true);
    expect(PSTACK_CRM_WALL_REQUIRED).toBe(true);
    expect(jobsCrmOpenHref(false)).toMatch(/\/signup\?/);
    expect(jobsCrmOpenHref(false)).toMatch(/src=jobs_activate/);
    expect(jobsCrmOpenHref(true)).toBe("/pipeline?src=jobs_activate");
  });

  it("refuses Gateway, Hermes, matcher-as-LLM, and a customer pstack chat", () => {
    expect(PSTACK_CUSTOMER_CHAT_FORBIDDEN).toBe(true);
    expect(refuseSiteAgent("vercel_ai_gateway").ok).toBe(false);
    expect(refuseSiteAgent("hermes_ingest").detail).toMatch(/retired/);
    expect(refuseSiteAgent("matcher_as_llm").detail).toMatch(/robot_job_capability_match/);
    expect(refuseSiteAgent("customer_pstack_chat").ok).toBe(false);
    expect(siteAgentAsk({ role: "act", surface: "scout_chat" }).ok).toBe(false);
    const findAsk = siteAgentAsk({ role: "how", surface: "jobs_find" });
    expect(findAsk.ok).toBe(true);
    if (findAsk.ok) {
      expect(findAsk.jobSource.kind).toBe("matcher");
      expect(findAsk.role).toBe("how");
    }
  });

  it("does not call a model or treat the matcher as an LLM", () => {
    const protocol = readFileSync(join(here, "./pstackSite.ts"), "utf8");
    expect(protocol).not.toMatch(/openai/i);
    expect(protocol).not.toMatch(/fetch\(/);
    expect(protocol).toMatch(/Do not call Vercel AI Gateway/);
    expect(protocol).not.toMatch(/chat\.completions/);
  });
});

describe("pstack site chrome", () => {
  it("renders on FIND and About, not as the CRM job source", () => {
    const chrome = readFileSync(join(here, "../components/JobsPstackProtocol.tsx"), "utf8");
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const about = readFileSync(join(here, "../pages/Intelligence.tsx"), "utf8");
    const desk = readFileSync(join(here, "../components/JobsCrmDesk.tsx"), "utf8");
    const scout = readFileSync(join(here, "../components/ScoutChat.tsx"), "utf8");
    const crm = readFileSync(join(here, "../pages/Crm.tsx"), "utf8");

    expect(chrome).toMatch(/aria-label="Jobs agent protocol"/);
    expect(chrome).toMatch(/PSTACK_ROLES/);
    expect(chrome).toMatch(/jobsMatcherPath/);
    expect(chrome).not.toMatch(/chat with pstack/i);
    expect(chrome).not.toMatch(/AI powered/i);

    expect(workspace).toMatch(/<JobsPstackProtocol/);
    expect(workspace).toMatch(/fetchRobotJobSearch/);
    expect(workspace).not.toMatch(/fetchRobotJobMatch/);
    expect(workspace).toMatch(/jobsCrmOpenHref/);

    expect(about).toMatch(/<JobsPstackProtocol aboutLink=\{false\}/);
    expect(about).toMatch(/id="jobs-protocol"|JobsPstackProtocol/);
    expect(about).not.toMatch(/\bSIGNAL\b/);

    expect(desk).not.toMatch(/JobsPstackProtocol/);
    expect(desk).not.toMatch(/robot-job-match/);
    expect(desk).toMatch(/jobsCrmOpenHref\(false, submissionId\)/);

    expect(scout).toMatch(/PSTACK_CUSTOMER_CHAT_FORBIDDEN/);
    expect(scout).not.toMatch(/ai-gateway/);
    expect(scout).not.toMatch(/generate-plan/);

    expect(crm).toMatch(/pstack_protocol\.py/);
    expect(crm).toMatch(/Do not retarget this POST to Vercel AI Gateway/);
  });
});
