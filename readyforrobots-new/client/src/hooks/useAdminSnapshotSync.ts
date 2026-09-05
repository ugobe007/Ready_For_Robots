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
  snapshotLooksEmpty,
  writeLocalAdminSnapshot,
} from "@/lib/adminSnapshot";

type AdminFetch = (path: string, init?: RequestInit) => Promise<Response>;

const SNAPSHOT_SECTION_RETRY_DELAY_MS = 500;
const SNAPSHOT_SECTION_COOLDOWN_MS = 45 * 1000;
const SNAPSHOT_SECTION_BREAKER_OPEN_MS = 45 * 1000;
const SNAPSHOT_SECTION_BREAKER_FAIL_STREAK = 3;

const isTransientSnapshotStatus = (status: number) =>
  [408, 429, 500, 502, 503, 504].includes(status);

const isTransientSnapshotError = (err: unknown) => {
  if (err instanceof DOMException && err.name === "AbortError") return true;
  if (err instanceof TypeError) return true;
  const msg = err instanceof Error ? err.message : String(err);
  return /network|failed to fetch|load failed|aborted|timeout/i.test(msg);
};

export function useAdminSnapshotSync(
  adminFetch: AdminFetch,
  opts: {
    sessionToken?: string;
    timeRange: string;
    onSection: (section: AdminSectionName, data: unknown) => void;
    onSnapshotMerged: (snapshot: AdminSnapshot) => void;
    onSyncComplete?: () => void;
  }
) {
  const {
    sessionToken,
    timeRange,
    onSection,
    onSnapshotMerged,
    onSyncComplete,
  } = opts;
  const [syncingSection, setSyncingSection] = useState<string | null>(null);
  const deferStarted = useRef(false);
  const onSectionRef = useRef(onSection);
  const onSnapshotMergedRef = useRef(onSnapshotMerged);
  const onSyncCompleteRef = useRef(onSyncComplete);
  const sectionInFlightRef = useRef<Map<AdminSectionName, Promise<void>>>(
    new Map()
  );
  const sectionCooldownUntilRef = useRef<Map<AdminSectionName, number>>(
    new Map()
  );
  const sectionBreakerOpenUntilRef = useRef<Map<AdminSectionName, number>>(
    new Map()
  );
  const sectionFailStreakRef = useRef<Map<AdminSectionName, number>>(new Map());
  const telemetryRef = useRef({
    attempts: 0,
    successes: 0,
    failures: 0,
    dedupes: 0,
    skips: 0,
    breakerOpenCount: 0,
    lastError: "",
  });
  onSectionRef.current = onSection;
  onSnapshotMergedRef.current = onSnapshotMerged;
  onSyncCompleteRef.current = onSyncComplete;

  const publishTelemetry = useCallback(() => {
    if (typeof window === "undefined") return;
    const attempts = telemetryRef.current.attempts;
    const failures = telemetryRef.current.failures;
    const now = Date.now();
    const activeCooldownSections = Array.from(
      sectionCooldownUntilRef.current.entries()
    )
      .filter(([, until]) => until > now)
      .map(([section]) => section);
    const activeBreakerSections = Array.from(
      sectionBreakerOpenUntilRef.current.entries()
    )
      .filter(([, until]) => until > now)
      .map(([section]) => section);
    (
      window as Window & {
        __rfrAdminSnapshotTelemetry?: Record<string, unknown>;
      }
    ).__rfrAdminSnapshotTelemetry = {
      ...telemetryRef.current,
      failRate: attempts > 0 ? Number((failures / attempts).toFixed(3)) : 0,
      inFlightSections: Array.from(sectionInFlightRef.current.keys()),
      cooldownSections: activeCooldownSections,
      breakerSections: activeBreakerSections,
    };
  }, []);

  const refreshSection = useCallback(
    async (section: AdminSectionName, force = false) => {
      const inFlight = sectionInFlightRef.current.get(section);
      if (inFlight) {
        telemetryRef.current.dedupes += 1;
        publishTelemetry();
        return inFlight;
      }

      const now = Date.now();
      const breakerOpenUntil =
        sectionBreakerOpenUntilRef.current.get(section) ?? 0;
      const cooldownUntil = sectionCooldownUntilRef.current.get(section) ?? 0;
      if (!force && (now < breakerOpenUntil || now < cooldownUntil)) {
        telemetryRef.current.skips += 1;
        publishTelemetry();
        return;
      }

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

      telemetryRef.current.attempts += 1;
      publishTelemetry();

      const run = (async () => {
        try {
          let res: Response | null = null;
          let attempts = 0;
          while (attempts < 2) {
            attempts += 1;
            res = await adminFetch(
              `/api/admin/snapshot/section/${section}?${params.toString()}`
            );
            if (res.status === 304) {
              sectionFailStreakRef.current.set(section, 0);
              sectionCooldownUntilRef.current.delete(section);
              telemetryRef.current.successes += 1;
              telemetryRef.current.lastError = "";
              publishTelemetry();
              return;
            }
            if (res.ok) break;
            if (attempts >= 2 || !isTransientSnapshotStatus(res.status)) break;
            await pause(SNAPSHOT_SECTION_RETRY_DELAY_MS);
          }

          if (!res || !res.ok) {
            const status = res?.status ?? 0;
            throw new Error(
              `snapshot section ${section} failed (${status || "network"})`
            );
          }

          const patch = (await res.json()) as {
            updated_at?: string;
            data?: unknown;
          };
          if (!patch.updated_at) {
            sectionFailStreakRef.current.set(section, 0);
            sectionCooldownUntilRef.current.delete(section);
            telemetryRef.current.successes += 1;
            telemetryRef.current.lastError = "";
            publishTelemetry();
            return;
          }

          const next = mergeSectionIntoSnapshot(
            current,
            section,
            patch.updated_at,
            patch.data
          );
          writeLocalAdminSnapshot(next);
          onSnapshotMergedRef.current(next);
          onSectionRef.current(section, patch.data);

          sectionFailStreakRef.current.set(section, 0);
          sectionCooldownUntilRef.current.delete(section);
          telemetryRef.current.successes += 1;
          telemetryRef.current.lastError = "";
          publishTelemetry();
        } catch (err) {
          const streak = (sectionFailStreakRef.current.get(section) ?? 0) + 1;
          sectionFailStreakRef.current.set(section, streak);
          sectionCooldownUntilRef.current.set(
            section,
            Date.now() + SNAPSHOT_SECTION_COOLDOWN_MS
          );
          if (streak >= SNAPSHOT_SECTION_BREAKER_FAIL_STREAK) {
            sectionBreakerOpenUntilRef.current.set(
              section,
              Date.now() + SNAPSHOT_SECTION_BREAKER_OPEN_MS
            );
            sectionFailStreakRef.current.set(section, 0);
            telemetryRef.current.breakerOpenCount += 1;
          }
          telemetryRef.current.failures += 1;
          telemetryRef.current.lastError =
            err instanceof Error ? err.message : "snapshot section failed";
          publishTelemetry();

          if (!isTransientSnapshotError(err)) {
            // Keep behavior non-throwing for callers, but still classify non-transient issues.
            return;
          }
        } finally {
          sectionInFlightRef.current.delete(section);
        }
      })();

      sectionInFlightRef.current.set(section, run);
      return run;
    },
    [adminFetch, publishTelemetry, timeRange]
  );

  const syncSections = useCallback(
    async (sections: AdminSectionName[]) => {
      for (const section of sections) {
        setSyncingSection(section);
        await refreshSection(section, false);
        await pause(40);
      }
      setSyncingSection(null);
    },
    [refreshSection]
  );

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

    let forceRefresh = false;
    try {
      const snapRes = await adminFetch("/api/admin/snapshot");
      if (snapRes.ok) {
        const server = (await snapRes.json()) as AdminSnapshot;
        const merged = mergeServerSnapshot(readLocalAdminSnapshot(), server);
        if (snapshotLooksEmpty(merged)) {
          forceRefresh = true;
        }
        writeLocalAdminSnapshot(merged);
        onSnapshotMergedRef.current(merged);
      }
    } catch {
      /* cached UI remains */
    }

    onSyncCompleteRef.current?.();

    const foreground = foregroundSectionsForHash(window.location.hash.slice(1));
    if (forceRefresh) {
      for (const section of foreground) {
        setSyncingSection(section);
        await refreshSection(section, true);
        await pause(40);
      }
      setSyncingSection(null);
    } else {
      await syncSections(foreground);
    }

    if (deferStarted.current) return;
    deferStarted.current = true;
    const runDeferred = () => {
      void syncDeferred();
    };
    if (typeof requestIdleCallback !== "undefined") {
      requestIdleCallback(runDeferred, { timeout: 5000 });
    } else {
      window.setTimeout(runDeferred, 500);
    }
  }, [adminFetch, sessionToken, syncDeferred, syncSections]);

  return { syncingSection, sync, refreshSection };
}
