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
  const shortlistUrl = `https://readyforrobots.com/pipeline?company=${encodeURIComponent(company)}`;

  const greeting = firstName ? `Hi ${firstName},` : `Hi Operations Team,`;
  const subject = `Robot job matches & feasibility review for ${company}`;

  const body = `${greeting}

I’m Phelan, a Robot Job Analyst at ReadyForRobots. We evaluate physical task requirements to match qualified robots to operational jobs.

For ${company}'s **${robotJob}** job, we identified a shortlist of qualified robot matches based on physical task requirements—matching payload capacity, cell reach, operating environment, and pre-trained task models.

You can review your shortlisted robot matches here:
${shortlistUrl}

**Next Steps:**
Once you've reviewed the matches, we can run a 3D cell-feasibility simulation to verify physical fit and provide a turnkey pilot proposal.

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

