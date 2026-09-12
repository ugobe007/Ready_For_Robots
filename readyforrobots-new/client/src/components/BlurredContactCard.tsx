import { useState } from "react";
import { Link } from "wouter";
import { Lock, ShieldCheck, Sparkles, UserCheck, ArrowRight, Bot, PhoneCall, Zap, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

type BlurredContactCardProps = {
  personName?: string;
  roleTitle?: string;
  companyName?: string;
  leadId?: number;
  isPaid?: boolean;
};

export default function BlurredContactCard({
  personName = "Verified Decision Maker",
  roleTitle = "VP of Global Operations & Automation",
  companyName = "Enterprise Buyer Account",
  leadId,
  isPaid = false,
}: BlurredContactCardProps) {
  const { session } = useAuth();
  const [dispatched, setDispatched] = useState(false);
  const [busy, setBusy] = useState(false);

  // Check if session has active paid subscription metadata (if available)
  const isPaidUser = isPaid || Boolean(session?.user?.user_metadata?.subscription_tier === "paid" || session?.user?.user_metadata?.is_paid);

  function handleDispatchCal() {
    setBusy(true);
    setTimeout(() => {
      setBusy(false);
      setDispatched(true);
      toast.success("ReadyForRobots Cal Outreach Agent dispatched! Cal is initiating the intro sequence with the buyer.");
    }, 1200);
  }

  // 1. Logged In & Paid User: Cal Managed Proxy (Email/Phone Hidden in Vault)
  if (session && isPaidUser) {
    return (
      <div className="rounded-xl border border-purple-500/40 bg-[#0d162d] p-4 shadow-xl text-slate-100">
        <div className="flex items-center justify-between mb-2">
          <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-purple-300 uppercase tracking-wider">
            <Bot className="h-3.5 w-3.5 text-purple-400" /> ReadyForRobots Cal Managed Proxy
          </span>
          <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-mono font-bold text-emerald-300 border border-emerald-500/30">
            Vault Protected
          </span>
        </div>

        <p className="text-sm font-bold text-white font-display">{personName}</p>
        <p className="text-xs text-slate-300 mb-3">{roleTitle} — {companyName}</p>

        <div className="rounded-lg border border-slate-700/80 bg-[#060c1c] p-3 text-xs font-mono space-y-1.5 mb-3">
          <div className="flex items-center justify-between text-slate-400">
            <span>Direct Email & Phone:</span>
            <span className="text-purple-300 font-bold">Hidden in Vault (Cal Proxy Active)</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Outreach Agent:</span>
            <span className="text-emerald-400">Cal Agent #804</span>
          </div>
        </div>

        {dispatched ? (
          <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 p-2.5 text-xs text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>Cal is executing the outreach sequence with {companyName}. Check your Cal desk for responses.</span>
          </div>
        ) : (
          <button
            type="button"
            onClick={handleDispatchCal}
            disabled={busy}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-purple-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-purple-500/30 hover:bg-purple-500 disabled:opacity-50 transition-all cursor-pointer font-sans"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>{busy ? "Dispatching Cal Agent…" : "Dispatch Cal Agent Outreach"}</span>
          </button>
        )}
      </div>
    );
  }

  // 2. Free or Non-Paid User: Paid Workspace Required to Activate Cal Lead
  return (
    <div className="relative overflow-hidden rounded-xl border border-purple-500/30 bg-[#0d162d] p-4 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-purple-300 uppercase tracking-wider">
          <Sparkles className="h-3.5 w-3.5 text-purple-400" /> Decision Maker Intel
        </span>
        <span className="rounded-full bg-purple-500/20 px-2.5 py-0.5 text-[10px] font-mono font-bold text-purple-200 border border-purple-500/30">
          🔒 Paid Workspace Required
        </span>
      </div>

      <p className="text-sm font-bold text-white font-display">{personName}</p>
      <p className="text-xs text-slate-300 mb-3">{roleTitle}</p>

      {/* Vault Locked Box */}
      <div className="relative rounded-lg border border-slate-700/60 bg-[#060c1c] p-3 backdrop-blur-md">
        <div className="filter blur-[5px] select-none pointer-events-none space-y-1.5 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <Bot className="h-3.5 w-3.5 text-purple-400" />
            <span>Cal Proxy: cal-agent-vault-protected@readyforrobots.com</span>
          </div>
          <div className="flex items-center gap-2">
            <PhoneCall className="h-3.5 w-3.5 text-purple-400" />
            <span>Cal Voice: +1 (800) ***-****</span>
          </div>
        </div>

        {/* Upgrade to Paid Button CTA */}
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70 backdrop-blur-[3px] p-2">
          <Link
            href="/pricing"
            className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-purple-500/30 hover:bg-purple-500 transition-all font-sans cursor-pointer"
          >
            <Lock className="h-3.5 w-3.5" />
            <span>Upgrade to Paid Workspace to Activate Cal Outreach</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
