import { useState } from "react";
import { ArrowRight, Zap } from "lucide-react";
import { useLocation } from "wouter";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { trackUrlScan } from "@/lib/siteAnalytics";

type Props = {
  onDark?: boolean;
};

export default function HeroUrlScan({ onDark = false }: Props) {
  const [, setLocation] = useLocation();
  const [url, setUrl] = useState("");

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const normalized = normalizeUrl(url);
    if (!normalized) return;
    trackUrlScan(normalized, "home_hero");
    setLocation(`/results?url=${encodeURIComponent(normalized)}`);
  }

  return (
    <form
      onSubmit={submit}
      className={`mb-3 max-w-xl ${onDark ? "" : ""}`}
    >
      <label
        htmlFor="hero-product-url"
        className={`mb-2 block text-xs font-semibold tracking-wide ${onDark ? "text-emerald-300/80" : "text-gray-600"}`}
      >
        Enter your company URL
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          id="hero-product-url"
          type="text"
          inputMode="url"
          autoComplete="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="yourcompany.com or URL"
          className={
            onDark
              ? "min-w-0 flex-1 rounded-xl border border-white/20 bg-white/[0.08] px-5 py-3.5 text-sm text-slate-50 placeholder-slate-500 shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_1px_2px_rgba(0,0,0,0.3)] outline-none backdrop-blur-md transition-all duration-200 focus:border-emerald-400/60 focus:bg-white/[0.12] focus:shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_0_0_3px_rgba(52,211,153,0.18)] focus:outline-none"
              : "min-w-0 flex-1 rounded-xl border-2 border-gray-200 bg-white px-5 py-3.5 text-sm text-gray-900 placeholder-gray-400 shadow-sm outline-none transition-colors focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
          }
        />
        <button
          type="submit"
          className={
            onDark
              ? "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-b from-emerald-400 to-emerald-600 px-6 py-3.5 text-sm font-bold text-slate-950 shadow-[0_0_0_1px_rgba(52,211,153,0.6),0_8px_28px_-6px_rgba(16,185,129,0.7)] transition-all duration-200 hover:from-emerald-300 hover:to-emerald-500 hover:shadow-[0_0_0_1px_rgba(52,211,153,0.8),0_10px_32px_-6px_rgba(16,185,129,0.85)] active:scale-[0.97]"
              : "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3.5 text-sm font-bold text-white shadow-sm transition-all duration-150 hover:bg-emerald-700 active:scale-[0.97]"
          }
        >
          <Zap size={16} />
          Find leads
          <ArrowRight size={15} />
        </button>
      </div>
    </form>
  );
}
