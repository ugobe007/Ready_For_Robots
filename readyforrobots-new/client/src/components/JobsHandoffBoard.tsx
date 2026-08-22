/**
 * Step 3 is CRM. Old /pipeline?src=jobs_* links redirect there.
 * Do not render a second save-confirmation page.
 */
import { useEffect } from "react";
import {
  JOBS_ACTIVATE_SRC,
  jobsActivateHref,
  jobsSignupHref,
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
    const dest = jobsActivateHref(props.submissionId);
    window.location.replace(
      props.signedIn ? dest : jobsSignupHref(dest, props.src || JOBS_ACTIVATE_SRC),
    );
  }, [props.signedIn, props.src, props.submissionId]);

  return (
    <p className="px-6 py-16 text-center font-mono text-sm uppercase tracking-[0.08em] text-slate-400">
      Opening CRM…
    </p>
  );
}
