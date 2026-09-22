/**
 * Central Sales Email Generator for ReadyForRobots.
 * Supports both Cal (Sales & Deployment Advisor) and Bob Christopher (President).
 * Zero internal engine names (no SIGNAL, no FIND).
 */

export type ExecutiveEmailOpts = {
  companyName: string;
  dmName?: string;
  robotTypes?: string[];
  taskType?: string;
  senderMode?: "cal" | "bob";
};

export function buildCalSalesEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  const rawName = (opts.dmName || "").trim();
  const firstName = rawName ? rawName.split(" ")[0] : "";
  const company = opts.companyName.trim();
  const companyPossessive = company.endsWith("s") ? `${company}’` : `${company}’s`;

  const greeting = firstName ? `Hi ${firstName},` : `Dear ${company} Operations Team,`;
  const subject = `Task feasibility & robotics evaluation for ${company}`;

  const body = `${greeting}

I'm Cal, Sales & Deployment Advisor at ReadyForRobots. We work with enterprise operations leaders to evaluate physical task feasibility, payload/throughput constraints, and commercial robotics options before vendor PoCs.

When evaluating automation for ${companyPossessive} facilities, the hardest part isn't choosing a robot—it's verifying whether the specific physical task (cell geometry, payload limits, cycle time) is truly ready for automation.

Instead of relying on vendor brochure claims, ReadyForRobots provides independent engineering evaluations, 3D cell simulations, and turnkey commercial quotes (CapEx and RaaS financing).

We've put together a preliminary task-feasibility summary for ${company}. If you're exploring automation options for your sites this year, I'd be glad to send over the evaluation.

Would you be open to a brief review of the feasibility and ROI summary for your facilities?

Best regards,

Cal
Sales & Deployment Advisor | ReadyForRobots
cal@readyforrobots.com
https://readyforrobots.com`;

  return { subject, body };
}

export function buildBobExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  if (opts.senderMode === "cal") {
    return buildCalSalesEmail(opts);
  }

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

