import { useState } from "react";
import { Bot, CheckCircle2, X, ArrowRight, Building2, MapPin, Mail, User, Sparkles } from "lucide-react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

type RequestTrialModalProps = {
  isOpen: boolean;
  onClose: () => void;
  robotName?: string;
};

export default function RequestTrialModal({
  isOpen,
  onClose,
  robotName = "Humanoid / AMR Deployment",
}: RequestTrialModalProps) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    location: "",
    robotType: robotName,
    timeline: "Within 30 Days",
  });
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.email.trim() || !form.company.trim()) return;
    setStatus("submitting");

    try {
      const res = await fetch(`${getApiBase()}/api/leads/report-download`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          email: form.email,
          company: `${form.company} (TRIAL REQUEST: ${form.robotType})`,
          robotCategory: form.robotType,
          website: form.location,
        }),
      }));

      if (!res.ok) throw new Error("Trial submission failed");
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-purple-500/40 bg-[#0d162d] p-6 shadow-2xl text-slate-100">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-purple-500/30 bg-purple-500/10 text-purple-300">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase font-bold text-purple-400 tracking-wider">
              Commercial Deployment Program
            </span>
            <h2 className="text-xl font-extrabold text-white font-display">
              Request a 30-Day Robot Trial
            </h2>
          </div>
        </div>

        {status === "success" ? (
          <div className="py-8 text-center space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Trial Request Submitted!</h3>
            <p className="text-xs text-slate-300 max-w-sm mx-auto">
              Our engineering team will review your workplace parameters and connect you with vetted OEM deployment specialists within 24 hours.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="mt-4 rounded-xl bg-purple-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg hover:bg-purple-500"
            >
              Back to Overview
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
            <div>
              <label className="mb-1 block font-mono font-bold text-slate-300">
                Work Email <span className="text-purple-400">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  required
                  type="email"
                  placeholder="name@company.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full rounded-xl border border-slate-700 bg-[#060c1c] py-2.5 pl-9 pr-3 text-slate-100 placeholder-slate-500 outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
                />
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block font-mono font-bold text-slate-300">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Alex Morgan"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full rounded-xl border border-slate-700 bg-[#060c1c] py-2.5 pl-9 pr-3 text-slate-100 placeholder-slate-500 outline-none focus:border-purple-400"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block font-mono font-bold text-slate-300">
                  Company / Workplace <span className="text-purple-400">*</span>
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    required
                    type="text"
                    placeholder="Acme Fulfillment LLC"
                    value={form.company}
                    onChange={(e) => setForm({ ...form, company: e.target.value })}
                    className="w-full rounded-xl border border-slate-700 bg-[#060c1c] py-2.5 pl-9 pr-3 text-slate-100 placeholder-slate-500 outline-none focus:border-purple-400"
                  />
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block font-mono font-bold text-slate-300">
                  Facility Location (City, State)
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Dallas, TX"
                    value={form.location}
                    onChange={(e) => setForm({ ...form, location: e.target.value })}
                    className="w-full rounded-xl border border-slate-700 bg-[#060c1c] py-2.5 pl-9 pr-3 text-slate-100 placeholder-slate-500 outline-none focus:border-purple-400"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block font-mono font-bold text-slate-300">
                  Deployment Target
                </label>
                <select
                  value={form.timeline}
                  onChange={(e) => setForm({ ...form, timeline: e.target.value })}
                  className="w-full rounded-xl border border-slate-700 bg-[#060c1c] p-2.5 text-slate-100 outline-none focus:border-purple-400"
                >
                  <option value="Within 30 Days">Immediate (Within 30 Days)</option>
                  <option value="Q3 2026">Q3 2026 Program</option>
                  <option value="Q4 2026">Q4 2026 Program</option>
                  <option value="Budgeting Phase">Budgeting / Feasibility Phase</option>
                </select>
              </div>
            </div>

            {status === "error" && (
              <p className="text-xs text-rose-400">Could not submit request. Please try again.</p>
            )}

            <div className="pt-2">
              <button
                type="submit"
                disabled={status === "submitting"}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-purple-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/30 hover:bg-purple-500 disabled:opacity-50 transition-all cursor-pointer font-sans"
              >
                {status === "submitting" ? "Submitting Trial Request…" : "Submit 30-Day Trial Request"}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
