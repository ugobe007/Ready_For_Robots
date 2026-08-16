/**
 * Legacy /experiment → /jobs (preserve robot/src where possible).
 */
import { Redirect } from "wouter";
import { experimentQueryToJobsPath } from "@/lib/jobsSlugs";

export default function ExperimentRedirect() {
  const target =
    typeof window !== "undefined"
      ? experimentQueryToJobsPath(window.location.search)
      : "/jobs";
  return <Redirect to={target} />;
}
