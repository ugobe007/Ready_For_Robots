import { useState } from "react";
import { Mail, CheckCircle2, Sparkles, Lock, ArrowRight, X } from "lucide-react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { toast } from "sonner";

interface DailyMatchBriefModalProps {
  isOpen: boolean;
  onClose: () => void;
  robotUrl?: string;
  robotName?: string;
  topMatchesCount?: number;
}

export default function DailyMatchBriefModal({
  isOpen,
  onClose,
  robotUrl = "",
  robotName = "Scanned Robot",
  topMatchesCount = 5,
}: DailyMatchBriefModalProps) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !email.includes("@")) {
      toast.error("Please enter a valid email address.");
      return;
    }

    setSubmitting(true);
    try {
      const api = getApiBase();
      const res = await fetch(
        `${api}/api/robot-buyer-leads`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            name: name || "Robot OEM Representative",
            company: company || "Robot OEM / Integrator",
            useCase: `Daily Top 5-10 Job Match Brief for ${robotName} (${robotUrl})`,
            website: robotUrl,
            source: "daily_match_brief_modal",
          }),
        })
      );

      if (!res.ok) {
        throw new Error("Could not save daily brief preferences.");
      }

      setSubmitted(true);
      toast.success("Daily Match Brief activated! Check your inbox.");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to activate daily brief."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl border border-purple-500/30 bg-gradient-to-b from-[#120a2a] via-[#0d132b] to-[#080d1e] p-6 sm:p-8 shadow-2xl shadow-purple-950/50">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {submitted ? (
          <div className="text-center py-6">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <h3 className="mt-4 text-xl font-bold text-white font-display">
              Daily Brief Activated for {email}
            </h3>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">
              We saved <strong className="text-purple-300">{robotName}</strong> to your free profile. You will receive a daily email brief featuring top buyer job matches & customer intent quotes every morning.
            </p>

            {/* Email Preview Snippet Card */}
            <div className="mt-6 rounded-2xl border border-purple-500/20 bg-slate-950/60 p-4 text-left">
              <div className="flex items-center justify-between text-[11px] text-purple-300 font-mono border-b border-white/10 pb-2 mb-3">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-purple-400" /> Daily Match Digest Preview
                </span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-emerald-300 font-bold">
                  Active
                </span>
              </div>

              <div className="space-y-2">
                <div className="rounded-lg bg-white/[0.04] p-2.5 border border-white/5 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-200">Hilton Hotels · Room Service & Floor Care</p>
                    <p className="text-[10px] text-slate-400">&ldquo;Looking for luggage & floor care robots across 40 resorts...&rdquo;</p>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">
                    98% Match
                  </span>
                </div>
                <div className="rounded-lg bg-white/[0.04] p-2.5 border border-white/5 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-200">5-Axis Bin Picking & Sorting</p>
                    <p className="text-[10px] text-slate-400">DHL Supply Chain · Texas</p>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">
                    95% Match
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-white/10 flex justify-between items-center text-[10px] text-slate-400">
                <span>Contact info locked until activation</span>
                <span className="text-purple-300 font-bold flex items-center gap-1">
                  <Lock className="h-3 w-3" /> Basic Plan ($19.99/mo)
                </span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="mt-6 w-full rounded-xl bg-purple-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-purple-600/30 hover:bg-purple-500 transition"
            >
              Back to Robot Workspace
            </button>
          </div>
        ) : (
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-400/30 bg-purple-500/10 px-3 py-1 text-xs font-bold text-purple-300 uppercase tracking-widest mb-3">
              <Sparkles className="h-3.5 w-3.5 text-purple-400" />
              <span>Free Daily Match Brief</span>
            </div>

            <h2 className="text-2xl font-extrabold text-white font-display tracking-tight">
              Save Your Robot & Get Daily Job Matches
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-slate-300 leading-relaxed">
              Never miss a high-intent buyer. Save <strong className="text-purple-300">{robotName}</strong> to receive a daily email brief featuring top buyer job matches and verified customer quotes — 100% free.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                  Work Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Your Name (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Alex Smith"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-xs text-white placeholder-slate-600 outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    placeholder="Robotics OEM / VAR"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-xs text-white placeholder-slate-600 outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              {/* Gamified Bonus Badge */}
              <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/15 via-purple-500/10 to-amber-500/10 p-3 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-base">🎰</span>
                  <div>
                    <p className="text-xs font-bold text-amber-300 font-display">
                      Daily Jackpot Match Bonus
                    </p>
                    <p className="text-[10px] text-slate-300">
                      Subscribers randomly unlock <strong>10 job matches</strong> + weekly market intelligence reports.
                    </p>
                  </div>
                </div>
                <span className="rounded-full bg-amber-400/20 border border-amber-400/40 px-2 py-0.5 text-[10px] font-mono font-bold text-amber-200 shrink-0">
                  🎁 1-in-3 Chance
                </span>
              </div>

              {/* Value prop list */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3.5 space-y-2 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Daily automated email brief (5–10 buyer job matches)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Verified customer quotes & automation buyer intent</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Weekly benchmark report & robotics market snippets</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Activate outreach anytime via Basic Plan ($19.99/mo)</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-extrabold text-white shadow-lg shadow-purple-600/30 hover:bg-purple-500 transition disabled:opacity-50"
              >
                {submitting ? (
                  <span>Saving Robot Profile...</span>
                ) : (
                  <>
                    <span>Activate Free Daily Match Brief</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <p className="text-[10px] text-center text-slate-400">
                Free workspace account. Unsubscribe anytime in 1 click. Raw buyer emails protected by Vault.
              </p>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
