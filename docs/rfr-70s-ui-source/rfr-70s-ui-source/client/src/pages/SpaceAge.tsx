/**
 * CONCEPT C — "SPACE-AGE ’72"
 * Design movement: NASA Graphics Standards Manual (1975) + grid modernism +
 * mission control. Strict grid, oversized numerals, hairline rules.
 * Signature color: NASA red #FC3D21 on warm white #F5F3EE, charcoal #1A1A1A.
 * Type: Michroma (worm-adjacent display) + Space Mono (data) + Archivo (body).
 */
import { useEffect, useRef, useState } from "react";
import { ConceptBanner } from "@/components/ConceptBanner";
import { ASSETS, DEFINITIONS, JOB_CARDS, STEPS } from "@/lib/jobs";

const RED = "#FC3D21";
const CHAR = "#1A1A1A";
const WHITE = "#F5F3EE";
const GREEN = "#2E7D32";

function useCountUp(target: number, duration = 1200, start = false) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!start) return;
    let raf: number;
    const t0 = performance.now();
    const step = (t: number) => {
      const p = Math.min(1, (t - t0) / duration);
      setVal(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration, start]);
  return val;
}

function OrbitLines() {
  return (
    <svg viewBox="0 0 800 800" className="absolute inset-0 w-full h-full opacity-[0.14] animate-[spin_90s_linear_infinite]" aria-hidden>
      {[120, 200, 290, 380].map((r, i) => (
        <ellipse
          key={i}
          cx="400"
          cy="400"
          rx={r}
          ry={r * 0.62}
          fill="none"
          stroke={WHITE}
          strokeWidth="1"
          transform={`rotate(${i * 24} 400 400)`}
        />
      ))}
      <circle cx="400" cy="400" r="6" fill={RED} />
    </svg>
  );
}

function MissionPatch({ size = 120 }: { size?: number }) {
  return (
    <img
      src={ASSETS.missionPatch}
      alt="ReadyForRobots mission patch"
      width={size}
      height={size}
      className="rounded-full object-contain"
      style={{ width: size, height: size }}
    />
  );
}

function Telemetry({ label, value, unit, accent = false }: { label: string; value: string; unit?: string; accent?: boolean }) {
  return (
    <div className="border-l-2 pl-3" style={{ borderColor: accent ? RED : `${WHITE}44` }}>
      <p className="text-[10px] tracking-[0.25em] uppercase" style={{ color: `${WHITE}99`, fontFamily: "'Space Mono', monospace" }}>
        {label}
      </p>
      <p className="text-lg md:text-xl font-bold" style={{ color: accent ? RED : WHITE, fontFamily: "'Space Mono', monospace" }}>
        {value}
        {unit && <span className="text-xs ml-1" style={{ color: `${WHITE}99` }}>{unit}</span>}
      </p>
    </div>
  );
}

function ManifestCard({ job, index }: { job: (typeof JOB_CARDS)[number]; index: number }) {
  const [open, setOpen] = useState(index === 0);
  return (
    <div className="border transition-colors duration-200" style={{ borderColor: `${CHAR}33`, background: WHITE }}>
      <button onClick={() => setOpen((v) => !v)} className="w-full text-left group">
        <div className="flex items-stretch">
          <div
            className="w-16 md:w-20 shrink-0 flex items-center justify-center text-2xl md:text-3xl transition-colors duration-200"
            style={{ background: open ? RED : CHAR, color: WHITE, fontFamily: "'Michroma', sans-serif" }}
          >
            {String(index + 1).padStart(2, "0")}
          </div>
          <div className="flex-1 p-4 md:p-5">
            <div className="flex items-baseline justify-between gap-3 flex-wrap">
              <h3 className="text-lg md:text-xl font-bold tracking-wide" style={{ color: CHAR, fontFamily: "'Michroma', sans-serif" }}>
                {job.employer.toUpperCase()}
              </h3>
              <span
                className="text-[10px] tracking-[0.3em] uppercase px-2 py-1"
                style={{
                  color: job.status === "OPEN" ? WHITE : CHAR,
                  background: job.status === "OPEN" ? GREEN : "transparent",
                  border: `1px solid ${job.status === "OPEN" ? GREEN : CHAR}`,
                  fontFamily: "'Space Mono', monospace",
                }}
              >
                {job.status === "OPEN" ? "● GO" : "○ CONDITIONAL"}
              </span>
            </div>
            <p className="mt-1 text-xs tracking-[0.2em] uppercase" style={{ color: `${CHAR}88`, fontFamily: "'Space Mono', monospace" }}>
              {job.id} · {job.sector}
            </p>
          </div>
          <div className="w-10 shrink-0 flex items-center justify-center border-l" style={{ borderColor: `${CHAR}22`, color: RED }}>
            <span className="transition-transform duration-200" style={{ transform: open ? "rotate(90deg)" : "none" }}>▸</span>
          </div>
        </div>
      </button>
      {open && (
        <div className="border-t p-4 md:p-6 grid md:grid-cols-2 gap-x-8 gap-y-3" style={{ borderColor: `${CHAR}22` }}>
          {[
            ["EMPLOYER", `${job.employer} — ${job.sector}`],
            ["WORKPLACE", job.workplace],
            ["WORK", job.work],
            ["DRIVERS", job.drivers.join(" · ")],
            ["WINDOW", job.window],
            ["VEHICLE FIT", job.fit.join(" · ")],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-[10px] tracking-[0.3em] uppercase" style={{ color: RED, fontFamily: "'Space Mono', monospace" }}>{k}</p>
              <p className="text-sm mt-0.5" style={{ color: CHAR, fontFamily: "'Archivo', sans-serif" }}>{v}</p>
            </div>
          ))}
          <p className="md:col-span-2 text-xs mt-1" style={{ color: `${CHAR}88`, fontFamily: "'Space Mono', monospace" }}>
            NOTE: QUALIFICATION IS EXPLAINABLE — NEVER A %. CARDS STAY CONDITIONAL UNTIL EVIDENCE.
          </p>
        </div>
      )}
    </div>
  );
}

export default function SpaceAge() {
  const heroRef = useRef<HTMLDivElement>(null);
  const [heroIn, setHeroIn] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setHeroIn(true), 100);
    return () => clearTimeout(t);
  }, []);
  const openJobs = useCountUp(5, 1200, heroIn);
  const matched = useCountUp(3, 1400, heroIn);
  const days = useCountUp(210, 1600, heroIn);

  return (
    <div className="min-h-screen pb-24" style={{ background: CHAR, color: WHITE, fontFamily: "'Archivo', sans-serif" }}>
      {/* Header */}
      <header className="border-b" style={{ borderColor: `${WHITE}22` }}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <MissionPatch size={44} />
            <span className="text-sm md:text-base tracking-[0.35em] uppercase" style={{ fontFamily: "'Michroma', sans-serif" }}>
              READY<span style={{ color: RED }}>FOR</span>ROBOTS
            </span>
          </div>
          <nav className="hidden md:flex gap-8 text-[11px] tracking-[0.3em] uppercase" style={{ fontFamily: "'Space Mono', monospace" }}>
            {["Jobs", "About", "CRM", "Sign In"].map((n) => (
              <a
                key={n}
                href="#"
                onClick={(e) => e.preventDefault()}
                className="relative py-1 transition-colors duration-200 hover:text-white group"
                style={{ color: `${WHITE}99` }}
              >
                {n}
                <span className="absolute left-0 -bottom-0.5 h-[2px] w-0 transition-all duration-200 group-hover:w-full" style={{ background: RED }} />
              </a>
            ))}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section ref={heroRef} className="relative overflow-hidden border-b" style={{ borderColor: `${WHITE}22` }}>
        <div className="absolute inset-0">
          <OrbitLines />
        </div>
        <div className="relative max-w-6xl mx-auto px-4 py-16 md:py-24 grid md:grid-cols-12 gap-8 items-center">
          <div className="md:col-span-7">
            <p className="text-[11px] tracking-[0.4em] uppercase" style={{ color: RED, fontFamily: "'Space Mono', monospace" }}>
              Mission Briefing · 1972
            </p>
            <h1
              className="mt-4 text-4xl md:text-6xl leading-[1.1] uppercase"
              style={{ fontFamily: "'Michroma', sans-serif" }}
            >
              Who is<br />this <span style={{ color: RED }}>visit?</span>
            </h1>
            <p className="mt-6 max-w-md text-base md:text-lg" style={{ color: `${WHITE}BB` }}>
              Jobs for a robot you already have, or robots for work you need done.
              Robots need jobs. We find the work.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <button
                className="px-6 py-3 text-xs tracking-[0.3em] uppercase font-bold transition-all duration-200 hover:tracking-[0.4em]"
                style={{ background: RED, color: WHITE, fontFamily: "'Space Mono', monospace" }}
              >
                Initiate Match →
              </button>
              <button
                className="px-6 py-3 text-xs tracking-[0.3em] uppercase transition-all duration-200 border hover:bg-white/5"
                style={{ borderColor: `${WHITE}55`, color: WHITE, fontFamily: "'Space Mono', monospace" }}
              >
                Post Work
              </button>
            </div>
          </div>
          <div className="md:col-span-5 flex flex-col items-center gap-6">
            <img src={ASSETS.spaceRobot} alt="Space-age robot" className="w-56 md:w-72 object-contain" />
            <div className="grid grid-cols-3 gap-6 w-full max-w-sm">
              <Telemetry label="Open" value={String(openJobs).padStart(2, "0")} accent />
              <Telemetry label="Matched" value={String(matched).padStart(2, "0")} />
              <Telemetry label="Window" value={String(days)} unit="d" />
            </div>
          </div>
        </div>
      </section>

      {/* Flight plan */}
      <section className="max-w-6xl mx-auto px-4 py-14 border-b" style={{ borderColor: `${WHITE}22` }}>
        <div className="flex items-baseline gap-6">
          <span className="text-6xl md:text-8xl" style={{ fontFamily: "'Michroma', sans-serif", color: `${WHITE}22` }}>01</span>
          <h2 className="text-xl md:text-2xl uppercase tracking-widest" style={{ fontFamily: "'Michroma', sans-serif" }}>
            Flight Plan
          </h2>
        </div>
        <div className="mt-8 grid md:grid-cols-3 gap-px" style={{ background: `${WHITE}22` }}>
          {STEPS.map((s, i) => (
            <div key={s.n} className="p-6 group transition-colors duration-200 hover:bg-white/5" style={{ background: CHAR }}>
              <p className="text-3xl" style={{ fontFamily: "'Michroma', sans-serif", color: i === 0 ? RED : `${WHITE}55` }}>
                {s.n}
              </p>
              <p className="mt-3 text-sm tracking-[0.2em] uppercase font-bold" style={{ fontFamily: "'Space Mono', monospace" }}>
                {s.title}
              </p>
              <p className="mt-2 text-sm" style={{ color: `${WHITE}99` }}>{s.body}</p>
              <div className="mt-4 h-[2px] w-8 transition-all duration-300 group-hover:w-full" style={{ background: RED }} />
            </div>
          ))}
        </div>
      </section>

      {/* Manifest */}
      <section className="max-w-6xl mx-auto px-4 py-14 border-b" style={{ borderColor: `${WHITE}22` }}>
        <div className="flex items-baseline gap-6">
          <span className="text-6xl md:text-8xl" style={{ fontFamily: "'Michroma', sans-serif", color: `${WHITE}22` }}>02</span>
          <div>
            <h2 className="text-xl md:text-2xl uppercase tracking-widest" style={{ fontFamily: "'Michroma', sans-serif" }}>
              Launch Manifest
            </h2>
            <p className="mt-1 text-xs tracking-[0.3em] uppercase" style={{ color: `${WHITE}77`, fontFamily: "'Space Mono', monospace" }}>
              5 open positions · 3 featured · status: go for hire
            </p>
          </div>
        </div>
        <div className="mt-8 space-y-4">
          {JOB_CARDS.map((j, i) => (
            <ManifestCard key={j.id} job={j} index={i} />
          ))}
        </div>
      </section>

      {/* Definitions + CTA */}
      <section className="max-w-6xl mx-auto px-4 py-14">
        <div className="flex items-baseline gap-6">
          <span className="text-6xl md:text-8xl" style={{ fontFamily: "'Michroma', sans-serif", color: `${WHITE}22` }}>03</span>
          <h2 className="text-xl md:text-2xl uppercase tracking-widest" style={{ fontFamily: "'Michroma', sans-serif" }}>
            Mission Glossary
          </h2>
        </div>
        <div className="mt-8 grid md:grid-cols-2 gap-x-12">
          {DEFINITIONS.map((d) => (
            <div key={d.term} className="py-4 border-b group" style={{ borderColor: `${WHITE}22` }}>
              <div className="flex items-baseline gap-4">
                <span className="w-2 h-2 shrink-0 transition-colors duration-200" style={{ background: RED }} />
                <p className="text-sm tracking-[0.25em] uppercase font-bold" style={{ fontFamily: "'Space Mono', monospace" }}>{d.term}</p>
              </div>
              <p className="mt-1 pl-6 text-sm" style={{ color: `${WHITE}99` }}>{d.def}</p>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-wrap items-center gap-6 border-t pt-8" style={{ borderColor: `${WHITE}22` }}>
          <MissionPatch size={72} />
          <div className="flex-1 min-w-[240px]">
            <p className="text-sm tracking-[0.2em] uppercase" style={{ fontFamily: "'Space Mono', monospace", color: RED }}>
              ReadyForRobots · Robot Employment Program
            </p>
            <p className="mt-1 text-xs" style={{ color: `${WHITE}77` }}>
              © 1972–2026 ReadyForRobots · Jobs for your robot · support@readyforrobots.com
            </p>
          </div>
          <button
            className="px-6 py-3 text-xs tracking-[0.3em] uppercase font-bold transition-all duration-200 hover:tracking-[0.4em]"
            style={{ background: RED, color: WHITE, fontFamily: "'Space Mono', monospace" }}
          >
            Start Free Workspace →
          </button>
        </div>
      </section>
      <ConceptBanner />
    </div>
  );
}
