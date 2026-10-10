/**
 * Legacy page — /experiment now redirects to /jobs.
 * Kept so old imports do not break during transition.
 */
import { Redirect } from "wouter";

export default function ExperimentIdeas() {
  return <Redirect to="/jobs" />;
}
