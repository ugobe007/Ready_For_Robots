/**
 * DARK NAVY + SUSAN KARE MACINTOSH ICON LANGUAGE
 * Base: the current site's dark navy. Accent: Kare's 1-bit Macintosh world —
 * pixel-drawn icons, hard square edges, 50% dither fills, window-chrome title
 * bars, Chicago-style UI type (Silkscreen). EB Garamond serif for headlines
 * only. No rainbow stripes, no rounded pills, no soft shadows.
 * Interaction: instant inverse-video hovers (like 1-bit Mac selection),
 * 2px hard offset shadows, no easing curves on state changes.
 */
import { useState } from "react";
import { DEFINITIONS, JOB_CARDS, STEPS } from "@/lib/jobs";

/* ── palette ─────────────────────────────────────────────── */
const NAVY = "#0A0F1E";
const NAVY_2 = "#0D1426";
const PANEL = "#111A30";
const GREEN = "#2EE6A8";
const INK = "#E8EEF7";
const MUTED = "#8B98B0";
const LINE = "rgba(139,152,176,0.22)";

/** 50% checkerboard dither — the signature Kare fill */
const DITHER =
  "repeating-conic-gradient(rgba(139,152,176,0.13) 0% 25%, transparent 0% 50%) 0 0 / 4px 4px";
const DITHER_GREEN =
  "repeating-conic-gradient(rgba(46,230,168,0.14) 0% 25%, transparent 0% 50%) 0 0 / 4px 4px";

const HEADLINE_OPTIONS = [
  { id: "A", headline: "Robots need jobs. We find the work.", note: "The existing tagline, promoted to headline. States the mission plainly." },
  { id: "B", headline: "Find the work your robot was built to do.", note: "Action-oriented, speaks to robot owners first." },
  { id: "C", headline: "The job board for robots.", note: "Six words. Instantly explains what the product is." },
  { id: "D", headline: "Put your robot to work.", note: "Short imperative with a clear payoff." },
  { id: "E", headline: "Real jobs, matched to real machines.", note: "Emphasizes evidence-based matching, not category guesses." },
] as const;

/* ── 1-bit pixel art (Kare-style, drawn on strict grids) ── */

/** Pixel robot face — the brand mark. 12×12 grid. */
function PixelRobot({ size = 32, color = GREEN }: { size?: number; color?: string }) {
  const cells: Array<[number, number]> = [
    // antenna
    [5, 0], [6, 0], [5, 1], [6, 1],
    // head outline
    ...([2, 3, 4, 5, 6, 7, 8, 9] as const).map((x) => [x, 2] as [number, number]),
    ...([2, 3, 4, 5, 6, 7, 8, 9] as const).map((x) => [x, 9] as [number, number]),
    ...([3, 4, 5, 6, 7, 8] as const).map((y) => [1, y] as [number, number]),
    ...([3, 4, 5, 6, 7, 8] as const).map((y) => [10, y] as [number, number]),
    // eyes
    [3, 4], [4, 4], [7, 4], [8, 4],
    // smile
    [3, 7], [4, 7], [5, 7], [6, 7], [7, 7], [8, 7],
  ];
  const px = 100 / 12;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" shapeRendering="crispEdges" aria-hidden>
      {cells.map(([x, y], i) => (
        <rect key={i} x={x * px} y={y * px} width={px} height={px} fill={color} />
      ))}
    </svg>
  );
}

/** Pixel briefcase — employer/work icon. */
function PixelBriefcase({ size = 28, color = INK }: { size?: number; color?: string }) {
  const rows = [
    "....XXXX....",
    "...X....X...",
    "...X....X...",
    ".XXXXXXXXXX.",
    ".X....X...X.",
    ".XXXXXXXXXX.",
    ".X........X.",
    ".X........X.",
    ".XXXXXXXXXX.",
  ];
  return <PixelGrid rows={rows} size={size} color={color} />;
}

/** Pixel document — job card icon. */
function PixelDoc({ size = 28, color = INK }: { size?: number; color?: string }) {
  const rows = [
    ".XXXXXXXX...",
    ".X......X...",
    ".X.XXXX.X...",
    ".X......X...",
    ".X.XXXX.X...",
    ".X......X...",
    ".X.XXXX.X...",
    ".X......X...",
    ".XXXXXXXX...",
  ];
  return <PixelGrid rows={rows} size={size} color={color} />;
}

/** Pixel hand/pointer — CTA icon. */
function PixelHand({ size = 28, color = INK }: { size?: number; color?: string }) {
  const rows = [
    "..XX........",
    ".X..X.......",
    ".X..X.XXX...",
    ".X..XX...XX.",
    ".X..X......X",
    "..X........X",
    "...X......X.",
    "....X....X..",
    ".....XXXX...",
  ];
  return <PixelGrid rows={rows} size={size} color={color} />;
}

function PixelGrid({ rows, size, color }: { rows: string[]; size: number; color: string }) {
  const w = rows[0].length;
  const h = rows.length;
  const px = 100 / Math.max(w, h);
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" shapeRendering="crispEdges" aria-hidden>
      {rows.flatMap((row, y) =>
        row.split("").map((c, x) =>
          c === "X" ? <rect key={`${x}-${y}`} x={x * px} y={y * px} width={px} height={px} fill={color} /> : null
        )
      )}
    </svg>
  );
}

/* ── primitives ──────────────────────────────────────────── */

/** Chicago-style label */
function Chip({ children, color = GREEN }: { children: React.ReactNode; color?: string }) {
  return (
    <p className="text-[11px] font-bold uppercase" style={{ color, fontFamily: "'Silkscreen', monospace", letterSpacing: "0.12em" }}>
      {children}
    </p>
  );
}

/** Hard-edged button: 2px offset shadow, inverts on hover like 1-bit selection */
function MacButton({
  children,
  primary = false,
}: {
  children: React.ReactNode;
  primary?: boolean;
}) {
  const [hov, setHov] = useState(false);
  const bg = primary ? (hov ? INK : GREEN) : hov ? GREEN : "transparent";
  const fg = primary ? (hov ? NAVY : NAVY) : hov ? NAVY : INK;
  return (
    <button
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      className="inline-flex items-center gap-2 px-5 py-2.5 text-[11px] font-bold uppercase transition-none"
      style={{
        fontFamily: "'Silkscreen', monospace",
        letterSpacing: "0.1em",
        background: bg,
        color: fg,
        border: `2px solid ${primary ? GREEN : LINE}`,
        boxShadow: hov ? `3px 3px 0 ${primary ? GREEN : MUTED}` : `3px 3px 0 rgba(0,0,0,0.55)`,
      }}
    >
      {children} <span aria-hidden>→</span>
    </button>
  );
}

/** Window-chrome title bar — the Mac window header strip */
function WindowBar({ title, right }: { title: string; right?: React.ReactNode }) {
  return (
    <div
      className="flex items-center justify-between px-3 py-2 border-b-2"
      style={{ borderColor: LINE, background: DITHER, backgroundColor: NAVY_2 }}
    >
      <div className="flex items-center gap-2">
        <span className="w-3 h-3 border-2" style={{ borderColor: MUTED }} aria-hidden />
        <span className="text-[10px] font-bold uppercase" style={{ fontFamily: "'Silkscreen', monospace", color: MUTED, letterSpacing: "0.12em" }}>
          {title}
        </span>
      </div>
      {right}
    </div>
  );
}

/* ── sections ────────────────────────────────────────────── */

function PathCard({
  label,
  title,
  body,
  cta,
  icon,
  primary = false,
}: {
  label: string;
  title: string;
  body: string;
  cta: string;
  icon: React.ReactNode;
  primary?: boolean;
}) {
  return (
    <div
      className="border-2"
      style={{
        borderColor: primary ? GREEN : LINE,
        background: PANEL,
        boxShadow: `4px 4px 0 rgba(0,0,0,0.55)`,
      }}
    >
      <WindowBar title={label} right={<span className="w-3 h-3" style={{ background: primary ? GREEN : "transparent", border: `2px solid ${primary ? GREEN : MUTED}` }} />} />
      <div className="p-6 md:p-8">
        <div className="flex items-start justify-between gap-4">
          <h3 className="text-2xl md:text-3xl font-semibold" style={{ fontFamily: "'EB Garamond', serif", color: INK }}>
            {title}
          </h3>
          <span className="shrink-0 mt-1">{icon}</span>
        </div>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: MUTED }}>{body}</p>
        <div className="mt-7">
          <MacButton primary={primary}>{cta}</MacButton>
        </div>
      </div>
    </div>
  );
}

function JobRow({ job, index }: { job: (typeof JOB_CARDS)[number]; index: number }) {
  const [open, setOpen] = useState(index === 0);
  return (
    <div className="border-2" style={{ borderColor: open ? GREEN : LINE, background: open ? PANEL : NAVY_2 }}>
      <button onClick={() => setOpen((v) => !v)} className="w-full text-left">
        <div className="flex items-center gap-3 md:gap-5 px-4 md:px-5 py-4">
          <span className="text-[10px] font-bold shrink-0 w-16" style={{ color: GREEN, fontFamily: "'Silkscreen', monospace" }}>
            {job.id}
          </span>
          <div className="flex-1 min-w-0">
            <p className="font-semibold truncate text-lg" style={{ fontFamily: "'EB Garamond', serif", color: INK }}>
              {job.employer}
            </p>
            <p className="text-[11px] truncate uppercase" style={{ color: MUTED, fontFamily: "'Silkscreen', monospace", letterSpacing: "0.08em" }}>
              {job.sector}
            </p>
          </div>
          <span
            className="hidden sm:inline-block text-[9px] font-bold uppercase px-2 py-1 shrink-0"
            style={{
              fontFamily: "'Silkscreen', monospace",
              letterSpacing: "0.1em",
              color: job.status === "OPEN" ? NAVY : MUTED,
              background: job.status === "OPEN" ? GREEN : "transparent",
              border: `2px solid ${job.status === "OPEN" ? GREEN : LINE}`,
            }}
          >
            {job.status}
          </span>
          <span style={{ color: GREEN, fontFamily: "'Silkscreen', monospace" }} aria-hidden>
            {open ? "▲" : "▼"}
          </span>
        </div>
      </button>
      {open && (
        <div className="border-t-2 px-4 md:px-5 pb-6 pt-4 grid md:grid-cols-2 gap-x-10 gap-y-4" style={{ borderColor: LINE, background: DITHER, backgroundColor: PANEL }}>
          {[
            ["Employer", `${job.employer} — ${job.sector}`],
            ["Workplace", job.workplace],
            ["Work", job.work],
            ["What's driving it", job.drivers.join(" · ")],
            ["Outreach window", job.window],
            ["Good fit for", job.fit.join(" · ")],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-[9px] font-bold uppercase" style={{ color: GREEN, fontFamily: "'Silkscreen', monospace", letterSpacing: "0.14em" }}>
                {k}
              </p>
              <p className="mt-1 text-sm leading-relaxed" style={{ color: INK }}>{v}</p>
            </div>
          ))}
          <p className="md:col-span-2 text-xs italic" style={{ color: MUTED, fontFamily: "'EB Garamond', serif" }}>
            Qualification is explainable — never a %. Cards stay Conditional until there is evidence.
          </p>
        </div>
      )}
    </div>
  );
}

/* ── page ────────────────────────────────────────────────── */
export default function Home() {
  const [headlineId, setHeadlineId] = useState<string>("A");
  const active = HEADLINE_OPTIONS.find((h) => h.id === headlineId) ?? HEADLINE_OPTIONS[0];

  return (
    <div className="min-h-screen" style={{ background: NAVY, color: INK, fontFamily: "'Archivo', sans-serif" }}>
      {/* ── Nav ── */}
      <header className="sticky top-0 z-40 border-b-2" style={{ borderColor: LINE, background: NAVY }}>
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <a href="#" onClick={(e) => e.preventDefault()} className="flex items-center gap-3">
            <PixelRobot />
            <span className="text-xl font-semibold tracking-tight" style={{ fontFamily: "'EB Garamond', serif" }}>
              ReadyForRobots
            </span>
          </a>
          <nav className="hidden md:flex items-center gap-7">
            {["Jobs", "About", "CRM"].map((n) => (
              <a
                key={n}
                href="#"
                onClick={(e) => e.preventDefault()}
                className="text-[11px] font-bold uppercase px-2 py-1 transition-none hover:bg-[#2EE6A8] hover:text-[#0A0F1E]"
                style={{ fontFamily: "'Silkscreen', monospace", letterSpacing: "0.12em", color: MUTED }}
              >
                {n}
              </a>
            ))}
            <button
              className="text-[11px] font-bold uppercase px-3 py-1.5 border-2 transition-none hover:bg-[#2EE6A8] hover:text-[#0A0F1E]"
              style={{ fontFamily: "'Silkscreen', monospace", letterSpacing: "0.12em", borderColor: GREEN, color: GREEN }}
            >
              Sign In
            </button>
          </nav>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative border-b-2" style={{ borderColor: LINE }}>
        <div className="absolute inset-0 pointer-events-none" aria-hidden style={{ background: DITHER_GREEN }} />
        <div className="relative max-w-6xl mx-auto px-4 pt-16 md:pt-24 pb-14">
          <Chip>ReadyForRobots · Robot Employment</Chip>
          <div className="mt-6 flex items-start gap-6 md:gap-10">
            <div className="flex-1 min-w-0">
              <h1
                className="text-5xl md:text-7xl font-medium leading-[1.04] tracking-tight max-w-3xl"
                style={{ fontFamily: "'EB Garamond', serif" }}
              >
                {active.headline.split(". ").map((part, i, arr) => (
                  <span key={i}>
                    <span style={i === arr.length - 1 ? { color: GREEN } : undefined}>
                      {part}
                      {i < arr.length - 1 ? ". " : ""}
                    </span>
                  </span>
                ))}
              </h1>
              <p className="mt-6 max-w-xl text-base md:text-lg leading-relaxed" style={{ color: MUTED }}>
                Jobs for a robot you already have, or robots for work you need done.
                Paste a product URL — we match it to real jobs, then keep them in CRM.
              </p>
            </div>
            {/* Hero icon tile — Kare-style framed icon */}
            <div
              className="hidden md:flex shrink-0 w-36 h-36 items-center justify-center border-2"
              style={{ borderColor: GREEN, background: DITHER_GREEN, backgroundColor: NAVY_2, boxShadow: "4px 4px 0 rgba(0,0,0,0.55)" }}
              aria-hidden
            >
              <PixelRobot size={88} />
            </div>
          </div>

          {/* headline switcher */}
          <div className="mt-10 border-2" style={{ borderColor: LINE, background: NAVY_2 }}>
            <WindowBar title="headline-options — replaces “who is this visit?”" />
            <div className="p-4 flex flex-wrap items-center gap-2">
              {HEADLINE_OPTIONS.map((h) => (
                <button
                  key={h.id}
                  onClick={() => setHeadlineId(h.id)}
                  className="w-9 h-9 text-[11px] font-bold border-2 transition-none"
                  style={{
                    fontFamily: "'Silkscreen', monospace",
                    borderColor: h.id === headlineId ? GREEN : LINE,
                    color: h.id === headlineId ? NAVY : MUTED,
                    background: h.id === headlineId ? GREEN : "transparent",
                  }}
                >
                  {h.id}
                </button>
              ))}
              <span className="text-xs ml-1 max-w-md" style={{ color: MUTED }}>{active.note}</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Split path cards ── */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-6">
          <PathCard
            label="Robot owner"
            title="Look for robot jobs"
            body="Paste a product URL, or pick a named catalog robot. We read the SKU — not a category guess — and match it to real jobs."
            cta="Look for robot jobs"
            icon={<PixelRobot size={40} color={GREEN} />}
            primary
          />
          <PathCard
            label="Employer"
            title="Look for robot candidates"
            body="Tell us the work. We match named catalog robots from the ontology. Then you can post the job."
            cta="Look for robot candidates"
            icon={<PixelBriefcase size={40} color={MUTED} />}
          />
        </div>
      </section>

      {/* ── Steps ── */}
      <section className="border-y-2" style={{ borderColor: LINE, background: NAVY_2 }}>
        <div className="max-w-6xl mx-auto px-4 py-16">
          <Chip>How Jobs works</Chip>
          <h2 className="mt-4 text-3xl md:text-5xl font-medium tracking-tight" style={{ fontFamily: "'EB Garamond', serif" }}>
            Three steps. No buyer pipeline.
          </h2>
          <div className="mt-10 grid md:grid-cols-3 gap-6">
            {STEPS.map((s) => (
              <div key={s.n} className="border-2" style={{ borderColor: LINE, background: PANEL, boxShadow: "4px 4px 0 rgba(0,0,0,0.45)" }}>
                <WindowBar title={`step ${s.n}`} right={<span className="text-[10px] font-bold" style={{ color: GREEN, fontFamily: "'Silkscreen', monospace" }}>{s.n}</span>} />
                <div className="p-6">
                  <h3 className="text-xl font-semibold" style={{ fontFamily: "'EB Garamond', serif" }}>{s.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed" style={{ color: MUTED }}>{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Job cards ── */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <Chip>Jobs brief · This week</Chip>
            <h2 className="mt-4 text-3xl md:text-5xl font-medium tracking-tight" style={{ fontFamily: "'EB Garamond', serif" }}>
              Work robots can take
            </h2>
          </div>
          <p className="text-[10px] max-w-xs uppercase" style={{ color: MUTED, fontFamily: "'Silkscreen', monospace", letterSpacing: "0.1em" }}>
            5 jobs on free. Cards stay Conditional until evidence.
          </p>
        </div>
        <div className="mt-8 space-y-4">
          {JOB_CARDS.map((j, i) => (
            <JobRow key={j.id} job={j} index={i} />
          ))}
        </div>
      </section>

      {/* ── Vocabulary ── */}
      <section className="border-y-2" style={{ borderColor: LINE, background: NAVY_2 }}>
        <div className="max-w-6xl mx-auto px-4 py-16">
          <Chip>Vocabulary</Chip>
          <h2 className="mt-4 text-3xl md:text-5xl font-medium tracking-tight" style={{ fontFamily: "'EB Garamond', serif" }}>
            Employer. Workplace. Work. Robot Job.
          </h2>
          <div className="mt-10 grid md:grid-cols-2 gap-6">
            {DEFINITIONS.map((d) => (
              <div key={d.term} className="border-2 p-5" style={{ borderColor: LINE, background: PANEL }}>
                <div className="flex items-center gap-3">
                  <PixelDoc size={22} color={GREEN} />
                  <h3 className="text-xl font-semibold" style={{ fontFamily: "'EB Garamond', serif" }}>{d.term}</h3>
                </div>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: MUTED }}>{d.def}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="border-2" style={{ borderColor: GREEN, background: PANEL, boxShadow: "6px 6px 0 rgba(0,0,0,0.55)" }}>
          <WindowBar title="readyforrobots — start" right={<PixelHand size={20} color={GREEN} />} />
          <div className="p-8 md:p-10 flex flex-wrap items-center gap-8 justify-between">
            <div>
              <h2 className="text-3xl md:text-4xl font-medium" style={{ fontFamily: "'EB Garamond', serif" }}>
                Robots need jobs. <span style={{ color: GREEN }}>We find the work.</span>
              </h2>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>
                Start a free workspace — 5 jobs, 5 CRM opportunities, no card required.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <MacButton primary>Start free workspace</MacButton>
              <MacButton>Download the 2026 briefing</MacButton>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t-2" style={{ borderColor: LINE }}>
        <div className="max-w-6xl mx-auto px-4 py-8 flex flex-wrap gap-x-10 gap-y-4 items-center justify-between">
          <div className="flex items-center gap-3">
            <PixelRobot size={22} />
            <span className="text-[10px] uppercase" style={{ color: MUTED, fontFamily: "'Silkscreen', monospace", letterSpacing: "0.1em" }}>
              © 2026 ReadyForRobots · Jobs for your robot
            </span>
          </div>
          <div className="flex gap-5">
            {["Pricing", "FAQ", "Privacy", "support@readyforrobots.com"].map((n) => (
              <a
                key={n}
                href="#"
                onClick={(e) => e.preventDefault()}
                className="text-[10px] font-bold uppercase px-1.5 py-0.5 transition-none hover:bg-[#2EE6A8] hover:text-[#0A0F1E]"
                style={{ color: MUTED, fontFamily: "'Silkscreen', monospace", letterSpacing: "0.1em" }}
              >
                {n}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
