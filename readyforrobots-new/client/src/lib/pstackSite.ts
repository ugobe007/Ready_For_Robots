/**
 * pstack on the Jobs site: role routing for site agents.
 *
 * Jobs still come from ontology + POST /api/robot-job-match.
 * pstack does not pick employers, invent rental dollars, or chat with customers.
 * Do not call Vercel AI Gateway. Do not resurrect Hermes ingest.
 */

export const PSTACK_ROLE_IDS = ["how", "act", "critic"] as const;
export type PstackRoleId = (typeof PSTACK_ROLE_IDS)[number];

export type PstackRole = {
  id: PstackRoleId;
  label: string;
  job: string;
};

export type JobsMatcherSource = {
  kind: "matcher";
  method: "POST";
  path: "/api/robot-job-match";
  owner: "app/services/robot_job_capability_match.py";
};

export type CriticGate = {
  id: "find" | "job_cards" | "wall" | "matcher";
  prove: string;
  fail: string;
};

export type SiteAgentRefusal =
  | "vercel_ai_gateway"
  | "hermes_ingest"
  | "matcher_as_llm"
  | "customer_pstack_chat"
  | "signal_hop"
  | "remove_crm_wall";

export const JOBS_MATCHER_SOURCE: JobsMatcherSource = {
  kind: "matcher",
  method: "POST",
  path: "/api/robot-job-match",
  owner: "app/services/robot_job_capability_match.py",
};

export const PSTACK_ROLES: readonly PstackRole[] = [
  {
    id: "how",
    label: "How",
    job: "Name the owner before anyone edits FIND, Job Cards, or CRM.",
  },
  {
    id: "act",
    label: "Act",
    job: "Change the Jobs path only. Keep the signup wall. Keep step 03 labeled CRM.",
  },
  {
    id: "critic",
    label: "Critic",
    job: "Prove FIND on /, named employers, the wall, and the matcher.",
  },
] as const;

export const CRITIC_GATES: readonly CriticGate[] = [
  {
    id: "find",
    prove: "FIND is /",
    fail: "smoking /experiment as FIND",
  },
  {
    id: "job_cards",
    prove: "named employer and real work",
    fail: "invented rental dollars",
  },
  {
    id: "wall",
    prove: "signup before the CRM desk",
    fail: "unsigned /pipeline?src=jobs_activate desk",
  },
  {
    id: "matcher",
    prove: "POST /api/robot-job-match",
    fail: "LLM as the job source",
  },
] as const;

export const PSTACK_CHROME_EYEBROW = "Jobs agent protocol";
export const PSTACK_CHROME_TITLE = "How this site finds work";
export const PSTACK_CHROME_LEAD =
  "Job Cards come from the robot ontology and POST /api/robot-job-match. That matcher is code. It is not a chat model.";
export const PSTACK_CHROME_FOOT =
  "Hermes is retired. Agents follow How, Act, and Critic. They do not invent rental dollars.";
export const PSTACK_ABOUT_HREF = "/intelligence#jobs-protocol";
export const PSTACK_CUSTOMER_CHAT_FORBIDDEN = true;
export const PSTACK_CRM_WALL_REQUIRED = true;

const FORBIDDEN: Record<SiteAgentRefusal, string> = {
  vercel_ai_gateway: "Do not call Vercel AI Gateway.",
  hermes_ingest: "Hermes ingest is retired.",
  matcher_as_llm: "Do not replace robot_job_capability_match.py with an LLM.",
  customer_pstack_chat: "pstack is not a customer chatbot.",
  signal_hop: "Do not hop Jobs traffic onto SIGNAL buyers.",
  remove_crm_wall: "Keep the signup wall in front of the CRM desk.",
};

export function jobsMatcherPath(): string {
  return `${JOBS_MATCHER_SOURCE.method} ${JOBS_MATCHER_SOURCE.path}`;
}

export function criticGateIds(): CriticGate["id"][] {
  return CRITIC_GATES.map(gate => gate.id);
}

export function crmWallRequired(): boolean {
  return PSTACK_CRM_WALL_REQUIRED;
}

export function refuseSiteAgent(reason: SiteAgentRefusal): { ok: false; reason: SiteAgentRefusal; detail: string } {
  return { ok: false, reason, detail: FORBIDDEN[reason] };
}

export function siteAgentAsk(input: {
  role: PstackRoleId;
  surface: "jobs_find" | "jobs_crm" | "crm_generate_plan" | "scout_chat";
}):
  | { ok: true; role: PstackRoleId; jobSource: JobsMatcherSource; gates: readonly CriticGate[] }
  | { ok: false; reason: SiteAgentRefusal; detail: string } {
  if (input.surface === "scout_chat") {
    return refuseSiteAgent("customer_pstack_chat");
  }
  if (input.role === "act" && input.surface === "crm_generate_plan") {
    return {
      ok: true,
      role: "act",
      jobSource: JOBS_MATCHER_SOURCE,
      gates: CRITIC_GATES,
    };
  }
  return {
    ok: true,
    role: input.role,
    jobSource: JOBS_MATCHER_SOURCE,
    gates: CRITIC_GATES,
  };
}

export function isMatcherTheJobSource(): boolean {
  return JOBS_MATCHER_SOURCE.kind === "matcher";
}
