/**
 * SuccessStoriesSection — "Precision Craft" design
 * Real Signals → Real Deals — case study cards with emerald left-border accent
 */

const stories = [
  {
    title: "Regional Hotel Chain → AMR Deployment",
    signal: '"Can\'t staff overnight shifts" + "40% housekeeping vacancy" in earnings call',
    action: "Reached out 4 months before RFP with overnight automation case study",
    result: "Shaped requirements, won pilot without competition → 15-robot deployment",
    tag: "Hospitality",
    tagColor: "oklch(0.488 0.243 264.376)",
    tagBg: "oklch(0.97 0.02 264.376)",
    icon: "🏨",
  },
  {
    title: "3PL Warehouse → Palletizing System",
    signal: '"Opening 2 new DCs" + posting for "automation engineer"',
    action: "Contacted during facility design phase with layout recommendations",
    result: "Designed automation into new buildings → $2.4M contract",
    tag: "Logistics",
    tagColor: "oklch(0.527 0.154 162.5)",
    tagBg: "oklch(0.982 0.016 162.5)",
    icon: "🏭",
  },
];

export default function SuccessStoriesSection() {
  return (
    <section className="py-20" style={{ backgroundColor: "oklch(0.982 0.016 162.5)" }}>
      <div className="container">
        {/* Header */}
        <div className="mb-12 animate-fade-up">
          <span className="section-label block mb-3">Success Stories</span>
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <h2
              className="text-4xl font-bold text-gray-900"
              style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
            >
              Real signals → real deals
            </h2>
            <p className="text-gray-500 text-sm max-w-xs">
              How robotics companies are using signals to close deals before RFPs.
            </p>
          </div>
        </div>

        {/* Story cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {stories.map((story, i) => (
            <div
              key={story.title}
              className="animate-fade-up card-lift bg-white rounded-2xl p-7 border border-gray-100 border-accent-emerald"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              {/* Tag + icon */}
              <div className="flex items-center justify-between mb-5">
                <span
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full"
                  style={{ backgroundColor: story.tagBg, color: story.tagColor }}
                >
                  {story.icon} {story.tag}
                </span>
              </div>

              {/* Title */}
              <h3
                className="text-lg font-bold text-gray-900 mb-5"
                style={{ fontFamily: "'Bricolage Grotesque', sans-serif" }}
              >
                {story.title}
              </h3>

              {/* Signal → Action → Result */}
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: "oklch(0.627 0.163 66.5)" }}>
                    S
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Signal detected</div>
                    <p className="text-sm text-gray-700 italic">{story.signal}</p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: "oklch(0.488 0.243 264.376)" }}>
                    A
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Action taken</div>
                    <p className="text-sm text-gray-700">{story.action}</p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}>
                    R
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Result</div>
                    <p className="text-sm font-semibold text-gray-900">{story.result}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
