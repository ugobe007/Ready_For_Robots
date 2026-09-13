import { useState, useEffect } from "react";
import { Quote, Sparkles, CheckCircle2, ChevronRight, ChevronLeft, Building2, Zap, Trophy } from "lucide-react";
import { FEATURED_BUYER_QUOTES, type BuyerQuote } from "@/lib/buyerQuotes";
import { Link } from "wouter";

export default function CustomerQuoteBanner() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const activeQuote: BuyerQuote = FEATURED_BUYER_QUOTES[currentIndex];

  // Auto rotate quotes every 8 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % FEATURED_BUYER_QUOTES.length);
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % FEATURED_BUYER_QUOTES.length);
  };

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + FEATURED_BUYER_QUOTES.length) % FEATURED_BUYER_QUOTES.length);
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <div className="relative overflow-hidden rounded-3xl border border-amber-500/30 bg-gradient-to-br from-[#1b122c] via-[#140e2b] to-[#0c1830] p-6 sm:p-8 shadow-2xl shadow-amber-950/20">
        <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-amber-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -left-12 -bottom-12 h-48 w-48 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10">
          {/* Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-4 mb-5">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/40 bg-amber-500/15 px-3 py-1 text-[11px] font-mono font-bold text-amber-300 uppercase tracking-wider">
                <Quote className="h-3.5 w-3.5 text-amber-400" />
                <span>Daily Customer Voice & Automation Intent</span>
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-bold">
                <CheckCircle2 className="h-3 w-3" /> Verified Buyer Quote
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handlePrev}
                className="rounded-full border border-white/10 bg-white/5 p-1.5 text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
                title="Previous Quote"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs font-mono text-slate-400">
                {currentIndex + 1} / {FEATURED_BUYER_QUOTES.length}
              </span>
              <button
                onClick={handleNext}
                className="rounded-full border border-white/10 bg-white/5 p-1.5 text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
                title="Next Quote"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Quote Body */}
          <div className="grid gap-6 md:grid-cols-12 items-center">
            <div className="md:col-span-8 space-y-4">
              <blockquote className="text-base sm:text-lg italic font-medium leading-relaxed text-slate-100">
                &ldquo;{activeQuote.quote}&rdquo;
              </blockquote>

              <div className="flex flex-wrap items-center gap-3 text-xs">
                <div className="flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-500/20 border border-amber-400/40 text-amber-300 font-bold text-sm">
                    {activeQuote.author.charAt(0)}
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-sm leading-tight">{activeQuote.author}</h4>
                    <p className="text-[11px] text-amber-300/90 font-mono">
                      {activeQuote.title} · <strong className="text-slate-200">{activeQuote.company}</strong>
                    </p>
                  </div>
                </div>

                <span className="hidden sm:inline text-slate-600">|</span>

                <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-300">
                  <Building2 className="h-3.5 w-3.5 text-purple-400" />
                  <span>{activeQuote.industry}</span>
                </div>
              </div>
            </div>

            {/* Right Card CTA & Specs */}
            <div className="md:col-span-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4 space-y-3">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 uppercase">
                <span>Timeline</span>
                <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  {activeQuote.timeline}
                </span>
              </div>

              <div>
                <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5">
                  Looking for Robots:
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {activeQuote.targetRobotTypes.map((type, i) => (
                    <span
                      key={i}
                      className="rounded-lg bg-purple-500/20 border border-purple-500/30 px-2 py-1 text-[11px] font-mono text-purple-200 font-bold"
                    >
                      {type}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-white/10">
                <Link
                  href="/pricing"
                  className="w-full inline-flex items-center justify-center gap-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-amber-500/20 transition-all"
                >
                  <Zap className="h-3.5 w-3.5 fill-slate-950" />
                  <span>Activate Outreach ($19.99/mo)</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
