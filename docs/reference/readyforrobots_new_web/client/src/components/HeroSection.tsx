/**
 * HeroSection — "Precision Craft" design
 * Live pipeline card: homepage spotlight leads + expandable CRM/signal detail.
 */

import LeadDetailPanel from "@/components/leads/LeadDetailPanel";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import type { LeadRow } from "@/lib/leadTypes";
import { signalDisplayExcerpt } from "@/lib/leadTypes";
import { cn } from "@/lib/utils";
import { ChevronDownIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation } from "wouter";

const HERO_BG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/L4rJPcZu4nTBCWZaQPghsQ/rfr-hero-bg-4v95aUL282YYEFnwDGvtP8.webp";

const STATIC_FALLBACK: LeadRow[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    industry: "Labor shortage + 2 new DCs",
    priority_tier: "HOT",
    score: { overall_score: 84 },
    signals: [],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels Corp.",
    industry: "Staffing crisis + expansion",
    priority_tier: "HOT",
    score: { overall_score: 79 },
    signals: [],
  },
  {
    id: -3,
    company_name: "Pepsi Beverage Co.",
    industry: "OSHA citation + CapEx signal",
    priority_tier: "HOT",
    score: { overall_score: 71 },
    signals: [],
  },
];

function heroSubline(lead: LeadRow): string {
  const cn = (lead.core_need || "").replace(/\n/g, " ").trim();
  if (cn.length > 72) return cn.slice(0, 69) + "…";
  if (cn) return cn;
  const s = lead.signals?.[0];
  const t = s ? signalDisplayExcerpt(s) : "";
  if (t.length > 72) return t.slice(0, 69) + "…";
  if (t) return t;
  return lead.industry || "";
}

export default function HeroSection() {
  const [, setLocation] = useLocation();
  const [urlInput, setUrlInput] = useState("");
  const [visibleLeads, setVisibleLeads] = useState(0);
  const [apiLeads, setApiLeads] = useState<LeadRow[] | null>(null);
  const [expandedHeroId, setExpandedHeroId] = useState<number | null>(null);

  const rows = useMemo(() => (apiLeads && apiLeads.length ? apiLeads : STATIC_FALLBACK), [apiLeads]);

  useEffect(() => {
    setVisibleLeads(0);
  }, [rows]);

  useEffect(() => {
    const timer = setInterval(() => {
      setVisibleLeads((v) => (v < rows.length ? v + 1 : v));
    }, 400);
    return () => clearInterval(timer);
  }, [rows.length]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const API = getApiBase();
        const r = await fetch(`${API}/api/leads/homepage?cb=${Date.now()}`, liveFetchInit());
        if (!r.ok || cancelled) return;
        const raw = await r.text();
        if (raw.trimStart().startsWith("<") || cancelled) return;
        const data = JSON.parse(raw) as { hotLeads?: LeadRow[] };
        const hl = data.hotLeads;
        if (Array.isArray(hl) && hl.length && !cancelled) {
          setApiLeads(hl.slice(0, 3));
        }
      } catch {
        /* keep fallback */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const scoreDisplay = (lead: LeadRow) => {
    const v = lead.score && typeof lead.score === "object" ? (lead.score as { overall_score?: number }).overall_score : undefined;
    return v != null ? Math.round(Number(v)) : "—";
  };

  return (
    <section
      id="pipeline"
      className="relative pt-24 pb-16 md:pt-32 md:pb-24 overflow-hidden"
      style={{
        background: "linear-gradient(135deg, #ffffff 0%, #f0fdf4 60%, #eff6ff 100%)",
      }}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `url(${HERO_BG})`,
          backgroundSize: "cover",
          backgroundPosition: "center right",
          opacity: 0.35,
        }}
      />

      <div className="container relative">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <div>
            <div className="flex items-center gap-2 mb-5">
              <span className="section-label">Signal Intelligence</span>
              <span className="text-xs text-gray-400">·</span>
              <span className="text-xs text-gray-500 font-mono-data">14 signal types · 150+ sources</span>
            </div>

            <h1
              className="text-5xl md:text-6xl font-extrabold text-gray-900 leading-[1.05] mb-6"
              style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.03em" }}
            >
              Find robot buyers
              <br />
              <span style={{ color: "oklch(0.527 0.154 162.5)" }}>before the RFP.</span>
            </h1>

            <p className="text-lg text-gray-600 leading-relaxed mb-6 max-w-lg">
              We track buying intent across 150+ sources — labor shortages, CapEx announcements, new facilities,
              executive hires. Paste your URL to see who&apos;s ready to buy today.
            </p>

            <form
              className="flex flex-col sm:flex-row gap-2 mb-4 max-w-xl"
              onSubmit={(e) => {
                e.preventDefault();
                const q = urlInput.trim();
                if (!q) {
                  setLocation("/dashboard");
                  return;
                }
                const looksLikeUrl = /^https?:\/\//i.test(q) || /^www\./i.test(q);
                setLocation(
                  looksLikeUrl ? "/dashboard" : `/dashboard?industry=${encodeURIComponent(q)}`
                );
              }}
            >
              <input
                type="text"
                name="company_url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="yourrobotics.com — see your top prospects"
                className="flex-1 min-w-0 rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
                autoComplete="url"
              />
              <button
                type="submit"
                className="inline-flex shrink-0 items-center justify-center gap-2 px-6 py-3 rounded-lg text-white font-semibold text-sm transition-all duration-150 hover:opacity-90 active:scale-[0.98] shadow-sm"
                style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
              >
                Preview pipeline
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                  <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </form>

            <div className="mb-6 flex flex-wrap gap-x-4 gap-y-2 text-sm">
              <a href="/dashboard" className="font-semibold hover:underline" style={{ color: "oklch(0.527 0.154 162.5)" }}>
                Browse all HOT leads this week →
              </a>
              <a href="/pipeline" className="font-semibold text-gray-600 hover:underline">
                Full pipeline →
              </a>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M7 1l1.5 4h4.2l-3.4 2.5 1.3 4L7 9 3.4 11.5l1.3-4L1.3 5H5.5z" fill="oklch(0.527 0.154 162.5)"/>
                </svg>
                No signup required
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <circle cx="7" cy="7" r="6" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5"/>
                  <path d="M4.5 7l2 2 3-3" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Instant results
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <rect x="1" y="3" width="12" height="9" rx="2" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5"/>
                  <path d="M5 3V2a2 2 0 014 0v1" stroke="oklch(0.527 0.154 162.5)" strokeWidth="1.5"/>
                </svg>
                Free trial
              </span>
            </div>
          </div>

          <div className="relative flex justify-center lg:justify-end">
            <div
              className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden"
              style={{ boxShadow: "0 20px 60px -10px rgba(5, 150, 105, 0.12), 0 4px 20px -4px rgba(0,0,0,0.08)" }}
            >
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-800" style={{ fontFamily: "'Bricolage Grotesque', sans-serif" }}>
                    Live Pipeline
                  </span>
                  <span className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: "oklch(0.982 0.016 162.5)", color: "oklch(0.527 0.154 162.5)" }}>
                    <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }} />
                    LIVE
                  </span>
                </div>
                <span className="text-xs text-gray-400 font-mono-data">{apiLeads ? "API" : "Demo"}</span>
              </div>

              <div className="divide-y divide-gray-200/90">
                {rows.map((lead, i) => {
                  const open = expandedHeroId === lead.id;
                  return (
                    <div
                      key={lead.id}
                      className="transition-all duration-500"
                      style={{
                        opacity: i < visibleLeads ? 1 : 0,
                        transform: i < visibleLeads ? "translateX(0)" : "translateX(12px)",
                      }}
                    >
                      <button
                        type="button"
                        className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-gray-50/80 gap-2"
                        onClick={() => setExpandedHeroId(open ? null : lead.id)}
                        aria-expanded={open}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div
                            className="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold text-white shrink-0"
                            style={{
                              backgroundColor:
                                i === 0 ? "oklch(0.527 0.154 162.5)" : i === 1 ? "oklch(0.488 0.243 264.376)" : "oklch(0.627 0.163 66.5)",
                            }}
                          >
                            {(lead.company_name || "?").charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <div className="text-sm font-semibold text-gray-900 truncate">{lead.company_name}</div>
                            <div className="text-xs text-gray-600 truncate">{heroSubline(lead)}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="badge-hot">🔥 HOT</span>
                          <span className="font-mono-data font-bold text-lg" style={{ color: "oklch(0.527 0.154 162.5)" }}>
                            {scoreDisplay(lead)}
                          </span>
                          <ChevronDownIcon className={cn("h-4 w-4 text-gray-400 transition-transform", open && "rotate-180")} />
                        </div>
                      </button>
                      {open ? (
                        <div className="px-3 pb-3 border-t border-gray-100 bg-gray-50/90 max-h-[min(70vh,22rem)] overflow-y-auto">
                          <LeadDetailPanel
                            lead={lead}
                            density="compact"
                            showFullAnalysisLink={lead.id > 0}
                          />
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>

              <div
                className="px-4 py-2.5 border-t border-gray-100/90 flex items-center gap-2.5 bg-gradient-to-r from-amber-50/80 via-white to-emerald-50/40"
                role="status"
                aria-live="polite"
              >
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 border border-amber-100/80 bg-white/80"
                  aria-hidden
                >
                  <span className="text-sm leading-none">📈</span>
                </div>
                <div className="min-w-0">
                  <div className="text-[11px] font-semibold text-gray-900 leading-tight">New signal detected</div>
                  <div className="text-[11px] text-gray-500 truncate">&quot;Opening 2 new DCs next Q&quot;</div>
                </div>
              </div>

              <div className="px-5 py-3 border-t border-gray-50" style={{ backgroundColor: "oklch(0.982 0.016 162.5)" }}>
                <a href="/pipeline" className="text-xs font-semibold flex items-center gap-1 hover:gap-2 transition-all"
                  style={{ color: "oklch(0.527 0.154 162.5)" }}>
                  View pipeline & expand leads
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6h8M6 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
