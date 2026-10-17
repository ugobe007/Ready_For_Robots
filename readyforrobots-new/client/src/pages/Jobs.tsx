/**
 * Canonical product front door (also /jobs/:slug personalization).
 *
 * `/` is the home hero; `/#find` goes to the robot jobs board (`/jobs`).
 * Bare `/?visit=jobs` is the board. `/?visit=jobs&url=` runs OEM FIND.
 * `/?visit=candidates` is employer MATCH/POST.
 * Wordmark returns to the hero. Lookup failure stays on FIND.
 */
import { useEffect, useState } from "react";
import { Redirect, useSearch } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import EditorialResults from "@/components/EditorialResults";
import JobsLanding from "@/components/JobsLanding";
import EmployerMatchWorkspace from "@/components/EmployerMatchWorkspace";
import RobotJobs from "@/pages/RobotJobs";
import {
  isFindBoardHash,
  isFindBoardSearch,
  landingVisitFromSearch,
  type LandingVisit,
} from "@/lib/jobsLanding";
import { JOBS_FRESH_HOME_EVENT } from "@/lib/jobsWorkflow";

export default function Jobs() {
  const search = useSearch();
  const [heroHome, setHeroHome] = useState(false);
  const [hash, setHash] = useState(() =>
    typeof window === "undefined" ? "" : window.location.hash
  );
  useEffect(() => {
    const onHash = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  useEffect(() => {
    const onFresh = () => setHeroHome(true);
    window.addEventListener(JOBS_FRESH_HOME_EVENT, onFresh);
    return () => window.removeEventListener(JOBS_FRESH_HOME_EVENT, onFresh);
  }, []);
  useEffect(() => {
    const next = landingVisitFromSearch(search);
    if (next === "jobs" || next === "candidates") setHeroHome(false);
  }, [search]);
  const fromSearch = landingVisitFromSearch(search);
  const visit: LandingVisit = heroHome ? "landing" : fromSearch;
  if (visit === "landing") {
    if (isFindBoardHash(hash)) return <Redirect to="/jobs" replace />;
    return <JobsLanding />;
  }
  if (visit === "candidates") {
    return (
      <div className="jobs-page min-h-screen bg-[#081126] text-slate-100">
        <ExperimentHeader />
        <main className="mx-auto w-full max-w-[1200px] px-3 pb-16 pt-16 sm:px-4">
          <EmployerMatchWorkspace />
        </main>
      </div>
    );
  }
  if (isFindBoardSearch(search)) {
    return <RobotJobs />;
  }
  return <EditorialResults />;
}
