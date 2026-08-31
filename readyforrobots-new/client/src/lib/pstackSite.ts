/**
 * pstack on the Jobs site: role routing for site agents AND the release gate.
 *
 * How / Act / Critic merge authority lives in pstack/ + scripts/pstack_release.py.
 * Protocol chrome on `/` or Jobs CRM is not a pass. Do not put JOBS AGENT
 * PROTOCOL back on the desk.
 *
 * Jobs still come from ontology + POST /api/robot-job-match.
 * pstack does not pick employers, invent invoices, or chat with customers.
 * Job Cards may show a labeled robot-pay estimate.
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
  id:
    | "find"
    | "find_abort"
    | "find_identity"
    | "crm_leftover"
    | "job_cards"
    | "wall"
    | "matcher"
    | "oem_extract"
    | "class_picker"
    | "healthcare_class"
    | "ontology_industry_language"
    | "url_workflow";
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
    job: "Drive a real OEM URL. Fail abort-as-failed, leftover CRM, Diligent-as-humanoid, and skip-green.",
  },
] as const;

export const CRITIC_GATES: readonly CriticGate[] = [
  {
    id: "find",
    prove: "FIND is /",
    fail: "smoking /experiment as FIND",
  },
  {
    id: "find_abort",
    prove: "AbortError and Failed to fetch stay silent",
    fail: "self-abort FIND shown as Research failed / Failed to fetch",
  },
  {
    id: "find_identity",
    prove: "submitted URL is the identity key",
    fail: "Greenfield shown as another OEM / leftover robot",
  },
  {
    id: "crm_leftover",
    prove: "CRM after FIND B is B",
    fail: "strawberry robot leftover on a new URL",
  },
  {
    id: "job_cards",
    prove: "named employer, real work, labeled pay estimate",
    fail: "fake invoices or unlabeled employer quotes",
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
  {
    id: "oem_extract",
    prove: "unknown OEM picker is evidence-only",
    fail: "chrome names or another company's robot in the FIND picker",
  },
  {
    id: "class_picker",
    prove: "class-picker click starts robot-job-search and settles jobs or empty",
    fail: "Agriculture click silently no-ops or dumps empty CRM as the only outcome",
  },
  {
    id: "healthcare_class",
    prove: "Diligent/Moxi is healthcare; Healthcare tile exists; class search returns named employers",
    fail: "Diligent classified humanoid, empty humanoid copy, or missing Healthcare class tile",
  },
  {
    id: "ontology_industry_language",
    prove: "Industry work words live in the ontology and outrank humanoid morphology where R33 says so",
    fail: "hospital/hotel/mining/warehouse work words missing from ontology files",
  },
  {
    id: "url_workflow",
    prove: "FIND URL critic reports product range, named SKUs, and per-product capabilities",
    fail: "mixed OEM flattened, chrome-as-SKU, cleaning-drone-as-scrubber, or company-class dump",
  },
] as const;

export const CRITIC_HELDOUT_FIND_URLS = [
  "https://advanced.farm/",
  "https://bedrockrobotics.com/",
  "https://www.xpeng.com/",
  "https://www.aandkrobotics.com/",
  "https://www.avatarrobotics.com/",
  "https://www.agtonomy.com/",
  "https://www.greenfieldincorporated.com/",
  "https://www.organifarms.de/",
  "https://www.diligentrobots.com/",
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

export function criticHeldoutFindUrls(): string[] {
  return [...CRITIC_HELDOUT_FIND_URLS];
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
