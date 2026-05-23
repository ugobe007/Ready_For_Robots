/**
 * Admin dashboard snapshot — instant localStorage hydrate + server delta sync.
 */

import type { DailyBriefData } from "@/components/DailyBriefPanel";

export const ADMIN_SNAPSHOT_STORAGE_KEY = "rfr_admin_snapshot_v1";

export type AdminSnapshotSection = {
  updated_at?: string;
  data?: unknown;
};

export type AdminSnapshot = {
  version?: number;
  built_at?: string;
  sections?: Record<string, AdminSnapshotSection>;
};

export type AdminSectionName =
  | "daily_brief"
  | "cal"
  | "stats"
  | "scout"
  | "user_stats"
  | "workflow"
  | "activity"
  | "users"
  | "targets"
  | "analytics";

export const ADMIN_SECTION_ORDER: AdminSectionName[] = [
  "daily_brief",
  "cal",
  "stats",
  "scout",
  "user_stats",
  "workflow",
  "activity",
  "users",
  "targets",
  "analytics",
];

const HASH_FOREGROUND: Record<string, AdminSectionName[]> = {
  "cal-outreach": ["cal", "daily_brief"],
  "scout-automation": ["scout", "daily_brief"],
  workflow: ["workflow", "daily_brief"],
};

const DEFAULT_FOREGROUND: AdminSectionName[] = ["daily_brief", "cal"];

/** Sections to check for deltas after first paint — rest load in idle time. */
export function foregroundSectionsForHash(hash: string): AdminSectionName[] {
  const key = hash.replace(/^#/, "");
  return HASH_FOREGROUND[key] ?? DEFAULT_FOREGROUND;
}

export function deferredSectionsForHash(hash: string): AdminSectionName[] {
  const fg = new Set(foregroundSectionsForHash(hash));
  return ADMIN_SECTION_ORDER.filter((name) => !fg.has(name));
}

const HASH_SECTION_PRIORITY: Record<string, AdminSectionName[]> = {
  "cal-outreach": ["cal", "daily_brief", "stats", "scout", "user_stats", "workflow", "activity", "users", "targets", "analytics"],
  "scout-automation": ["scout", "cal", "daily_brief", "stats", "user_stats", "workflow", "activity", "users", "targets", "analytics"],
  workflow: ["workflow", "daily_brief", "cal", "stats", "scout", "user_stats", "activity", "users", "targets", "analytics"],
};

export function sectionOrderForHash(hash: string): AdminSectionName[] {
  const key = hash.replace(/^#/, "");
  return HASH_SECTION_PRIORITY[key] ?? ADMIN_SECTION_ORDER;
}

export function readLocalAdminSnapshot(): AdminSnapshot | null {
  try {
    const raw = localStorage.getItem(ADMIN_SNAPSHOT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AdminSnapshot;
    if (!parsed?.sections || typeof parsed.sections !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

export function writeLocalAdminSnapshot(snapshot: AdminSnapshot): void {
  try {
    localStorage.setItem(ADMIN_SNAPSHOT_STORAGE_KEY, JSON.stringify(snapshot));
  } catch {
    /* quota / private mode */
  }
}

export function mergeSectionIntoSnapshot(
  snapshot: AdminSnapshot,
  section: string,
  updatedAt: string,
  data: unknown,
): AdminSnapshot {
  return {
    version: snapshot.version ?? 1,
    built_at: new Date().toISOString(),
    sections: {
      ...(snapshot.sections ?? {}),
      [section]: { updated_at: updatedAt, data },
    },
  };
}

export function mergeServerSnapshot(local: AdminSnapshot | null, server: AdminSnapshot): AdminSnapshot {
  const merged: AdminSnapshot = {
    version: server.version ?? local?.version ?? 1,
    built_at: server.built_at ?? local?.built_at,
    sections: { ...(local?.sections ?? {}) },
  };
  for (const [name, entry] of Object.entries(server.sections ?? {})) {
    const localEntry = merged.sections?.[name];
    const localTs = localEntry?.updated_at ?? "";
    const serverTs = entry?.updated_at ?? "";
    if (!localEntry || serverTs >= localTs) {
      merged.sections = { ...merged.sections, [name]: entry };
    }
  }
  return merged;
}

export type AdminSnapshotApplied = {
  dailyBrief: DailyBriefData | null;
  calStatus: unknown;
  stats: unknown;
  scoutStatus: unknown;
  userStats: unknown;
  workflow: unknown;
  activity: unknown[];
  users: unknown[];
  targets: unknown;
  analytics: unknown;
};

export function snapshotToApplied(snapshot: AdminSnapshot | null): AdminSnapshotApplied {
  const s = snapshot?.sections ?? {};
  const activityData = s.activity?.data as { activity?: unknown[] } | undefined;
  const usersData = s.users?.data as { users?: unknown[] } | undefined;
  return {
    dailyBrief: (s.daily_brief?.data as DailyBriefData) ?? null,
    calStatus: s.cal?.data ?? null,
    stats: s.stats?.data ?? null,
    scoutStatus: s.scout?.data ?? null,
    userStats: s.user_stats?.data ?? null,
    workflow: s.workflow?.data ?? null,
    activity: activityData?.activity ?? (Array.isArray(s.activity?.data) ? s.activity.data as unknown[] : []),
    users: usersData?.users ?? [],
    targets: s.targets?.data ?? null,
    analytics: s.analytics?.data ?? null,
  };
}

export function sectionUpdatedAt(snapshot: AdminSnapshot | null, section: string): string | undefined {
  return snapshot?.sections?.[section]?.updated_at;
}

/** Pause between sequential section fetches so the server never gets a parallel storm. */
export function pause(ms = 80): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
