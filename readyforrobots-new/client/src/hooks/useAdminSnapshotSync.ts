import { useCallback, useState } from "react";
import {
  type AdminSectionName,
  type AdminSnapshot,
  mergeSectionIntoSnapshot,
  mergeServerSnapshot,
  pause,
  readLocalAdminSnapshot,
  sectionOrderForHash,
  sectionUpdatedAt,
  writeLocalAdminSnapshot,
} from "@/lib/adminSnapshot";

type AdminFetch = (path: string, init?: RequestInit) => Promise<Response>;

export function useAdminSnapshotSync(
  adminFetch: AdminFetch,
  opts: {
    sessionToken?: string;
    timeRange: string;
    onSection: (section: AdminSectionName, data: unknown) => void;
    onSnapshotMerged: (snapshot: AdminSnapshot) => void;
    onSyncComplete?: () => void;
  },
) {
  const { sessionToken, timeRange, onSection, onSnapshotMerged, onSyncComplete } = opts;
  const [syncingSection, setSyncingSection] = useState<string | null>(null);

  const refreshSection = useCallback(async (section: AdminSectionName, force = false) => {
    const current = readLocalAdminSnapshot() ?? { sections: {} };
    const since = sectionUpdatedAt(current, section) ?? "";
    const params = new URLSearchParams();
    if (force || !since) {
      params.set("refresh", "1");
    } else {
      params.set("since", since);
    }
    if (section === "analytics") {
      params.set("analytics_range", timeRange);
    }

    let res = await adminFetch(`/api/admin/snapshot/section/${section}?${params.toString()}`);
    if (res.status === 304) return;
    if (res.status === 503 && since) {
      res = await adminFetch(
        `/api/admin/snapshot/section/${section}?refresh=1&analytics_range=${encodeURIComponent(timeRange)}`,
      );
    }
    if (!res.ok) return;

    const patch = await res.json() as { updated_at?: string; data?: unknown };
    if (!patch.updated_at) return;

    const next = mergeSectionIntoSnapshot(current, section, patch.updated_at, patch.data);
    writeLocalAdminSnapshot(next);
    onSnapshotMerged(next);
    onSection(section, patch.data);
  }, [adminFetch, onSection, onSnapshotMerged, timeRange]);

  const sync = useCallback(async () => {
    if (!sessionToken) return;

    try {
      const snapRes = await adminFetch("/api/admin/snapshot");
      if (snapRes.ok) {
        const server = await snapRes.json() as AdminSnapshot;
        const merged = mergeServerSnapshot(readLocalAdminSnapshot(), server);
        writeLocalAdminSnapshot(merged);
        onSnapshotMerged(merged);
      }
    } catch { /* cached UI remains */ }

    const order = sectionOrderForHash(window.location.hash.slice(1));
    for (const section of order) {
      setSyncingSection(section);
      const since = sectionUpdatedAt(readLocalAdminSnapshot(), section);
      await refreshSection(section, !since);
      await pause(80);
    }
    setSyncingSection(null);
    onSyncComplete?.();
  }, [adminFetch, onSnapshotMerged, onSyncComplete, refreshSection, sessionToken]);

  return { syncingSection, sync, refreshSection };
}
