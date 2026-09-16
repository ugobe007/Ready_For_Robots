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

  const subject = `Robotics task matching for ${company}?`;
  const body = `Dear ${name},

Nice to meet you.

I am with ReadyForRobots. We help enterprise operators evaluate commercial robotics—matching specific robot models to your exact job requirements, facility constraints, and operational timing, and helping structure vendor PoCs when you're ready.

I’m reaching out because we’ve been following ${companyPossessive} growth and operational scale. In commercial robotics today, market demand is high, but finding the right robot model for a specific task—and navigating vendor claims, integration timelines, and PoC requirements—is much harder than vendors acknowledge.

Having spent my career in robotics—leading teams at Panasonic, RichTech Robotics, and Anybots—I founded ReadyForRobots to help operators cut through the noise. Whether you're early in planning, evaluating budget timing, or looking at specific tasks, we help you identify which models match your job requirements and coordinate vendor PoCs when the time is right.

If you’re currently thinking about automation or exploring upcoming facility needs, I’d be glad to share a task-matching evaluation for ${company}.

Either way, I’d be curious to hear how your team is thinking about robotics across your facilities right now.

Best regards,

Bob

Bob Christopher
President | ReadyForRobots
bob@readyforrobots.com
https://readyforrobots.com/robot-ready`;

  return { subject, body };
}

