import { useState, useEffect, useCallback } from "react";
import { ChevronRight, ChevronLeft, ArrowUpRight, CheckCircle2, Building2, MapPin, Zap } from "lucide-react";
import { FEATURED_BUYER_QUOTES, type BuyerQuote } from "@/lib/buyerQuotes";
import { Link } from "wouter";

export default function CustomerQuoteBanner() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const activeQuote: BuyerQuote = FEATURED_BUYER_QUOTES[currentIndex];

  const handleNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % FEATURED_BUYER_QUOTES.length);
  }, []);

  const handlePrev = useCallback(() => {
    setCurrentIndex(
      (prev) => (prev - 1 + FEATURED_BUYER_QUOTES.length) % FEATURED_BUYER_QUOTES.length
    );
  }, []);

  useEffect(() => {
    if (isPaused) return;
    const timer = setInterval(() => {
      handleNext();
    }, 7000);
    return () => clearInterval(timer);
  }, [isPaused, handleNext]);

  return (
    <div 
      className="w-full rounded-xl border border-slate-800/80 bg-gradient-to-r from-slate-950 via-[#0B1528] to-slate-950 p-3.5 sm:p-4 shadow-xl transition-all duration-300 hover:border-slate-700/80"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="flex flex-col gap-3">
        {/* Top Header Beat: Verified Customer Lead Status & Controls */}
        <div className="flex items-center justify-between gap-2 border-b border-slate-800/60 pb-2 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="h-3 w-3 text-emerald-400" />
              Verified Buyer Demand Quote
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-400/10 px-2 py-0.5 font-mono text-[10px] font-bold text-amber-300 border border-amber-400/20">
              <Zap className="h-3 w-3" />
              {activeQuote.heatTier || "HOT LEAD"}
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 text-slate-400 text-[11px]">
              <MapPin className="h-3 w-3 text-slate-500" />
              {activeQuote.location}
            </span>
          </div>

          {/* Carousel Navigation Controls */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-mono text-slate-400 mr-1">
              {currentIndex + 1} / {FEATURED_BUYER_QUOTES.length}
            </span>
            <button
              onClick={handlePrev}
              className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              title="Previous Quote"
              type="button"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleNext}
              className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              title="Next Quote"
              type="button"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Main Body: Customer Quote & Direct Job Opportunity Connection */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 text-left">
          <div className="flex-1 space-y-1.5">
            <p className="text-xs sm:text-sm italic font-medium text-slate-100 leading-relaxed">
              &ldquo;{activeQuote.quote}&rdquo;
            </p>

            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
              <span className="font-bold text-amber-300 font-display">
                — {activeQuote.author}
              </span>
              <span className="text-slate-300 font-medium">
                {activeQuote.title},
              </span>
              <span className="font-semibold text-emerald-300 flex items-center gap-1">
                <Building2 className="h-3 w-3 text-emerald-400 inline" />
                {activeQuote.company}
              </span>
              <span className="text-slate-600 hidden sm:inline">·</span>
              <span className="text-slate-400 text-[11px]">
                Seeking: <strong className="text-slate-200">{activeQuote.targetRobotTypes.join(" or ")}</strong>
              </span>
            </div>
          </div>

          {/* Direct CTA: Connect Quote to Customer Job Opportunity */}
          <div className="flex shrink-0 items-center gap-2 pt-1 lg:pt-0">
            <Link
              href={activeQuote.opportunityHref}
              className="inline-flex w-full lg:w-auto items-center justify-center gap-2 rounded-lg bg-emerald-500 px-3.5 py-2 text-xs font-semibold text-slate-950 transition-all duration-200 hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/20 active:scale-[0.98]"
            >
              <span className="truncate">
                Check Job Opportunity ({activeQuote.company})
              </span>
              <ArrowUpRight className="h-3.5 w-3.5 stroke-[2.5]" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
