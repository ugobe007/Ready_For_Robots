import { useState } from "react";
import { Link } from "wouter";
import { ArrowRight, ShieldCheck, Zap, Eye, Cpu, Lock, Battery, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";

// ── Data ─────────────────────────────────────────────────────────────────────

const CRITERIA = [
  {
    number: "01",
    icon: Cpu,
    color: "#93c5fd",
    bg: "rgba(96,165,250,0.08)",
    border: "rgba(96,165,250,0.2)",
    label: "Technology & Basic Abilities",
    summary: "Sensors, manipulation, walking speed, and gripping force.",
    description:
      "Examines the installed hardware and software stack and tests foundational physical capabilities. This determines the robot's technological potential before evaluating complex tasks.",
    tests: [
      "Sensor stack audit (vision, audio, text & speech recognition, human detection)",
      "Manipulation assessment — gripper type, finger count, degrees of freedom",
      "Walking speed measurement via 3D Vicon tracker",
      "Gripping force and maximum payload tests",
    ],
    g1Results: [
      { label: "Walking (slow)", value: "0.49 m/s (1.1 mph)" },
      { label: "Walking (fast)", value: "0.84 m/s (1.9 mph)" },
      { label: "Dexterity", value: "Below human level — requires additional software" },
      { label: "Arm endurance", value: "1–2 min before actuator overheat at full extension" },
    ],
    standard: null,
    verdict: "Current humanoids require significant software work before autonomous task execution is viable.",
  },
  {
    number: "02",
    icon: Zap,
    color: "#10b981",
    bg: "rgba(5,150,105,0.08)",
    border: "rgba(167,139,250,0.2)",
    label: "Complex Abilities",
    summary: "Whole-body movement, navigation, obstacle courses, and precision control.",
    description:
      "Tests combined use of technologies across realistic task domains. Intentionally designed to exceed current capabilities — establishing a forward-compatible benchmark across generations.",
    tests: [
      "Whole-body movements: running, jumping, climbing, ramp navigation",
      "Manipulative tasks: opening doors, object retrieval",
      "Obstacle course navigation",
      "Precision and force control under varying loads",
    ],
    g1Results: [
      { label: "Stair climbing", value: "Not supported per manufacturer specs" },
      { label: "Ramp stability (20% incline)", value: "Good — no balance loss recorded" },
      { label: "Floor recovery", value: "Requires high-friction surface — fails on tile/hardwood" },
      { label: "Obstacle course", value: "Not feasible with onboard abilities" },
    ],
    standard: null,
    verdict: "Most complex benchmarks are forward-looking. Only future hardware generations will fully pass — by design.",
  },
  {
    number: "03",
    icon: Eye,
    color: "#34d399",
    bg: "rgba(52,211,153,0.08)",
    border: "rgba(52,211,153,0.2)",
    label: "Cleanliness",
    summary: "Particle emissions, outgassing, and hygienic design for sensitive environments.",
    description:
      "Evaluates whether the robot can operate in semiconductor, pharmaceutical, food, or biotech production without causing contamination. Fraunhofer IPA has qualified 3,000+ automation components under ISO 14644.",
    tests: [
      "Particle emission testing per ISO 14644-14",
      "Outgassing measurement per ISO 14644-15",
      "Cleanability and hygienic design assessment",
    ],
    g1Results: [
      { label: "Particle emissions", value: "Compliant with ISO Class 5 cleanrooms" },
      { label: "Outgassing", value: "Promising — no critical contamination detected" },
      {
        label: "Hygienic design",
        value: "Not suitable for high-hygiene environments — joints have inaccessible gaps",
      },
    ],
    standard: "ISO 14644-14 / ISO 14644-15",
    verdict: "Suitable for semiconductor cleanrooms but not food or pharma environments without hardware modifications.",
  },
  {
    number: "04",
    icon: ShieldCheck,
    color: "#fbbf24",
    bg: "rgba(251,191,36,0.08)",
    border: "rgba(251,191,36,0.2)",
    label: "Functional Safety",
    summary: "Collision forces, stability, emergency stop, and human co-working risk.",
    description:
      "Humanoids are designed to operate alongside humans. This section measures actual collision forces, stability across surfaces, and compliance with human-robot collaboration safety standards. The ISO standard for humanoids (ISO 25785-1) is not expected until 2028.",
    tests: [
      "Collision force measurement — arm movements and full-body contact",
      "Slope stability testing (ramp walking, stops, direction changes)",
      "Multi-surface stability (steps, cable ducts, approach angles)",
      "Emergency stop accessibility audit",
    ],
    g1Results: [
      {
        label: "Collision force (full-body)",
        value: "> 500 N — exceeds ISO TS 15066 pain thresholds",
        warn: true,
      },
      { label: "Surface stability", value: "Strong — difficult to destabilize even on challenging surfaces" },
      { label: "Emergency stop", value: "No physical E-stop — must remove battery to cut power", warn: true },
      { label: "Joint pinch points", value: "Improvement needed at joint edges" },
    ],
    standard: "ISO 10218 / ISO TS 15066 (cobots) — ISO 25785-1 for humanoids expected 2028",
    verdict: "Not safe for unguarded human co-working at current collision forces. Requires case-by-case risk assessment.",
  },
  {
    number: "05",
    icon: Lock,
    color: "#f87171",
    bg: "rgba(248,113,113,0.08)",
    border: "rgba(248,113,113,0.2)",
    label: "Cybersecurity",
    summary: "Vulnerability analysis, secure lifecycle, network interfaces, and penetration resistance.",
    description:
      "As network-connected devices that receive regular updates, humanoids present an expanding attack surface. This module covers four areas: vulnerability management, software lifecycle, network security, and operational resilience.",
    tests: [
      "Known vulnerability analysis (CVE database review)",
      "Software update handling and end-of-life policy review",
      "Network interface security (WiFi, Bluetooth, cloud connections)",
      "Load testing and penetration resistance",
    ],
    g1Results: [
      {
        label: "Bluetooth vulnerability",
        value: "Remote code execution found — patched in later firmware",
        warn: true,
      },
      {
        label: "Data transmission",
        value: "Continuous sensor data sent to manufacturer — no disable option documented",
        warn: true,
      },
      { label: "Update transparency", value: "No published EOL or patch schedule" },
      { label: "Load stability", value: "Performed well under stress testing" },
    ],
    standard: null,
    verdict: "Significant data governance and vulnerability disclosure gaps. Require contractual commitments from vendors before deployment.",
  },
  {
    number: "06",
    icon: Battery,
    color: "#6ee7b7",
    bg: "rgba(52,211,153,0.05)",
    border: "rgba(110,231,183,0.2)",
    label: "Energy Efficiency",
    summary: "Power consumption by mode, battery runtime, and charging behavior.",
    description:
      "Battery life determines operational window and shift planning. This benchmark measures real power draw across defined scenarios (standing, walking flat, walking uphill, carrying load) to produce a standardized energy metric.",
    tests: [
      "Power consumption in standing, walking flat, walking uphill, and loaded scenarios",
      "Power-on / power-off cycle measurement",
      "Battery charge time and degradation curve",
    ],
    g1Results: [
      { label: "Standing power", value: "~154 W avg" },
      { label: "Walking (flat)", value: "~272 W avg" },
      { label: "Walking (10% incline)", value: "~283 W avg" },
      { label: "Typical scenario avg", value: "~239 W" },
      { label: "Battery life (standing)", value: "2 h 49 min" },
      { label: "Battery life (typical)", value: "1 h 49 min" },
    ],
    standard: null,
    verdict: "Under 2-hour battery life in active operation. Multi-shift deployments require battery swaps or charging infrastructure.",
  },
];

const BUYERS_CHECKLIST = [
  "Request independent benchmark results — not just vendor marketing demos",
  "Test collision forces against ISO TS 15066 before any human co-working application",
  "Ask for a written cybersecurity disclosure: known CVEs, EOL policy, data transmission practices",
  "Define your floor surface conditions — recovery and stability vary significantly",
  "Confirm cleanroom or hygiene requirements before procurement",
  "Model charging cycles into shift planning — assume ~1.5–2 hour active windows per charge",
  "Get contractual software update commitments — current humanoids are early-stage products",
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function Benchmark() {
  const [expanded, setExpanded] = useState<number | null>(null);

  const toggle = (i: number) => setExpanded(expanded === i ? null : i);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-gray-900">
      <Header />

      {/* ── Hero ── */}
      <section className="mx-auto max-w-5xl px-4 pt-24 pb-16 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-gray-200 px-4 py-1.5 text-[11px] font-bold uppercase tracking-widest text-gray-500">
          Buyer Evaluation Guide
        </div>
        <h1
          className="mb-5 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl"
         
        >
          How to benchmark a<br />
          <span style={{ color: "#10b981" }}>humanoid robot</span>
        </h1>
        <p className="mx-auto max-w-2xl text-base text-gray-500 leading-relaxed">
          Most vendors show demos. Independent benchmarks show reality. Fraunhofer IPA — one of Europe's
          largest applied research institutes — developed a six-criteria test framework for humanoids.
          This is what every buyer should ask for before deploying.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-[12px] text-gray-400">
          <span>Source: Fraunhofer IPA, May 2026</span>
          <span className="text-gray-300">·</span>
          <a
            href="https://www.therobotreport.com/fraunhofer-ipa-offers-new-test-benchmark-for-humanoid-robots/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 hover:text-gray-600 transition-colors"
          >
            Original article <ExternalLink className="h-3 w-3" />
          </a>
          <span className="text-gray-300">·</span>
          <span>Reference robot: Unitree G1</span>
        </div>
      </section>

      {/* ── Six criteria ── */}
      <section className="mx-auto max-w-4xl px-4 pb-16 space-y-3">
        {CRITERIA.map((c, i) => {
          const Icon = c.icon;
          const open = expanded === i;
          return (
            <div
              key={i}
              className={`rounded-2xl border overflow-hidden transition-all bg-white shadow-sm ${open ? "ring-1 ring-emerald-100" : ""}`}
              style={{ borderColor: open ? c.border : "rgba(15,23,42,0.08)" }}
            >
              {/* Header row */}
              <button
                type="button"
                onClick={() => toggle(i)}
                className="w-full flex items-center gap-4 px-6 py-5 text-left"
              >
                <span
                  className="shrink-0 flex items-center justify-center rounded-xl w-10 h-10 font-mono text-[11px] font-bold"
                  style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}` }}
                >
                  {c.number}
                </span>
                <Icon className="h-5 w-5 shrink-0" style={{ color: c.color }} />
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-gray-900 text-[15px]">{c.label}</p>
                  <p className="text-[12px] text-gray-500 mt-0.5">{c.summary}</p>
                </div>
                {open ? (
                  <ChevronUp className="h-4 w-4 text-gray-400 shrink-0" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" />
                )}
              </button>

              {/* Expanded detail */}
              {open && (
                <div className="px-6 pb-6 space-y-5 border-t border-gray-100 pt-5">
                  <p className="text-sm text-gray-500 leading-relaxed">{c.description}</p>

                  {c.standard && (
                    <p className="text-[11px] font-mono text-gray-400">
                      Standard: <span className="text-gray-500">{c.standard}</span>
                    </p>
                  )}

                  {/* Tests */}
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">What is tested</p>
                    <ul className="space-y-1.5">
                      {c.tests.map((t, j) => (
                        <li key={j} className="flex items-start gap-2 text-[12px] text-gray-500">
                          <span className="mt-1.5 h-1 w-1 rounded-full shrink-0" style={{ background: c.color }} />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* G1 results */}
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">
                      Unitree G1 results (reference)
                    </p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {c.g1Results.map((r, j) => (
                        <div
                          key={j}
                          className="rounded-xl px-3 py-2.5"
                          style={{
                            background: r.warn ? "rgba(248,113,113,0.07)" : "rgba(255,255,255,0.03)",
                            border: r.warn ? "1px solid rgba(248,113,113,0.2)" : "1px solid rgba(255,255,255,0.06)",
                          }}
                        >
                          <p className="text-[10px] text-gray-400 mb-0.5">{r.label}</p>
                          <p className="text-[12px] font-semibold" style={{ color: r.warn ? "#f87171" : "rgba(255,255,255,0.75)" }}>
                            {r.value}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Verdict */}
                  <div
                    className="rounded-xl px-4 py-3"
                    style={{ background: `${c.color}0d`, border: `1px solid ${c.border}` }}
                  >
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: c.color }}>
                      Buyer takeaway
                    </p>
                    <p className="text-[12px] text-gray-600">{c.verdict}</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </section>

      {/* ── Buyer checklist ── */}
      <section
        className="mx-auto max-w-4xl px-4 pb-16"
      >
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-8">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-emerald-700">
            Before you buy
          </div>
          <h2 className="font-display text-2xl font-extrabold text-gray-900 mb-6">
            7 questions every buyer should ask
          </h2>
          <ul className="space-y-3">
            {BUYERS_CHECKLIST.map((item, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="shrink-0 flex items-center justify-center rounded-full w-5 h-5 text-[10px] font-bold mt-0.5 bg-emerald-100 text-emerald-700">
                  {i + 1}
                </span>
                <p className="text-sm text-gray-600 leading-relaxed">{item}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-4 pb-12 text-center">
        <div className="rounded-2xl border border-gray-200 bg-white px-8 py-12 shadow-sm">
          <h2 className="font-display text-2xl font-extrabold text-gray-900 mb-3">
            Ready to find the right robot for your operation?
          </h2>
          <p className="text-sm text-gray-500 mb-7 max-w-lg mx-auto">
            Ready For Robots matches buyer requirements to vetted robot vendors — with signal data, not demos.
            We know which vendors are deploying in your industry right now.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/find-robots"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-bold text-white hover:bg-emerald-700"
            >
              Find robots <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/intelligence"
              className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-6 py-3 text-sm font-bold text-gray-700 hover:bg-gray-50"
            >
              View market intelligence
            </Link>
          </div>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
