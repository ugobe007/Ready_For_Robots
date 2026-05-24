import { useCallback, useRef, useState } from "react";
import {
  type AdminSectionName,
  type AdminSnapshot,
  deferredSectionsForHash,
  foregroundSectionsForHash,
  mergeSectionIntoSnapshot,
  mergeServerSnapshot,
  pause,
  readLocalAdminSnapshot,
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
  const deferStarted = useRef(false);
  const onSectionRef = useRef(onSection);
  const onSnapshotMergedRef = useRef(onSnapshotMerged);
  const onSyncCompleteRef = useRef(onSyncComplete);
  onSectionRef.current = onSection;
  onSnapshotMergedRef.current = onSnapshotMerged;
  onSyncCompleteRef.current = onSyncComplete;

  const refreshSection = useCallback(async (section: AdminSectionName, force = false) => {
    const current = readLocalAdminSnapshot() ?? { sections: {} };
    const since = sectionUpdatedAt(current, section) ?? "";
    const params = new URLSearchParams();
    if (force) {
      params.set("refresh", "1");
    } else if (since) {
      params.set("since", since);
    }
    if (section === "analytics") {
      params.set("analytics_range", timeRange);
    }

    const res = await adminFetch(`/api/admin/snapshot/section/${section}?${params.toString()}`);
    if (res.status === 304) return;
    if (!res.ok) return;

    const patch = await res.json() as { updated_at?: string; data?: unknown };
    if (!patch.updated_at) return;

    const next = mergeSectionIntoSnapshot(current, section, patch.updated_at, patch.data);
    writeLocalAdminSnapshot(next);
    onSnapshotMergedRef.current(next);
    onSectionRef.current(section, patch.data);
  }, [adminFetch, timeRange]);

  const syncSections = useCallback(async (sections: AdminSectionName[]) => {
    for (const section of sections) {
      setSyncingSection(section);
      await refreshSection(section, false);
      await pause(40);
    }
    setSyncingSection(null);
  }, [refreshSection]);

  const syncDeferred = useCallback(async () => {
    const deferred = deferredSectionsForHash(window.location.hash.slice(1));
    for (const section of deferred) {
      setSyncingSection(section);
      await refreshSection(section, false);
      await pause(60);
    }
    setSyncingSection(null);
  }, [refreshSection]);

  const sync = useCallback(async () => {
    if (!sessionToken) return;

    try {
      const snapRes = await adminFetch("/api/admin/snapshot");
      if (snapRes.ok) {
        const server = await snapRes.json() as AdminSnapshot;
        const merged = mergeServerSnapshot(readLocalAdminSnapshot(), server);
        writeLocalAdminSnapshot(merged);
        onSnapshotMergedRef.current(merged);
      }
    } catch { /* cached UI remains */ }

    onSyncCompleteRef.current?.();

    const foreground = foregroundSectionsForHash(window.location.hash.slice(1));
    await syncSections(foreground);

    if (deferStarted.current) return;
    deferStarted.current = true;
    const runDeferred = () => { void syncDeferred(); };
    if (typeof requestIdleCallback !== "undefined") {
      requestIdleCallback(runDeferred, { timeout: 5000 });
    } else {
      window.setTimeout(runDeferred, 500);
    }
  }, [adminFetch, sessionToken, syncDeferred, syncSections]);

  return { syncingSection, sync, refreshSection };
}
