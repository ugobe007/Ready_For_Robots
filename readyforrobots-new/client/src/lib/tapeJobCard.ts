/**
 * Shared job-card open for the home board and FIND (`/?visit=jobs`).
 * A click sets `job` and opens LiveJobDetailModal. FIND keeps `visit=jobs`.
 */
import { useEffect, useState } from "react";
import { getPublicReadApiBase } from "@/lib/apiBase";
import { MARKET_TAPE_JOBS, type TapeFamily, type TapeJob } from "@/lib/jobsTapeCorpus";

const FAMILIES: TapeFamily[] = [
  "transport",
  "cart",
  "pallet",
  "scrub",
  "inspect",
  "gripper",
];

export function tapeJobCardHref(
  pathname: string,
  search: string,
  jobKey: string | null
): string {
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search
  );
  if (jobKey) params.set("job", jobKey);
  else params.delete("job");
  if (params.get("visit") !== "jobs") params.delete("visit");
  const qs = params.toString();
  return `${pathname}${qs ? `?${qs}` : ""}`;
}

export function pushTapeJobCard(jobKey: string | null): void {
  try {
    const next = tapeJobCardHref(
      window.location.pathname,
      window.location.search,
      jobKey
    );
    if (jobKey) {
      window.history.pushState({ jobKey }, "", next);
      return;
    }
    if (window.location.search.includes("job=")) {
      window.history.pushState({}, "", next);
    }
  } catch {
    /* history failures stay on the open card */
  }
}

export async function resolveTapeJob(jobKey: string): Promise<TapeJob | null> {
  const matched = MARKET_TAPE_JOBS.find(
    job => job.key.toLowerCase() === jobKey.toLowerCase()
  );
  if (matched) return matched;
  try {
    const base = getPublicReadApiBase();
    const res = await fetch(
      `${base}/api/robot-job-card/${encodeURIComponent(jobKey)}`
    );
    if (!res.ok) return null;
    const data = await res.json();
    const card = data?.job;
    if (!card?.key || !card?.employer) return null;
    const family = FAMILIES.includes(card.family) ? card.family : "transport";
    return {
      key: String(card.key),
      title: String(card.title || "Work"),
      industry: String(
        card.industry ||
          [card.employer, card.locality].filter(Boolean).join(" · ")
      ),
      path: String(card.path || card.locality || "WORKSITE → WORKSITE"),
      family,
      customer: String(card.employer),
      location: card.locality ? String(card.locality) : undefined,
      headline: card.description ? String(card.description) : undefined,
    };
  } catch {
    return null;
  }
}

export function useTapeJobCard() {
  const [selectedTapeJob, setSelectedTapeJob] = useState<TapeJob | null>(null);

  useEffect(() => {
    let cancelled = false;
    const apply = () => {
      const jobKey = new URLSearchParams(window.location.search).get("job");
      if (!jobKey) {
        setSelectedTapeJob(null);
        return;
      }
      void resolveTapeJob(jobKey).then(job => {
        if (!cancelled && job) setSelectedTapeJob(job);
      });
    };
    apply();
    window.addEventListener("popstate", apply);
    return () => {
      cancelled = true;
      window.removeEventListener("popstate", apply);
    };
  }, []);

  const handleSelectJob = (job: TapeJob) => {
    setSelectedTapeJob(job);
    pushTapeJobCard(job.key);
  };

  const handleCloseModal = () => {
    setSelectedTapeJob(null);
    pushTapeJobCard(null);
  };

  return { selectedTapeJob, handleSelectJob, handleCloseModal };
}
