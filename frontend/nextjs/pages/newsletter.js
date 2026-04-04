import { useState, useEffect } from 'react';
import Link from 'next/link';
import Head from 'next/head';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import IndustryBriefBlock from '../components/IndustryBriefBlock';

// Base URL for share links
const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

function buildTweetText(headline, description) {
  // X posts: headline first (fresh/relevant), then first 2 sentences of summary.
  // Total budget ~250 chars (URL adds ~23, leaving room).
  const head = (headline || '').trim();
  const body = (description || '').trim();
  if (!head && !body) return 'Automation buying signals — Ready For Robots';
  if (!head) return body.slice(0, 240);
  if (!body) return head.slice(0, 240);
  // Combine: headline\n\nbody — truncate body so total fits
  const maxBody = 240 - head.length - 2;
  const truncBody = maxBody > 30 ? (body.length > maxBody ? body.slice(0, maxBody - 1) + '…' : body) : '';
  return truncBody ? `${head}\n\n${truncBody}` : head;
}

function ShareButtons({ url, title, headline, description, compact = false, id }) {
  const shareUrl = url || (typeof window !== 'undefined' ? `${window.location.origin}${window.location.pathname}` : `${BASE_URL}/newsletter`);
  const shareTitle = title || 'Daily Automation News | Automation Sales Leads with Actionable Signals';
  // LinkedIn gets the full description; X gets headline-first text
  const linkedInText = description || `${shareTitle} — Ready For Robots`;
  const tweetText = buildTweetText(headline || shareTitle, description);
  const copyId = id || 'share-copy';

  const links = {
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(tweetText)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
  };

  const copyLink = () => {
    navigator.clipboard?.writeText(shareUrl).then(() => {
      const btn = document.getElementById(copyId) || document.getElementById(`${copyId}-full`);
      if (btn) {
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = orig; }, 1500);
      }
    });
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-neutral-500 uppercase tracking-wider">Share:</span>
        <a href={links.linkedin} target="_blank" rel="noopener noreferrer" aria-label="Share on LinkedIn"
          className="p-1.5 rounded bg-neutral-800 hover:bg-[#0a66c2] text-neutral-400 hover:text-white transition-colors">
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        </a>
        <a href={links.twitter} target="_blank" rel="noopener noreferrer" aria-label="Share on X"
          className="p-1.5 rounded bg-neutral-800 hover:bg-black text-neutral-400 hover:text-white transition-colors">
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
        <a href={links.facebook} target="_blank" rel="noopener noreferrer" aria-label="Share on Facebook"
          className="p-1.5 rounded bg-neutral-800 hover:bg-[#1877f2] text-neutral-400 hover:text-white transition-colors">
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
        </a>
        <button id={copyId} onClick={copyLink} aria-label="Copy link"
          className="px-2 py-1 rounded bg-neutral-800 hover:bg-emerald-600 text-neutral-400 hover:text-white text-[10px] font-medium transition-colors">
          Link
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="text-sm text-neutral-400">Share this:</span>
      <a href={links.linkedin} target="_blank" rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-[#0a66c2] text-neutral-300 hover:text-white transition-colors text-sm font-medium">
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        LinkedIn
      </a>
      <a href={links.twitter} target="_blank" rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-black text-neutral-300 hover:text-white transition-colors text-sm font-medium">
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        X
      </a>
      <a href={links.facebook} target="_blank" rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-[#1877f2] text-neutral-300 hover:text-white transition-colors text-sm font-medium">
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
        Facebook
      </a>
      <button id={`${copyId}-full`} onClick={copyLink}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-emerald-600 text-neutral-300 hover:text-white transition-colors text-sm font-medium">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
        Copy link
      </button>
    </div>
  );
}

function CopyStoryButton({ story, buttonId, socialMode = false }) {
  const [copied, setCopied] = useState(false);
  const copyContent = () => {
    let text;
    if (socialMode) {
      // Social mode: just the intelligence summary + URL — perfect header for a post
      const summary = story.summary || story.snippet || `${story.company}: ${story.headline}`;
      text = `${summary}\n\n🤖 More at readyforrobots.com/newsletter/`;
    } else {
      // Full content mode: summary as header, then body
      const summary = story.summary || story.snippet || '';
      const body = (story.fullText || '').trim();
      text = [
        `${story.company}: ${story.headline}`,
        summary ? `\n\n${summary}` : '',
        body ? `\n\n${body}` : '',
        '\n\n🤖 readyforrobots.com/newsletter/',
      ].filter(Boolean).join('');
    }
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      id={buttonId}
      type="button"
      onClick={copyContent}
      aria-label={socialMode ? 'Copy for social post' : 'Copy full content'}
      className={`px-2 py-1 rounded text-[10px] font-medium transition-colors whitespace-nowrap ${
        socialMode
          ? 'bg-emerald-900/40 hover:bg-emerald-600 text-emerald-400 hover:text-white border border-emerald-800/50'
          : 'bg-neutral-800 hover:bg-emerald-600 text-neutral-400 hover:text-white'
      }`}
    >
      {copied ? 'Copied!' : socialMode ? 'Copy for social' : 'Copy content'}
    </button>
  );
}

const API_BASE = getApiBase();

// Fallback edition when API returns empty
const FALLBACK_EDITION = {
  date: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
  edition: `#${Math.floor(Date.now() / 86400000) % 365}`,
  headline: 'Automation Sales Leads with Actionable Signals',
  subheadline: 'Daily roundup of robot-ready companies and buying intent. 14 signal types · 150+ sources.'
};

const FALLBACK_STORIES = [
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

export default function Newsletter() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [email, setEmail] = useState('');
  const [showPreview, setShowPreview] = useState(true);
  const [expandedStories, setExpandedStories] = useState({});
  const [edition, setEdition] = useState(FALLBACK_EDITION);
  const [topStories, setTopStories] = useState(FALLBACK_STORIES);
  const [industryBrief, setIndustryBrief] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const subscribed = localStorage.getItem('newsletter_subscribed') === 'true';
    setIsSubscribed(subscribed);
    setShowPreview(!subscribed);
  }, []);

  useEffect(() => {
    const fetchEdition = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/newsletter/edition?limit=8`, liveFetchInit());
        const data = await res.json();
        if (data?.latestEdition) setEdition(data.latestEdition);
        if (data?.topStories?.length > 0) setTopStories(data.topStories);
        if (data?.industryBrief) setIndustryBrief(data.industryBrief);
      } catch (err) {
        console.error('Newsletter fetch:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchEdition();
  }, []);

  const toggleStory = (idx) => {
    setExpandedStories(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleSubscribe = (e) => {
    e.preventDefault();
    localStorage.setItem('newsletter_subscribed', 'true');
    setIsSubscribed(true);
    setShowPreview(false);
    alert(`✅ Subscribed! Welcome to the Robot Intelligence Brief.\n\nYou'll receive:\n• Daily automation leads\n• ROI benchmarking data\n• Hot deals with actionable signals (share to X, LinkedIn)\n• Deployment roundups & vendor insights`);
  };

  const latestEdition = edition;

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
        <title>Robot Intelligence Brief | Automation Sales Leads with Actionable Signals</title>
        <meta name="description" content="Daily automation news and hot leads. Real companies with buying signals — labor shortages, CapEx, expansion. Automation Sales Leads with Actionable Signals." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={`${BASE_URL}/newsletter`} />
        <meta property="og:title" content="Robot Intelligence Brief | Automation Sales Leads with Actionable Signals" />
        <meta property="og:description" content="Daily automation news and hot leads. Real companies with buying signals. Automation Sales Leads with Actionable Signals." />
        <meta property="og:image" content={`${BASE_URL}/og-logo.png`} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="Ready for Robots" />
        <meta name="twitter:card" content="summary_large_image" />
        {/* Pythia glyph used for all @pythh X posts — drop delphi-pythia-icon-glyph-dark.jpg into public/images/ */}
        <meta name="twitter:image" content={`${BASE_URL}/images/delphi-pythia-icon-glyph-dark.jpg`} />
        <meta name="twitter:title" content="Robot Intelligence Brief | Automation Sales Leads with Actionable Signals" />
        <meta name="twitter:description" content="Daily automation news and hot leads. Real companies with buying signals." />
      </Head>

      <div className="min-h-screen bg-black text-white">
        {/* Navigation Bar */}
        <div className="border-b border-neutral-800">
          <div className="max-w-6xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2">
                <img src="/logo-r.png" alt="Ready For Robots" className="w-12 h-12 object-contain" />
              </Link>
              <div className="flex items-center gap-4">
                <Link href="/" className="text-sm text-neutral-400 hover:text-emerald-400 transition-colors">
                  ← Back to Home
                </Link>
                <Link href="/social" className="text-sm text-violet-400 hover:text-violet-300 transition-colors">
                  Content Studio
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
              Daily Automation News
            </h1>
            <p className="text-base text-neutral-400 mb-4 max-w-2xl mx-auto">
              Automation Sales Leads with Actionable Signals. We track buying intent across 150+ sources — labor shortages, CapEx, new facilities, executive hires.
            </p>
            <div className="text-xs text-neutral-500">
              <span className="text-emerald-400">✓</span> 14 Signal Types · <span className="text-emerald-400">✓</span> Daily Roundups · <span className="text-emerald-400">✓</span> ROI Benchmarks · <span className="text-emerald-400">✓</span> Hot Deals · <span className="text-emerald-400">✓</span> Share to social
            </div>
          </div>
        </div>

        {/* Latest Edition Header */}
        <div className="border-b border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <div className="flex items-start justify-between mb-4 flex-wrap gap-4">
              <div>
                <div className="text-xs text-neutral-500 mb-1">LATEST EDITION {latestEdition.edition}</div>
                <h2 className="text-2xl font-bold text-white mb-1">{latestEdition.headline}</h2>
                <p className="text-sm text-neutral-400">{latestEdition.subheadline}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="text-right">
                  <div className="text-xs text-neutral-500">Published</div>
                  <div className="text-sm text-emerald-400">{latestEdition.date}</div>
                </div>
                <ShareButtons
                  headline={latestEdition.headline}
                  title={latestEdition.headline}
                  description={`${latestEdition.headline} — ${latestEdition.subheadline}`}
                />
              </div>
            </div>
          </div>
        </div>

        {industryBrief && (
          <div className="border-b border-neutral-800">
            <div className="max-w-4xl mx-auto px-4 py-6">
              <IndustryBriefBlock brief={industryBrief} />
            </div>
          </div>
        )}

        {/* Top Stories */}
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-xl">🔥</span> Top Stories
            {loading && <span className="text-sm font-normal text-neutral-500">Loading fresh leads...</span>}
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
                <div className="flex items-start justify-between mb-3 gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                      {story.category}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></div>
                      <span className="text-xs text-emerald-400 font-semibold">{story.signalStrength}/10</span>
                    </div>
                  </div>
                  <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-2">
                    <ShareButtons
                      compact
                      id={`share-story-${idx}`}
                      headline={`${story.company}: ${story.headline}`}
                      title={`${story.company}: ${story.headline}`}
                      description={story.summary || story.snippet || `${story.company} — ${story.headline}`}
                    />
                    <CopyStoryButton story={story} buttonId={`copy-story-${idx}`} socialMode />
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
                      <div className="text-xs text-cyan-400 font-semibold">{(story.economics || '').replace(/\bUnknown\b/gi, 'New')}</div>
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
                    expandedStories[idx] ? 'max-h-[3000px] opacity-100 mt-4' : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="pt-4 border-t border-emerald-500/30 space-y-4">

                    {/* Intelligence summary — prominent, social-ready */}
                    {story.summary && (
                      <div className="rounded-lg bg-neutral-900/70 border border-emerald-900/50 p-4 space-y-3">
                        <div className="text-[10px] font-semibold text-emerald-500 uppercase tracking-wider">Intelligence Summary</div>
                        <p className="text-sm text-neutral-200 leading-relaxed">{story.summary}</p>
                        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-neutral-800">
                          <span className="text-[10px] text-neutral-500">Post this to social:</span>
                          <ShareButtons
                            compact
                            id={`share-summary-${idx}`}
                            headline={`${story.company}: ${story.headline}`}
                            title={`${story.company}: ${story.headline}`}
                            description={story.summary}
                          />
                          <CopyStoryButton story={story} buttonId={`copy-social-${idx}`} socialMode />
                        </div>
                      </div>
                    )}

                    {/* Full signal breakdown */}
                    <div className="select-text rounded bg-neutral-900/50 p-3 border border-neutral-800" role="article">
                      {(story.fullText || '').split('\n\n').map((para, pIdx) => (
                        <p key={pIdx} className="text-neutral-300 text-sm leading-relaxed whitespace-pre-line mb-3 last:mb-0">
                          {para}
                        </p>
                      ))}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <CopyStoryButton story={story} buttonId={`copy-story-expanded-${idx}`} />
                      {story.company_id && (
                        <Link href={`/dashboard?analyze=${story.company_id}`} className="inline-flex items-center gap-2 text-sm text-emerald-400 hover:text-emerald-300">
                          View full AI analysis →
                        </Link>
                      )}
                    </div>

                    <div className="pt-3 border-t border-neutral-800 flex items-center gap-2 text-xs text-neutral-500">
                      <span>Select text to copy, or use buttons above. Click to collapse</span>
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
                Get this delivered to your inbox daily. Free automation leads, hot deals, and actionable signals.
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

        {/* Share our banner */}
        <div className="border-t border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <span className="text-xl">📣</span> Share Ready For Robots
            </h3>
            <p className="text-sm text-neutral-400 mb-4">
              Use our banner with any social post. On the homepage, every hot lead has a Share button — post to X or LinkedIn with one click.
            </p>
            <div className="border-2 border-neutral-800 rounded-lg overflow-hidden bg-neutral-900/50">
              <a href={`${BASE_URL}`} target="_blank" rel="noopener noreferrer" className="block">
                <img
                  src="/og-logo.png"
                  alt="Ready For Robots - Automation Sales Leads with Actionable Signals"
                  className="w-full h-auto"
                  style={{ maxHeight: '320px', objectFit: 'cover' }}
                />
              </a>
              <div className="p-4 flex flex-wrap items-center justify-between gap-4 border-t border-neutral-800">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-neutral-500">Link:</span>
                  <code className="text-sm text-emerald-400 bg-neutral-800 px-2 py-1 rounded">{BASE_URL.replace(/^https?:\/\//, '')}</code>
                </div>
                <ShareButtons url={BASE_URL} id="banner-share" title="Ready For Robots" description="Automation Sales Leads with Actionable Signals. Daily automation news and hot leads." />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-800">
          <div className="max-w-4xl mx-auto px-4 py-6 text-center text-xs text-neutral-500">
            <p className="mb-2 flex items-center justify-center gap-2">
              <img src="/logo-r.png" alt="Ready For Robots" className="w-6 h-6 object-contain" />
              <span>Robot Automation Sales Leads with Actionable Signals</span>
            </p>
            <p>Daily deployment roundups, ROI benchmarks, and hot deals across labor-intensive industries.</p>
          </div>
        </div>
      </div>
    </>
  );
}
