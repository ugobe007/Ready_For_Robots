/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 * Slug may stay in the URL for marketing; the product surface is always the
 * Jobs workspace — never the old Qualify / See-all-jobs experiment overlay.
 *
 * `/?new=1` resets FIND inside the workspace. Strip the query in an effect
 * after paint. Do not remount the tree, and do not resetToFind while
 * research is in flight — that is the submit loop.
 */
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsWorkspace from "@/components/RobotJobsWorkspace";

export default function Jobs() {
  return (
    <div className="jobs-page min-h-screen bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto w-full max-w-[1200px] px-3 pb-16 pt-16 sm:px-4">
        <RobotJobsWorkspace />
      </main>
    </div>
  );
}
