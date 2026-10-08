/** Phelan intro to a robot company. Blanks stay blanks. Not FIND. */

export const OEM_INTRO_BLANK = "_______";
export const OEM_INTRO_PAY_BLANK = "______";
export const OEM_INTRO_TERM_BLANK = "_____________ months/years";

const EMPTY_CONTACT = /not named|hunter\.io found no|will not invent/i;
const INVENTED_LEAD = /^operational lead\b/i;

function clean(value: unknown, limit = 360): string {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) return "";
  return text.length <= limit ? text : `${text.slice(0, limit - 1).trimEnd()}…`;
}

function named(value: unknown): string {
  const text = clean(value, 240);
  if (!text || EMPTY_CONTACT.test(text) || INVENTED_LEAD.test(text)) return "";
  return text;
}

function firstName(value: unknown): string {
  const text = named(value);
  return text ? text.split(" ")[0] : "";
}

function clause(value: unknown): string {
  const text = named(value);
  return text.replace(/[.,;:]+$/g, "");
}

function pay(value: unknown): string {
  let text = clean(value, 40);
  if (text.startsWith("$")) text = text.slice(1).trim();
  return /\d/.test(text) ? text : "";
}

export function composeEmployerNeedIntro(opts: {
  contactName?: string | null;
  announcedNeed?: string | null;
  automationTasks?: string | null;
  skills?: string | null;
  capabilities?: string | null;
}): string {
  const hi = firstName(opts.contactName) || OEM_INTRO_BLANK;
  const need = clause(opts.announcedNeed) || OEM_INTRO_BLANK;
  let tasks = clause(opts.automationTasks) || OEM_INTRO_BLANK;
  if (tasks.toLowerCase() === need.toLowerCase()) tasks = OEM_INTRO_BLANK;
  const skill = clause(opts.skills) || OEM_INTRO_BLANK;
  const caps = clause(opts.capabilities) || OEM_INTRO_BLANK;
  return [
    `Hi ${hi}, nice to meet you. My name is Phelan, I am a robot coordinator for ReadyForRobots where I help find robots for automation jobs. I noticed you announced the need for ${need} to help with ${tasks} automation tasks at your company. I understand the task requires robots with ${skill} skills and capabilities of ${caps}. On that note I found a few robots that match these requirements I would like to share with you. May I send them to you for review? Thanks and look forward to learning more.`,
    "",
    "Phelan.",
  ].join("\n");
}

export function composeRobotCompanyIntro(opts: {
  contactName?: string | null;
  robotName?: string | null;
  title?: string | null;
  employer?: string | null;
  locality?: string | null;
  monthlyComp?: string | null;
  duration?: string | null;
  requirements?: string | null;
  decisionMakerName?: string | null;
}): string {
  const hi = firstName(opts.contactName) || OEM_INTRO_BLANK;
  const robot = named(opts.robotName) || OEM_INTRO_BLANK;
  const company = named(opts.employer);
  const workTitle = clean(opts.title, 240);
  const place = clean(opts.locality, 160);
  let work = workTitle;
  if (workTitle && company && place) work = `${workTitle} at ${company} in ${place}`;
  else if (workTitle && company) work = `${workTitle} at ${company}`;
  else if (!workTitle && company) work = `work at ${company}`;
  work = work || OEM_INTRO_BLANK;
  const monthly = pay(opts.monthlyComp) || OEM_INTRO_PAY_BLANK;
  const term = clean(opts.duration, 80) || OEM_INTRO_TERM_BLANK;
  const reqs = clean(opts.requirements, 360) || OEM_INTRO_BLANK;
  const person = firstName(opts.decisionMakerName);
  const callWith =
    person && company ? `${person} at ${company}` : company || person || OEM_INTRO_BLANK;
  return [
    `Hi ${hi}, nice to meet you. My name is Phelan and I am a robot coordinator for ReadyForRobots. My job is to help identify and place robots into robot automation jobs. On that note I found a few job opportunities for your ${robot} robot that I would like to discuss with you. The job is ${work} with an expected comp level of $${monthly} per month for ${term}. The job requirements of ${reqs} match up with your ${robot} robot(s). If interested in the job I can arrange a call with ${callWith} to discuss their requirements and how your robots are an ideal match. Let me know you are interested and available for a quick chat on the job for more specifics. Thanks and look forward to speaking with you.`,
    "",
    "Phelan.",
  ].join("\n");
}
