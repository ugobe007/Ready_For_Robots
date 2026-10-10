/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 *
 * First beat on `/` is the landing fork (JobsLanding).
 * `/?visit=jobs` is OEM FIND. `/?visit=candidates` is employer MATCH/POST.
 * `/?new=1` returns to the landing fork. Strip the query in an effect
 * after paint. Do not remount the tree, and do not resetToFind while
 * research is in flight — that is the submit loop.
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
  const [forcedLanding, setForcedLanding] = useState(false);
  useEffect(() => {
    const onFresh = () => setForcedLanding(true);
    window.addEventListener(JOBS_FRESH_HOME_EVENT, onFresh);
    return () => window.removeEventListener(JOBS_FRESH_HOME_EVENT, onFresh);
  }, []);
  useEffect(() => {
    if (landingVisitFromSearch(search) !== "landing") {
      setForcedLanding(false);
    }
  }, [search]);
  const fromSearch = landingVisitFromSearch(search);
  // Wordmark may fire JOBS_FRESH_HOME_EVENT. FIND timeout/500/abort must
  // keep `?visit=jobs` — do not dump them onto the landing fork.
  const visit: LandingVisit =
    forcedLanding && fromSearch === "landing" ? "landing" : fromSearch;
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
