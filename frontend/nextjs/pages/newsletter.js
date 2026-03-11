import { useState, useEffect } from 'react';
import Link from 'next/link';
import Head from 'next/head';

export default function Newsletter() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [email, setEmail] = useState('');
  const [showPreview, setShowPreview] = useState(true);
  const [expandedStories, setExpandedStories] = useState({});
  
  // Mock subscription check (in production, check against backend/Supabase)
  useEffect(() => {
    const subscribed = localStorage.getItem('newsletter_subscribed') === 'true';
    setIsSubscribed(subscribed);
    setShowPreview(!subscribed);
  }, []);

  const toggleStory = (idx) => {
    setExpandedStories(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const handleSubscribe = (e) => {
    e.preventDefault();
    // In production: send to backend, create Supabase entry, send confirmation email
    localStorage.setItem('newsletter_subscribed', 'true');
    setIsSubscribed(true);
    setShowPreview(false);
    alert(`✅ Subscribed! Welcome to the Robot Intelligence Brief.\n\nYou'll receive:\n• Daily deployment roundups\n• ROI benchmarking data\n• Vendor market share tracking\n• Technology trend analysis`);
  };

  // Mock newsletter data (in production, fetch from backend/database)
  const latestEdition = {
    date: 'March 11, 2026',
    edition: '#48',
    headline: 'Warehouse AMRs Hit 30% Deployment Growth YoY',
    subheadline: 'MiR and Locus lead market as ROI drops to 18-month payback average'
  };

  const topStories = [
    {
      category: 'DEPLOYMENT',
      company: 'Marriott International',
      headline: 'Expands Savioke Robot Fleet to 100 Properties',
      snippet: 'Hotel giant reports 14-month payback, 30% reduction in staff walking time...',
      roi: '14-month payback',
      economics: '$2,500/mo robot vs $3,500/mo labor',
      impact: 'Guest satisfaction up 12 points',
      signalStrength: 10,
      fullText: `Marriott International announced expansion of its Savioke Relay robot deployment from 50 to 100 properties across North America, citing better-than-expected ROI and guest satisfaction improvements.
      
**Key Metrics:**
- **Payback Period:** 14 months (beat internal 18-month target)
- **Labor Economics:** Robot lease $2,500/month vs. equivalent labor $3,500/month
- **Productivity:** Staff walking time reduced 30%, allowing focus on guest interaction
- **Guest Impact:** Satisfaction scores increased 12 points (NPS 58 → 70)
- **Reliability:** 98.2% uptime across existing fleet

**Why It Matters:**
Marriott's expansion validates the hospitality delivery robot business case. The 14-month payback is among the fastest in service robotics, driven by labor shortage (35% housekeeping vacancy rates) and wage inflation.

**Competitive Response:**
Hilton and Hyatt accelerating pilots in response. Savioke now holds estimated 50%+ market share in hotel delivery robots.

**Investor Angle:**
Savioke's unit economics work: $30K robot lease revenue over 3 years = $90K vs. $50K manufacturing cost. Gross margins 45%+.`
    },
    {
      category: 'ECONOMICS',
      company: 'Warehouse Automation Market',
      headline: 'AMR Payback Period Drops to 18 Months (From 24)',
      snippet: 'Improving unit economics and labor costs accelerate automation ROI...',
      roi: '18-month average',
      economics: 'Down from 24 months in 2024',
      impact: 'Expanding addressable market',
      signalStrength: 9,
      fullText: `Industry-wide warehouse AMR payback periods have compressed from 24 months (2024) to 18 months (2026), driven by falling robot costs, rising labor expenses, and software improvements.

**What Changed:**
- **Robot Costs:** Down 15% annually (China manufacturing scale)
- **Labor Costs:** Up 25% since 2024 (wage inflation + shortage)
- **Software:** Fleet management improvements increase utilization 20%
- **Financing:** RaaS models lowering upfront CapEx barrier

**Market Impact:**
18-month payback opens automation to mid-market warehouses (100K-200K sq ft) previously priced out at 24-month horizons.

**Addressable Market Expansion:**
- 2024: 12,000 warehouses economically viable for AMRs
- 2026: 25,000+ warehouses now viable
- TAM increase: $8B → $15B

**Vendor Beneficiaries:**
- **MiR:** 30% deployment growth YoY
- **Locus Robotics:** Warehouse picking robots in 500+ facilities
- **Fetch/Zebra:** Goods-to-person systems scaling

**Buyer Insight:**
If your warehouse has >50 employees and >100K sq ft, automation now pencils at 18-month payback. Labor shortage makes ROI calculation easier: robots available when humans aren't.`
    },
    {
      category: 'TECHNOLOGY TREND',
      company: 'Computer Vision Picking',
      headline: 'AI Vision Enables 10,000+ SKU Variety Without Pre-Programming',
      snippet: 'Amazon, Berkshire Grey deploy CV-based picking, eliminating standardization requirement...',
      roi: 'Unlocks smaller warehouses',
      economics: 'No fixed-bin requirement',
      impact: 'Democratizes automation',
      signalStrength: 8,
      fullText: `Computer vision-powered picking robots can now handle 10,000+ SKU variety without pre-programming or fixed bin locations, removing the biggest barrier to warehouse automation for mid-market companies.

**The Old Problem:**
Traditional warehouse automation required:
- Fixed bin locations
- Standardized packaging
- SKU pre-programming
- Warehouse redesign ($500K-$2M)

**The New Reality:**
AI-powered vision systems (Cognex, Keyence, custom solutions) enable robots to:
- Identify arbitrary objects
- Handle varying packaging
- Pick from random bin locations
- Learn new SKUs via image recognition

**Who's Deploying:**
- **Amazon:** 200+ facilities using CV-based picking
- **Berkshire Grey:** Retail fulfillment systems in 50+ warehouses
- **RightHand Robotics:** Grocery picking (produce, irregular items)

**Why It Matters:**
Smaller warehouses (<200K sq ft, <5,000 SKUs) couldn't justify automation before. Computer vision removes the standardization requirement, expanding TAM 3x.

**ROI Shift:**
- **Before:** $2M automation + $1M warehouse redesign = $3M, 36-month payback
- **After:** $800K automation + $0 redesign = $800K, 18-month payback

**Investor Thesis:**
CV picking is the "iPhone moment" for warehouse automation—takes technology from enterprise-only to mid-market accessible. Companies to watch: RightHand, Berkshire Grey, Covariant.`
    },
    {
      category: 'COMPETITIVE DYNAMICS',
      company: 'Hilton vs. Marriott',
      headline: 'Hilton Accelerates Robot Pilot After Marriott Expansion',
      snippet: 'Competitive pressure drives adoption as hotel chains race to automate...',
      roi: 'Defensive deployment',
      economics: 'Match competitor efficiency',
      impact: 'Industry-wide acceleration',
      signalStrength: 7,
      fullText: `Hilton Hotels announced acceleration of its robot delivery pilot from 5 to 25 properties within 60 days of Marriott's 100-property expansion announcement—a textbook competitive response.

**The Dynamics:**
1. **Marriott moves first:** 100-property Savioke deployment
2. **Guest perception shifts:** "Marriott feels more modern/tech-forward"
3. **Operational gap emerges:** Marriott's labor cost per occupied room drops 8%
4. **Hilton responds:** Accelerate automation to match

**Why This Matters:**
Competitive pressure drives adoption faster than ROI alone. Hotels automate because **rivals did**, not just because payback pencils.

**The Cascade Effect:**
- Marriott deploys → Hilton accelerates
- Hilton deploys → Hyatt evaluates
- Hyatt deploys → InterContinental responds
- Top 10 chains deploy → Mid-tier brands forced to follow

**Analyst View:**
Automation becomes **table stakes**, not competitive advantage. Companies that lag face:
- Higher labor costs (can't compete on pricing)
- Guest perception of "outdated" (especially Gen Z travelers)
- Talent attraction issues (workers prefer modern workplaces)

**Vendor Opportunity:**
Competitive dynamics create urgency. Sales cycles compress from 12 months to 6 months when buyer sees competitor deploy successfully.`
    }
  ];

  const marketInsights = {
    deployments: [
      { vendor: 'Savioke', vertical: 'Hospitality', count: '100+ properties', growth: '+45% YoY', marketShare: '~50%' },
      { vendor: 'MiR', vertical: 'Warehouse AMRs', count: '500+ facilities', growth: '+30% YoY', marketShare: '~25%' },
      { vendor: 'Locus Robotics', vertical: 'Warehouse Picking', count: '500+ facilities', growth: '+40% YoY', marketShare: '~20%' },
      { vendor: 'Universal Robots', vertical: 'Manufacturing Cobots', count: '50,000+ installs', growth: '+20% YoY', marketShare: '~35%' },
      { vendor: 'Diligent (Moxi)', vertical: 'Hospital Logistics', count: '50+ hospitals', growth: '+60% YoY', marketShare: '~40%' },
    ],
    roiBenchmarks: [
      { vertical: 'Hotel Delivery', typical: '14-18 months', best: '12 months', worst: '24 months' },
      { vertical: 'Warehouse AMRs', typical: '18-24 months', best: '14 months', worst: '30 months' },
      { vertical: 'Manufacturing Cobots', typical: '8-12 months', best: '6 months', worst: '18 months' },
      { vertical: 'Hospital Disinfection', typical: '12-18 months', best: '9 months', worst: '24 months' },
      { vertical: 'Warehouse Picking', typical: '24-30 months', best: '18 months', worst: '36 months' },
    ],
    trends: [
      { trend: 'Robotics-as-a-Service (RaaS)', adoption: '35% of new deployments', impact: 'Lowers CapEx barrier, accelerates adoption' },
      { trend: 'Computer Vision Picking', adoption: '25% of warehouse automation', impact: 'Eliminates standardization requirement' },
      { trend: 'Fleet Management Software', adoption: '80% of multi-robot deployments', impact: 'Enables 100+ robot coordination' },
      { trend: 'AI-Powered Navigation', adoption: '60% of AMRs', impact: 'Adapts to dynamic environments' },
    ]
  };

  return (
    <>
      <Head>
        <title>Robot Intelligence Brief | Daily Automation News & Analytics</title>
        <meta name="description" content="Daily roundup of robot deployments, ROI data, market trends, and vendor intelligence. Track automation adoption across hospitality, logistics, healthcare, and manufacturing." />
      </Head>

      <div className="min-h-screen bg-black text-white">
        {/* Navigation Bar */}
        <div className="border-b border-neutral-800">
          <div className="max-w-6xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2">
                <h1 className="text-lg font-semibold text-white">
                  <span className="text-white">READY</span>
                  {' '}
                  <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">→</span>
                  {' '}
                  <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">ROBOTS</span>
                </h1>
              </Link>
              <div className="flex items-center gap-4">
                <Link href="/" className="text-sm text-neutral-400 hover:text-emerald-400 transition-colors">
                  ← Back to Home
                </Link>
                {!isSubscribed && (
                  <button
                    onClick={() => document.getElementById('subscribe-form').scrollIntoView({ behavior: 'smooth' })}
                    className="text-sm px-4 py-2 border-2 border-emerald-500 text-emerald-400 rounded-lg hover:border-cyan-500 hover:text-cyan-400 transition-colors"
                  >
                    Subscribe Free
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <div className="border-b border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-8 text-center">
            <div className="mb-3 text-xs text-emerald-400">
              📰 ROBOT INTELLIGENCE BRIEF
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-3 text-white">
              Daily Automation News with Signal Intelligence
            </h1>
            <p className="text-base text-neutral-400 mb-4 max-w-2xl mx-auto">
              Real-world robot deployments, ROI benchmarks, vendor market share, and technology trends. 
              Robot Ready Sales Leads with Signal Intelligence.
            </p>
            <div className="text-xs text-neutral-500">
              <span className="text-emerald-400">✓</span> Daily Roundups · <span className="text-emerald-400">✓</span> ROI Benchmarks · <span className="text-emerald-400">✓</span> Hot Deals · <span className="text-emerald-400">✓</span> Market Intelligence
            </div>
          </div>
        </div>

        {/* Latest Edition Header */}
        <div className="border-b border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="text-xs text-neutral-500 mb-1">LATEST EDITION {latestEdition.edition}</div>
                <h2 className="text-2xl font-bold text-white mb-1">{latestEdition.headline}</h2>
                <p className="text-sm text-neutral-400">{latestEdition.subheadline}</p>
              </div>
              <div className="text-right">
                <div className="text-xs text-neutral-500">Published</div>
                <div className="text-sm text-emerald-400">{latestEdition.date}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Top Stories */}
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-xl">🔥</span> Top Stories
          </h3>

          <div className="space-y-4">
            {topStories.map((story, idx) => (
              <div 
                key={idx} 
                className={`border-2 rounded-lg p-4 transition-all duration-300 ${
                  expandedStories[idx] 
                    ? 'border-emerald-500 bg-emerald-950/20 shadow-lg shadow-emerald-500/10' 
                    : 'border-neutral-800 hover:border-emerald-500/50'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                      {story.category}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></div>
                      <span className="text-xs text-emerald-400 font-semibold">{story.signalStrength}/10</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => toggleStory(idx)}
                  className="w-full text-left group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-white mb-1 group-hover:text-emerald-400 transition-colors">
                        {story.company}
                      </h4>
                      <h5 className="text-base text-emerald-400 mb-3 group-hover:text-cyan-400 transition-colors">
                        {story.headline}
                      </h5>
                    </div>
                    <div className={`text-emerald-400 text-2xl transition-transform duration-300 ${expandedStories[idx] ? 'rotate-180' : ''}`}>
                      ▼
                    </div>
                  </div>

                  {/* Preview (always visible) */}
                  <p className="text-sm text-neutral-400 mb-3 italic">{story.snippet}</p>

                  {/* Quick Stats - Enhanced with icons */}
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="bg-neutral-900/50 rounded px-2 py-1.5 border border-neutral-800">
                      <div className="text-[10px] text-neutral-500 uppercase mb-0.5">💰 ROI</div>
                      <div className="text-xs text-emerald-400 font-semibold">{story.roi}</div>
                    </div>
                    <div className="bg-neutral-900/50 rounded px-2 py-1.5 border border-neutral-800">
                      <div className="text-[10px] text-neutral-500 uppercase mb-0.5">💵 Economics</div>
                      <div className="text-xs text-cyan-400 font-semibold">{story.economics}</div>
                    </div>
                    <div className="bg-neutral-900/50 rounded px-2 py-1.5 border border-neutral-800">
                      <div className="text-[10px] text-neutral-500 uppercase mb-0.5">📊 Impact</div>
                      <div className="text-xs text-amber-400 font-semibold">{story.impact}</div>
                    </div>
                  </div>
                </button>

                {/* Collapseable Full Story */}
                <div 
                  className={`overflow-hidden transition-all duration-500 ${
                    expandedStories[idx] ? 'max-h-[2000px] opacity-100 mt-4' : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="pt-4 border-t border-emerald-500/30 space-y-3">
                    {story.fullText.split('\n\n').map((para, pIdx) => (
                      <p key={pIdx} className="text-neutral-300 text-sm leading-relaxed whitespace-pre-line">
                        {para}
                      </p>
                    ))}
                    
                    <div className="mt-4 pt-3 border-t border-neutral-800 flex items-center gap-2 text-xs text-neutral-500">
                      <span>Click to collapse</span>
                      <span className="text-emerald-400">▲</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Intelligence (now available to all) */}
        <div className="border-t border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-xl">📊</span> Market Intelligence
            </h3>

            <div className="space-y-6">
              {/* Vendor Deployments */}
              <div>
                <h4 className="text-base font-semibold text-emerald-400 mb-3">Vendor Deployment Tracking</h4>
                <div className="border border-neutral-800 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-neutral-900 border-b border-neutral-800">
                      <tr>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Vendor</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Vertical</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Deployments</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Growth</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Market Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marketInsights.deployments.map((item, idx) => (
                        <tr key={idx} className="border-b border-neutral-800 hover:bg-neutral-900/50">
                          <td className="p-2 text-sm text-white font-semibold">{item.vendor}</td>
                          <td className="p-2 text-sm text-neutral-400">{item.vertical}</td>
                          <td className="p-2 text-sm text-cyan-400">{item.count}</td>
                          <td className="p-2 text-sm text-emerald-400">{item.growth}</td>
                          <td className="p-2 text-sm text-amber-400">{item.marketShare}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* ROI Benchmarks */}
              <div>
                <h4 className="text-base font-semibold text-emerald-400 mb-3">ROI Benchmarking by Vertical</h4>
                <div className="border border-neutral-800 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-neutral-900 border-b border-neutral-800">
                      <tr>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Vertical</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Typical Payback</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Best Case</th>
                        <th className="text-left p-2 text-xs text-neutral-400 font-semibold">Worst Case</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marketInsights.roiBenchmarks.map((item, idx) => (
                        <tr key={idx} className="border-b border-neutral-800 hover:bg-neutral-900/50">
                          <td className="p-2 text-sm text-white font-semibold">{item.vertical}</td>
                          <td className="p-2 text-sm text-cyan-400">{item.typical}</td>
                          <td className="p-2 text-sm text-emerald-400">{item.best}</td>
                          <td className="p-2 text-sm text-amber-400">{item.worst}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Technology Trends */}
              <div>
                <h4 className="text-base font-semibold text-emerald-400 mb-3">Technology Adoption Trends</h4>
                <div className="space-y-2">
                  {marketInsights.trends.map((item, idx) => (
                    <div key={idx} className="border border-neutral-800 rounded p-3 hover:border-emerald-500/30 transition-colors">
                      <div className="flex items-start justify-between mb-1">
                        <h5 className="text-sm font-semibold text-white">{item.trend}</h5>
                        <span className="text-sm text-cyan-400">{item.adoption}</span>
                      </div>
                      <p className="text-sm text-neutral-400">{item.impact}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Subscribe CTA */}
        {!isSubscribed && (
          <div id="subscribe-form" className="border-t border-neutral-800">
            <div className="max-w-2xl mx-auto px-4 py-10 text-center">
              <div className="text-3xl mb-3">🚀</div>
              <h3 className="text-2xl font-bold text-white mb-3">
                Never Miss a Robot Intelligence Brief
              </h3>
              <p className="text-base text-neutral-400 mb-6">
                Get this delivered to your inbox daily. Free deployment data, hot deals, ROI benchmarks, and vendor intelligence with Signal Intelligence.
              </p>

              <form onSubmit={handleSubscribe} className="max-w-md mx-auto">
                <div className="flex gap-3 mb-6">
                  <input
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="flex-1 px-4 py-3 bg-neutral-900 border border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    type="submit"
                    className="px-6 py-3 border-2 border-emerald-500 text-emerald-400 rounded-lg hover:border-cyan-500 hover:text-cyan-400 transition-colors font-semibold whitespace-nowrap"
                  >
                    Subscribe
                  </button>
                </div>
              </form>

              <div className="text-xs text-neutral-500">
                <span className="text-emerald-400">✓</span> Daily deployment roundups · <span className="text-emerald-400">✓</span> ROI benchmarking · <span className="text-emerald-400">✓</span> Vendor market share · <span className="text-emerald-400">✓</span> Technology trends
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="border-t border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-6 text-center text-xs text-neutral-500">
            <p className="mb-2">
              <span className="text-white">READY</span>
              {' '}
              <span className="text-emerald-400">→</span>
              {' '}
              <span className="text-emerald-400">ROBOTS</span>
              {' | '}
              Robot Ready Sales Leads with Signal Intelligence
            </p>
            <p>Daily deployment roundups, ROI benchmarks, and hot deals across labor-intensive industries.</p>
          </div>
        </div>
      </div>
    </>
  );
}
