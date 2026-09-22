/**
 * Central Executive Sales Email Generator
 * Standardized across all sales leads, CRM desks, pipeline cards, and admin panels.
 * Zero internal engine names (no SIGNAL, no Cal, no FIND).
 */

export type ExecutiveEmailOpts = {
  companyName: string;
  dmName?: string;
  robotTypes?: string[];
  taskType?: string;
};

export function buildBobExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  const rawName = (opts.dmName || "").trim();
  const firstName = rawName ? rawName.split(" ")[0] : "";
  const company = opts.companyName.trim();
  const companyPossessive = company.endsWith("s") ? `${company}’` : `${company}’s`;

  const greeting = firstName ? `Dear ${firstName},` : `Dear ${company} Operations Leadership,`;
  const subject = `Engineering task feasibility & robotics evaluation for ${company}`;

  const body = `${greeting}

My name is Bob Christopher, President of ReadyForRobots. I am reaching out regarding operational task feasibility and commercial robotics evaluation for ${companyPossessive} facilities.

In commercial robotics, evaluating whether a specific physical task can be reliably automated requires analyzing cell geometry, payload limits, throughput rates, and payback timelines before vendor commitments.

Rather than relying on vendor brochure claims, ReadyForRobots provides enterprise operators with independent engineering evaluations, 3D feasibility simulations, and turnkey commercial quotes (CapEx and RaaS).

We have compiled a preliminary task-feasibility framework tailored for ${companyPossessive} operations. If your team is evaluating upcoming facility automation or considering pilot programs this year, I would be glad to share our analysis.

Would you be open to reviewing a brief feasibility and ROI summary for your facilities?

Best regards,

Bob Christopher
President | ReadyForRobots
bob@readyforrobots.com
https://readyforrobots.com`;

  return { subject, body };
}

