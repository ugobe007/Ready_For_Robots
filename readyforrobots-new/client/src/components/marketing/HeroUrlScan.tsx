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
        Enter URL
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
              ? "min-w-0 flex-1 rounded-xl border-2 border-emerald-400/55 bg-slate-900/80 px-4 py-3 text-sm text-slate-50 placeholder-slate-300 shadow-sm outline-none transition-colors focus:border-emerald-300 focus:ring-2 focus:ring-emerald-300/30"
              : "min-w-0 flex-1 rounded-xl border-2 border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-400 shadow-sm outline-none transition-colors focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
          }
        />
        <button
          type="submit"
          className={
            onDark
              ? "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-transparent px-6 py-3 text-base font-semibold text-emerald-300 transition-all duration-150 hover:bg-emerald-500/10 hover:text-emerald-200 active:scale-[0.97]"
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
