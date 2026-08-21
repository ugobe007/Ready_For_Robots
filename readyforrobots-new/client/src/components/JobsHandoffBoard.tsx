/**
 * Leftover Jobs hops used to render a second FIND list on /results and
 * /pipeline. That screen killed the workflow. Bounce back to `/`.
 */
import { useEffect } from "react";
import { armJobsWorkspaceRestore } from "@/lib/jobsWorkflow";

export default function JobsHandoffBoard(_props: {
  robotUrl: string;
  cap: number;
  src?: string | null;
  signedIn: boolean;
  variant: "results" | "pipeline";
}) {
  useEffect(() => {
    window.location.replace(armJobsWorkspaceRestore());
  }, []);

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
        Jobs
      </p>
      <h1 className="mt-1 font-display text-2xl font-bold text-slate-100 sm:text-3xl">
        Taking you back to your jobs…
      </h1>
      <p className="mt-2 text-sm text-slate-400">
        Your jobs stay on the Jobs terminal. This page is not a second job
        list.
      </p>
    </main>
  );
}
