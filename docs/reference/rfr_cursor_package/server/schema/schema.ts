import { bigint, int, mysqlEnum, mysqlTable, text, timestamp, varchar, json } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// ── SCOUT Persistence ──────────────────────────────────────────────────────────

/**
 * scoutSessions — one row per anonymous visitor (identified by browser fingerprint)
 * or per authenticated user. Stores their robot category, vertical, and territory
 * so SCOUT can greet them with context on return visits.
 */
export const scoutSessions = mysqlTable("scoutSessions", {
  id: int("id").autoincrement().primaryKey(),
  /** Browser fingerprint (localStorage UUID) — identifies anonymous visitors */
  fingerprint: varchar("fingerprint", { length: 64 }).notNull().unique(),
  /** Authenticated user ID if they've logged in */
  userId: int("userId"),
  /** Robot category chosen in the intro (amr, industrial, service, food, healthcare, partnerships, other) */
  robotCategory: varchar("robotCategory", { length: 32 }),
  /** Free-text vertical description (e.g. "warehouse AMRs for cold storage") */
  vertical: text("vertical"),
  /** Territory / region of interest */
  territory: varchar("territory", { length: 128 }),
  /** Company name if provided */
  companyName: varchar("companyName", { length: 256 }),
  /** Company URL if scanned */
  companyUrl: varchar("companyUrl", { length: 512 }),
  /** Number of conversations held */
  conversationCount: int("conversationCount").default(0).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  lastSeenAt: timestamp("lastSeenAt").defaultNow().onUpdateNow().notNull(),
});

export type ScoutSession = typeof scoutSessions.$inferSelect;
export type InsertScoutSession = typeof scoutSessions.$inferInsert;

/**
 * scoutMessages — full conversation history per session.
 * Enables SCOUT to resume context across page reloads and return visits.
 */
export const scoutMessages = mysqlTable("scoutMessages", {
  id: int("id").autoincrement().primaryKey(),
  sessionId: int("sessionId").notNull(),
  /** "scout" for SCOUT messages, "user" for visitor messages */
  role: mysqlEnum("role", ["scout", "user"]).notNull(),
  content: text("content").notNull(),
  /** Which skill was invoked to produce this message, if any */
  skillInvoked: varchar("skillInvoked", { length: 64 }),
  /** Structured skill output stored as JSON (prospect cards, partner cards, etc.) */
  skillData: json("skillData"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type ScoutMessage = typeof scoutMessages.$inferSelect;
export type InsertScoutMessage = typeof scoutMessages.$inferInsert;

/**
 * scoutProfiles — aggregated interest profile per session.
 * Tracks which companies, signals, and drafts the visitor has engaged with
 * so SCOUT can personalise future interactions.
 */
export const scoutProfiles = mysqlTable("scoutProfiles", {
  id: int("id").autoincrement().primaryKey(),
  sessionId: int("sessionId").notNull().unique(),
  /** JSON array of company URLs the visitor has scanned or viewed */
  companiesViewed: json("companiesViewed").$type<string[]>().default([]),
  /** JSON array of prospect/partner IDs the visitor approved outreach for */
  draftsApproved: json("draftsApproved").$type<string[]>().default([]),
  /** JSON array of signal types the visitor has engaged with */
  signalsSeen: json("signalsSeen").$type<string[]>().default([]),
  /** Free-text notes SCOUT has inferred about the visitor's needs */
  inferredNeeds: text("inferredNeeds"),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type ScoutProfile = typeof scoutProfiles.$inferSelect;
export type InsertScoutProfile = typeof scoutProfiles.$inferInsert;

/**
 * leads — captures name + email from the Results page lead capture modal.
 */
export const leads = mysqlTable("leads", {
  id: int("id").autoincrement().primaryKey(),
  name: text("name").notNull(),
  email: varchar("email", { length: 320 }).notNull(),
  companyUrl: varchar("company_url", { length: 512 }),
  source: varchar("source", { length: 64 }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type Lead = typeof leads.$inferSelect;
export type InsertLead = typeof leads.$inferInsert;

/**
 * pipelineOpportunities — one row per prospect or partner opportunity in the pipeline.
 * Stores the SCOUT Score breakdown, outreach timeline state, and pipeline mode.
 */
export const pipelineOpportunities = mysqlTable("pipelineOpportunities", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  /** Company name */
  companyName: varchar("companyName", { length: 256 }).notNull(),
  /** Company domain / URL */
  companyUrl: varchar("companyUrl", { length: 512 }),
  /** Industry vertical (e.g. 'Warehouse & Logistics') */
  industry: varchar("industry", { length: 128 }),
  /** Robot category tag (e.g. 'WAREHOUSE AMR') */
  robotCategory: varchar("robotCategory", { length: 64 }),
  /** Opportunity type: sales lead or partnership */
  opportunityType: mysqlEnum("opportunityType", ["sales_lead", "partnership"]).default("sales_lead").notNull(),
  /** The buying signal that triggered this opportunity */
  signal: text("signal"),
  /** Source where signal was detected */
  signalSource: varchar("signalSource", { length: 128 }),

  // ── SCOUT Score (0-100) ──────────────────────────────────────────────────
  /** Composite SCOUT Score 0-100 */
  scoutScore: int("scoutScore").default(0).notNull(),
  /** Tier 1: Readiness to buy (0-25) */
  scoreReadiness: int("scoreReadiness").default(0).notNull(),
  /** Tier 1: Well-defined use case (0-20) */
  scoreUseCase: int("scoreUseCase").default(0).notNull(),
  /** Tier 1: Achievable ROI (0-15) */
  scoreRoi: int("scoreRoi").default(0).notNull(),
  /** Tier 2: Size of deployment (0-15) */
  scoreDeploymentSize: int("scoreDeploymentSize").default(0).notNull(),
  /** Tier 2: Recognizable problem (0-15) */
  scoreRecognizableProblem: int("scoreRecognizableProblem").default(0).notNull(),
  /** Tier 2: Customer value / brand (0-10) */
  scoreCustomerValue: int("scoreCustomerValue").default(0).notNull(),
  /** JSON notes explaining each factor score */
  scoreNotes: json("scoreNotes").$type<Record<string, string>>().default({}),

  // ── Pipeline Mode ────────────────────────────────────────────────────────
  /** assisted = user approves before send; autopilot = SCOUT sends automatically */
  pipelineMode: mysqlEnum("pipelineMode", ["assisted", "autopilot"]).default("assisted").notNull(),

  // ── Outreach Timeline ────────────────────────────────────────────────────
  /** Current outreach stage */
  outreachStage: mysqlEnum("outreachStage", ["pending", "intro_scheduled", "intro_sent", "followup_sent", "linkedin_sent", "final_sent", "meeting_booked", "closed", "paused"]).default("pending").notNull(),
  /** When the intro email is scheduled to send (UTC ms) */
  introScheduledAt: bigint("introScheduledAt", { mode: "number" }),
  /** When the intro was actually sent */
  introSentAt: bigint("introSentAt", { mode: "number" }),
  /** When follow-up #1 was sent (2 days after intro if no reply) */
  followupSentAt: bigint("followupSentAt", { mode: "number" }),
  /** When LinkedIn touch was sent (5 days after intro if no reply) */
  linkedinSentAt: bigint("linkedinSentAt", { mode: "number" }),
  /** When final follow-up was sent (14 days after intro) */
  finalSentAt: bigint("finalSentAt", { mode: "number" }),
  /** When a meeting was booked */
  meetingBookedAt: bigint("meetingBookedAt", { mode: "number" }),

  // ── Contact ──────────────────────────────────────────────────────────────
  /** Inferred or provided contact email for outreach */
  contactEmail: varchar("contactEmail", { length: 320 }),

  // ── Status ───────────────────────────────────────────────────────────────
  status: mysqlEnum("status", ["active", "paused", "archived"]).default("active").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type PipelineOpportunity = typeof pipelineOpportunities.$inferSelect;
export type InsertPipelineOpportunity = typeof pipelineOpportunities.$inferInsert;

/**
 * userSettings — per-user SCOUT configuration.
 * Stores pipeline mode default, outreach persona, and sender identity.
 */
export const userSettings = mysqlTable("userSettings", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().unique(),
  /** Default pipeline mode for new opportunities */
  defaultPipelineMode: mysqlEnum("defaultPipelineMode", ["assisted", "autopilot"]).default("assisted").notNull(),
  /** Who SCOUT sends outreach as */
  outreachPersona: mysqlEnum("outreachPersona", ["on_behalf", "independent"]).default("on_behalf").notNull(),
  /** Company name to use in on-behalf persona */
  senderCompanyName: varchar("senderCompanyName", { length: 256 }),
  /** Sender name for on-behalf persona */
  senderName: varchar("senderName", { length: 128 }),
  /** Sender email for on-behalf persona */
  senderEmail: varchar("senderEmail", { length: 320 }),
  /** Sender title for on-behalf persona */
  senderTitle: varchar("senderTitle", { length: 128 }),
  /** Tone preference for outreach drafts */
  outreachTone: mysqlEnum("outreachTone", ["professional", "conversational", "direct"]).default("professional").notNull(),
  /** Robot categories this user sells (JSON array) */
  robotCategories: json("robotCategories").$type<string[]>().default([]),
  /** Target verticals (JSON array) */
  targetVerticals: json("targetVerticals").$type<string[]>().default([]),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type UserSettings = typeof userSettings.$inferSelect;
export type InsertUserSettings = typeof userSettings.$inferInsert;

/**
 * waitlistSignups — captures email + tier intent from the Pricing page.
 * Used to measure demand per tier and notify the owner of new signups.
 */
export const waitlistSignups = mysqlTable("waitlistSignups", {
  id: int("id").autoincrement().primaryKey(),
  name: text("name").notNull(),
  email: varchar("email", { length: 320 }).notNull(),
  /** Which pricing tier they expressed interest in */
  tier: mysqlEnum("tier", ["preview", "growth", "enterprise"]).notNull(),
  /** Robot category or company context if provided */
  robotCategory: varchar("robotCategory", { length: 128 }),
  companyUrl: varchar("companyUrl", { length: 512 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type WaitlistSignup = typeof waitlistSignups.$inferSelect;
export type InsertWaitlistSignup = typeof waitlistSignups.$inferInsert;
