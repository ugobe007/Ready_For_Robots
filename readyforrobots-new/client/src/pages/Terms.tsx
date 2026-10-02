import LegalDocument from "./LegalDocument";

const SECTIONS = [
  {
    title: "Agreement",
    body: [
      'These terms apply to readyforrobots.com and the ReadyForRobots Copilot in ChatGPT, operated by ReadyForRobots, Inc. ("ReadyForRobots," "we," "us"). By using the site or the Copilot, you agree to these terms and to the privacy policy at readyforrobots.com/privacy.',
    ],
  },
  {
    title: "What the service does",
    body: [
      "ReadyForRobots matches robots to described work and shows job information drawn from public sources. A job card is not an offer of employment, a signed contract, or a promise that a robot can perform the work.",
      "The Copilot can search buyer opportunities, suggest robot types, match a robot to jobs, and calculate a labor payback example from the numbers you provide. Those results are estimates for review, not a quote.",
    ],
  },
  {
    title: "Accounts and acceptable use",
    body: [
      "Some site features require an account. You are responsible for the activity under your login and for the accuracy of information you submit, including robot URLs and payback inputs.",
      "Do not use the site or the Copilot to break the law, interfere with the service, or misrepresent a robot, an employer, or a job.",
    ],
  },
  {
    title: "Payments",
    body: [
      "The Copilot does not take payment inside ChatGPT. If you choose a paid workspace or job activation, that purchase happens on readyforrobots.com. Card payments there are processed by Stripe. We do not store full card numbers on our servers.",
    ],
  },
  {
    title: "Changes and contact",
    body: [
      "We may update these terms by posting a revised version on this page with a new effective date.",
      "Questions: support@readyforrobots.com.",
    ],
  },
];

export default function Terms() {
  return (
    <LegalDocument
      eyebrow="Legal"
      title="Terms of Service"
      description="The rules for using ReadyForRobots and the Copilot."
      effectiveDate="October 2, 2026"
      sections={SECTIONS}
    />
  );
}
