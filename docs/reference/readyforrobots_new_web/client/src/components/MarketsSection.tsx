/**
 * MarketsSection — "Precision Craft" design
 * 3-column card grid of industry verticals with hover lift
 */

const markets = [
  { icon: "🏭", name: "Logistics & Warehousing", type: "Warehouse AMR Fleet", isNew: false },
  { icon: "🏨", name: "Hospitality & Hotels", type: "Service & Delivery Robots", isNew: false },
  { icon: "🏥", name: "Healthcare & Senior Living", type: "Clinical Logistics Robots", isNew: false },
  { icon: "🍽️", name: "Food Service & Restaurants", type: "BOH Kitchen Automation", isNew: false },
  { icon: "🏗️", name: "Food Processing & Mfg", type: "EOL Line Automation", isNew: true },
  { icon: "📦", name: "CPG & Consumer Goods", type: "Palletizing & Case Packing", isNew: true },
  { icon: "🔧", name: "Contract Manufacturing", type: "Flexible EOL Robotics", isNew: true },
  { icon: "🛒", name: "Retail & Grocery", type: "Picking & Restocking", isNew: false },
  { icon: "✈️", name: "Airports & Transportation", type: "Ground Ops Robots", isNew: false },
  { icon: "🎰", name: "Casinos & Gaming", type: "Floor & F&B Delivery", isNew: false },
  { icon: "🏢", name: "Real Estate & Facilities", type: "Cleaning & Concierge", isNew: false },
  { icon: "🚢", name: "Cruise Lines", type: "Onboard Delivery", isNew: false },
];

export default function MarketsSection() {
  return (
    <section id="markets" className="py-20 bg-white">
      <div className="container">
        {/* Header */}
        <div className="mb-12 animate-fade-up">
          <span className="section-label block mb-3">Coverage</span>
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <h2
              className="text-4xl font-bold text-gray-900"
              style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
            >
              Markets we track
            </h2>
            <p className="text-gray-500 text-sm max-w-sm">
              Every vertical below has live signals — click to filter and explore active automation projects.
            </p>
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {markets.map((market, i) => (
            <a
              key={market.name}
              href="/markets"
              className="animate-fade-up card-lift group flex items-start gap-4 p-5 rounded-xl border border-gray-100 bg-white hover:border-emerald-200 transition-colors duration-200"
              style={{ animationDelay: `${i * 40}ms`, borderColor: "oklch(0.92 0.004 285)" }}
            >
              <div className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
                style={{ backgroundColor: "oklch(0.982 0.016 162.5)" }}>
                {market.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-semibold text-gray-900 truncate">{market.name}</span>
                  {market.isNew && <span className="badge-new flex-shrink-0">NEW</span>}
                </div>
                <span className="text-xs text-gray-500">{market.type}</span>
              </div>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 text-gray-300 group-hover:text-emerald-500 transition-colors mt-0.5">
                <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </a>
          ))}
        </div>

        {/* Why signals matter */}
        <div className="mt-10 animate-fade-up">
          <a
            href="#signals"
            className="inline-flex items-center gap-2 text-sm font-semibold transition-colors hover:opacity-80"
            style={{ color: "oklch(0.527 0.154 162.5)" }}
          >
            <span className="text-base">💡</span>
            Why Signals Matter — Learn how we identify buying intent
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3 7h8M7 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}
