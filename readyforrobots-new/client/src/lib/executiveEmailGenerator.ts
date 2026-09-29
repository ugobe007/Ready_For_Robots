/**
 * Central Sales Email Generator for ReadyForRobots.
 * Powered by ReadyForRobots AI Sales Advisor.
 * Explains recruitment and placement infrastructure for robotic labor before pitching.
 */

export type ExecutiveEmailOpts = {
  companyName: string;
  dmName?: string;
  robotTypes?: string[];
  taskType?: string;
  senderMode?: "cal" | "bob" | "ai";
};

export function buildSalesAiExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  const rawName = (opts.dmName || "").trim();
  const firstName = rawName ? rawName.split(" ")[0] : "";
  const company = opts.companyName.trim();
  const companyPossessive = company.endsWith("s") ? `${company}’` : `${company}’s`;

  const greeting = firstName ? `Hi ${firstName},` : `Dear ${company} Operations Leadership,`;
  const subject = `Robotic labor placement & task feasibility evaluation for ${company}`;

  const body = `${greeting}

I am the ReadyForRobots AI Sales Advisor. ReadyForRobots is recruitment and placement infrastructure for robotic labor. We evaluate physical task feasibility, cell constraints, payload/throughput requirements, and hardware capabilities to match qualified robotic labor directly to real, verified job openings at enterprise and industrial facilities.

When evaluating automation for ${companyPossessive} facilities, the critical first step isn't picking a robot—it's verifying whether the specific physical task is ready for automation and matching physical task requirements with qualified hardware.

Rather than relying on vendor brochure claims, ReadyForRobots provides enterprise operators with independent engineering task-feasibility evaluations, 3D cell simulations, and turnkey commercial proposals (CapEx and RaaS financing) with verified Robot Job Cards.

We have compiled a preliminary task-feasibility evaluation and qualified robot job cards tailored for ${companyPossessive} operations. If your team is evaluating upcoming facility automation options this year, I would be glad to share our analysis.

Would you be open to reviewing a brief task feasibility and robotic labor placement summary for your facilities?

Best regards,

ReadyForRobots AI Sales Advisor
Robotic Labor Recruitment & Placement Infrastructure
outreach@readyforrobots.com
https://readyforrobots.com`;

  return { subject, body };
}

export function buildCalSalesEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  return buildSalesAiExecutiveEmail(opts);
}

export function buildBobExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  return buildSalesAiExecutiveEmail(opts);
}

