/**
 * SIGNAL chat shell — light emerald theme, matches site redesign.
 */
import { createContext, useCallback, useContext, useState } from "react";
import { Link, useLocation } from "wouter";
import { MessageSquare, X, Zap } from "lucide-react";

type ScoutChatCtx = { openChat: () => void };
const ScoutChatContext = createContext<ScoutChatCtx>({ openChat: () => {} });

export function useScoutChat() {
  return useContext(ScoutChatContext);
}

function ScoutPanel({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 sm:p-6 bg-black/40 backdrop-blur-sm">
      <button type="button" className="absolute inset-0 cursor-default" aria-label="Close" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-2xl border border-gray-200 bg-white shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-emerald-50">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-display font-semibold text-gray-900">SIGNAL</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="h-8 w-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100"
            aria-label="Close chat"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5 text-sm text-gray-600 leading-relaxed">
          <p className="mb-3">
            SIGNAL scans your URL, captures qualified buyer leads, scores alignment, and queues activation plans from the results page.
          </p>
          <Link
            href="/signup"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            <Zap className="h-4 w-4" />
            Activate SIGNAL
          </Link>
          <p className="mt-4 text-xs text-gray-400">
            Follow-up automation starts after you activate aligned leads or select individual leads on the pipeline.
          </p>
        </div>
      </div>
    </div>
  );
}

export function ScoutChat({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [location] = useLocation();
  const openChat = useCallback(() => setOpen(true), []);
  const onPipeline = location === "/pipeline" || location.startsWith("/admin/prospects");
  const hideFab =
    location === "/" ||
    location.startsWith("/?") ||
    location === "/jobs" ||
    location.startsWith("/jobs/") ||
    location.startsWith("/jobs?") ||
    location === "/experiment" ||
    location.startsWith("/experiment?");

  return (
    <ScoutChatContext.Provider value={{ openChat }}>
      {children}
      {open && <ScoutPanel onClose={() => setOpen(false)} />}
      {!open && !hideFab && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className={`fixed right-4 z-40 flex items-center gap-2 text-sm font-semibold px-4 py-2.5 rounded-xl border border-emerald-600 bg-white text-emerald-700 shadow-lg transition-all hover:bg-emerald-50 hover:-translate-y-0.5 ${onPipeline ? "bottom-24" : "bottom-4"}`}
        >
          <MessageSquare className="h-4 w-4" />
          Signal
          <span className="relative inline-flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
        </button>
      )}
    </ScoutChatContext.Provider>
  );
}
