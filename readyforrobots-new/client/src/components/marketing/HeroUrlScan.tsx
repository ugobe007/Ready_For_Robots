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
      className={`mb-3 max-w-xl rounded-2xl ${onDark ? "p-0" : ""}`}
    >
      <label
        htmlFor="hero-product-url"
        className={`mb-1.5 block text-xs font-semibold ${onDark ? "text-emerald-200" : "text-gray-600"}`}
      >
        Enter your company URL
      </label>
      <div className="flex flex-col gap-1.5 sm:flex-row">
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
              ? "min-w-0 flex-1 rounded-xl border border-white/15 bg-white/[0.06] px-4 py-3 text-sm text-slate-50 placeholder-slate-400 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] outline-none backdrop-blur-sm transition-all focus:border-emerald-300/70 focus:bg-slate-900/70 focus:ring-2 focus:ring-emerald-300/25"
              : "min-w-0 flex-1 rounded-xl border-2 border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-400 shadow-sm outline-none transition-colors focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
          }
        />
        <button
          type="submit"
          className={
            onDark
              ? "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-b from-emerald-400 to-emerald-500 px-6 py-3 text-base font-semibold text-slate-950 shadow-[0_8px_24px_-8px_rgba(16,185,129,0.65)] transition-all duration-150 hover:from-emerald-300 hover:to-emerald-400 hover:shadow-[0_10px_28px_-8px_rgba(16,185,129,0.8)] active:scale-[0.97]"
              : "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-transparent px-6 py-3 text-base font-semibold text-emerald-700 transition-all duration-150 hover:bg-emerald-50 active:scale-[0.97]"
          }
        >
          <Zap size={18} />
          Find leads
          <ArrowRight size={16} />
        </button>
      </div>
    </form>
  );
}
