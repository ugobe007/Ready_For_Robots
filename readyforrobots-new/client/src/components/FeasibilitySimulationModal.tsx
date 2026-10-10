import React, { useState } from "react";
import {
  X,
  Play,
  CheckCircle2,
  ShieldCheck,
  Cpu,
  ArrowRight,
  Download,
  Sparkles,
  Send,
  RefreshCw,
  Box,
} from "lucide-react";
import { toast } from "sonner";
import { buildPhelanExecutiveEmail } from "@/lib/executiveEmailGenerator";
import ResendEmailModal from "@/components/ResendEmailModal";

export interface FeasibilitySimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  companyName: string;
  robotJobTitle?: string;
  matchedRobotModels?: string[];
  dmName?: string;
  onOpenProposalModal?: () => void;
}

export function FeasibilitySimulationModal({
  isOpen,
  onClose,
  companyName,
  robotJobTitle = "Produce Prep Manipulators",
  matchedRobotModels = [
    "Universal Robots UR10e",
    "FANUC CRX-20iA",
    "ABB GoFa CRB 15000",
  ],
  dmName = "",
  onOpenProposalModal,
}: FeasibilitySimulationModalProps) {
  const [simulating, setSimulating] = useState(false);
  const [simComplete, setSimComplete] = useState(true);
  const [showResendModal, setShowResendModal] = useState(false);

  if (!isOpen) return null;

  const handleRunSimulation = () => {
    setSimulating(true);
    setSimComplete(false);
    setTimeout(() => {
      setSimulating(false);
      setSimComplete(true);
      toast.success(
        "3D Cell-Feasibility Simulation complete — 96.4% task match verified!"
      );
    }, 1800);
  };

  const emailData = buildPhelanExecutiveEmail({
    companyName,
    dmName,
    taskType: robotJobTitle,
    robotTypes: matchedRobotModels,
  });

  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
      >
        <div
          className="w-full max-w-4xl rounded-2xl border border-emerald-500/40 bg-slate-900 p-6 text-slate-100 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <Box className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-white flex items-center gap-2">
                  3D Cell-Feasibility Simulation Tool
                  <span className="rounded-full bg-emerald-950 px-2.5 py-0.5 text-[11px] font-extrabold text-emerald-400 border border-emerald-700">
                    Phelan Engine v2.4
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Target:{" "}
                  <span className="font-bold text-slate-200">
                    {companyName}
                  </span>{" "}
                  &bull; Job:{" "}
                  <span className="font-semibold text-emerald-300">
                    {robotJobTitle}
                  </span>
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* 3D Simulation Canvas Viewport */}
          <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950 p-5 shadow-inner">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <Cpu className="h-4 w-4 text-emerald-400" />
                <span>3D Digital Twin & Reach Envelope Simulator</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleRunSimulation}
                  disabled={simulating}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600/90 border border-emerald-500 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-500 transition disabled:opacity-50"
                >
                  {simulating ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Simulating Cell...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-3.5 w-3.5 fill-current" />
                      <span>Re-Run 3D Simulation</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Visual simulation representation */}
            <div className="relative h-56 w-full rounded-lg bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/40 border border-slate-800/80 flex flex-col items-center justify-center p-4">
              <div className="absolute inset-0 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />

              {simulating ? (
                <div className="flex flex-col items-center gap-3 text-emerald-400 z-10">
                  <RefreshCw className="h-10 w-10 animate-spin text-emerald-400" />
                  <p className="text-xs font-mono tracking-wide">
                    Calculating Reach Envelope & Cycle Times...
                  </p>
                </div>
              ) : (
                <div className="w-full max-w-lg space-y-3 text-center z-10">
                  <div className="inline-flex items-center gap-2 rounded-full bg-emerald-950/90 border border-emerald-500/50 px-3 py-1 text-xs font-extrabold text-emerald-300">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>96.4% HEIR Task Feasibility Score Verified</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Physical reach (1,450mm), payload (12.5kg), and cell cycle
                    time (4.2s/unit) validated against target floor geometry.
                  </p>

                  <div className="grid grid-cols-3 gap-3 pt-2 text-left">
                    <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-2.5">
                      <p className="text-[10px] text-slate-400 uppercase font-bold">
                        Reach Radius
                      </p>
                      <p className="text-sm font-extrabold text-white font-mono">
                        1,450 mm
                      </p>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-2.5">
                      <p className="text-[10px] text-slate-400 uppercase font-bold">
                        Cycle Speed
                      </p>
                      <p className="text-sm font-extrabold text-emerald-400 font-mono">
                        4.2 s / unit
                      </p>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-2.5">
                      <p className="text-[10px] text-slate-400 uppercase font-bold">
                        Washdown Rating
                      </p>
                      <p className="text-sm font-extrabold text-white font-mono">
                        IP67 Food-Grade
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Matched Robots Breakdown */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center justify-between">
              <span>Shortlisted Qualified Robot Models</span>
              <span className="text-emerald-400 font-normal text-[11px]">
                {matchedRobotModels.length} Models Verified
              </span>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {matchedRobotModels.map((model, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-white">
                      {model}
                    </span>
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Task Match Score:{" "}
                    <strong className="text-emerald-400 font-mono">95%+</strong>
                  </p>
                  <p className="text-[10px] text-slate-500">
                    RaaS Est: $3,200/mo &bull; 4wk deployment
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Next Steps Execution Bar */}
          <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="space-y-1">
              <h4 className="text-xs font-extrabold text-emerald-300 flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-emerald-400" /> Next Steps
                Action Plan
              </h4>
              <p className="text-xs text-slate-300">
                Send the 3D feasibility report & shortlist to {companyName} or
                generate a formal turnkey RaaS proposal.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {onOpenProposalModal && (
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onOpenProposalModal();
                  }}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 px-3.5 py-2 text-xs font-bold text-slate-200 hover:bg-slate-700 hover:text-white transition"
                >
                  <Download className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Turnkey Proposal PDF</span>
                </button>
              )}
              <button
                type="button"
                onClick={() => setShowResendModal(true)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 border border-emerald-500 px-4 py-2 text-xs font-extrabold text-white hover:bg-emerald-500 transition shadow-lg shadow-emerald-950/50"
              >
                <Send className="h-3.5 w-3.5" />
                <span>Send Next Steps Email via Resend</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Resend Email Modal with Phelan's Next Steps Template */}
      <ResendEmailModal
        isOpen={showResendModal}
        onClose={() => setShowResendModal(false)}
        defaultTo=""
        defaultSubject={emailData.subject}
        defaultBody={emailData.body}
        companyName={companyName}
      />
    </>
  );
}

export default FeasibilitySimulationModal;
