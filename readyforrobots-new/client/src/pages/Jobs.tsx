/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 *
 * `/` is the home hero. `/?visit=jobs` is OEM FIND.
 * `/?visit=candidates` is employer MATCH/POST.
 * Wordmark returns to the hero. Lookup failure stays on FIND.
 */
import { useEffect, useState } from "react";
import { useSearch } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsWorkspace from "@/components/RobotJobsWorkspace";
import JobsLanding from "@/components/JobsLanding";
import EmployerMatchWorkspace from "@/components/EmployerMatchWorkspace";
import { landingVisitFromSearch, type LandingVisit } from "@/lib/jobsLanding";
import { JOBS_FRESH_HOME_EVENT } from "@/lib/jobsWorkflow";

export default function Jobs() {
  const search = useSearch();
  const [heroHome, setHeroHome] = useState(false);
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
    return (
      <div className="jobs-page min-h-screen bg-[#0A0F1E] text-slate-100">
        <ExperimentHeader />
        <JobsLanding />
      </div>
    );
  }
  return (
    <div className="jobs-page min-h-screen bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto w-full max-w-[1200px] px-3 pb-16 pt-16 sm:px-4">
        {visit === "candidates" ? (
          <EmployerMatchWorkspace />
        ) : (
          <RobotJobsWorkspace />
        )}
      </main>
    </div>
  );
}
