/**
 * HowItWorksSection — "Precision Craft" design
 * CRM builder feature (60/40 split)
 */

export default function HowItWorksSection() {
  return (
    <section className="py-20 bg-white">
      <div className="container">

        {/* CRM Feature block */}
        <div id="crm" className="animate-fade-up scroll-mt-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="section-label block mb-3">Free CRM Builder</span>
              <h2
                className="text-4xl font-bold text-gray-900 mb-5"
                style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
              >
                Build your customer CRM in minutes
              </h2>
              <p className="text-gray-600 leading-relaxed mb-6">
                Automation projects are difficult to discover and plan for without great data. We deliver live, not stale data — then help you shape your timing and strategy so opportunities turn into PoCs and projects.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href="/crm"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-white font-semibold text-sm transition-all duration-150 hover:opacity-90 shadow-sm"
                  style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
                >
                  Build CRM pipeline
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </a>
              </div>
              <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                <span>✓ No signup required</span>
                <span>✓ Instant results</span>
                <span>✓ Free trial</span>
              </div>
            </div>

            {/* CRM visual */}
            <div className="relative">
              <div
                className="rounded-2xl p-6 border border-gray-100"
                style={{ backgroundColor: "oklch(0.982 0.016 162.5)" }}
              >
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Your CRM Pipeline</div>
                {/* Mock CRM rows */}
                {[
                  { company: "Lineage Logistics", status: "Active Eval", score: 84, stage: "PoC" },
                  { company: "Hyatt Hotels", status: "Warm Lead", score: 67, stage: "Outreach" },
                  { company: "Walmart Stores", status: "Hot Lead", score: 88, stage: "Demo" },
                ].map((row, i) => (
                  <div key={row.company} className="flex items-center justify-between bg-white rounded-xl px-4 py-3 mb-2 border border-gray-100 shadow-sm">
                    <div>
                      <div className="text-sm font-semibold text-gray-900">{row.company}</div>
                      <div className="text-xs text-gray-500">{row.status}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                        style={{
                          backgroundColor: i === 2 ? "oklch(0.985 0.03 66.5)" : "oklch(0.97 0.02 264.376)",
                          color: i === 2 ? "oklch(0.627 0.163 66.5)" : "oklch(0.488 0.243 264.376)",
                        }}>
                        {row.stage}
                      </span>
                      <span className="font-mono-data font-bold text-sm" style={{ color: "oklch(0.527 0.154 162.5)" }}>
                        {row.score}
                      </span>
                    </div>
                  </div>
                ))}
                <div className="text-center mt-3">
                  <span className="text-xs text-gray-400">+ Add company by URL →</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
