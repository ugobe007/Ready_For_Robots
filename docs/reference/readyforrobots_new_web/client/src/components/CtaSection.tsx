/**
 * CtaSection — "Precision Craft" design
 * Final CTA with soft emerald gradient background
 */

const CTA_BG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/L4rJPcZu4nTBCWZaQPghsQ/rfr-cta-bg-KDA35Gut3Vop4fmfpfS2dY.webp";

export default function CtaSection() {
  return (
    <section
      className="relative py-24 overflow-hidden"
      style={{ background: "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #eff6ff 100%)" }}
    >
      {/* Background image overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `url(${CTA_BG})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          opacity: 0.4,
        }}
      />

      <div className="container relative text-center">
        <div className="animate-fade-up max-w-2xl mx-auto">
          <span className="section-label block mb-4">Start Today</span>
          <h2
            className="text-5xl font-extrabold text-gray-900 mb-5"
            style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.03em" }}
          >
            Find your next robot deal
            <br />
            <span style={{ color: "oklch(0.527 0.154 162.5)" }}>before the competition does.</span>
          </h2>
          <p className="text-lg text-gray-600 mb-8 leading-relaxed">
            Enter your robot company URL and see your top 5 prospects instantly. No credit card. No commitment. Just signal intelligence.
          </p>

          {/* URL input */}
          <div className="flex flex-col sm:flex-row gap-3 max-w-lg mx-auto mb-6">
            <input
              type="text"
              placeholder="Enter your robot company website (e.g., amplibotics.ai)"
              className="flex-1 px-4 py-3 rounded-lg border border-gray-200 bg-white text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-sm"
            />
            <button
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-white font-semibold text-sm transition-all duration-150 hover:opacity-90 active:scale-95 shadow-sm whitespace-nowrap"
              style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
            >
              Build CRM pipeline
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          {/* Trust row */}
          <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
            <span className="flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5"/>
                <path d="M4.5 7l2 2 3-3" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              No signup required
            </span>
            <span className="flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5"/>
                <path d="M4.5 7l2 2 3-3" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Instant results
            </span>
            <span className="flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5"/>
                <path d="M4.5 7l2 2 3-3" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Free trial
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
