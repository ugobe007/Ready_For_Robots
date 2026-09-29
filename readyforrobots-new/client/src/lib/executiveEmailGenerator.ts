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

I’m Phelan, a Robot Job Analyst at ReadyForRobots.

We match robots to jobs—and jobs to robots.

We’ve identified work within ${company} that may be a good fit for robotic labor.

ReadyForRobots qualifies and matches robots to specific jobs based on the physical requirements of the task, robot capabilities, operating environment, and the models and training required to perform the work.

For your **${robotJob}** job, we’ve identified a shortlist of qualified robot matches for your review.

Once you’ve had a chance to review the matches, let’s schedule a short call to discuss your job requirements in more detail and determine which robots are best suited for the work.

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

