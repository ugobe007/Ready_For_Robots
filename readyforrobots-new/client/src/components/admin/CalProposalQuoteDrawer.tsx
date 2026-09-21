import { useState, useEffect } from "react";
import { Link } from "wouter";
import { toast } from "sonner";
import {
  X,
  FileText,
  Copy,
  ExternalLink,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Send,
  Building2,
  Bot,
  DollarSign,
  Sparkles,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import type { ProposalQuoteData } from "@/pages/ProposalOemReview";

type CalProposalQuoteDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedQuoteId?: string | null;
};

const DEFAULT_QUOTES: ProposalQuoteData[] = [
  {
    id: "PROP-8842-APEX",
    job_title: "Autonomous Pallet Stacker & Conveyor Tending Operator",
    company_name: "Apex Logistics Solutions",
    location: "Chicago, IL (Midwest Hub)",
    matched_robot: {
      oem_name: "KUKA Robotics",
      model_name: "KUKA KR IONTEC & KMP 1500i AMR",
      payload_capacity: "1,500 kg payload capacity",
      reach: "3,101 mm reach",
      category: "Autonomous Heavy Palletizing & Transport",
    },
    pricing: {
      raas_monthly_rate: 4850,
      hardware_cost: 165000,
      estimated_deployment_weeks: 3,
      sla_tier: "Enterprise 24/7 SLA + 4hr On-Site Swap",
      annual_human_labor_cost: 162000,
      projected_annual_savings: 103800,
      payback_period_months: 7.2,
    },
    oem_technical_notes: "Unit standard equipped with high-grip EOAT pallet gripper and laser safety scanner suite. Fully compatible with Apex's SAP EWM warehouse management system via REST API.",
    status: "awaiting_oem_approval",
    buyer_contact: {
      name: "Marcus Vance",
      title: "VP of Automation & Distribution Infrastructure",
      email: "m.vance@apexlogistics-demo.com",
    },
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
  {
    id: "PROP-7291-VELOX",
    job_title: "High-Speed Parcels Sorting & Bin Tending Cell",
    company_name: "Velox Express Fulfillment",
    location: "Dallas-Fort Worth, TX",
    matched_robot: {
      oem_name: "Universal Robots",
      model_name: "UR20 Cobot Arm + Robotiq 3-Finger Gripper",
      payload_capacity: "20 kg payload capacity",
      reach: "1,750 mm reach",
      category: "Parcels Induction & Sortation",
    },
    pricing: {
      raas_monthly_rate: 3400,
      hardware_cost: 92000,
      estimated_deployment_weeks: 2,
      sla_tier: "Premium 24/7 SLA",
      annual_human_labor_cost: 118000,
      projected_annual_savings: 77200,
      payback_period_months: 6.8,
    },
    oem_technical_notes: "Configured with vision-guided sorting software module. Tested up to 1,400 picks/hr.",
    status: "oem_approved",
    buyer_contact: {
      name: "Sarah Jenkins",
      title: "Director of Operations",
      email: "s.jenkins@velox-fulfillment-demo.com",
    },
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: "PROP-9104-NEXUS",
    job_title: "Heavy Machining CNC Lathe Tend & Deburring Station",
    company_name: "Nexus Precision Component Corp",
    location: "Detroit, MI",
    matched_robot: {
      oem_name: "FANUC Robotics",
      model_name: "FANUC M-710iC/50 Industrial Robot",
      payload_capacity: "50 kg payload capacity",
      reach: "2,050 mm reach",
      category: "Machine Tending & Heavy Material Handling",
    },
    pricing: {
      raas_monthly_rate: 5600,
      hardware_cost: 195000,
      estimated_deployment_weeks: 4,
      sla_tier: "Enterprise 24/7 SLA + On-site Spares",
      annual_human_labor_cost: 210000,
      projected_annual_savings: 142800,
      payback_period_months: 8.1,
    },
    oem_technical_notes: "Dual-gripper configuration for simultaneous loading/unloading of CNC chucks.",
    status: "awaiting_oem_approval",
    buyer_contact: {
      name: "David Sterling",
      title: "Plant Manager",
      email: "d.sterling@nexusprecision-demo.com",
    },
    created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
  }
];

export default function CalProposalQuoteDrawer({
  isOpen,
  onClose,
  selectedQuoteId,
}: CalProposalQuoteDrawerProps) {
  const [quotes, setQuotes] = useState<ProposalQuoteData[]>([]);
  const [activeQuoteId, setActiveQuoteId] = useState<string | null>(null);

  useEffect(() => {
    // Load from localStorage or merge defaults
    const loaded: ProposalQuoteData[] = [];
    DEFAULT_QUOTES.forEach(def => {
      const stored = localStorage.getItem(`cal_proposal_quote_${def.id}`);
      if (stored) {
        try {
          loaded.push(JSON.parse(stored));
        } catch {
          loaded.push(def);
        }
      } else {
        loaded.push(def);
      }
    });
    setQuotes(loaded);
    setActiveQuoteId(selectedQuoteId || loaded[0]?.id || null);
  }, [isOpen, selectedQuoteId]);

  if (!isOpen) return null;

  const currentQuote = quotes.find(q => q.id === activeQuoteId) || quotes[0];

  const handleCopyOemLink = (id: string) => {
    const origin = typeof window !== "undefined" ? window.location.origin : "https://readyforrobots.com";
    const url = `${origin}/proposal/oem-review?id=${id}`;
    navigator.clipboard.writeText(url);
    toast.success("OEM Approval Link copied to clipboard!");
  };

  const handleForceApprove = (id: string) => {
    const updated = quotes.map(q => {
      if (q.id === id) {
        const u = { ...q, status: "oem_approved" as const, updated_at: new Date().toISOString() };
        localStorage.setItem(`cal_proposal_quote_${id}`, JSON.stringify(u));
        return u;
      }
      return q;
    });
    setQuotes(updated);
    toast.success(`Quote ${id} marked as OEM Approved!`);
  };

  const handleAutoDispatchAll = () => {
    const updated = quotes.map(q => {
      const u = { ...q, status: "oem_approved" as const, updated_at: new Date().toISOString() };
      localStorage.setItem(`cal_proposal_quote_${q.id}`, JSON.stringify(u));
      return u;
    });
    setQuotes(updated);
    toast.success("Cal Autopilot: Auto-dispatched OEM tee-up emails and approved buyer quotes for all active matches!");
  };

  const handleRunNurtureCycle = () => {
    toast.success("Cal Multi-Touch Nurture Engine: Triggered OEM Day-3 Nudges & Buyer Day-4 Follow-ups across all active quotes!");
  };

  const handleSimulateBuyerAcceptance = (id: string) => {
    const updated = quotes.map(q => {
      if (q.id === id) {
        const u = { ...q, status: "buyer_accepted" as const, updated_at: new Date().toISOString() };
        localStorage.setItem(`cal_proposal_quote_${id}`, JSON.stringify(u));
        return u;
      }
      return q;
    });
    setQuotes(updated);
    toast.success(`🎉 Employer accepted quote ${id}! Cal notified the OEM and prepared site onboarding.`);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm flex justify-end transition-opacity animate-in fade-in duration-200">
      {/* Drawer Overlay backdrop click */}
      <div className="fixed inset-0" onClick={onClose} />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col z-10 font-sans text-slate-100 overflow-hidden">
        {/* Drawer Header */}
        <div className="px-6 py-5 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-white flex items-center gap-2">
                Cal Robot Proposal & OEM Quotes
                <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Autopilot Active
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Automatic OEM tee-up outreach & pre-send approval gate
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Automatic Dispatch & Multi-Touch Nurture Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-cyan-950/40 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
                  Cal Autopilot Engine
                </span>
                <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded">
                  Fully Automatic Outreach & Nurture
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                Cal automatically matches job openings, sends OEM tee-ups, and triggers Day-3 OEM nudges and Day-4 buyer follow-ups.
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={handleRunNurtureCycle}
                className="px-3 py-1.5 rounded-lg border border-cyan-500/40 bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 text-xs font-bold transition-all"
              >
                Run Nurture Nudge
              </button>
              <button
                onClick={handleAutoDispatchAll}
                className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-extrabold uppercase tracking-wide transition-all shadow-md shadow-emerald-500/20"
              >
                Auto-Dispatch All
              </button>
            </div>
          </div>
          {/* Quote List Selector Tabs */}
          <div>
            <label className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-2">
              Select Proposal Quote
            </label>
            <div className="grid grid-cols-1 gap-2">
              {quotes.map(q => {
                const isActive = q.id === currentQuote?.id;
                return (
                  <button
                    key={q.id}
                    onClick={() => setActiveQuoteId(q.id)}
                    className={`p-3.5 rounded-xl border text-left transition-all flex items-center justify-between ${
                      isActive
                        ? "bg-cyan-950/40 border-cyan-500/50 text-white shadow-lg shadow-cyan-950/30"
                        : "bg-slate-950/60 border-slate-800/80 text-slate-300 hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold font-mono text-cyan-400">{q.id}</span>
                        <span className="text-xs text-slate-400">• {q.matched_robot.oem_name}</span>
                      </div>
                      <div className="text-xs font-semibold text-slate-200 line-clamp-1">{q.job_title}</div>
                      <div className="text-[11px] text-slate-400">{q.company_name} ({q.location})</div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5 ml-3">
                      {q.status === "awaiting_oem_approval" && (
                        <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                          Awaiting OEM
                        </span>
                      )}
                      {q.status === "oem_approved" && (
                        <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> OEM Approved
                        </span>
                      )}
                      {(q.status === "buyer_accepted" || q.status === "oem_notified_buyer_accepted") && (
                        <span className="text-[10px] font-mono font-bold text-emerald-300 bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Buyer Accepted (YES!)
                        </span>
                      )}
                      <span className="text-xs font-mono font-bold text-slate-200">
                        ${q.pricing.raas_monthly_rate.toLocaleString()}/mo
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Quote Detail Inspector */}
          {currentQuote && (
            <div className="rounded-xl bg-slate-950 border border-slate-800 p-5 space-y-5">
              {/* Header Info */}
              <div className="flex items-start justify-between border-b border-slate-800/80 pb-4">
                <div>
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block">
                    Active Proposal Inspector
                  </span>
                  <h3 className="text-base font-extrabold text-white mt-0.5">{currentQuote.job_title}</h3>
                  <p className="text-xs text-slate-300 font-medium">{currentQuote.company_name}</p>
                </div>
                
                <Link
                  href={`/proposal/oem-review?id=${currentQuote.id}`}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-bold flex items-center gap-1.5 transition-colors"
                >
                  Open OEM Portal <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Matched Hardware */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 text-[10px] font-mono block">Robot OEM & Model</span>
                  <span className="text-slate-200 font-bold block mt-0.5">{currentQuote.matched_robot.oem_name}</span>
                  <span className="text-slate-400 text-[11px] block">{currentQuote.matched_robot.model_name}</span>
                </div>

                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 text-[10px] font-mono block">Financial Structuring</span>
                  <span className="text-emerald-400 font-extrabold font-mono text-sm block mt-0.5">
                    ${currentQuote.pricing.raas_monthly_rate.toLocaleString()}/mo
                  </span>
                  <span className="text-slate-400 text-[11px] block">Turnkey Buyout: ${currentQuote.pricing.hardware_cost.toLocaleString()}</span>
                </div>
              </div>

              {/* OEM Approval Gate & Actions */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-400 uppercase flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" /> Pre-Send OEM Approval Gate
                  </span>
                  {currentQuote.status === "awaiting_oem_approval" ? (
                    <span className="text-amber-400 font-semibold font-mono text-[11px]">
                      Pending OEM Sign-Off
                    </span>
                  ) : currentQuote.status === "buyer_accepted" || currentQuote.status === "oem_notified_buyer_accepted" ? (
                    <span className="text-emerald-400 font-bold font-mono text-[11px] flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Buyer Accepted (YES!)
                    </span>
                  ) : (
                    <span className="text-emerald-400 font-semibold font-mono text-[11px]">
                      OEM Signed Off & Dispatched
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">
                  Send this link to <strong className="text-cyan-300">{currentQuote.matched_robot.oem_name}</strong> partner engineering team so they can confirm equipment lead time and approve proposal pricing before dispatch to enterprise buyer <strong className="text-white">{currentQuote.buyer_contact.name}</strong>.
                </p>

                <div className="flex flex-wrap items-center gap-2 pt-2">
                  <button
                    onClick={() => handleCopyOemLink(currentQuote.id)}
                    className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5 text-cyan-400" /> Copy OEM Review Link
                  </button>

                  {currentQuote.status === "awaiting_oem_approval" && (
                    <button
                      onClick={() => handleForceApprove(currentQuote.id)}
                      className="px-3.5 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Override & Mark OEM Approved
                    </button>
                  )}

                  {currentQuote.status !== "buyer_accepted" && currentQuote.status !== "oem_notified_buyer_accepted" && (
                    <button
                      onClick={() => handleSimulateBuyerAcceptance(currentQuote.id)}
                      className="px-3.5 py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> Simulate Employer 'YES'
                    </button>
                  )}
                </div>
              </div>

              {/* OEM Tee-Up Email Preview Snippet */}
              <div className="p-4 rounded-xl bg-slate-900/90 border border-amber-500/30 space-y-2 text-xs">
                <div className="flex items-center justify-between text-amber-400 font-mono font-bold text-[11px]">
                  <span>Cal OEM Tee-Up Email (Supply Side Outreach)</span>
                  <span className="text-slate-400">To: {currentQuote.matched_robot.oem_name} Partner Engineering</span>
                </div>
                <div className="font-mono text-[11px] text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1.5 leading-relaxed">
                  <p className="font-semibold text-white">Hi {currentQuote.matched_robot.oem_name} Team,</p>
                  <p className="font-bold text-amber-300">I find jobs for robot companies.</p>
                  <p>We identified an active job opening at <strong>{currentQuote.company_name}</strong> in {currentQuote.location} for the <strong>{currentQuote.job_title}</strong> role.</p>
                  <p className="text-slate-400">Matched Hardware: {currentQuote.matched_robot.oem_name} {currentQuote.matched_robot.model_name} (${currentQuote.pricing.raas_monthly_rate.toLocaleString()}/mo RaaS / ${currentQuote.pricing.hardware_cost.toLocaleString()} buyout)</p>
                </div>
              </div>

              {/* Technical Notes Summary */}
              <div className="text-xs space-y-1.5">
                <span className="font-mono text-slate-400 text-[10px] uppercase">OEM Technical Integration Notes:</span>
                <p className="font-mono text-[11px] text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                  {currentQuote.oem_technical_notes}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between text-xs text-slate-400">
          <span className="font-mono">Cal Autopilot Engine v2.4 • OEM Gate</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-colors"
          >
            Close Workspace
          </button>
        </div>
      </div>
    </div>
  );
}
