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

export type NextAction = {
  id: string;
  label: string;
  companyName: string;
  priority: "low" | "medium" | "high";
  route?: string;
  entity_type?: string;
  entity_id?: string;
  score?: number;
  meta?: Record<string, unknown>;
};

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
  route?: string;
  entity_id?: string;
};

export type DailySummary = {
  signalsDetected: number;
  companiesQualified: number;
  outreachDraftsCreated: number;
  followupsSent: number;
  opportunitiesAdvanced: number;
  repliesReceived?: number;
  highlights?: NextAction[];
};
