/**
 * /privacy — Privacy Policy (required for social sharing and compliance).
 */
import LegalDocument from "./LegalDocument";

const SECTIONS: { title: string; body: string[] }[] = [
  {
    title: "Overview",
    body: [
      'ReadyForRobots, Inc. ("ReadyForRobots," "we," "us") operates readyforrobots.com and related services that help robotics sales teams discover buyers, score market signals, and prepare outreach.',
      "This Privacy Policy explains what information we collect, how we use it, and the choices you have. By using our site or services, you agree to this policy.",
    ],
  },
  {
    title: "Information we collect",
    body: [
      "Account information: name, work email, company, and credentials you provide when you sign up or update your profile.",
      "Usage data: pages viewed, features used, pipeline searches, and interaction with Cal recommendations — collected via logs and analytics to improve the product.",
      "Communications: messages you send through our platform, newsletter subscriptions, and support requests.",
      "Payment data: billing details are processed by our payment provider (Stripe). We do not store full card numbers on our servers.",
      "Public market signals: we aggregate and score publicly available business signals (filings, job posts, press, permits, etc.) to surface sales opportunities. This data is derived from public sources, not private consumer data.",
    ],
  },
  {
    title: "How we use information",
    body: [
      "Provide and improve ReadyForRobots — pipeline scoring, Cal recommendations, outreach drafts, and integrations.",
      "Authenticate users and secure accounts.",
      "Send product updates, newsletters, and transactional email (you can unsubscribe from marketing email at any time).",
      "Analyze usage to fix bugs, measure performance, and develop new features.",
      "Comply with law and enforce our terms.",
    ],
  },
  {
    title: "Third-party integrations",
    body: [
      "LinkedIn: optional OAuth connects your LinkedIn account for sharing pipeline content. Company page posts use the organizational entity URN format urn:li:organization:{company_id} as required by LinkedIn's Community Management API. Ready For Robots company page URN: urn:li:organization:114404417.",
      "HubSpot, Google Calendar, Stripe, Resend, and other providers process data according to their own privacy policies when you enable those integrations.",
    ],
  },
  {
    title: "Sharing and disclosure",
    body: [
      "We do not sell your personal information.",
      "We share data with service providers who help us operate the platform — hosting (Vercel, Fly.io), database (Supabase), email (Resend), payments (Stripe), and analytics — under contracts that limit their use to providing services to us.",
      "We may disclose information if required by law, to protect rights and safety, or in connection with a merger or acquisition.",
      "Pipeline and lead data you save may be visible to other members of your organization account, per your workspace settings.",
    ],
  },
  {
    title: "Cookies and tracking",
    body: [
      "We use cookies and similar technologies for authentication, session management, and basic analytics.",
      "You can control cookies through your browser settings. Disabling cookies may limit some features (e.g. staying signed in).",
    ],
  },
  {
    title: "Data retention",
    body: [
      "We retain account and usage data while your account is active and for a reasonable period afterward for backup, audit, and legal purposes.",
      "You may request deletion of your account by contacting support@readyforrobots.com.",
    ],
  },
  {
    title: "Security",
    body: [
      "We use industry-standard measures — encryption in transit (HTTPS), access controls, and secure infrastructure providers — to protect your data.",
      "No method of transmission or storage is 100% secure. Report concerns to support@readyforrobots.com.",
    ],
  },
  {
    title: "Your rights",
    body: [
      "Depending on your location, you may have rights to access, correct, delete, or export personal data we hold about you.",
      "California residents: we do not sell personal information as defined under the CCPA.",
      "EEA/UK residents: you may have additional rights under GDPR. Contact us to exercise them.",
    ],
  },
  {
    title: "Children",
    body: [
      "ReadyForRobots is a business-to-business service. We do not knowingly collect information from anyone under 16.",
    ],
  },
  {
    title: "Changes",
    body: [
      "We may update this policy from time to time. We will post the revised version on this page with an updated effective date.",
    ],
  },
  {
    title: "Contact",
    body: [
      "Questions about this policy: support@readyforrobots.com",
      "ReadyForRobots · readyforrobots.com",
    ],
  },
];

export default function Privacy() {
  return (
    <LegalDocument
      eyebrow="Legal"
      title="Privacy Policy"
      description="How ReadyForRobots collects, uses, and protects your information."
      effectiveDate="June 16, 2026"
      sections={SECTIONS}
    />
  );
}
