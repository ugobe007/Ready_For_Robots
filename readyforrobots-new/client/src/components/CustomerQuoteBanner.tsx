import { useState, useEffect } from "react";
import { ChevronRight, ChevronLeft, ArrowUpRight } from "lucide-react";
import { FEATURED_BUYER_QUOTES, type BuyerQuote } from "@/lib/buyerQuotes";
import { Link } from "wouter";

export default function CustomerQuoteBanner() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const activeQuote: BuyerQuote = FEATURED_BUYER_QUOTES[currentIndex];

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
    setCurrentIndex(
      (prev) => (prev - 1 + FEATURED_BUYER_QUOTES.length) % FEATURED_BUYER_QUOTES.length
    );
  };

  return (
    <div className="w-full py-1">
      {/* Supabase-style inline quote beat — zero heavy box padding */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 text-left">
        <div className="flex-1 space-y-1">
          <p className="text-xs sm:text-sm italic font-medium text-slate-200 leading-relaxed">
            &ldquo;{activeQuote.quote}&rdquo;
          </p>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="font-bold text-amber-300 font-display">
              — {activeQuote.author}
            </span>
            <span className="text-slate-400">
              {activeQuote.title}, <strong className="text-slate-200">{activeQuote.company}</strong>
            </span>
            <span className="text-slate-600">·</span>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-0.5 text-emerald-400 hover:text-emerald-300 font-mono font-bold text-[11px] underline underline-offset-2"
            >
              <span>Activate Outreach ($19.99/mo)</span>
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
