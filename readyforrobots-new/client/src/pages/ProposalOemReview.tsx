import { useEffect, useState } from "react";
import { Link, useSearch } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import { JOBS_HEADER_OFFSET_CLASS } from "@/lib/jobsWorkflow";
import { toast } from "sonner";
import {
  CheckCircle2,
  Building2,
  Bot,
  DollarSign,
  Clock,
  ShieldCheck,
  Send,
  Sparkles,
  FileText,
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  ExternalLink,
  Edit3,
  RefreshCw,
  Check,
  Zap,
} from "lucide-react";

export type ProposalQuoteData = {
  id: string;
  job_title: string;
  company_name: string;
  location: string;
  matched_robot: {
    oem_name: string;
    model_name: string;
    payload_capacity: string;
    reach: string;
    category: string;
  };
  pricing: {
    raas_monthly_rate: number;
    hardware_cost: number;
    estimated_deployment_weeks: number;
    sla_tier: string;
    annual_human_labor_cost: number;
    projected_annual_savings: number;
    payback_period_months: number;
  };
  oem_technical_notes: string;
  status: "awaiting_oem_approval" | "oem_approved" | "revisions_requested" | "dispatched_to_buyer";
  buyer_contact: {
    name: string;
    title: string;
    email: string;
  };
  oem_contact?: {
    name: string;
    title: string;
    email: string;
  };
  feasibility_metrics?: {
    heir_score: number;
    active_deployments: number;
    buyer_qualification_tier: string;
    oem_allocation_expires_hours: number;
    poc_simulation_url?: string;
  };
  created_at: string;
  updated_at?: string;
};

// Default sample proposal quote for demo & fallback
const SAMPLE_PROPOSAL_QUOTE: ProposalQuoteData = {
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
  oem_contact: {
    name: "KUKA Partner Engineering Team",
    title: "Application Engineering & Channel Direct",
    email: "partner-sales@kuka-robotics-demo.com",
  },
  feasibility_metrics: {
    heir_score: 94.2,
    active_deployments: 482,
    buyer_qualification_tier: "Enterprise Tier 1 ($100M+ Revenue, 14 Distribution Hubs)",
    oem_allocation_expires_hours: 48,
    poc_simulation_url: "/preview",
  },
  created_at: new Date().toISOString(),
};

export default function ProposalOemReview() {
  const searchString = useSearch();
  const searchParams = new URLSearchParams(searchString);
  const quoteId = searchParams.get("id") || searchParams.get("quote_id") || "PROP-8842-APEX";

  const [quote, setQuote] = useState<ProposalQuoteData>(() => {
    const saved = localStorage.getItem(`cal_proposal_quote_${quoteId}`);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to parse saved proposal quote", e);
      }
    }
    return { ...SAMPLE_PROPOSAL_QUOTE, id: quoteId };
  });

  const [activeTab, setActiveTab] = useState<"pricing" | "specs" | "oem_teeup" | "buyer_email">("pricing");
  const [isEditing, setIsEditing] = useState(false);
  const [editedMonthly, setEditedMonthly] = useState(quote.pricing.raas_monthly_rate);
  const [editedHardware, setEditedHardware] = useState(quote.pricing.hardware_cost);
  const [editedWeeks, setEditedWeeks] = useState(quote.pricing.estimated_deployment_weeks);
  const [editedNotes, setEditedNotes] = useState(quote.oem_technical_notes);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Recalculate metrics based on edited rates
  const annualRaas = editedMonthly * 12;
  const annualSavings = Math.max(0, quote.pricing.annual_human_labor_cost - annualRaas);
  const paybackMonths = editedMonthly > 0 ? Number(((editedHardware / (quote.pricing.annual_human_labor_cost / 12 - editedMonthly)).toFixed(1))) : 8.5;

  const handleSaveEdits = () => {
    const updated: ProposalQuoteData = {
      ...quote,
      pricing: {
        ...quote.pricing,
        raas_monthly_rate: editedMonthly,
        hardware_cost: editedHardware,
        estimated_deployment_weeks: editedWeeks,
        projected_annual_savings: annualSavings,
        payback_period_months: paybackMonths > 0 ? paybackMonths : 7.5,
      },
      oem_technical_notes: editedNotes,
      updated_at: new Date().toISOString(),
    };
    setQuote(updated);
    localStorage.setItem(`cal_proposal_quote_${quoteId}`, JSON.stringify(updated));
    setIsEditing(false);
    toast.success("Quote pricing and deployment terms updated successfully.");
  };

  const handleApproveProposal = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      const updated: ProposalQuoteData = {
        ...quote,
        status: "oem_approved",
        updated_at: new Date().toISOString(),
      };
      setQuote(updated);
      localStorage.setItem(`cal_proposal_quote_${quoteId}`, JSON.stringify(updated));
      setIsSubmitting(false);
      toast.success("Proposal approved & supported! Cal AI is now dispatching the proposal quote to Apex Logistics.");
    }, 800);
  };

  const handleRequestRevisions = () => {
    const updated: ProposalQuoteData = {
      ...quote,
      status: "revisions_requested",
      updated_at: new Date().toISOString(),
    };
    setQuote(updated);
    localStorage.setItem(`cal_proposal_quote_${quoteId}`, JSON.stringify(updated));
    toast.info("Revision request sent back to Cal AI sales dispatcher.");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      <ExperimentHeader />

      <main className={`flex-grow container mx-auto px-4 sm:px-6 lg:px-8 pb-16 ${JOBS_HEADER_OFFSET_CLASS}`}>
        {/* Top Navigation & Status Bar */}
        <div className="pt-6 pb-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Link href="/sales-console" className="hover:text-cyan-400 transition-colors">
              Sales Console
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-slate-300 font-semibold">Cal OEM Proposal Review Gate</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-cyan-400">{quote.id}</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400">Status:</span>
            {quote.status === "awaiting_oem_approval" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                Awaiting OEM Approval
              </span>
            )}
            {quote.status === "oem_approved" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Approved & Supported by OEM
              </span>
            )}
            {quote.status === "revisions_requested" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                <AlertTriangle className="w-3.5 h-3.5" />
                Revisions Requested
              </span>
            )}
          </div>
        </div>

        {/* OEM Portal Hero Section */}
        <div className="mt-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-indigo-950/50 border border-slate-800 p-6 sm:p-8 relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono tracking-wider uppercase mb-2">
                <Sparkles className="w-4 h-4 text-cyan-400 animate-spin-slow" />
                Cal Autopilot OEM Pre-Send Approval Workspace
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Review & Confirm Robot Proposal Quote
              </h1>
              <p className="mt-2 text-sm text-slate-300 max-w-2xl">
                Cal AI matched <span className="font-semibold text-cyan-300">{quote.matched_robot.oem_name} {quote.matched_robot.model_name}</span> to an active job opening at <span className="font-semibold text-white">{quote.company_name}</span>. Please review pricing, SLA warranty, and technical notes before Cal dispatches the proposal quote to the buyer.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {quote.status === "awaiting_oem_approval" ? (
                <>
                  <button
                    onClick={handleRequestRevisions}
                    className="px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition-all flex items-center gap-2"
                  >
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Request Revisions
                  </button>
                  <button
                    onClick={handleApproveProposal}
                    disabled={isSubmitting}
                    className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs tracking-wide uppercase transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 flex items-center gap-2"
                  >
                    {isSubmitting ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                    Approve & Support Proposal
                  </button>
                </>
              ) : (
                <div className="px-5 py-3 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs font-medium flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  OEM Approval Confirmed & Registered
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Two-Column Grid: Job & Match Context + Detailed Quote Controls */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (4 cols): Match & Buyer Context Card */}
          <div className="lg:col-span-4 space-y-6">
            {/* Target Job Opportunity */}
            <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-cyan-400" /> Enterprise Buyer Opportunity
                </span>
                <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-mono">
                  Verified Opening
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-white">{quote.job_title}</h3>
                <p className="text-xs text-cyan-300 font-medium mt-0.5">{quote.company_name}</p>
                <p className="text-xs text-slate-400 mt-1">{quote.location}</p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Buyer Decision Maker:</span>
                  <span className="text-slate-200 font-medium">{quote.buyer_contact.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Title:</span>
                  <span className="text-slate-300">{quote.buyer_contact.title}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Contact Email:</span>
                  <span className="text-cyan-400 font-mono text-[11px]">{quote.buyer_contact.email}</span>
                </div>
              </div>
            </div>

            {/* Robot Model Specs */}
            <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Bot className="w-4 h-4 text-cyan-400" /> Matched Robot Hardware
                </span>
                <span className="text-xs text-cyan-400 font-semibold font-mono">{quote.matched_robot.oem_name}</span>
              </div>

              <div>
                <h4 className="text-sm font-extrabold text-cyan-300">{quote.matched_robot.model_name}</h4>
                <p className="text-xs text-slate-400 mt-0.5">{quote.matched_robot.category}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400 block text-[10px] uppercase font-mono">Payload</span>
                  <span className="text-slate-200 font-semibold text-xs">{quote.matched_robot.payload_capacity}</span>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400 block text-[10px] uppercase font-mono">Reach / Specs</span>
                  <span className="text-slate-200 font-semibold text-xs">{quote.matched_robot.reach}</span>
                </div>
              </div>
            </div>

            {/* Quick Metrics Callout */}
            <div className="rounded-xl bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/20 p-5">
              <div className="flex items-center gap-2 text-xs font-mono text-indigo-300 uppercase tracking-wider mb-3">
                <Zap className="w-4 h-4 text-indigo-400" /> Cal ROI Calculator Projection
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-baseline">
                  <span className="text-xs text-slate-400">Est. Annual Labor Replaced:</span>
                  <span className="text-sm font-mono font-bold text-white">${quote.pricing.annual_human_labor_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="text-xs text-slate-400">Net Buyer Annual Savings:</span>
                  <span className="text-sm font-mono font-bold text-emerald-400">+${annualSavings.toLocaleString()} / yr</span>
                </div>
                <div className="flex justify-between items-baseline pt-2 border-t border-slate-800">
                  <span className="text-xs text-slate-400">Hardware Payback Period:</span>
                  <span className="text-sm font-mono font-bold text-cyan-400">{paybackMonths} months</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (8 cols): Interactive Proposal Quote Tabs */}
          <div className="lg:col-span-8 space-y-6">
            {/* Tab Controls */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setActiveTab("pricing")}
                  className={`px-3.5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    activeTab === "pricing"
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <DollarSign className="w-3.5 h-3.5" /> Quote Pricing & Terms
                </button>
                <button
                  onClick={() => setActiveTab("specs")}
                  className={`px-3.5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    activeTab === "specs"
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" /> OEM Specs & SLA
                </button>
                <button
                  onClick={() => setActiveTab("oem_teeup")}
                  className={`px-3.5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    activeTab === "oem_teeup"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-amber-400" /> OEM Tee-Up Email
                </button>
                <button
                  onClick={() => setActiveTab("buyer_email")}
                  className={`px-3.5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    activeTab === "buyer_email"
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <Send className="w-3.5 h-3.5 text-cyan-400" /> Buyer Dispatch Email
                </button>
              </div>

              {!isEditing && quote.status === "awaiting_oem_approval" && activeTab !== "oem_teeup" && activeTab !== "buyer_email" && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-300 flex items-center gap-1.5 transition-all"
                >
                  <Edit3 className="w-3.5 h-3.5 text-cyan-400" /> Edit Pricing & Notes
                </button>
              )}
            </div>

            {/* Tab Content: Pricing & Terms */}
            {activeTab === "pricing" && (
              <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-6 space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-white">Commercial Proposal Quote Breakdown</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Configure baseline RaaS leasing and turnkey hardware purchase prices for {quote.company_name}.
                    </p>
                  </div>
                  {isEditing && (
                    <span className="text-xs font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-md">
                      Editing Mode Active
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* RaaS Monthly Rate Card */}
                  <div className="rounded-xl bg-slate-950/80 border border-slate-800 p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>Robots-as-a-Service (RaaS)</span>
                      <span className="font-mono text-emerald-400">Monthly Billing</span>
                    </div>
                    {isEditing ? (
                      <div>
                        <label className="text-[11px] text-slate-400 font-mono block mb-1">RaaS Monthly Rate ($)</label>
                        <input
                          type="number"
                          value={editedMonthly}
                          onChange={e => setEditedMonthly(Number(e.target.value))}
                          className="w-full bg-slate-900 border border-cyan-500/50 rounded-lg px-3 py-2 text-white font-mono text-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                      </div>
                    ) : (
                      <div>
                        <span className="text-3xl font-extrabold font-mono text-white">
                          ${quote.pricing.raas_monthly_rate.toLocaleString()}
                        </span>
                        <span className="text-xs text-slate-400 font-mono"> / month</span>
                      </div>
                    )}
                    <p className="text-xs text-slate-400">
                      Includes 24/7 teleoperation support, scheduled maintenance, and software updates.
                    </p>
                  </div>

                  {/* Turnkey Hardware Cost Card */}
                  <div className="rounded-xl bg-slate-950/80 border border-slate-800 p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>Turnkey Capital Buyout</span>
                      <span className="font-mono text-cyan-400">CapEx Hardware</span>
                    </div>
                    {isEditing ? (
                      <div>
                        <label className="text-[11px] text-slate-400 font-mono block mb-1">Hardware & System Cost ($)</label>
                        <input
                          type="number"
                          value={editedHardware}
                          onChange={e => setEditedHardware(Number(e.target.value))}
                          className="w-full bg-slate-900 border border-cyan-500/50 rounded-lg px-3 py-2 text-white font-mono text-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                      </div>
                    ) : (
                      <div>
                        <span className="text-3xl font-extrabold font-mono text-white">
                          ${quote.pricing.hardware_cost.toLocaleString()}
                        </span>
                        <span className="text-xs text-slate-400 font-mono"> total</span>
                      </div>
                    )}
                    <p className="text-xs text-slate-400">
                      Turnkey price for robot arm, end-effector gripper, cell safety cage, and PLC integration.
                    </p>
                  </div>
                </div>

                {/* Deployment Timeframe & SLA */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-800">
                  <div>
                    <label className="text-xs font-mono text-slate-400 block mb-1.5">
                      Estimated Deployment Lead Time
                    </label>
                    {isEditing ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          value={editedWeeks}
                          onChange={e => setEditedWeeks(Number(e.target.value))}
                          className="w-24 bg-slate-900 border border-cyan-500/50 rounded-lg px-3 py-1.5 text-white font-mono text-sm"
                        />
                        <span className="text-xs text-slate-300">weeks from PO</span>
                      </div>
                    ) : (
                      <div className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                        <Clock className="w-4 h-4 text-cyan-400" />
                        {quote.pricing.estimated_deployment_weeks} weeks standard deployment window
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-xs font-mono text-slate-400 block mb-1.5">
                      Service & SLA Guarantee
                    </label>
                    <div className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      {quote.pricing.sla_tier}
                    </div>
                  </div>
                </div>

                {/* Edit Controls */}
                {isEditing && (
                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-4 py-2 rounded-lg border border-slate-700 bg-slate-900 text-slate-300 text-xs font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveEdits}
                      className="px-5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold flex items-center gap-1.5"
                    >
                      <Check className="w-4 h-4" /> Save Updated Quote
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tab Content: OEM Technical Notes & Integration Specs */}
            {activeTab === "specs" && (
              <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white">OEM Application & Technical Engineering Notes</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    These technical notes will be appended to the proposal documentation sent to the customer engineering team.
                  </p>
                </div>

                <div>
                  <label className="text-xs font-mono text-slate-400 block mb-2">
                    Manufacturer System & Cell Integration Details
                  </label>
                  {isEditing ? (
                    <textarea
                      rows={5}
                      value={editedNotes}
                      onChange={e => setEditedNotes(e.target.value)}
                      className="w-full bg-slate-950 border border-cyan-500/50 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
                    />
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed">
                      {quote.oem_technical_notes}
                    </div>
                  )}
                </div>

                <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-2">
                  <span className="text-xs font-bold text-indigo-300 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-400" /> Cal AI Verification Safeguard
                  </span>
                  <p className="text-xs text-slate-300">
                    By approving this proposal, {quote.matched_robot.oem_name} confirms hardware availability for the {quote.pricing.estimated_deployment_weeks}-week window and authorizes Cal to present these pricing options to {quote.company_name}.
                  </p>
                </div>
              </div>
            )}

            {/* Tab Content: Cal OEM Tee-Up Email */}
            {activeTab === "oem_teeup" && (
              <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-6 space-y-6">
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      Cal OEM Tee-Up Email
                      <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                        Supply-Side Partner Outreach
                      </span>
                    </h3>
                    <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded-md border border-slate-700">
                      Recipient: {quote.oem_contact?.email || "partner-sales@kuka-robotics-demo.com"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    This is the initial outreach email Cal sends to the Robot Manufacturer / Distributor to tee up the deal before buyer dispatch.
                  </p>
                </div>

                <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden text-xs">
                  <div className="bg-slate-900/90 p-3 border-b border-slate-800 font-mono text-slate-300 space-y-1">
                    <div><span className="text-slate-500">From:</span> Cal @ Ready For Robots &lt;cal@readyforrobots.com&gt;</div>
                    <div><span className="text-slate-500">To:</span> {quote.oem_contact?.name || quote.matched_robot.oem_name} &lt;{quote.oem_contact?.email || "partner-sales@kuka-robotics-demo.com"}&gt;</div>
                    <div><span className="text-slate-500">Subject:</span> New Robot Job Opening: {quote.matched_robot.oem_name} {quote.matched_robot.model_name} for {quote.company_name}</div>
                  </div>

                  <div className="p-5 font-sans space-y-4 text-slate-200 leading-relaxed">
                    <p className="text-sm font-semibold text-white">
                      Hi {quote.matched_robot.oem_name} Partner Team,
                    </p>

                    <p className="text-sm font-bold text-amber-300">
                      I find jobs for robot companies.
                    </p>

                    <p>
                      We identified an active enterprise job opening at <strong>{quote.company_name}</strong> in {quote.location} looking for a robot solution to automate their <strong>{quote.job_title}</strong> role.
                    </p>

                    <p>
                      We matched your <strong>{quote.matched_robot.oem_name} {quote.matched_robot.model_name}</strong> as the optimal hardware package for this site. We built an initial commercial proposal quote to present to their VP of Automation ({quote.buyer_contact.name}):
                    </p>

                    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 font-mono text-xs">
                      <div className="text-amber-400 font-bold">Matched Enterprise Opportunity & Commercial Summary:</div>
                      <div>• Target Enterprise Buyer: {quote.company_name} ({quote.feasibility_metrics?.buyer_qualification_tier || "Enterprise Tier 1, $100M+ Revenue"})</div>
                      <div>• Matched Hardware Model: {quote.matched_robot.oem_name} {quote.matched_robot.model_name}</div>
                      <div>• HEIR Feasibility Benchmark: {quote.feasibility_metrics?.heir_score || 94.2}% Task-Match Score ({quote.feasibility_metrics?.active_deployments || 482} active fleet deployments)</div>
                      <div>• Proposed RaaS Monthly Rate: ${quote.pricing.raas_monthly_rate.toLocaleString()}/mo (${(quote.pricing.raas_monthly_rate * 12).toLocaleString()}/yr)</div>
                      <div>• Proposed Turnkey CapEx Buyout: ${quote.pricing.hardware_cost.toLocaleString()}</div>
                      <div>• Estimated Deployment Lead Time: {quote.pricing.estimated_deployment_weeks} weeks</div>
                      <div>• OEM Allocation Reservation Window: {quote.feasibility_metrics?.oem_allocation_expires_hours || 48} Hours</div>
                    </div>

                    <p>
                      Please review the proposal quote specs, confirm your equipment lead time window, and click <strong>Approve & Support Proposal</strong> so we can dispatch the proposal directly to <strong>{quote.buyer_contact.name}</strong> ({quote.buyer_contact.title}).
                    </p>

                    <div className="py-2">
                      <span className="inline-block px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs tracking-wide shadow-md transition-all">
                        Review & Approve Robot Proposal Quote →
                      </span>
                    </div>

                    <p className="text-slate-400 text-[11px] border-t border-slate-800/80 pt-3">
                      Best regards,<br />
                      <strong>Cal</strong> | AI Robotics Procurement Specialist<br />
                      Ready For Robots (readyforrobots.com)
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Tab Content: Cal Buyer Dispatch Email */}
            {activeTab === "buyer_email" && (
              <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-6 space-y-6">
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      Cal Buyer Dispatch Email
                      <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30">
                        Dispatched Post OEM Sign-Off
                      </span>
                    </h3>
                    <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-md border border-cyan-500/20">
                      Recipient: {quote.buyer_contact.email}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    This email is dispatched directly to the enterprise decision-maker once {quote.matched_robot.oem_name} approves the proposal.
                  </p>
                </div>

                <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden text-xs">
                  <div className="bg-slate-900/90 p-3 border-b border-slate-800 font-mono text-slate-300 space-y-1">
                    <div><span className="text-slate-500">From:</span> Cal @ Ready For Robots &lt;cal@readyforrobots.com&gt;</div>
                    <div><span className="text-slate-500">To:</span> {quote.buyer_contact.name} &lt;{quote.buyer_contact.email}&gt;</div>
                    <div><span className="text-slate-500">Subject:</span> Custom Robot Proposal & Quote: {quote.matched_robot.oem_name} {quote.matched_robot.model_name} for {quote.job_title}</div>
                  </div>

                  <div className="p-5 font-sans space-y-4 text-slate-200 leading-relaxed">
                    <p className="text-sm font-semibold text-white">Hi {quote.buyer_contact.name.split(" ")[0]},</p>

                    <p className="text-sm font-bold text-cyan-300">
                      I find jobs for robot companies.
                    </p>

                    <p>
                      I saw <strong>{quote.company_name}</strong> is actively looking to fill the <strong>{quote.job_title}</strong> role in {quote.location}. We matched your operational requirements with <strong>{quote.matched_robot.oem_name}</strong> and worked directly with their engineering team to structure a pre-approved proposal and commercial quote for your facility.
                    </p>

                    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 font-mono text-xs">
                      <div className="text-cyan-400 font-bold">Proposal & Commercial Quote Highlights:</div>
                      <div>• Matched Hardware: {quote.matched_robot.oem_name} {quote.matched_robot.model_name} ({quote.matched_robot.category})</div>
                      <div>• Operational Feasibility: {quote.feasibility_metrics?.heir_score || 94.2}% HEIR Task-Match Score ({quote.feasibility_metrics?.active_deployments || 482} active fleet deployments)</div>
                      <div>• RaaS Monthly Subscription: ${quote.pricing.raas_monthly_rate.toLocaleString()}/mo</div>
                      <div>• Turnkey Hardware Buyout: ${quote.pricing.hardware_cost.toLocaleString()}</div>
                      <div>• EBITDA Financial Impact: Replaces ${quote.pricing.annual_human_labor_cost.toLocaleString()}/yr labor spend for ${(quote.pricing.raas_monthly_rate * 12).toLocaleString()}/yr RaaS = +${annualSavings.toLocaleString()}/yr Net EBITDA Expansion</div>
                      <div>• Estimated Deployment Lead Time: {quote.pricing.estimated_deployment_weeks} weeks</div>
                      <div>• SLA Warranty Guarantee: {quote.pricing.sla_tier}</div>
                    </div>

                    <p>
                      <strong>{quote.matched_robot.oem_name}</strong> has pre-approved this hardware package and pricing configuration. You can view 3D cell simulations, video proof-of-concept, and schedule a 15-minute engineering feasibility call here:
                    </p>

                    <div className="py-2 flex flex-wrap gap-3">
                      <Link
                        href={quote.feasibility_metrics?.poc_simulation_url || "/preview"}
                        className="inline-block px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-xs tracking-wide shadow-md transition-all"
                      >
                        View 3D Cell Simulation & Video Proof-of-Concept →
                      </Link>
                    </div>

                    <p className="text-slate-400 text-[11px] border-t border-slate-800/80 pt-3">
                      Best regards,<br />
                      <strong>Cal</strong> | AI Robotics Procurement Specialist<br />
                      Ready For Robots (readyforrobots.com)
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
