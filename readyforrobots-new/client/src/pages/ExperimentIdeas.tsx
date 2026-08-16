/**
 * Experiment lab — focused robot → jobs conversion loop.
 * Acquisition chrome only (no Signal / Pipeline nav).
 * Dark navy surface — same palette as Home / Login / Signup.
 */
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsExperiment from "@/components/RobotJobsExperiment";

export default function ExperimentIdeas() {
  return (
    <div className="experiment-page min-h-screen bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto max-w-3xl px-4 pb-24 pt-20 sm:px-6">
        <RobotJobsExperiment />
      </main>
    </div>
  );
}
