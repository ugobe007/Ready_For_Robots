/**
 * New Member Onboarding / Welcome Landing Page — ReadyForRobots
 * Unlocked reports, sales leads, commercial proposals, and search navigation.
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import {
  CheckCircle2,
  Sparkles,
  FileSpreadsheet,
  Target,
  FileText,
  Search,
  ArrowRight,
  ShieldCheck,
  Zap,
  Building2,
  Bot,
  Layers,
  Share2,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import { useAuth } from "@/contexts/AuthContext";
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";

export default function Welcome() {
  const { session } = useAuth();
  const [, setLocation] = useLocation();
  const [copied, setCopied] = useState(false);

  const user = session?.user;
  const email = user?.email || "Member";
  const userDomain = email.includes("@") ? email.split("@")[1] : "";

  const handleCopyWorkspaceLink = async () => {
    try {
      const link = `${window.location.origin}/?visit=jobs`;
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(link);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      <ExperimentHeader />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-24 pb-16 space-y-10">
        {/* Welcome & Account Confirmation Banner */}
        <section className="relative overflow-hidden rounded-3xl border border-emerald-500/40 bg-gradient-to-r from-emerald-950/90 via-slate-900 to-cyan-950/90 p-6 sm:p-10 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 space-y-4">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Registration Confirmed · Free Workspace Active
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl sm:text-4xl font-extrabold text-white font-display tracking-tight leading-tight">
                  Welcome to ReadyForRobots, <span className="text-emerald-400">{email}</span>!
                </h1>
                <p className="mt-2 text-sm sm:text-base text-slate-300 max-w-2xl">
                  Your enterprise workspace is unlocked. You now have access to independent engineering feasibility benchmarks, 3D cell evaluation reports, verified buyer leads, and turnkey commercial proposal tools.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
                <Link
                  href="/?visit=jobs"
                  className="px-5 py-3 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-extrabold text-xs tracking-wide uppercase transition-all shadow-lg shadow-emerald-400/20 text-center flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Search className="w-4 h-4" />
                  Run Robot Search →
                </Link>
                <Link
                  href="/crm"
                  className="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs tracking-wide uppercase transition-all border border-slate-700 text-center flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Building2 className="w-4 h-4 text-emerald-400" />
                  Opportunity CRM →
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* 3 Unlocked Resource Hubs */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white font-display">
                Unlocked Member Features & Resources
              </h2>
              <p className="text-xs sm:text-sm text-slate-400">
                Select any hub below to access your unlocked reports, buyer signals, or generate proposals.
              </p>
            </div>

            <button
              type="button"
              onClick={handleCopyWorkspaceLink}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 text-xs font-mono text-slate-300 hover:text-white transition-colors cursor-pointer"
            >
              <Share2 className="w-3.5 h-3.5 text-emerald-400" />
              {copied ? "Link Copied!" : "Copy Share Link"}
            </button>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {/* Card 1: Engineering Feasibility Reports */}
            <div className="rounded-2xl border border-slate-800 bg-[#081126] p-6 flex flex-col justify-between hover:border-emerald-500/40 transition-all group shadow-xl">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 group-hover:scale-105 transition-transform">
                    <FileSpreadsheet className="w-6 h-6" />
                  </span>
                  <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                    Unlocked
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white font-display">
                    Engineering Feasibility & Reports
                  </h3>
                  <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                    Compare 200+ commercial robot models across duty cycles, payload capacities, floor navigation, and ISO safety standards.
                  </p>
                </div>

                <div className="space-y-2 pt-2">
                  <Link
                    href="/benchmark"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <Bot className="w-4 h-4 text-emerald-400" /> HEIR Humanoid Benchmark
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>

                  <Link
                    href="/reports/benchmarking"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-emerald-400" /> Industry Feasibility Reports
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>

                  <Link
                    href="/compare"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <Layers className="w-4 h-4 text-emerald-400" /> Robot Model Comparison
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-800 mt-6">
                <Link
                  href="/reports/benchmarking"
                  className="w-full py-2.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-bold text-xs tracking-wide uppercase transition-colors text-center block border border-emerald-500/30"
                >
                  Access All Reports →
                </Link>
              </div>
            </div>

            {/* Card 2: Verified Sales Leads & Signals */}
            <div className="rounded-2xl border border-slate-800 bg-[#081126] p-6 flex flex-col justify-between hover:border-amber-500/40 transition-all group shadow-xl">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-amber-500/30 bg-amber-500/10 text-amber-400 group-hover:scale-105 transition-transform">
                    <Target className="w-6 h-6" />
                  </span>
                  <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full">
                    Live Feed
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white font-display">
                    Sales Leads & Buyer Demand
                  </h3>
                  <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                    Access real-time commercial automation demand signals, facility expansions, and classified robot job opportunities.
                  </p>
                </div>

                <div className="space-y-2 pt-2">
                  <Link
                    href="/?visit=jobs"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-amber-400" /> Live Robot Jobs Feed
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>

                  <Link
                    href="/signals"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-amber-400" /> Real-Time Buyer Signals
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>

                  <Link
                    href="/marketplace"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-amber-400" /> Automation Marketplace
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-800 mt-6">
                <Link
                  href="/?visit=jobs"
                  className="w-full py-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 font-bold text-xs tracking-wide uppercase transition-colors text-center block border border-amber-500/30"
                >
                  Explore Buyer Leads →
                </Link>
              </div>
            </div>

            {/* Card 3: Commercial Proposals & CRM */}
            <div className="rounded-2xl border border-slate-800 bg-[#081126] p-6 flex flex-col justify-between hover:border-cyan-500/40 transition-all group shadow-xl">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 group-hover:scale-105 transition-transform">
                    <FileText className="w-6 h-6" />
                  </span>
                  <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-full">
                    Turnkey Quotes
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white font-display">
                    Commercial Proposals & CRM
                  </h3>
                  <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                    Build turnkey multi-vendor commercial proposals, CapEx vs. RaaS lease models, and manage your pipeline of buyer opportunities.
                  </p>
                </div>

                <div className="space-y-2 pt-2">
                  <Link
                    href="/crm"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-cyan-400" /> Opportunity CRM Desk
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>

                  <Link
                    href="/sales-console"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-cyan-400" /> Executive Sales Console
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>

                  <Link
                    href="/pricing"
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-200 hover:text-white transition-colors border border-slate-800"
                  >
                    <span className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-cyan-400" /> Upgrade Plan & Capacity
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </Link>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-800 mt-6">
                <Link
                  href="/crm"
                  className="w-full py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 font-bold text-xs tracking-wide uppercase transition-colors text-center block border border-cyan-500/30"
                >
                  Open Proposal Desk →
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Quick Navigation Action Banner */}
        <section className="rounded-2xl border border-slate-800 bg-[#081126] p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-left">
            <h3 className="text-lg font-bold text-white">
              Ready to explore jobs for your robot or run feasibility searches?
            </h3>
            <p className="text-xs sm:text-sm text-slate-400">
              Paste any robot product URL on the main site to run hardware task-matching and generate quotes.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0 w-full sm:w-auto">
            <Link
              href="/?visit=jobs"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-extrabold text-xs uppercase tracking-wider text-center flex items-center justify-center gap-2 transition-all cursor-pointer shadow-lg shadow-emerald-400/20"
            >
              <Search className="w-4 h-4" />
              Go to Main Site & Search →
            </Link>

            <Link
              href="/crm"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs uppercase tracking-wider text-center flex items-center justify-center gap-2 transition-all border border-slate-700 cursor-pointer"
            >
              Build CRM of Opportunities →
            </Link>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
