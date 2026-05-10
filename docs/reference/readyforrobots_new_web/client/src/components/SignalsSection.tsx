/**
 * SignalsSection — "Precision Craft" design
 * What Are Buying Signals? — 3 signal types + lead scoring breakdown
 * Background: soft emerald-tinted section
 */

const SIGNALS_VISUAL = "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/L4rJPcZu4nTBCWZaQPghsQ/rfr-signals-visual-mghifCvSora7P4h977Jdxf.webp";

const signals = [
  {
    icon: "🔥",
    title: "Labor Shortage Signals",
    weight: 35,
    color: "oklch(0.627 0.163 66.5)",
    bgColor: "oklch(0.985 0.03 66.5)",
    borderColor: "oklch(0.95 0.09 66.5)",
    quotes: [
      '"We can\'t find enough workers to cover shifts"',
      '"Turnover is killing us — constant training"',
      '"Wages up 30%, still can\'t fill positions"',
    ],
    label: "Strongest automation trigger",
  },
  {
    icon: "📈",
    title: "Expansion Signals",
    weight: 30,
    color: "oklch(0.488 0.243 264.376)",
    bgColor: "oklch(0.97 0.02 264.376)",
    borderColor: "oklch(0.93 0.06 264.376)",
    quotes: [
      '"Opening new facility next quarter"',
      '"Need 24/7 operations but can\'t staff it"',
      '"Scaling to meet new demand"',
    ],
    label: "Growth-driven automation",
  },
  {
    icon: "⚠️",
    title: "Safety Signals",
    weight: 20,
    color: "oklch(0.527 0.154 162.5)",
    bgColor: "oklch(0.982 0.016 162.5)",
    borderColor: "oklch(0.951 0.044 162.5)",
    quotes: [
      '"OSHA citation for repetitive stress"',
      '"Multiple injuries in manual operations"',
      '"Heavy lifting causing worker comp claims"',
    ],
    label: "Risk reduction driver",
  },
];

const scoreFactors = [
  { label: "Labor Pain", pct: 35, color: "oklch(0.627 0.163 66.5)" },
  { label: "Expansion", pct: 30, color: "oklch(0.488 0.243 264.376)" },
  { label: "Automation Fit", pct: 25, color: "oklch(0.527 0.154 162.5)" },
  { label: "Timing", pct: 10, color: "oklch(0.65 0.12 162.5)" },
];

export default function SignalsSection() {
  return (
    <section
      id="signals"
      className="py-20 border-t border-emerald-900/10"
      style={{ backgroundColor: "oklch(0.955 0.022 162.5)" }}
    >
      <div className="container">
        {/* Header */}
        <div className="mb-14 animate-fade-up">
          <span className="section-label block mb-3">Signal Intelligence</span>
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <h2
              className="text-4xl font-bold text-gray-950 max-w-xl"
              style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
            >
              What are buying signals?
            </h2>
            <p className="text-gray-800 text-sm max-w-sm leading-relaxed font-medium border-l-4 border-emerald-700/40 pl-4">
              Real-world indicators that a company needs automation — before they post an RFP.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-14">
          {signals.map((signal, i) => (
            <div
              key={signal.title}
              className="animate-fade-up card-lift rounded-2xl border border-gray-200 bg-white p-6 shadow-md ring-1 ring-black/[0.04]"
              style={{
                borderTopWidth: "4px",
                borderTopColor: signal.color,
                animationDelay: `${i * 80}ms`,
              }}
            >
              {/* Icon + title */}
              <div className="flex items-start gap-3 mb-4">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0 border border-gray-200 shadow-sm"
                  style={{ backgroundColor: signal.bgColor }}
                >
                  {signal.icon}
                </div>
                <div>
                  <h3
                    className="text-base font-bold text-gray-950"
                    style={{ fontFamily: "'Bricolage Grotesque', sans-serif" }}
                  >
                    {signal.title}
                  </h3>
                  <span className="text-xs font-bold" style={{ color: signal.color }}>
                    {signal.weight}% weight
                  </span>
                </div>
              </div>

              {/* Quotes */}
              <div className="space-y-2.5 mb-5">
                {signal.quotes.map((q) => (
                  <p
                    key={q}
                    className="text-sm text-gray-800 leading-snug border-l-[3px] pl-3.5 py-0.5 bg-gray-50/80 rounded-r-md"
                    style={{ borderColor: signal.color }}
                  >
                    {q}
                  </p>
                ))}
              </div>

              {/* Label */}
              <div className="text-xs font-bold uppercase tracking-wide mt-auto" style={{ color: signal.color }}>
                {signal.label}
              </div>
            </div>
          ))}
        </div>

        {/* Lead scoring */}
        <div className="animate-fade-up rounded-2xl border border-gray-200 bg-white p-8 shadow-lg ring-1 ring-black/[0.05]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div>
              <h3
                className="text-2xl font-bold text-gray-950 mb-3"
                style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
              >
                How we score leads
              </h3>
              <p className="text-gray-700 text-sm leading-relaxed font-medium">
                Every company gets a score from 0–100 based on four weighted factors. Higher scores mean stronger
                buying intent and better timing for outreach.
              </p>
            </div>
            <div className="space-y-3.5">
              {scoreFactors.map((f) => (
                <div key={f.label} className="flex items-center gap-3">
                  <div className="text-sm font-semibold text-gray-900 w-28 flex-shrink-0">{f.label}</div>
                  <div className="flex-1 h-2.5 rounded-full bg-gray-200 overflow-hidden border border-gray-300/60">
                    <div
                      className="h-full rounded-full transition-all duration-700 shadow-sm"
                      style={{ width: `${f.pct}%`, backgroundColor: f.color }}
                    />
                  </div>
                  <div className="text-sm font-bold font-mono-data w-10 text-right tabular-nums" style={{ color: f.color }}>
                    {f.pct}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
