/**
 * CONCEPT A — "MAINFRAME ’74"
 * Design movement: 1970s corporate computing — IBM 3270 terminals, punch cards,
 * computer-room beige. The whole site becomes a job-system terminal session.
 * Signature color: phosphor amber #FFB000 on CRT black #0B0F0A.
 * Type: VT323 everywhere. Interaction = keystrokes, inverse-video hover.
 */
import { useEffect, useState } from "react";
import { ConceptBanner } from "@/components/ConceptBanner";
import { ASSETS, DEFINITIONS, JOB_CARDS, STEPS, TAGLINE } from "@/lib/jobs";

const AMBER = "#FFB000";
const GREEN = "#33FF66";

function useTypewriter(lines: string[], speed = 14, startDelay = 400) {
  const [shown, setShown] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  useEffect(() => {
    let line = 0;
    let ch = 0;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      if (line >= lines.length) {
        setDone(true);
        return;
      }
      ch++;
      const current = lines[line].slice(0, ch);
      setShown((prev) => {
        const next = prev.slice(0, line);
        next[line] = current;
        return next;
      });
      if (ch >= lines[line].length) {
        line++;
        ch = 0;
        timer = setTimeout(tick, 120);
      } else {
        timer = setTimeout(tick, speed);
      }
    };
    timer = setTimeout(tick, startDelay);
    return () => clearTimeout(timer);
  }, [lines, speed, startDelay]);
  return { shown, done };
}

function Cursor() {
  return (
    <span
      className="inline-block w-[0.6em] h-[1em] align-[-0.15em] ml-1 animate-pulse"
      style={{ background: AMBER }}
    />
  );
}

function KeyCap({ label, onClick, accent = false }: { label: string; onClick?: () => void; accent?: boolean }) {
  return (
    <button
      onClick={onClick}
      className="group inline-flex items-center gap-2 border-2 px-4 py-2 text-lg tracking-widest uppercase transition-colors duration-100"
      style={{
        borderColor: accent ? GREEN : AMBER,
        color: accent ? GREEN : AMBER,
        background: "transparent",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = accent ? GREEN : AMBER;
        e.currentTarget.style.color = "#0B0F0A";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = accent ? GREEN : AMBER;
      }}
    >
      [ {label} ]
    </button>
  );
}

function PunchCard({ job, index }: { job: (typeof JOB_CARDS)[number]; index: number }) {
  const [open, setOpen] = useState(index === 0);
  return (
    <div
      className="relative border-2 text-left"
      style={{
        borderColor: AMBER,
        background: "#10150c",
        clipPath:
          "polygon(18px 0, 100% 0, 100% calc(100% - 18px), calc(100% - 18px) 100%, 0 100%, 0 18px)",
      }}
    >
      {/* perforation holes */}
      <div className="flex gap-2 px-6 pt-3" aria-hidden>
        {Array.from({ length: 24 }).map((_, i) => (
          <span key={i} className="w-1.5 h-1.5 rounded-full" style={{ background: "#0B0F0A", outline: `1px solid ${AMBER}55` }} />
        ))}
      </div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full px-6 py-4 flex items-baseline justify-between gap-4 text-left"
        style={{ color: AMBER }}
      >
        <span className="text-xl md:text-2xl tracking-wider">
          {job.id} :: {job.employer.toUpperCase()}
        </span>
        <span className="text-sm" style={{ color: job.status === "OPEN" ? GREEN : AMBER }}>
          {open ? "▲ CLOSE" : "▼ OPEN"} · {job.status}
        </span>
      </button>
      {open && (
        <div className="px-6 pb-6 space-y-2 text-base md:text-lg" style={{ color: "#E8D9A0" }}>
          <p><span style={{ color: AMBER }}>EMPLOYER..:</span> {job.employer} — {job.sector}</p>
          <p><span style={{ color: AMBER }}>WORKPLACE:</span> {job.workplace}</p>
          <p><span style={{ color: AMBER }}>WORK.....:</span> {job.work}</p>
          <p><span style={{ color: AMBER }}>DRIVERS..:</span> {job.drivers.join(" · ")}</p>
          <p><span style={{ color: AMBER }}>WINDOW...:</span> {job.window}</p>
          <p><span style={{ color: AMBER }}>GOOD FIT.:</span> {job.fit.join(" · ")}</p>
          <p className="pt-2" style={{ color: GREEN }}>
            &gt; QUALIFICATION: EXPLAINABLE — NEVER A %. EVIDENCE REQUIRED BEFORE STATUS=OPEN.
          </p>
        </div>
      )}
      <div className="flex gap-2 px-6 pb-3" aria-hidden>
        {Array.from({ length: 24 }).map((_, i) => (
          <span key={i} className="w-1.5 h-1.5 rounded-full" style={{ background: "#0B0F0A", outline: `1px solid ${AMBER}55` }} />
        ))}
      </div>
    </div>
  );
}

export default function Mainframe() {
  const boot = useTypewriter(
    [
      "READYFORROBOTS JOB SYSTEM  V2.3  —  SYS/370 EMULATION",
      "CONNECTING TO JOB QUEUE ............ OK",
      "5 POSITIONS OPEN. 3 FEATURED BELOW.",
      "WHO IS THIS VISIT? SELECT MODE:",
    ],
    12
  );

  return (
    <div
      className="min-h-screen w-full flex items-stretch justify-center p-3 md:p-8 pb-20"
      style={{ background: "#1a1d18", fontFamily: "'VT323', monospace" }}
    >
      {/* Equipment bezel */}
      <div
        className="w-full max-w-6xl rounded-[2rem] p-3 md:p-6 shadow-2xl"
        style={{ background: "linear-gradient(160deg,#d8cfb8 0%,#b8ae94 100%)" }}
      >
        <div className="flex items-center justify-between px-4 pb-3">
          <span className="text-neutral-800 text-lg tracking-widest">RFR-370 DISPLAY STATION</span>
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full bg-red-600 shadow-inner" />
            <span className="w-3 h-3 rounded-full" style={{ background: GREEN }} />
            <span className="text-neutral-700 text-sm">PWR · RDY</span>
          </div>
        </div>

        {/* CRT screen */}
        <div
          className="relative rounded-[1.5rem] overflow-hidden"
          style={{
            background: "radial-gradient(ellipse at center, #14210f 0%, #0B0F0A 75%)",
            boxShadow: "inset 0 0 80px rgba(0,0,0,0.9)",
          }}
        >
          {/* scanlines + flicker */}
          <div
            className="pointer-events-none absolute inset-0 z-20"
            style={{
              background:
                "repeating-linear-gradient(0deg, rgba(0,0,0,0.28) 0px, rgba(0,0,0,0.28) 1px, transparent 1px, transparent 3px)",
              mixBlendMode: "multiply",
            }}
          />
          <div
            className="pointer-events-none absolute inset-0 z-20 opacity-[0.06] animate-pulse"
            style={{ background: AMBER }}
          />

          <div className="relative z-10 p-5 md:p-10 min-h-[80vh]" style={{ textShadow: `0 0 8px ${AMBER}66` }}>
            {/* header */}
            <pre className="text-sm md:text-base leading-tight overflow-x-auto" style={{ color: AMBER }}>
{`╔══════════════════════════════════════════════════════════════╗
║  READYFORROBOTS · JOB ENTRY SUBSYSTEM · 09/01/74 · 09:14:22  ║
╚══════════════════════════════════════════════════════════════╝`}
            </pre>

            {/* boot sequence */}
            <div className="mt-6 space-y-1 text-lg md:text-2xl" style={{ color: AMBER }}>
              {boot.shown.map((l, i) => (
                <p key={i}>&gt; {l}{i === boot.shown.length - 1 && !boot.done && <Cursor />}</p>
              ))}
              {boot.done && <Cursor />}
            </div>

            {/* mode select — the "Who is this visit?" split */}
            <div className="mt-8 grid md:grid-cols-2 gap-6">
              <div className="border-2 p-5" style={{ borderColor: AMBER }}>
                <p className="text-xl md:text-2xl" style={{ color: GREEN }}>MODE 1 — ROBOT OWNER</p>
                <p className="mt-2 text-lg md:text-xl" style={{ color: "#E8D9A0" }}>
                  LOOK FOR ROBOT JOBS. Paste a product URL, or pick a named catalog robot.
                  We match it to real jobs.
                </p>
                <div className="mt-4">
                  <KeyCap label="F1 · Look for robot jobs" accent />
                </div>
              </div>
              <div className="border-2 p-5" style={{ borderColor: AMBER }}>
                <p className="text-xl md:text-2xl" style={{ color: AMBER }}>MODE 2 — EMPLOYER</p>
                <p className="mt-2 text-lg md:text-xl" style={{ color: "#E8D9A0" }}>
                  LOOK FOR ROBOT CANDIDATES. Tell us the work. We match named catalog robots.
                  Then you can post the job.
                </p>
                <div className="mt-4">
                  <KeyCap label="F2 · Look for candidates" />
                </div>
              </div>
            </div>

            {/* procedure */}
            <div className="mt-10">
              <p className="text-xl md:text-2xl" style={{ color: AMBER }}>
                ── OPERATING PROCEDURE ──────────────────────────────
              </p>
              <div className="mt-4 grid md:grid-cols-3 gap-4">
                {STEPS.map((s) => (
                  <div key={s.n} className="border p-4" style={{ borderColor: `${AMBER}88` }}>
                    <p className="text-2xl" style={{ color: GREEN }}>{s.n}</p>
                    <p className="text-xl" style={{ color: AMBER }}>{s.title.toUpperCase()}</p>
                    <p className="text-base mt-1" style={{ color: "#E8D9A0" }}>{s.body.toUpperCase()}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* job queue */}
            <div className="mt-10">
              <p className="text-xl md:text-2xl" style={{ color: AMBER }}>
                ── JOB QUEUE · PUNCH-CARD TICKETS ───────────────────
              </p>
              <div className="mt-4 space-y-4">
                {JOB_CARDS.map((j, i) => (
                  <PunchCard key={j.id} job={j} index={i} />
                ))}
              </div>
            </div>

            {/* glossary */}
            <div className="mt-10 grid md:grid-cols-2 gap-6">
              <div className="border-2 p-5" style={{ borderColor: AMBER }}>
                <p className="text-xl" style={{ color: GREEN }}>GLOSSARY.SYS</p>
                <div className="mt-2 space-y-2 text-base md:text-lg" style={{ color: "#E8D9A0" }}>
                  {DEFINITIONS.map((d) => (
                    <p key={d.term}>
                      <span style={{ color: AMBER }}>{d.term.toUpperCase().padEnd(12, " ")}:</span>{" "}
                      {d.def.toUpperCase()}
                    </p>
                  ))}
                </div>
              </div>
              <div className="border-2 p-5 flex flex-col items-center justify-center gap-4" style={{ borderColor: AMBER }}>
                <img
                  src={ASSETS.terminal}
                  alt="1970s terminal with robot face"
                  className="w-48 md:w-64 rounded"
                  style={{ filter: "sepia(0.4) brightness(0.9)", mixBlendMode: "screen" }}
                />
                <p className="text-lg text-center" style={{ color: "#E8D9A0" }}>{TAGLINE.toUpperCase()}</p>
              </div>
            </div>

            {/* footer status bar */}
            <div
              className="mt-10 flex flex-wrap items-center justify-between gap-2 border-t-2 pt-3 text-base md:text-lg"
              style={{ borderColor: AMBER, color: AMBER }}
            >
              <span>READY. TYPE F1 TO SUBMIT ROBOT · F2 TO POST WORK</span>
              <span style={{ color: GREEN }}>■ SYS/370 READY</span>
            </div>
          </div>
        </div>
      </div>
      <ConceptBanner />
    </div>
  );
}
