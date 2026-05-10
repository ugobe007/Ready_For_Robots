// ReadyForRobots — Type Definitions
// Design: Clean Workflow / Elevated SaaS (Stripe/Linear aesthetic)
// Colors: Emerald (live/approved), Amber (pending), Blue (AI/system)

export type AutonomyMode = "manual" | "assisted" | "auto";

export type ActivityStatus =
  | "new_signal"
  | "draft_ready"
  | "followup_sent"
  | "qualified"
  | "meeting_suggested";

export type ActivityItem = {
  id: string;
  companyName: string;
  industry: string;
  signalType: string;
  signalSummary: string;
  robotUseCase: string;
  recommendedAction: string;
  status: ActivityStatus;
  confidenceScore: number;
  createdAt: string;
};

export type NextAction = {
  id: string;
  label: string;
  companyName: string;
  priority: "low" | "medium" | "high";
};

export type DailySummary = {
  signalsDetected: number;
  companiesQualified: number;
  outreachDraftsCreated: number;
  followupsSent: number;
  opportunitiesAdvanced: number;
};
