/**
 * Central Sales Email Generator for ReadyForRobots.
 * Powered by Phelan — Robot Job Analyst at ReadyForRobots.
 * Explains recruitment and placement infrastructure for robotic labor before pitching.
 */

export type ExecutiveEmailOpts = {
  companyName: string;
  dmName?: string;
  robotTypes?: string[];
  taskType?: string;
  senderMode?: "cal" | "bob" | "ai" | "phelan";
};

export function buildPhelanExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  const rawName = (opts.dmName || "").trim();
  const firstName = rawName ? rawName.split(" ")[0] : "";
  const company = opts.companyName.trim();
  const robotJob = opts.taskType || opts.robotTypes?.[0] || "facility automation";

  const greeting = firstName ? `Hi ${firstName},` : `Hi Operations Team,`;
  const subject = `Robot job match & qualified labor review for ${company}`;

  const body = `${greeting}

I’m Phelan, a Robot Job Analyst at ReadyForRobots. We evaluate physical task requirements to match robots to operational jobs.

We identified potential robotic labor fits within ${company}, specifically around **${robotJob}**.

If helpful, I can send over our shortlist of qualified robot options for your team to review.

Best regards,

Phelan
Robot Job Analyst | ReadyForRobots
phelan@readyforrobots.com
readyforrobots.com`;

  return { subject, body };
}

export function buildSalesAiExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  return buildPhelanExecutiveEmail(opts);
}

export function buildCalSalesEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  return buildPhelanExecutiveEmail(opts);
}

export function buildBobExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  return buildPhelanExecutiveEmail(opts);
}

