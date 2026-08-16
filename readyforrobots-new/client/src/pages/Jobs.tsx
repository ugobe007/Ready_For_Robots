/**
 * /jobs — Robot Employment Office (dark RFR brand).
 */
import { useRoute } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsExperiment from "@/components/RobotJobsExperiment";

export default function Jobs() {
  const [, params] = useRoute("/jobs/:slug");
  const slug = params?.slug;

  return (
    <div className="jobs-page min-h-screen bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto max-w-[1200px] px-3 pb-10 pt-[52px] sm:px-4">
        <RobotJobsExperiment slug={slug} />
      </main>
    </div>
  );
}
