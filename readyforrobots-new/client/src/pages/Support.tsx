import LegalDocument from "./LegalDocument";

const SECTIONS = [
  {
    title: "Contact",
    body: [
      "Email support@readyforrobots.com. Include the page or Copilot prompt you used, the robot or job URL if you have one, and what you expected to see.",
      "We read support mail on business days. This page does not promise a response time.",
    ],
  },
  {
    title: "ReadyForRobots Copilot",
    body: [
      "The Copilot is the ChatGPT plugin that finds jobs for a robot, suggests robots for described work, and calculates a labor payback example. It uses the production service at ready-2-robot.fly.dev.",
      "If a result looks wrong, send the prompt and the result to support@readyforrobots.com. Do not send passwords or card numbers.",
    ],
  },
  {
    title: "The website",
    body: [
      "Job search starts at readyforrobots.com. Account, workspace, and billing questions can go to the same support address.",
      "Paid workspace or job activation, when you choose it, is completed on readyforrobots.com. The Copilot does not charge you inside ChatGPT.",
    ],
  },
  {
    title: "Policies",
    body: [
      "Privacy: readyforrobots.com/privacy. Terms: readyforrobots.com/terms.",
    ],
  },
];

export default function Support() {
  return (
    <LegalDocument
      eyebrow="Help"
      title="Support"
      description="How to reach ReadyForRobots about the site or the Copilot."
      effectiveDate="October 2, 2026"
      sections={SECTIONS}
    />
  );
}
