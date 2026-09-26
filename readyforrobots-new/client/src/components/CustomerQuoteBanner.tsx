import { useState, useEffect, useCallback } from "react";
import { ChevronRight, ChevronLeft, ArrowUpRight } from "lucide-react";
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
      className="w-full py-1 text-left"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="flex flex-col gap-1.5">
        {/* Quote Text */}
        <p className="text-xs sm:text-sm italic font-medium text-slate-200 leading-relaxed">
          &ldquo;{activeQuote.quote}&rdquo;
        </p>

        {/* Inline Author, Company & Direct Job Opportunity Link (Supabase Style) */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
          <span className="font-bold text-amber-300 font-display">
            — {activeQuote.author}
          </span>
          <span className="text-slate-400">
            {activeQuote.title}, <strong className="text-slate-200">{activeQuote.company}</strong>
          </span>
          <span className="text-slate-600">·</span>

          {/* Supabase-style Inline Link to Job Lead */}
          <Link
            href={activeQuote.opportunityHref}
            className="inline-flex items-center gap-0.5 text-emerald-400 hover:text-emerald-300 font-mono font-bold text-[11px] underline underline-offset-2 transition-colors"
          >
            <span>View {activeQuote.company} Job Opportunity ({activeQuote.matchedJobTitle})</span>
            <ArrowUpRight className="h-3 w-3 shrink-0" />
          </Link>

          {/* Minimal Controls */}
          <div className="ml-auto flex items-center gap-1 text-[11px]">
            <span className="font-mono text-slate-500 mr-0.5 text-[10px]">
              {currentIndex + 1}/{FEATURED_BUYER_QUOTES.length}
            </span>
            <button
              onClick={handlePrev}
              className="p-0.5 text-slate-400 hover:text-slate-200 transition-colors"
              title="Previous Quote"
              type="button"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleNext}
              className="p-0.5 text-slate-400 hover:text-slate-200 transition-colors"
              title="Next Quote"
              type="button"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
