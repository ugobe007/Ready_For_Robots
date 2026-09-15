/**
 * Central Executive Sales Email Generator
 * Standardized across all sales leads, CRM desks, pipeline cards, and admin panels.
 */

export type ExecutiveEmailOpts = {
  companyName: string;
  dmName?: string;
  robotTypes?: string[];
};

export function buildBobExecutiveEmail(opts: ExecutiveEmailOpts): { subject: string; body: string } {
  const name = opts.dmName ? opts.dmName.split(" ")[0] : "there";
  const company = opts.companyName.trim();
  const companyPossessive = company.endsWith("s") ? `${company}’` : `${company}’s`;

  const subject = `Robotics feasibility at ${company}?`;
  const body = `Dear ${name},

Nice to meet you.

I am with ReadyForRobots, we provide independent, vendor-neutral feasibility benchmarks comparing leading commercial platforms across duty cycles, floor navigation, and real-world payback targets.

I’m reaching out because we’ve been following ${companyPossessive} growth and operational scale. In commercial robotics today, we see an interesting pattern: market demand for automation is high, but getting from an impressive demonstration to a scalable deployment in real facility environments is much harder than vendors acknowledge.

Having spent my career in robotics—leading teams at Panasonic, RichTech Robotics and Anybots—I founded ReadyForRobots to help enterprise operators evaluate the noise. If you’re currently evaluating automation options or planning for upcoming operational loads, I’d be glad to share our latest 2-page benchmark report.

Either way, I’d be curious to hear how your team is thinking about robotics feasibility across your facilities right now.

Best regards,

Bob

Bob Christopher
President | ReadyForRobots
bob@readyforrobots.com
https://readyforrobots.com/robot-ready`;

  return { subject, body };
}
