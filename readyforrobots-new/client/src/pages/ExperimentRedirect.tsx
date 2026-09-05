/**
 * Legacy /experiment → / (or /jobs/:slug when robot= is present).
 */
import { Redirect } from "wouter";
import { experimentQueryToJobsPath } from "@/lib/jobsSlugs";

export default function ExperimentRedirect() {
  const target =
    typeof window !== "undefined"
      ? experimentQueryToJobsPath(window.location.search)
      : "/";
  return <Redirect to={target} />;
}
