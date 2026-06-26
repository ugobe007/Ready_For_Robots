import { useState } from "react";
import { ArrowRight, Zap } from "lucide-react";
import { useLocation } from "wouter";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { trackUrlScan } from "@/lib/siteAnalytics";

export default function HeroUrlScan() {
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
      <label htmlFor="hero-product-url" className="mb-2 block text-xs font-semibold text-gray-600">
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
          className="min-w-0 flex-1 rounded-xl border-2 border-gray-200 bg-white px-4 py-3.5 text-sm text-gray-900 placeholder-gray-400 shadow-sm outline-none transition-colors focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
        />
        <button
          type="submit"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3.5 text-base font-semibold text-white shadow-md transition-all duration-150 hover:bg-emerald-700 hover:shadow-lg active:scale-[0.97]"
        >
          <Zap size={18} />
          Find buyers
          <ArrowRight size={16} />
        </button>
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-gray-600">
        See who is buying robots like yours —{" "}
        <span className="font-semibold text-amber-800">before your competitor&apos;s SDR does.</span>
      </p>
    </form>
  );
}
