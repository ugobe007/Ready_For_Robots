/**
 * Home hero — compact live lead ticker aligned with site editorial theme.
 */
import ExperimentLeadTicker from "@/components/ExperimentLeadTicker";

export default function HeroLeadTicker() {
  return (
    <ExperimentLeadTicker
      maxVisible={4}
      tickMs={6000}
      title="Live pipeline"
      subtitle="Verified buyer signals"
      showPipelineLink
    />
  );
}
