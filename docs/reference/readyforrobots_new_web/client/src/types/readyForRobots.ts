// =====================================================
// ReadyForRobots — Core Types
// =====================================================

// -----------------------------
// Autonomy Modes
// -----------------------------
export type AutonomyMode = "manual" | "assisted" | "auto";

// -----------------------------
// Activity Status Types
// -----------------------------
export type ActivityStatus =
  | "new_signal"
  | "draft_ready"
  | "outreach_sent"
  | "followup_sent"
  | "qualified"
  | "meeting_suggested"
  | "opportunity_created";

// -----------------------------
// Priority Levels
// -----------------------------
export type PriorityLevel = "low" | "medium" | "high";

// -----------------------------
// Activity Item (Core Object)
// -----------------------------
export type ActivityItem = {
  id: string;

  // Company Info
  companyName: string;
  industry: string;

  // Signal Info
  signalType: string; // e.g. Hiring, Expansion, Operational
  signalSummary: string;

  // System Insight
  robotUseCase: string; // e.g. warehouse robots, service robots
  recommendedAction: string;

  // State
  status: ActivityStatus;
  confidenceScore: number; // 0–100

  // Metadata
  createdAt: string;
};

// -----------------------------
// Next Best Action
// -----------------------------
export type NextAction = {
  id: string;
  label: string;
  companyName: string;
  priority: PriorityLevel;
};

// -----------------------------
// Daily Summary (Reports)
// -----------------------------
export type DailySummary = {
  signalsDetected: number;
  companiesQualified: number;
  outreachDraftsCreated: number;
  followupsSent: number;
  opportunitiesAdvanced: number;
};

// -----------------------------
// While You Were Away Log Item
// -----------------------------
export type ActivityLogItem = {
  id: string;
  description: string;
  timestamp: string;
};

// -----------------------------
// Extended Activity Detail (Future)
// -----------------------------
export type ActivityDetail = {
  activityId: string;

  // Reasoning
  whyThisCompany: string;
  whyNow: string;

  // Suggested Message
  outreachMessage?: string;

  // History
  history?: {
    action: string;
    timestamp: string;
  }[];
};
