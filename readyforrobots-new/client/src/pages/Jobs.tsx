/**
 * /jobs — customer acquisition surface (CAPABILITIES → FIND WORK).
 * Minimal chrome. Personalized via /jobs/{slug}?src=
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
      <main className="mx-auto max-w-3xl px-4 pb-24 pt-20 sm:px-6">
        <RobotJobsExperiment slug={slug} />
      </main>
    </div>
  );
}
