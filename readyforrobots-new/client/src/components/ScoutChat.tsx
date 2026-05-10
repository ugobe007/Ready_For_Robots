/**
 * SCOUT chat shell — provides openChat() for Header / mobile drawer.
 * Full LLM + history lives in FastAPI `/api/scout/*`; this UI is a lightweight placeholder until wired.
 */
import { createContext, useCallback, useContext, useState } from "react";
import { MessageSquare, X } from "lucide-react";

type ScoutChatCtx = { openChat: () => void };
const ScoutChatContext = createContext<ScoutChatCtx>({ openChat: () => {} });

export function useScoutChat() {
  return useContext(ScoutChatContext);
}

function ScoutPanel({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 sm:p-6" style={{ background: "rgba(0,0,0,0.65)" }}>
      <button type="button" className="absolute inset-0 cursor-default" aria-label="Close" onClick={onClose} />
      <div
        className="relative w-full max-w-lg rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
        style={{ background: "rgba(13,5,32,0.98)", backdropFilter: "blur(16px)" }}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/8">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" style={{ color: "#FFB000" }} />
            <span className="text-sm font-semibold text-white">SCOUT</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="h-8 w-8 flex items-center justify-center rounded-lg text-white/50 hover:text-white hover:bg-white/10"
            aria-label="Close chat"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5 text-sm text-white/60 leading-relaxed">
          <p className="mb-3">
            SCOUT can scan your URL, match prospective sales leads, and queue follow-up plans from the results page. Use{" "}
            <strong className="text-white/80">Activate Pipeline</strong> or{" "}
            <strong className="text-white/80">Scan URL</strong> to start.
          </p>
          <p className="text-xs text-white/35">Follow-up automation starts after you activate all matched leads or select individual leads.</p>
        </div>
      </div>
    </div>
  );
}

export function ScoutChat({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const openChat = useCallback(() => setOpen(true), []);

  return (
    <ScoutChatContext.Provider value={{ openChat }}>
      {children}
      {open && <ScoutPanel onClose={() => setOpen(false)} />}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="fixed bottom-4 right-4 z-50 flex items-center gap-2 text-sm font-semibold px-4 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
          style={{
            color: "#FFB000",
            border: "1.5px solid #FFB000",
            background: "rgba(13,5,32,0.85)",
            backdropFilter: "blur(12px)",
            boxShadow: "0 4px 20px rgba(255,176,0,0.12)",
          }}
        >
          <MessageSquare className="h-4 w-4" />
          Talk to SCOUT
          <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#FFB000" }} />
        </button>
      )}
    </ScoutChatContext.Provider>
  );
}
