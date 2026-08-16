/**
 * Experiment lab — focused robot → jobs conversion loop.
 * Acquisition chrome only (no Signal / Pipeline nav).
 */
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsExperiment from "@/components/RobotJobsExperiment";

export default function ExperimentIdeas() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <ExperimentHeader />
      <main className="mx-auto max-w-3xl px-4 pb-20 pt-20 sm:px-6">
        <RobotJobsExperiment />
      </main>
    </div>
  );
}
