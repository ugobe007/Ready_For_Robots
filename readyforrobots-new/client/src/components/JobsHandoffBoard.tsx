/**
 * Step 3 is CRM. Old /pipeline?src=jobs_* links redirect there.
 * Do not render a second save-confirmation page.
 */
import { useEffect } from "react";
import {
  isJobsAutomateSrc,
  jobsCrmOpenHref,
} from "@/lib/jobsWorkflow";

export default function JobsHandoffBoard(props: {
  robotUrl: string;
  cap: number;
  src?: string | null;
  signedIn: boolean;
  variant: "results" | "pipeline";
  submissionId?: number | null;
}) {
  useEffect(() => {
    if (isJobsAutomateSrc(props.src)) return;
    window.location.replace(jobsCrmOpenHref(props.signedIn, props.submissionId));
  }, [props.src, props.submissionId]);

  return (
    <p className="px-6 py-16 text-center font-mono text-sm uppercase tracking-[0.08em] text-slate-400">
      Opening CRM…
    </p>
  );
}
