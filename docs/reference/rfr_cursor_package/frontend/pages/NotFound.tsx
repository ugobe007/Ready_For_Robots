import { ArrowLeft, Zap } from "lucide-react";
import { useLocation } from "wouter";
import { useScoutChat } from "@/components/ScoutChat";

export default function NotFound() {
  const [, setLocation] = useLocation();
  const { openChat } = useScoutChat();

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "#0d0520" }}
    >
      {/* Glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(124,58,237,0.10) 0%, transparent 70%)" }}
      />

      <div className="relative text-center max-w-md">
        {/* 404 number */}
        <p
          className="font-extrabold leading-none mb-4 select-none"
          style={{
            fontSize: "clamp(6rem, 20vw, 10rem)",
            fontFamily: "'Sora', system-ui, sans-serif",
            background: "linear-gradient(135deg, rgba(124,58,237,0.25) 0%, rgba(3,218,197,0.15) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.04em",
          }}
        >
          404
        </p>

        {/* SCOUT badge */}
        <div className="inline-flex items-center gap-2 mb-5">
          <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
          <span className="text-xs font-bold uppercase tracking-[0.15em]" style={{ color: "#c4b5fd" }}>
            SCOUT couldn't find this page
          </span>
        </div>

        <h1
          className="font-extrabold text-white mb-3"
          style={{ fontSize: "clamp(1.5rem, 4vw, 2rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
        >
          Page not found
        </h1>
        <p className="text-white/40 text-sm leading-relaxed mb-8">
          The page you're looking for doesn't exist or has been moved.
          SCOUT is still out there finding robot deals — just not on this URL.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => setLocation("/")}
            className="flex items-center gap-2 text-sm font-semibold px-5 py-3 rounded-xl transition-all hover:-translate-y-0.5"
            style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.7)" }}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </button>
          <button
            onClick={openChat}
            className="flex items-center gap-2 text-sm font-semibold px-5 py-3 rounded-xl transition-all hover:-translate-y-0.5 hover:bg-teal-400/8"
            style={{ color: "#FFB000", border: "1.5px solid rgba(255,176,0,0.5)", background: "transparent" }}
          >
            <Zap className="h-4 w-4" />
            Activate Pipeline
          </button>
        </div>
      </div>
    </div>
  );
}
