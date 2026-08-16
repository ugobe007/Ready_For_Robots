/**
 * Experiment lab — focused robot → jobs conversion loop.
 * Acquisition chrome only (no Signal / Pipeline nav).
 */
import ExperimentHeader from "@/components/ExperimentHeader";
import RobotJobsExperiment from "@/components/RobotJobsExperiment";

export default function ExperimentIdeas() {
  return (
    <div className="experiment-page relative min-h-screen text-slate-900">
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden
        style={{
          background:
            "radial-gradient(1200px 560px at 12% -10%, rgba(16,185,129,0.14), transparent 55%), radial-gradient(900px 480px at 92% 8%, rgba(15,23,42,0.05), transparent 50%), linear-gradient(180deg, #ffffff 0%, #f8fafc 48%, #f1f5f9 100%)",
        }}
      />
      <ExperimentHeader />
      <main className="mx-auto max-w-3xl px-4 pb-24 pt-20 sm:px-6">
        <RobotJobsExperiment />
      </main>
    </div>
  );
}
