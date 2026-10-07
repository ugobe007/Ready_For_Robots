import React, { useState, useEffect } from "react";
import {
  X,
  Share2,
  Check,
  Sparkles,
  Building2,
  Cpu,
  ShieldCheck,
  Zap,
  UserPlus,
  Clock,
  DollarSign,
  Layers,
} from "lucide-react";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD } from "@/lib/kareIcons";
import {
  TAPE_ICONS,
  type TapeJob,
} from "@/lib/jobsTapeCorpus";

type Props = {
  job: TapeJob | null;
  isOpen: boolean;
  onClose: () => void;
  onUnlockSignup?: () => void;
};

export default function LiveJobDetailModal({
  job,
  isOpen,
  onClose,
  onUnlockSignup,
}: Props) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !job) return null;

  const shareUrl = `${window.location.origin}/?visit=jobs&job=${encodeURIComponent(job.key)}`;

  const handleShare = async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(shareUrl);
      } else {
        const input = document.createElement("input");
        input.value = shareUrl;
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const iconMap = TAPE_ICONS[job.family] || TAPE_ICONS.transport;

  // Form factor & spec defaults based on job family
  const formFactor =
    job.family === "pallet"
      ? "Autonomous Pallet AMR & Heavy Cobot"
      : job.family === "scrub"
        ? "Commercial Scrubbing Robot & Floor AMR"
        : job.family === "gripper"
          ? "Mobile Dual-Arm Manipulator / Humanoid"
          : job.family === "inspect"
            ? "Vision-Guided Quadruped / Inspection Drone"
            : "Autonomous Mobile Robot (AMR) & Tugger";

  const specs = {
    payload: job.family === "pallet" ? "500kg - 1,200kg" : job.family === "gripper" ? "15kg - 35kg" : "50kg - 250kg",
    shift: "3-Shift Continuous (24/7 Deployment)",
    payback: "Est. 8.4-month payback · $8.5k/mo RaaS option",
    wms: "WMS / PLC REST API & ROS2 Interface Compliant",
    safety: "ANSI/RIA R15.08 & ISO 3691-4 Safety Standard",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0d1b38] text-slate-100 shadow-2xl transition-all my-auto z-10">
        {/* Top Header Band */}
        <div className="flex items-center justify-between border-b border-slate-700/80 bg-[#081126] px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10">
              <PixelIcon
                map={iconMap}
                scale={1.5}
                fill={FACE_EMERALD}
                background="transparent"
              />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2.5 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                  Verified Work Opportunity
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  ID: {job.key}
                </span>
              </div>
              <h2 className="mt-0.5 text-lg sm:text-xl font-extrabold text-white font-display">
                {job.title}
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Company & Sector Badges */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-3.5 flex items-start gap-3">
              <Building2 className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
              <div>
                <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Employer / Industry
                </p>
                <p className="mt-0.5 text-sm font-bold text-white">
                  {job.industry}
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-3.5 flex items-start gap-3">
              <Layers className="h-4 w-4 text-cyan-400 mt-0.5 shrink-0" />
              <div>
                <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Worksite Path / Location
                </p>
                <p className="mt-0.5 text-xs font-mono font-bold text-cyan-300">
                  {job.path}
                </p>
              </div>
            </div>
          </div>

          {/* Form Factor & Hardware Suitability */}
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
            <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-emerald-400">
              <Cpu className="h-4 w-4 text-emerald-400" /> Form Factor & Hardware Suitability
            </div>
            <p className="mt-1.5 text-sm font-bold text-slate-100">
              {formFactor}
            </p>
            <p className="mt-1 text-xs text-slate-300">
              This task model requires automated navigation, obstacle avoidance, and standardized payload transfer mechanisms.
            </p>
          </div>

          {/* Technical Specifications Table */}
          <div className="space-y-2">
            <p className="font-mono text-xs font-bold uppercase tracking-wider text-slate-400">
              Operational Constraints & Feasibility Specs
            </p>

            <div className="rounded-xl border border-slate-700/60 bg-[#081126] divide-y divide-slate-800 text-xs">
              <div className="flex items-center justify-between p-3">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5 text-amber-400" /> Payload & Weight Limit
                </span>
                <span className="font-semibold text-slate-100 font-mono">{specs.payload}</span>
              </div>
              <div className="flex items-center justify-between p-3">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-emerald-400" /> Shift & Operating Schedule
                </span>
                <span className="font-semibold text-slate-100">{specs.shift}</span>
              </div>
              <div className="flex items-center justify-between p-3">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <DollarSign className="h-3.5 w-3.5 text-cyan-400" /> ROI & RaaS Financing
                </span>
                <span className="font-semibold text-amber-300 font-mono">{specs.payback}</span>
              </div>
              <div className="flex items-center justify-between p-3">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-purple-400" /> WMS & Safety Standard
                </span>
                <span className="font-semibold text-slate-200">{specs.safety}</span>
              </div>
            </div>
          </div>

          {/* Turnkey Proposal Note */}
          <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4 text-xs text-slate-300 space-y-1.5">
            <div className="flex items-center gap-1.5 text-slate-100 font-semibold">
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" /> Feasibility & Commercial Proposal Ready
            </div>
            <p>
              ReadyForRobots has pre-mapped this task model against 109+ commercial robot specifications. Sign up for a free enterprise workspace to generate full 3D cell simulations and turnkey commercial quotes for this lead.
            </p>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-700/80 bg-[#081126] px-6 py-4">
          <button
            type="button"
            onClick={handleShare}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs tracking-wide transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 text-emerald-400" />
                <span>Link Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="h-4 w-4 text-slate-400" />
                <span>Share Opportunity</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              onClose();
              if (onUnlockSignup) onUnlockSignup();
            }}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-extrabold text-xs tracking-wide uppercase transition-all shadow-lg shadow-emerald-400/20 flex items-center justify-center gap-2 cursor-pointer"
          >
            <UserPlus className="h-4 w-4" />
            <span>Unlock Full Feasibility & Quote →</span>
          </button>
        </div>
      </div>
    </div>
  );
}
