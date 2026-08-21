/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 * Slug may stay in the URL for marketing; the product surface is always the
 * Jobs workspace — never the old Qualify / See-all-jobs experiment overlay.
 *
 * `/?new=1` remounts the workspace so the wordmark always returns to FIND.
 */
import { useLocation } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsWorkspace from "@/components/RobotJobsWorkspace";
import { isJobsFreshQuery } from "@/lib/jobsWorkflow";

export default function Jobs() {
  const [location] = useLocation();
  const search = location.includes("?") ? location.slice(location.indexOf("?")) : "";
  const workspaceKey = isJobsFreshQuery(search) ? "fresh-find" : "workspace";
  return (
    <div className="jobs-page min-h-screen bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto w-full max-w-[1200px] px-3 pb-16 pt-[52px] sm:px-4">
        <RobotJobsWorkspace key={workspaceKey} />
      </main>
    </div>
  );
}
