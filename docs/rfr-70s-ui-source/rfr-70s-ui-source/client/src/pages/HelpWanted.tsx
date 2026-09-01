/**
 * CONCEPT B — "HELP WANTED ’76"
 * Design movement: 1970s American print vernacular — newspaper classifieds,
 * Yellow Pages, Sears catalog. Earth-tone palette on cream paper.
 * Signature color: avocado #5B7A2A with harvest gold #E8A020 on cream #F4EDDA.
 * Type: Shrikhand (display) + Courier Prime (classifieds) + Archivo (UI).
 */
import { useState } from "react";
import { ConceptBanner } from "@/components/ConceptBanner";
import { ASSETS, DEFINITIONS, JOB_CARDS, STEPS } from "@/lib/jobs";

const AVOCADO = "#5B7A2A";
const GOLD = "#E8A020";
const ORANGE = "#C4501B";
const BROWN = "#4A2E15";
const CREAM = "#F4EDDA";

function WavyStripes() {
  return (
    <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="w-full h-10 md:h-14" aria-hidden>
      {[
        { y: 6, c: AVOCADO },
        { y: 20, c: GOLD },
        { y: 34, c: ORANGE },
        { y: 48, c: BROWN },
      ].map((s, i) => (
        <path
          key={i}
          d={`M0 ${s.y} Q 75 ${s.y - 12}, 150 ${s.y} T 300 ${s.y} T 450 ${s.y} T 600 ${s.y} T 750 ${s.y} T 900 ${s.y} T 1050 ${s.y} T 1200 ${s.y}`}
          fill="none"
          stroke={s.c}
          strokeWidth="7"
          strokeLinecap="round"
        />
      ))}
    </svg>
  );
}

function Starburst({ text, color = ORANGE, className = "" }: { text: string; color?: string; className?: string }) {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg viewBox="0 0 100 100" className="w-24 h-24 animate-[spin_24s_linear_infinite]">
        <polygon
          points={Array.from({ length: 24 })
            .map((_, i) => {
              const r = i % 2 === 0 ? 50 : 38;
              const a = (i * Math.PI) / 12;
              return `${50 + r * Math.cos(a)},${50 + r * Math.sin(a)}`;
            })
            .join(" ")}
          fill={color}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-center text-[11px] font-bold leading-tight px-3"
        style={{ color: CREAM, fontFamily: "'Archivo', sans-serif" }}
      >
        {text}
      </span>
    </div>
  );
}

function Stamp({ text }: { text: string }) {
  return (
    <span
      className="inline-block border-4 rounded px-2 py-0.5 text-xs font-bold tracking-widest uppercase rotate-[-6deg] opacity-80"
      style={{ borderColor: ORANGE, color: ORANGE, fontFamily: "'Courier Prime', monospace" }}
    >
      {text}
    </span>
  );
}

function CouponCTA({ children, color = AVOCADO }: { children: React.ReactNode; color?: string }) {
  return (
    <button
      className="relative border-2 border-dashed px-6 py-3 text-sm font-bold uppercase tracking-widest transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[4px_4px_0_rgba(74,46,21,0.9)] active:translate-y-0 active:shadow-none"
      style={{
        borderColor: color,
        color: CREAM,
        background: color,
        fontFamily: "'Archivo', sans-serif",
        boxShadow: "3px 3px 0 rgba(74,46,21,0.55)",
      }}
    >
      ✂ - - {children} - - →
    </button>
  );
}

function ClassifiedAd({ job }: { job: (typeof JOB_CARDS)[number] }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="break-inside-avoid mb-6 border-2 p-4 transition-all duration-200 hover:shadow-[6px_6px_0_rgba(74,46,21,0.35)] hover:-translate-y-0.5"
      style={{ borderColor: BROWN, background: "#FBF6E6" }}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-lg font-bold leading-tight" style={{ color: BROWN, fontFamily: "'Courier Prime', monospace" }}>
          {job.employer.toUpperCase()} — {job.sector}
        </h4>
        {job.status === "CONDITIONAL" && <Stamp text="Conditional" />}
      </div>
      <p className="mt-2 text-sm leading-snug" style={{ color: "#3a2a18", fontFamily: "'Courier Prime', monospace" }}>
        <strong>WORKPLACE:</strong> {job.workplace}. <strong>WORK:</strong> {job.work}
      </p>
      {open && (
        <div className="mt-2 text-sm leading-snug space-y-1" style={{ color: "#3a2a18", fontFamily: "'Courier Prime', monospace" }}>
          <p><strong>DRIVING IT:</strong> {job.drivers.join("; ")}.</p>
          <p><strong>OUTREACH WINDOW:</strong> {job.window}.</p>
          <p><strong>GOOD FIT FOR:</strong> {job.fit.join(", ")}.</p>
          <p className="italic">Qualification is explainable, never a %. Cards stay Conditional until there is evidence.</p>
        </div>
      )}
      <button
        onClick={() => setOpen((v) => !v)}
        className="mt-3 text-xs font-bold uppercase tracking-widest underline decoration-2 underline-offset-4"
        style={{ color: ORANGE, fontFamily: "'Archivo', sans-serif" }}
      >
        {open ? "▲ Less" : "▼ Full particulars"}
      </button>
    </div>
  );
}

export default function HelpWanted() {
  return (
    <div
      className="min-h-screen pb-24"
      style={{
        background: CREAM,
        backgroundImage: `url(${ASSETS.paper})`,
        backgroundBlendMode: "multiply",
        fontFamily: "'Archivo', sans-serif",
        color: BROWN,
      }}
    >
      {/* Masthead */}
      <header className="border-b-8 double" style={{ borderColor: BROWN }}>
        <div className="max-w-6xl mx-auto px-4 pt-6">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-widest" style={{ color: AVOCADO }}>
            <span>Vol. 76 — No. 9</span>
            <span>The Robot Employment Gazette</span>
            <span>Price: FREE!</span>
          </div>
          <div className="flex items-end justify-between gap-4 py-4 flex-wrap">
            <h1
              className="text-5xl md:text-7xl leading-none"
              style={{ fontFamily: "'Shrikhand', serif", color: AVOCADO, textShadow: `3px 3px 0 ${GOLD}` }}
            >
              ReadyForRobots
            </h1>
            <img src={ASSETS.groovyRobot} alt="Friendly 1970s robot" className="w-24 h-24 md:w-32 md:h-32 object-contain" />
          </div>
          <nav className="flex flex-wrap gap-x-6 gap-y-1 pb-3 text-sm font-bold uppercase tracking-widest">
            {["Jobs", "About", "CRM", "Sign In"].map((n) => (
              <a key={n} href="#" onClick={(e) => e.preventDefault()} className="hover:underline decoration-4 underline-offset-4 transition-all" style={{ color: ORANGE, textDecorationColor: GOLD }}>
                {n}
              </a>
            ))}
          </nav>
        </div>
        <WavyStripes />
      </header>

      <main className="max-w-6xl mx-auto px-4">
        {/* Hero — Who is this visit? */}
        <section className="py-10 border-b-4" style={{ borderColor: BROWN }}>
          <div className="flex items-start gap-6 flex-wrap">
            <div className="flex-1 min-w-[280px]">
              <p className="text-sm font-bold uppercase tracking-[0.3em]" style={{ color: ORANGE }}>
                ★ Attention robot owners & employers ★
              </p>
              <h2
                className="mt-2 text-4xl md:text-6xl leading-[1.05]"
                style={{ fontFamily: "'Shrikhand', serif", color: BROWN }}
              >
                Who is this <span style={{ color: ORANGE }}>visit?</span>
              </h2>
              <p className="mt-4 text-lg max-w-xl" style={{ fontFamily: "'Courier Prime', monospace" }}>
                Jobs for a robot you already have, or robots for work you need done.
                Robots need jobs. We find the work.
              </p>
            </div>
            <Starburst text="5 JOBS FREE!" className="shrink-0" />
          </div>

          <div className="mt-8 grid md:grid-cols-2 gap-6">
            <div className="border-4 p-6 relative" style={{ borderColor: AVOCADO, background: "#EDF2DC" }}>
              <Starburst text="ROBOT OWNERS" color={AVOCADO} className="absolute -top-8 -right-4 scale-75" />
              <h3 className="text-2xl" style={{ fontFamily: "'Shrikhand', serif", color: AVOCADO }}>
                Look for robot jobs
              </h3>
              <p className="mt-2" style={{ fontFamily: "'Courier Prime', monospace" }}>
                Paste a product URL, or pick a named catalog robot. We match it to real jobs.
              </p>
              <div className="mt-5">
                <CouponCTA color={AVOCADO}>Look for robot jobs</CouponCTA>
              </div>
            </div>
            <div className="border-4 p-6 relative" style={{ borderColor: ORANGE, background: "#F9E8D8" }}>
              <Starburst text="EMPLOYERS" color={ORANGE} className="absolute -top-8 -right-4 scale-75" />
              <h3 className="text-2xl" style={{ fontFamily: "'Shrikhand', serif", color: ORANGE }}>
                Look for robot candidates
              </h3>
              <p className="mt-2" style={{ fontFamily: "'Courier Prime', monospace" }}>
                Tell us the work. We match named catalog robots. Then you can post the job.
              </p>
              <div className="mt-5">
                <CouponCTA color={ORANGE}>Look for robot candidates</CouponCTA>
              </div>
            </div>
          </div>
        </section>

        {/* How it works — 3 steps */}
        <section className="py-10 border-b-4" style={{ borderColor: BROWN }}>
          <h2 className="text-3xl md:text-4xl" style={{ fontFamily: "'Shrikhand', serif", color: AVOCADO }}>
            How Jobs works — easy as 1 · 2 · 3
          </h2>
          <div className="mt-6 grid md:grid-cols-3 gap-6">
            {STEPS.map((s, i) => (
              <div key={s.n} className="relative border-2 p-5 pt-8" style={{ borderColor: BROWN, background: "#FBF6E6" }}>
                <span
                  className="absolute -top-5 left-4 w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold"
                  style={{ background: [AVOCADO, GOLD, ORANGE][i], color: CREAM, fontFamily: "'Shrikhand', serif" }}
                >
                  {s.n}
                </span>
                <h3 className="text-xl font-bold" style={{ fontFamily: "'Shrikhand', serif", color: BROWN }}>{s.title}</h3>
                <p className="mt-2 text-sm" style={{ fontFamily: "'Courier Prime', monospace" }}>{s.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Classifieds */}
        <section className="py-10 border-b-4" style={{ borderColor: BROWN }}>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="text-3xl md:text-4xl" style={{ fontFamily: "'Shrikhand', serif", color: ORANGE }}>
              Help Wanted — This Week’s Openings
            </h2>
            <Stamp text="Updated Weekly" />
          </div>
          <p className="mt-2 text-sm uppercase tracking-widest font-bold" style={{ color: AVOCADO }}>
            Employer · Workplace · Work — cards stay Conditional until evidence
          </p>
          <div className="mt-6 columns-1 md:columns-2 lg:columns-3 gap-6">
            {JOB_CARDS.map((j) => (
              <ClassifiedAd key={j.id} job={j} />
            ))}
            {/* Decorative ad */}
            <div
              className="break-inside-avoid mb-6 border-2 p-4 text-center"
              style={{ borderColor: GOLD, background: "#FDF3D8" }}
            >
              <p className="text-2xl" style={{ fontFamily: "'Shrikhand', serif", color: GOLD }}>WANTED</p>
              <p className="mt-1 text-sm" style={{ fontFamily: "'Courier Prime', monospace" }}>
                One (1) reliable robot. Good pay, honest work. No category guesses — we read the SKU.
                Apply within.
              </p>
              <div className="mt-3">
                <CouponCTA color={GOLD}>Clip this coupon</CouponCTA>
              </div>
            </div>
          </div>
        </section>

        {/* Definitions */}
        <section className="py-10">
          <h2 className="text-3xl md:text-4xl" style={{ fontFamily: "'Shrikhand', serif", color: BROWN }}>
            Know your terms
          </h2>
          <div className="mt-6 grid md:grid-cols-2 gap-x-10 gap-y-4">
            {DEFINITIONS.map((d, i) => (
              <div key={d.term} className="flex gap-4 items-baseline border-b-2 border-dotted pb-3" style={{ borderColor: [AVOCADO, GOLD, ORANGE, BROWN][i] }}>
                <span className="text-lg font-bold shrink-0" style={{ fontFamily: "'Shrikhand', serif", color: [AVOCADO, GOLD, ORANGE, BROWN][i] }}>
                  {d.term}
                </span>
                <span className="text-sm" style={{ fontFamily: "'Courier Prime', monospace" }}>{d.def}</span>
              </div>
            ))}
          </div>
          <div className="mt-10 flex flex-wrap items-center gap-6">
            <CouponCTA color={AVOCADO}>Start free workspace</CouponCTA>
            <CouponCTA color={ORANGE}>Download the 2026 briefing</CouponCTA>
            <p className="text-xs uppercase tracking-widest font-bold" style={{ color: BROWN }}>
              © 1976 ReadyForRobots · Jobs for your robot · support@readyforrobots.com
            </p>
          </div>
        </section>
      </main>
      <ConceptBanner />
    </div>
  );
}
