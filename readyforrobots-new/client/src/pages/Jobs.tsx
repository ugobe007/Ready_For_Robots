/**
 * Canonical product front door (also /jobs/:slug personalization).
 * /jobs index redirects to /.
 */
import { useRoute } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsExperiment from "@/components/RobotJobsExperiment";
import RobotJobsWorkspace from "@/components/RobotJobsWorkspace";

export default function Jobs() {
  const [, params] = useRoute("/jobs/:slug");
  const slug = params?.slug;

  return (
    <div className="jobs-page flex min-h-screen flex-col bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto flex w-full max-w-[1200px] flex-1 flex-col px-3 pb-6 pt-[52px] sm:px-4">
        {/* Front door `/` = the ReadyForRobots work terminal (FIND→RESEARCH→SELECT→REVIEW→JOBS). */}
        {/* /jobs/:slug keeps the marketing personalization surface + persona telemetry. */}
        {slug ? <RobotJobsExperiment slug={slug} /> : <RobotJobsWorkspace />}
      </main>
    </div>
  );
}
