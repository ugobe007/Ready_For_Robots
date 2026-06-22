/**
 * Home hero — compact live lead ticker (replaces typewriter spotlight panel).
 */
import ExperimentLeadTicker from "@/components/ExperimentLeadTicker";

export default function HeroLeadTicker() {
  return (
    <ExperimentLeadTicker
      maxVisible={8}
      tickMs={6000}
      minHeightClass="min-h-[460px] lg:min-h-[520px]"
      title="Live pipeline"
      subtitle="SIGNAL · robot demand"
      showPipelineLink
    />
  );
}
