import { useState } from "react";
import { Link } from "wouter";
import { Lock, Mail, Phone, ShieldCheck, Sparkles, UserCheck, ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

type BlurredContactCardProps = {
  personName?: string;
  roleTitle?: string;
  companyName?: string;
  inferredEmail?: string;
  inferredPhone?: string;
  leadId?: number;
};

export default function BlurredContactCard({
  personName = "VP of Global Operations & Automation",
  roleTitle = "Senior Decision Maker · Facilities & CapEx",
  companyName = "Enterprise Buyer Account",
  inferredEmail = "b.smith@enterprise-buyer.com",
  inferredPhone = "(555) 382-9104",
  leadId,
}: BlurredContactCardProps) {
  const { session } = useAuth();
  const [showModal, setShowModal] = useState(false);

  const maskedEmail = inferredEmail.replace(/^([^@]{2})[^@]+(@.+)$/, "$1***$2");
  const maskedPhone = inferredPhone.replace(/\d{4}$/, "****");

  if (session) {
    // Logged-in user sees full unmasked contact details
    return (
      <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/20 p-4 shadow-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-emerald-400 uppercase tracking-wider">
            <UserCheck className="h-3.5 w-3.5" /> Verified Decision Maker
          </span>
          <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-mono font-bold text-emerald-300">
            Direct Intel
          </span>
        </div>
        <p className="text-sm font-bold text-white font-display">{personName}</p>
        <p className="text-xs text-slate-300 mb-3">{roleTitle} — {companyName}</p>
        <div className="grid gap-2 text-xs font-mono sm:grid-cols-2">
          <a href={`mailto:${inferredEmail}`} className="flex items-center gap-2 rounded-lg bg-[#081126] p-2 border border-slate-700/80 text-emerald-300 hover:border-emerald-400 transition-colors">
            <Mail className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">{inferredEmail}</span>
          </a>
          <a href={`tel:${inferredPhone}`} className="flex items-center gap-2 rounded-lg bg-[#081126] p-2 border border-slate-700/80 text-emerald-300 hover:border-emerald-400 transition-colors">
            <Phone className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
            <span>{inferredPhone}</span>
          </a>
        </div>
      </div>
    );
  }

  // Free / Guest user sees blurred high-intent contact teaser
  return (
    <>
      <div className="relative overflow-hidden rounded-xl border border-purple-500/30 bg-[#0d162d] p-4 shadow-xl">
        <div className="flex items-center justify-between mb-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-purple-300 uppercase tracking-wider">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" /> High-Intent Contact Intelligence
          </span>
          <span className="rounded-full bg-purple-500/20 px-2.5 py-0.5 text-[10px] font-mono font-bold text-purple-200 border border-purple-500/30">
            🔒 Restricted
          </span>
        </div>
        <p className="text-sm font-bold text-white font-display">{personName}</p>
        <p className="text-xs text-slate-300 mb-3">{roleTitle}</p>

        {/* Blurred Teaser Overlay */}
        <div className="relative rounded-lg border border-slate-700/60 bg-[#060c1c] p-3 backdrop-blur-md">
          <div className="filter blur-[5px] select-none pointer-events-none space-y-1.5 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <Mail className="h-3.5 w-3.5 text-purple-400" />
              <span>{maskedEmail}</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="h-3.5 w-3.5 text-purple-400" />
              <span>{maskedPhone}</span>
            </div>
          </div>

          {/* Unlock Button CTA */}
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/60 backdrop-blur-[3px] p-2">
            <Link
              href={leadId ? `/signup?lead=${leadId}` : "/signup"}
              className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-purple-500/30 hover:bg-purple-500 transition-all font-sans cursor-pointer"
            >
              <Lock className="h-3.5 w-3.5" />
              <span>Unlock Direct Email & Phone</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
