import ExperimentLeadTicker from "@/components/ExperimentLeadTicker";

/** Compact live-lead ticker for homepage FOMO — sits under the URL scan CTA. */
export default function HeroFomoTicker() {
  return (
    <div className="mb-4 max-w-xl rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50/80 to-white p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-amber-800">
          Moving now in pipeline
        </p>
        <span className="text-[10px] font-medium text-gray-600">Updated live</span>
      </div>
      <ExperimentLeadTicker
        maxVisible={4}
        tickMs={4500}
        minHeightClass="min-h-[168px]"
        title=""
        subtitle=""
        showPipelineLink={false}
      />
      <p className="mt-2 text-[11px] leading-relaxed text-gray-700">
        Your competitors are still buying lists.{" "}
        <span className="font-semibold text-gray-900">SIGNAL already knows who is buying robots — and when.</span>
      </p>
    </div>
  );
}
