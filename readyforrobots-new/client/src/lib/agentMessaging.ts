// Customer-facing outreach voice — written as the robot sales rep, not ReadyForRobots.
export const OUTREACH_CTA = "Worth a quick reply if you're the right person to explore this?";
export const OUTREACH_SIGNATURE = "Best,\n[Your name]";

/** @deprecated Use rep voice in body only — no platform intro line. */
export const OUTREACH_INTRO = "";

export const BUYER_SIGNAL_EXPLANATION =
  "I help ops teams narrow the robotics vendor field. We monitor public signals — hiring spikes, new facilities, CapEx notes, automation-related job posts — and flag accounts that look like they're entering a real evaluation, not just collecting brochures.";

// Admin-only Cal persona (internal tooling only — do not surface on user pages).
export const CAL_INTRO = "Hi — Cal from Ready For Robots.";
export const CAL_VENDOR_SHERPA_LINE =
  "Most robot companies are engineer-led, not sales-led. I act as a guide through trials and deployments — honest readouts, no theater.";
export const CAL_SIGNATURE = ["— Cal", "Ready For Robots"].join("\n");
