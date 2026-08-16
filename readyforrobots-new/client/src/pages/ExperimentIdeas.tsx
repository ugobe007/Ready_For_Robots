/**
 * Experiment lab — focused robot → jobs conversion loop.
 */
import Header from "@/components/Header";
import RobotJobsExperiment from "@/components/RobotJobsExperiment";

export default function ExperimentIdeas() {
  return (
    <div className="min-h-screen bg-slate-50 text-gray-900">
      <Header />

      <main className="mx-auto max-w-2xl px-4 pb-16 pt-24 sm:px-6">
        <RobotJobsExperiment />
      </main>
    </div>
  );
}
