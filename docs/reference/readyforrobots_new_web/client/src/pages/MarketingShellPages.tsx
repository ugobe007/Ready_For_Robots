import SiteShell from "@/components/SiteShell";
import MarketingPageLayout from "@/components/MarketingPageLayout";
import type { ReactNode } from "react";

function mk(
  title: string,
  opts: {
    kicker?: string;
    subtitle?: string;
    children: ReactNode;
  }
) {
  return function Page() {
    return (
      <SiteShell>
        <MarketingPageLayout kicker={opts.kicker} title={title} subtitle={opts.subtitle}>
          {opts.children}
        </MarketingPageLayout>
      </SiteShell>
    );
  };
}

export const PipelineResultsPage = mk("Pipeline results", {
  kicker: "Product",
  subtitle: "Ranked lists and exports from your latest pipeline runs.",
  children: (
    <>
      <p>Pipeline run summaries, CSV export, and drill-downs will connect here.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/pipeline-results</code>
      </p>
    </>
  ),
});

export const PipelineHealthPage = mk("Pipeline health", {
  kicker: "Product",
  subtitle: "Quality and coverage metrics for your lead engine.",
  children: (
    <>
      <p>Health scores, source mix, and decay alerts will render in this layout.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/pipeline-health</code>
      </p>
    </>
  ),
});

export const CrmPage = mk("CRM", {
  kicker: "Product",
  subtitle: "Lightweight CRM built around signal context.",
  children: (
    <>
      <p>Accounts, stages, tasks, and notes tied to each lead&apos;s evidence trail.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/crm</code>
      </p>
    </>
  ),
});

export const AnalyticsPage = mk("Analytics", {
  kicker: "Product",
  subtitle: "Funnels, conversion, and signal mix over time.",
  children: (
    <>
      <p>Charts and tables from your workspace will use the shared chart primitives.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/analytics</code>
      </p>
    </>
  ),
});

export const MarketInsightsPage = mk("Market insights", {
  kicker: "Research",
  subtitle: "Vertical and macro views for planning outreach.",
  children: (
    <>
      <p>Curated insight pages and downloadable snapshots will live here.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/market-insights</code>
      </p>
    </>
  ),
});

export const PilotCalculatorPage = mk("Pilot calculator", {
  kicker: "Tools",
  subtitle: "Scope pilot economics and success criteria.",
  children: (
    <>
      <p>Pilot-specific assumptions and outputs will port here.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/pilot-calculator</code>
      </p>
    </>
  ),
});

export const NewsletterPage = mk("Newsletter", {
  kicker: "Stay close",
  subtitle: "Weekly signal digest and product updates.",
  children: (
    <>
      <p>Subscribe form and archive will connect to your existing provider.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/newsletter</code>
      </p>
    </>
  ),
});

export const LoginPage = mk("Sign in", {
  kicker: "Account",
  subtitle: "Access your workspace.",
  children: (
    <>
      <p>Supabase (or your current auth) sign-in will embed on this page.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/login</code>
      </p>
    </>
  ),
});

export const ProfilePage = mk("Profile", {
  kicker: "Account",
  subtitle: "Your preferences and organization.",
  children: (
    <>
      <p>User profile and workspace settings will mount here.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/profile</code>
      </p>
    </>
  ),
});

export const RobotCompaniesPage = mk("Robot companies", {
  kicker: "Directory",
  subtitle: "Vendor and OEM directory for partnership planning.",
  children: (
    <>
      <p>Directory views and filters from the legacy robot-companies page.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/robot-companies</code>
      </p>
    </>
  ),
});

export const RobotReadyPage = mk("Robot ready", {
  kicker: "Programs",
  subtitle: "Accounts qualified for robotics programs.",
  children: (
    <>
      <p>Program-specific lists and playbooks will use this layout.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/robot-ready</code>
      </p>
    </>
  ),
});

export const BriefPage = mk("Brief", {
  kicker: "Product",
  subtitle: "One-page account briefs for calls.",
  children: (
    <>
      <p>Printable / shareable brief templates will render here.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/brief</code>
      </p>
    </>
  ),
});

export const SocialPage = mk("Social", {
  kicker: "Product",
  subtitle: "Social proof and shareables.",
  children: (
    <>
      <p>Social integrations or link hub from the legacy social page.</p>
      <p className="text-sm text-gray-500 font-mono">
        Legacy route: <code>/social</code>
      </p>
    </>
  ),
});

