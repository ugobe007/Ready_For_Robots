/**
 * scoutDb.ts — Database helpers for SCOUT persistence
 * Handles session upsert, message history, and profile tracking
 */
import { eq, desc } from "drizzle-orm";
import { getDb } from "./db";
import {
  scoutSessions,
  scoutMessages,
  scoutProfiles,
  type InsertScoutSession,
  type ScoutSession,
  type ScoutMessage,
  type ScoutProfile,
} from "../drizzle/schema";

// ── Session ────────────────────────────────────────────────────────────────────

/**
 * Get or create a SCOUT session by browser fingerprint.
 * Returns the session row and a boolean indicating if it's new.
 */
export async function upsertScoutSession(
  fingerprint: string,
  userId?: number
): Promise<{ session: ScoutSession; isNew: boolean }> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await db
    .select()
    .from(scoutSessions)
    .where(eq(scoutSessions.fingerprint, fingerprint))
    .limit(1);

  if (existing.length > 0) {
    // Update lastSeenAt and optionally link userId
    const updates: Partial<InsertScoutSession> = {};
    if (userId && !existing[0].userId) updates.userId = userId;

    if (Object.keys(updates).length > 0) {
      await db
        .update(scoutSessions)
        .set(updates)
        .where(eq(scoutSessions.fingerprint, fingerprint));
    }
    return { session: existing[0], isNew: false };
  }

  // Create new session
  await db.insert(scoutSessions).values({
    fingerprint,
    userId,
    conversationCount: 0,
  });

  const created = await db
    .select()
    .from(scoutSessions)
    .where(eq(scoutSessions.fingerprint, fingerprint))
    .limit(1);

  // Create empty profile for the new session
  await db.insert(scoutProfiles).values({ sessionId: created[0].id });

  return { session: created[0], isNew: true };
}

/**
 * Update a session's profile data (robot category, vertical, territory, company).
 */
export async function updateScoutSession(
  sessionId: number,
  updates: Partial<Pick<InsertScoutSession, "robotCategory" | "vertical" | "territory" | "companyName" | "companyUrl" | "conversationCount">>
): Promise<void> {
  const db = await getDb();
  if (!db) return;
  await db.update(scoutSessions).set(updates).where(eq(scoutSessions.id, sessionId));
}

// ── Messages ───────────────────────────────────────────────────────────────────

/**
 * Append a message to the conversation history for a session.
 */
export async function appendScoutMessage(
  sessionId: number,
  role: "scout" | "user",
  content: string,
  skillInvoked?: string,
  skillData?: unknown
): Promise<void> {
  const db = await getDb();
  if (!db) return;
  await db.insert(scoutMessages).values({
    sessionId,
    role,
    content,
    skillInvoked: skillInvoked ?? null,
    skillData: skillData ?? null,
  });
}

/**
 * Load the last N messages for a session (most recent first, then reversed for display).
 */
export async function getScoutHistory(
  sessionId: number,
  limit = 40
): Promise<ScoutMessage[]> {
  const db = await getDb();
  if (!db) return [];
  const rows = await db
    .select()
    .from(scoutMessages)
    .where(eq(scoutMessages.sessionId, sessionId))
    .orderBy(desc(scoutMessages.createdAt))
    .limit(limit);
  return rows.reverse();
}

// ── Profile ────────────────────────────────────────────────────────────────────

/**
 * Get the profile for a session.
 */
export async function getScoutProfile(sessionId: number): Promise<ScoutProfile | null> {
  const db = await getDb();
  if (!db) return null;
  const rows = await db
    .select()
    .from(scoutProfiles)
    .where(eq(scoutProfiles.sessionId, sessionId))
    .limit(1);
  return rows[0] ?? null;
}

/**
 * Add a company URL to the companiesViewed list.
 */
export async function trackCompanyViewed(sessionId: number, url: string): Promise<void> {
  const db = await getDb();
  if (!db) return;
  const profile = await getScoutProfile(sessionId);
  if (!profile) return;
  const current = (profile.companiesViewed as string[]) ?? [];
  if (!current.includes(url)) {
    await db
      .update(scoutProfiles)
      .set({ companiesViewed: [...current, url] })
      .where(eq(scoutProfiles.sessionId, sessionId));
  }
}

/**
 * Record that a draft was approved.
 */
export async function trackDraftApproved(sessionId: number, draftId: string): Promise<void> {
  const db = await getDb();
  if (!db) return;
  const profile = await getScoutProfile(sessionId);
  if (!profile) return;
  const current = (profile.draftsApproved as string[]) ?? [];
  if (!current.includes(draftId)) {
    await db
      .update(scoutProfiles)
      .set({ draftsApproved: [...current, draftId] })
      .where(eq(scoutProfiles.sessionId, sessionId));
  }
}

/**
 * Update SCOUT's inferred needs summary for a session.
 */
export async function updateInferredNeeds(sessionId: number, needs: string): Promise<void> {
  const db = await getDb();
  if (!db) return;
  await db
    .update(scoutProfiles)
    .set({ inferredNeeds: needs })
    .where(eq(scoutProfiles.sessionId, sessionId));
}
