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
    <form onSubmit={submit} className="mb-4 max-w-xl">
      <label htmlFor="hero-product-url" className={`mb-2 block text-xs font-semibold ${onDark ? "text-slate-400" : "text-gray-600"}`}>
        Enter your product URL → see matched leads instantly
      </label>
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          id="hero-product-url"
          type="text"
          inputMode="url"
          autoComplete="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="yourcompany.com or product page URL"
          className={
            onDark
              ? "min-w-0 flex-1 rounded-xl border border-sky-300/30 bg-white/10 px-4 py-3.5 text-sm text-white placeholder-slate-500 shadow-sm outline-none transition-colors focus:border-sky-400/70 focus:ring-2 focus:ring-sky-400/25"
              : "min-w-0 flex-1 rounded-xl border-2 border-gray-200 bg-white px-4 py-3.5 text-sm text-gray-900 placeholder-gray-400 shadow-sm outline-none transition-colors focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
          }
        />
        <button
          type="submit"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-amber-500 px-6 py-3.5 text-base font-semibold text-slate-950 shadow-md transition-all duration-150 hover:bg-amber-400 hover:shadow-lg active:scale-[0.97]"
        >
          <Zap size={18} />
          Find buyers
          <ArrowRight size={16} />
        </button>
      </div>
      <p className={`mt-2 text-[11px] leading-relaxed ${onDark ? "text-slate-500" : "text-gray-600"}`}>
        See who is buying robots like yours —{" "}
        <span className={`font-semibold ${onDark ? "text-sky-200" : "text-sky-800"}`}>before your competitor&apos;s SDR does.</span>
      </p>
    </form>
  );
}
