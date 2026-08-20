/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 * Slug may stay in the URL for marketing; the product surface is always the
 * Jobs workspace — never the old Qualify / See-all-jobs experiment overlay.
 */
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsWorkspace from "@/components/RobotJobsWorkspace";

export default function Jobs() {
  return (
    <div className="jobs-page flex min-h-screen flex-col bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto flex w-full max-w-[1200px] flex-1 flex-col px-3 pb-6 pt-[52px] sm:px-4">
        <RobotJobsWorkspace />
      </main>
    </div>
  );
}
