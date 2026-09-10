import { useState } from "react";
import { ArrowRight, Sparkles, Zap, CheckCircle2 } from "lucide-react";
import { useLocation } from "wouter";

interface WorkflowDriveBannerProps {
  title?: string;
  subtitle?: string;
  buttonText?: string;
  compact?: boolean;
}

export default function WorkflowDriveBanner({
  title = "Ready to Find Jobs for Your Robot?",
  subtitle = "Paste your robot URL to analyze target applications and generate your 25-lead buyer pipeline.",
  buttonText = "Build 25 Lead Pipeline",
  compact = false,
}: WorkflowDriveBannerProps) {
  const [url, setUrl] = useState("");
  const [, setLocation] = useLocation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setLocation("/pipeline");
      return;
    }
    const clean = url.trim().startsWith("http") ? url.trim() : `https://${url.trim()}`;
    setLocation(`/?url=${encodeURIComponent(clean)}`);
  };

  if (compact) {
    return (
      <div className="my-6 rounded-2xl border border-purple-500/30 bg-gradient-to-r from-[#120826] via-[#1b1035] to-[#0d162d] p-5 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-lg border border-purple-400/40 bg-purple-500/20 p-2 text-purple-300">
              <Zap className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-display text-base font-bold text-white">{title}</h3>
              <p className="text-xs text-slate-300">{subtitle}</p>
            </div>
          </div>
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <input
              type="text"
              placeholder="e.g. bostondynamics.com/stretch"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full md:w-64 rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2 text-xs text-white placeholder-slate-400 outline-none focus:border-purple-500"
            />
            <button
              type="submit"
              className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-xl bg-purple-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-purple-500/25 transition hover:bg-purple-500"
            >
              <span>{buttonText}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="my-10 rounded-3xl border border-purple-500/40 bg-gradient-to-br from-[#150a2e] via-[#1a1138] to-[#0c1630] p-8 shadow-2xl relative overflow-hidden">
      <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-purple-600/10 blur-3xl" />
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-xl space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-400/30 bg-purple-500/10 px-3 py-1 text-xs font-bold text-purple-300 uppercase tracking-widest">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>Product Workflow</span>
          </div>
          <h2 className="font-display text-2xl font-extrabold text-white sm:text-3xl tracking-tight">
            {title}
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            {subtitle}
          </p>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-2">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-purple-400" /> 25 Verified Leads
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-purple-400" /> Instant Task Alignment
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-purple-400" /> Ready-to-Send Outreach
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="w-full md:w-auto flex flex-col sm:flex-row items-stretch gap-2.5">
          <input
            type="text"
            placeholder="Paste robot URL (e.g., unitree.com/h1)..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full sm:w-72 rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm text-white placeholder-slate-400 outline-none focus:border-purple-500"
          />
          <button
            type="submit"
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-extrabold text-white shadow-lg shadow-purple-600/30 transition hover:bg-purple-500"
          >
            <span>{buttonText}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
