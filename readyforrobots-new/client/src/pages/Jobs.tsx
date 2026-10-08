/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 *
 * `/` is FIND. `/?visit=jobs` is the same FIND document.
 * `/?visit=candidates` is employer MATCH/POST.
 * Wordmark resets FIND in place. Lookup failure stays on FIND.
 */
import { useSearch } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsWorkspace from "@/components/RobotJobsWorkspace";
import EmployerMatchWorkspace from "@/components/EmployerMatchWorkspace";
import { landingVisitFromSearch } from "@/lib/jobsLanding";

export default function Jobs() {
  const search = useSearch();
  const visit = landingVisitFromSearch(search);
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
